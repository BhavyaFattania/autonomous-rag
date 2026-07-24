"""Tests for NodeEventRepository's durable per-tick event log, added so the
web dashboard can show what happened at every pipeline node instead of just
the experiment-level summary."""

import os
from pathlib import Path

import pytest
from src.storage.database import Database
from src.storage.models import NodeEvent
from src.storage.repositories.node_event_repository import NodeEventRepository


@pytest.fixture
def temp_db():
    # Project-local temp dir -- pytest's own tmp_path fixture hits a
    # PermissionError on this machine (see tests/test_storage.py for the
    # established workaround this fixture copies).
    base = Path("pytest_temp")
    base.mkdir(exist_ok=True)
    d = base / "node_event_repository_test"
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


async def _seed(path: str, **overrides) -> int:
    db = Database(path)
    await db.init()
    defaults = dict(
        run_id="run-1",
        experiment_uuid="uuid-1",
        experiment_seq=1,
        node="scientist",
        status="RUNNING",
        timestamp="2026-07-24T00:00:00+00:00",
    )
    defaults.update(overrides)
    return await NodeEventRepository().insert(NodeEvent(**defaults))


@pytest.mark.asyncio
async def test_find_by_experiment_uuid_returns_ticks_in_execution_order(temp_db):
    await _seed(temp_db, experiment_uuid="uuid-1", node="scientist")
    await _seed(temp_db, experiment_uuid="uuid-1", node="validator")
    await _seed(temp_db, experiment_uuid="uuid-2", node="scientist")

    rows = await NodeEventRepository().find_by_experiment_uuid("uuid-1")

    assert [row.node for row in rows] == ["scientist", "validator"]


@pytest.mark.asyncio
async def test_find_by_experiment_uuid_returns_empty_list_for_unknown_uuid(temp_db):
    await _seed(temp_db, experiment_uuid="uuid-1")

    rows = await NodeEventRepository().find_by_experiment_uuid("no-such-uuid")

    assert rows == []


@pytest.mark.asyncio
async def test_find_by_run_id_returns_only_matching_run_newest_first(temp_db):
    await _seed(temp_db, run_id="run-1", node="scientist", timestamp="t1")
    await _seed(temp_db, run_id="run-2", node="scientist", timestamp="t2")
    await _seed(temp_db, run_id="run-1", node="validator", timestamp="t3")

    rows = await NodeEventRepository().find_by_run_id("run-1")

    assert [row.node for row in rows] == ["validator", "scientist"]


@pytest.mark.asyncio
async def test_find_by_run_id_filters_by_node_and_status(temp_db):
    await _seed(temp_db, node="scientist", status="RUNNING")
    await _seed(temp_db, node="validator", status="RUNNING")
    await _seed(temp_db, node="validator", status="FAILED_VALIDATION")

    rows = await NodeEventRepository().find_by_run_id("run-1", node="validator")
    assert {row.status for row in rows} == {"RUNNING", "FAILED_VALIDATION"}

    rows = await NodeEventRepository().find_by_run_id("run-1", status="FAILED_VALIDATION")
    assert [row.node for row in rows] == ["validator"]


@pytest.mark.asyncio
async def test_find_by_run_id_paginates_with_before_id_cursor(temp_db):
    ids = [await _seed(temp_db, node=f"node-{i}") for i in range(5)]

    first_page = await NodeEventRepository().find_by_run_id("run-1", limit=2)
    assert [row.id for row in first_page] == [ids[4], ids[3]]

    second_page = await NodeEventRepository().find_by_run_id(
        "run-1", limit=2, before_id=first_page[-1].id
    )
    assert [row.id for row in second_page] == [ids[2], ids[1]]


@pytest.mark.asyncio
async def test_insert_round_trips_all_fields(temp_db):
    event_id = await _seed(
        temp_db,
        node="evaluator",
        status="RUNNING",
        cost_total_usd=1.23,
        message="Building index",
        hypothesis="larger chunks help",
        reasoning="recall trended up last 3 runs",
        config_json='{"chunk_size": 512}',
        metrics_json='{"median_weighted_score": 0.9}',
        failure_reason="",
        progress_current=64,
        progress_total=128,
        raw_event_json='{"evaluator": {"status": "RUNNING"}}',
    )

    [row] = await NodeEventRepository().find_by_experiment_uuid("uuid-1")

    assert row.id == event_id
    assert row.cost_total_usd == 1.23
    assert row.hypothesis == "larger chunks help"
    assert row.config_json == '{"chunk_size": 512}'
    assert row.progress_current == 64
    assert row.progress_total == 128
