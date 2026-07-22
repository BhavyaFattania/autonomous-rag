"""Tests for the REST history API: GET /api/runs, GET /api/runs/{id}/experiments,
GET /api/experiments/{id}."""

import asyncio
import os
from pathlib import Path

import aiosqlite
import pytest
from fastapi.testclient import TestClient
from src.core.events import EventBus
from src.storage.database import Database
from src.storage.models import Experiment
from src.storage.repositories.experiment_repository import ExperimentRepository
from src.web.server import create_app


@pytest.fixture
def temp_db():
    base = Path("pytest_temp")
    base.mkdir(exist_ok=True)
    d = base / "web_history_test"
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


async def _seed_run_and_experiment(path: str) -> int:
    db = Database(path)
    await db.init()
    async with aiosqlite.connect(path) as conn:
        await conn.execute(
            "INSERT INTO runs (run_id, started_at, status) VALUES (?, ?, ?)",
            ("run-1", "2026-07-21T00:00:00+00:00", "RUNNING"),
        )
        await conn.commit()
    experiment_id = await ExperimentRepository().insert(
        Experiment(
            experiment_uuid="uuid-1",
            run_id="run-1",
            config_hash="hash-1",
            config_json="{}",
            status="ACCEPTED",
            started_at="2026-07-21T00:00:00+00:00",
            hypothesis="larger chunks help",
        )
    )
    return experiment_id


def _run(coro):
    # Not asyncio.run(): a nest_asyncio.apply() side effect from
    # src/utils/openrouter_embedding.py (imported transitively elsewhere in
    # the suite) patches asyncio.run to depend on get_event_loop(), which
    # pytest-asyncio's per-test event loop teardown can leave in a state
    # that raises "no current event loop" for later, unrelated tests. A
    # loop we own end-to-end sidesteps that global-state interaction.
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def test_list_runs_endpoint_returns_seeded_run(temp_db):
    _run(_seed_run_and_experiment(temp_db))
    app = create_app(EventBus())

    with TestClient(app) as client:
        response = client.get("/api/runs")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["run_id"] == "run-1"


def test_list_run_experiments_endpoint(temp_db):
    _run(_seed_run_and_experiment(temp_db))
    app = create_app(EventBus())

    with TestClient(app) as client:
        response = client.get("/api/runs/run-1/experiments")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["hypothesis"] == "larger chunks help"


def test_get_experiment_endpoint_returns_full_detail(temp_db):
    experiment_id = _run(_seed_run_and_experiment(temp_db))
    app = create_app(EventBus())

    with TestClient(app) as client:
        response = client.get(f"/api/experiments/{experiment_id}")

    assert response.status_code == 200
    assert response.json()["hypothesis"] == "larger chunks help"


def test_get_experiment_endpoint_404s_for_unknown_id(temp_db):
    _run(_seed_run_and_experiment(temp_db))
    app = create_app(EventBus())

    with TestClient(app) as client:
        response = client.get("/api/experiments/999999")

    assert response.status_code == 404
