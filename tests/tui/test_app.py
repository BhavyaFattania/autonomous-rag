"""Proves the TUI's event-queue worker updates the screen — the minimal
plumbing every later widget builds on."""

import asyncio
from datetime import UTC, datetime

import pytest
from src.core.events import ExperimentEvent
from src.tui.app import RagOptimizerApp


def _event(**overrides) -> ExperimentEvent:
    defaults = dict(
        experiment=1,
        node="scientist",
        status="RUNNING",
        timestamp=datetime.now(UTC),
        cost_total_usd=0.0,
    )
    defaults.update(overrides)
    return ExperimentEvent(**defaults)


@pytest.mark.asyncio
async def test_app_updates_status_from_queued_event():
    queue: asyncio.Queue[ExperimentEvent] = asyncio.Queue()
    app = RagOptimizerApp(queue)

    async with app.run_test() as pilot:
        queue.put_nowait(_event(node="validator", status="RUNNING"))
        await pilot.pause()

        status = app.query_one("#status")
        assert "validator" in str(status.content)
        assert "RUNNING" in str(status.content)


@pytest.mark.asyncio
async def test_app_processes_events_in_order():
    queue: asyncio.Queue[ExperimentEvent] = asyncio.Queue()
    app = RagOptimizerApp(queue)

    async with app.run_test() as pilot:
        queue.put_nowait(_event(node="scientist", status="RUNNING"))
        queue.put_nowait(_event(node="validator", status="RUNNING"))
        await pilot.pause()

        status = app.query_one("#status")
        assert "validator" in str(status.content)


@pytest.mark.asyncio
async def test_app_has_full_keybinding_set():
    app = RagOptimizerApp(asyncio.Queue())
    binding_keys = set(app._bindings.key_to_bindings.keys())
    for expected_key in ("1", "2", "3", "4", "5", "tab", "slash", "r", "b", "space", "q"):
        assert expected_key in binding_keys, f"missing binding for {expected_key!r}"


@pytest.mark.asyncio
async def test_quit_binding_exits_app():
    async with RagOptimizerApp(asyncio.Queue()).run_test() as pilot:
        await pilot.press("q")
        await pilot.pause()
        assert pilot.app._exit is True
