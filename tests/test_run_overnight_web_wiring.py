"""Confirms _run() starts the FastAPI web dashboard (via create_app +
uvicorn) and feeds it the same EventBus/adapt() pipeline as before, without
asserting on FastAPI's actual HTTP serving (that's covered by tests/web/)
or on real graph execution (too heavy for a unit test). Replaces
tests/test_run_overnight_tui_wiring.py, whose entire premise (RagOptimizerApp,
sys.stdout.isatty() branching) no longer exists."""

import shutil
from pathlib import Path

import pytest
import scripts.run_overnight as run_overnight
from src.core.events import EventBus
from src.utils.function_trace import close_trace


@pytest.fixture
def _cwd_in_pytest_temp(monkeypatch):
    # See docs/debug_reports/superpowers/specs/2026-07-21-web-ui-dashboard-plan.md's
    # Global Constraints: pytest's own tmp_path fixture hits a PermissionError
    # on this machine.
    base = Path("pytest_temp").resolve()
    base.mkdir(exist_ok=True)
    d = base / "run_overnight_web_wiring_test"
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


class _FakeUvicornServer:
    """Stands in for uvicorn.Server: never actually binds a port. serve()
    just waits until should_exit is set, matching the real Server's
    documented programmatic-shutdown contract closely enough for this test."""

    def __init__(self, config):
        self.config = config
        self.should_exit = False

    async def serve(self):
        import asyncio

        while not self.should_exit:
            await asyncio.sleep(0)


@pytest.mark.asyncio
async def test_run_starts_web_dashboard_and_publishes_every_tick(monkeypatch, _cwd_in_pytest_temp):
    published = []

    class _FakeBus(EventBus):
        def publish(self, event):
            published.append(event)
            super().publish(event)

    fake_bus = _FakeBus()
    monkeypatch.setattr(run_overnight, "EventBus", lambda: fake_bus)
    monkeypatch.setattr(
        run_overnight,
        "uvicorn",
        type("_M", (), {"Server": _FakeUvicornServer, "Config": lambda **kw: kw}),
    )

    created_apps = []

    def _fake_create_app(bus):
        created_apps.append(bus)
        return object()  # never actually served, since uvicorn.Server is faked

    monkeypatch.setattr(run_overnight, "create_app", _fake_create_app)

    ticks = [
        {"scientist": {"status": "RUNNING", "hypothesis": "h"}},
        {"validator": {"status": "RUNNING"}},
    ]

    def _fake_build_graph(**kwargs):
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

            @staticmethod
            def get_total():
                return 0.0

    async def _async_result(value):
        return value

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
        close_trace()

    assert created_apps == [fake_bus]
    assert len(published) == 2
    assert published[0].node == "scientist"
    assert published[1].node == "validator"


@pytest.mark.asyncio
async def test_run_creates_and_finishes_run_row(monkeypatch, _cwd_in_pytest_temp):
    from src.storage.database import Database
    from src.storage.repositories.run_repository import RunRepository

    monkeypatch.setattr(run_overnight, "EventBus", lambda: EventBus())
    monkeypatch.setattr(
        run_overnight,
        "uvicorn",
        type("_M", (), {"Server": _FakeUvicornServer, "Config": lambda **kw: kw}),
    )
    monkeypatch.setattr(run_overnight, "create_app", lambda bus: object())

    ticks = [
        {
            "scientist": {
                "status": "RUNNING",
                "hypothesis": "h",
                "experiments_completed": 3,
                "experiments_accepted": 1,
                "current_best_config": {"a": 1},
                "current_best_weighted_score": 0.75,
                "total_cost_usd": 0.42,
            }
        },
    ]

    def _fake_build_graph(**kwargs):
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

            @staticmethod
            def get_total():
                return 0.0

    async def _async_result(value):
        return value

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
        close_trace()

    await Database().init()
    runs = await RunRepository().list_runs()
    assert len(runs) == 1
    run = runs[0]
    assert run.status == "COMPLETED"
    assert run.n_experiments == 3
    assert run.n_accepted == 1
    assert run.total_cost == 0.42
    assert run.best_score == 0.75
    assert run.finished_at is not None


@pytest.mark.asyncio
async def test_dashboard_stays_up_through_final_best_eval(monkeypatch, _cwd_in_pytest_temp):
    """The visibility-gap fix: evaluate_final_best() must run while the
    dashboard server is still serving, not after it's already been told to
    shut down. Regression test for the browser seeing
    net::ERR_CONNECTION_REFUSED during the final evaluation phase."""
    monkeypatch.setattr(run_overnight, "EventBus", lambda: EventBus())

    servers = []

    class _TrackedFakeServer(_FakeUvicornServer):
        def __init__(self, config):
            super().__init__(config)
            servers.append(self)

    monkeypatch.setattr(
        run_overnight,
        "uvicorn",
        type("_M", (), {"Server": _TrackedFakeServer, "Config": lambda **kw: kw}),
    )
    monkeypatch.setattr(run_overnight, "create_app", lambda bus: object())

    ticks = [{"scientist": {"status": "RUNNING", "hypothesis": "h"}}]
    monkeypatch.setattr(run_overnight, "build_graph", lambda **kwargs: _FakeGraph(ticks))

    class _Settings:
        class run:
            cost_hard_ceiling_usd = 10.0

        class evaluation:
            baseline_score_override = 0.5
            run_final_best_eval = True

    class _Provider:
        class cost_tracker:
            @staticmethod
            def initialize(**kwargs):
                pass

            @staticmethod
            def get_total():
                return 0.0

    async def _async_result(value):
        return value

    monkeypatch.setattr(
        run_overnight, "evaluate_baseline", lambda *a, **k: (_async_result((0.5, {})))
    )

    should_exit_during_final_eval = []

    async def _fake_evaluate_final_best(state, settings, env, provider):
        should_exit_during_final_eval.append(servers[0].should_exit)

    monkeypatch.setattr(run_overnight, "evaluate_final_best", _fake_evaluate_final_best)

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
        close_trace()

    assert should_exit_during_final_eval == [False]
    assert servers[0].should_exit is True
