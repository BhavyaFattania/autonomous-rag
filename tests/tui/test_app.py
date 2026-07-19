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


@pytest.mark.asyncio
async def test_bad_widget_update_does_not_crash_worker(monkeypatch):
    from src.tui.widgets.experiment_panel import ExperimentPanel

    def _boom(self, event, best_config):
        raise RuntimeError("boom")

    monkeypatch.setattr(ExperimentPanel, "apply_event", _boom)

    queue: asyncio.Queue = asyncio.Queue()
    app = RagOptimizerApp(queue)
    async with app.run_test() as pilot:
        queue.put_nowait(_event(node="scientist", status="RUNNING", hypothesis="h"))
        await pilot.pause()

        # the worker survived the exception and keeps processing later events
        queue.put_nowait(_event(node="validator", status="RUNNING"))
        await pilot.pause()

        status = app.query_one("#status")
        assert "validator" in str(status.content)


@pytest.mark.asyncio
async def test_failed_event_shows_failure_banner():
    queue: asyncio.Queue = asyncio.Queue()
    app = RagOptimizerApp(queue)
    async with app.run_test() as pilot:
        queue.put_nowait(
            _event(node="smoke_test", status="FAILED_SMOKE", failure_reason="zero results")
        )
        await pilot.pause()

        banner = app.query_one("#failure-banner")
        assert "zero results" in str(banner.content)
        assert banner.styles.display != "none"


@pytest.mark.asyncio
async def test_no_failure_banner_hidden_by_default():
    app = RagOptimizerApp(asyncio.Queue())
    async with app.run_test():
        banner = app.query_one("#failure-banner")
        assert banner.styles.display == "none"


@pytest.mark.asyncio
async def test_footer_shows_run_id():
    app = RagOptimizerApp(asyncio.Queue(), run_id="abc-123")
    async with app.run_test():
        text = str(app.query_one("#run-id").content)
        assert "abc-123" in text


@pytest.mark.asyncio
async def test_export_hint_binding_logs_export_command():
    app = RagOptimizerApp(asyncio.Queue(), run_id="abc-123")
    async with app.run_test() as pilot:
        await pilot.press("e")
        await pilot.pause()

        from textual.widgets import Log

        log_widget = app.query_one(Log)
        joined = "\n".join(log_widget.lines)
        assert "scripts/export_experiments.py" in joined
        assert "--run-id abc-123" in joined
