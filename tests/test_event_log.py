"""Tests for the durable node-event log: an independent EventBus subscriber
that must persist every tick without ever affecting the live run."""

import asyncio
import os
from datetime import UTC, datetime
from pathlib import Path

import pytest
from src.core.events import EventBus, ExperimentEvent
from src.storage.database import Database
from src.storage.event_log import persist_events
from src.storage.repositories.node_event_repository import NodeEventRepository


@pytest.fixture
def temp_db():
    base = Path("pytest_temp")
    base.mkdir(exist_ok=True)
    d = base / "event_log_test"
    d.mkdir(exist_ok=True)
    path = str(d / "experiments.sqlite")

    old_default = Database.default_path
    Database.default_path = path
    yield path
    Database.default_path = old_default
    for suffix in ("", "-wal", "-shm"):
        p = Path(f"{path}{suffix}")
        if p.exists():
            os.remove(p)


def _event(**overrides) -> ExperimentEvent:
    defaults = dict(
        experiment=1,
        experiment_uuid="uuid-1",
        node="scientist",
        status="RUNNING",
        timestamp=datetime.now(UTC),
        cost_total_usd=0.0,
    )
    defaults.update(overrides)
    return ExperimentEvent(**defaults)


@pytest.mark.asyncio
async def test_persist_events_writes_published_ticks_to_node_events(temp_db):
    await Database().init()
    bus = EventBus()
    task = asyncio.create_task(persist_events(bus, run_id="run-1"))
    await asyncio.sleep(0)  # let persist_events reach bus.subscribe() before we publish

    bus.publish(_event(node="scientist", status="RUNNING", hypothesis="h"))
    bus.publish(_event(node="validator", status="RUNNING"))
    await asyncio.sleep(0.05)

    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    rows = await NodeEventRepository().find_by_experiment_uuid("uuid-1")
    assert [row.node for row in rows] == ["scientist", "validator"]
    assert rows[0].run_id == "run-1"
    assert rows[0].hypothesis == "h"


@pytest.mark.asyncio
async def test_persist_events_serializes_config_and_metrics_as_json(temp_db):
    await Database().init()
    bus = EventBus()
    task = asyncio.create_task(persist_events(bus, run_id="run-1"))
    await asyncio.sleep(0)  # let persist_events reach bus.subscribe() before we publish

    bus.publish(
        _event(
            node="evaluator",
            config={"chunk_size": 512},
            metrics={"median_weighted_score": 0.9},
        )
    )
    await asyncio.sleep(0.05)

    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    [row] = await NodeEventRepository().find_by_experiment_uuid("uuid-1")
    assert row.config_json == '{"chunk_size": 512}'
    assert row.metrics_json == '{"median_weighted_score": 0.9}'


@pytest.mark.asyncio
async def test_persist_events_skips_bad_tick_without_dying(temp_db, monkeypatch):
    await Database().init()
    bus = EventBus()

    calls = {"n": 0}
    real_insert = NodeEventRepository.insert

    async def _flaky_insert(self, event):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("disk full")
        return await real_insert(self, event)

    monkeypatch.setattr(NodeEventRepository, "insert", _flaky_insert)

    task = asyncio.create_task(persist_events(bus, run_id="run-1"))
    await asyncio.sleep(0)  # let persist_events reach bus.subscribe() before we publish
    bus.publish(_event(node="scientist"))
    bus.publish(_event(node="validator"))
    await asyncio.sleep(0.05)

    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    rows = await NodeEventRepository().find_by_experiment_uuid("uuid-1")
    assert [row.node for row in rows] == ["validator"]


@pytest.mark.asyncio
async def test_persist_events_serializes_writes_through_coordinator(temp_db):
    """With a WriteCoordinator injected, concurrent ticks are serialized onto
    one connection -- the fix that replaced the old lock-retry loop. Every
    published tick still lands, with no `database is locked`."""
    from src.storage.write_coordinator import WriteCoordinator

    await Database().init()
    writer = WriteCoordinator(temp_db)
    bus = EventBus()
    task = asyncio.create_task(persist_events(bus, run_id="run-1", writer=writer))
    await asyncio.sleep(0)

    for i in range(10):
        bus.publish(_event(node=f"node-{i}", status="RUNNING"))
    await asyncio.sleep(0.1)

    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    await writer.aclose()

    rows = await NodeEventRepository().find_by_experiment_uuid("uuid-1")
    assert len(rows) == 10
