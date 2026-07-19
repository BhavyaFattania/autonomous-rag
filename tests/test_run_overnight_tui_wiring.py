"""Confirms _run() constructs one EventBus and feeds it through adapt() for
every astream() tick, without asserting on Textual's rendering (that's
covered by tests/tui/) or on real graph execution (too heavy for a unit test)."""

import shutil
from pathlib import Path

import pytest
import scripts.run_overnight as run_overnight
from src.core.events import EventBus
from src.utils.function_trace import close_trace


@pytest.fixture
def _cwd_in_pytest_temp(monkeypatch):
    # pytest's own `tmp_path` fixture hits a permission error on this
    # machine (WinError 5 under `pytest-of-*`); the rest of this repo's
    # suite works around the same issue with a local `pytest_temp/` dir
    # (see tests/test_storage.py), so _run()'s real Database().init() and
    # AsyncSqliteSaver.from_conn_string("experiments.sqlite") calls write
    # there instead of the repo root. _run() also creates a "data/" trace
    # subdirectory (src/utils/function_trace.py's init_trace()), so cleanup
    # needs rmtree, not a flat unlink loop.
    base = Path("pytest_temp").resolve()
    base.mkdir(exist_ok=True)
    d = base / "run_overnight_tui_wiring_test"
    d.mkdir(exist_ok=True)
    monkeypatch.chdir(d)
    yield
    shutil.rmtree(d, ignore_errors=True)


class _FakeGraph:
    def __init__(self, ticks):
        self._ticks = ticks

    async def aget_state(self, config):
        return None

    async def astream(self, state, config):
        for tick in self._ticks:
            yield tick


@pytest.mark.asyncio
async def test_run_constructs_event_bus_and_publishes_every_tick(monkeypatch, _cwd_in_pytest_temp):
    published = []

    class _FakeBus(EventBus):
        def publish(self, event):
            published.append(event)
            super().publish(event)

    fake_bus = _FakeBus()
    monkeypatch.setattr(run_overnight, "EventBus", lambda: fake_bus)
    monkeypatch.setattr(run_overnight.sys.stdout, "isatty", lambda: False)

    ticks = [
        {"scientist": {"status": "RUNNING", "hypothesis": "h"}},
        {"validator": {"status": "RUNNING"}},
    ]

    def _fake_build_graph(**kwargs):
        # build_graph() is synchronous in this codebase (src/orchestrator/graph.py
        # returns a CompiledStateGraph directly, no await) -- the fake must match,
        # or _run()'s unawaited `build_graph(...)` call receives a bare coroutine
        # object instead of a graph.
        assert kwargs["event_bus"] is fake_bus
        return _FakeGraph(ticks)

    monkeypatch.setattr(run_overnight, "build_graph", _fake_build_graph)

    class _Settings:
        class run:
            cost_hard_ceiling_usd = 10.0

        class evaluation:
            baseline_score_override = 0.5
            run_final_best_eval = False

    class _Provider:
        class cost_tracker:
            @staticmethod
            def initialize(**kwargs):
                pass

    monkeypatch.setattr(
        run_overnight,
        "evaluate_baseline",
        lambda *a, **k: (_async_result((0.5, {}))),
    )

    try:
        await run_overnight._run(
            max_exp=1,
            max_hours=1.0,
            resume=False,
            settings=_Settings(),
            env=None,
            provider=_Provider(),
        )
    finally:
        # _run() opens a trace file via init_trace() but never closes it --
        # only main()'s try/finally does that in production. Close it here so
        # the fixture's rmtree isn't blocked by a Windows file lock.
        close_trace()

    assert len(published) == 2
    assert published[0].node == "scientist"
    assert published[1].node == "validator"


async def _async_result(value):
    return value
