"""Tests for RunRepository.list_runs(), added for the web dashboard's REST
history API."""

import os
from pathlib import Path

import aiosqlite
import pytest
from src.storage.database import Database
from src.storage.repositories.run_repository import RunRepository


@pytest.fixture
def temp_db():
    base = Path("pytest_temp")
    base.mkdir(exist_ok=True)
    d = base / "run_repository_history_test"
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


async def _seed_run(path: str, run_id: str, started_at: str) -> None:
    db = Database(path)
    await db.init()
    async with aiosqlite.connect(path) as conn:
        await conn.execute(
            "INSERT INTO runs (run_id, started_at, status) VALUES (?, ?, ?)",
            (run_id, started_at, "RUNNING"),
        )
        await conn.commit()


@pytest.mark.asyncio
async def test_list_runs_returns_newest_first(temp_db):
    await _seed_run(temp_db, "run-old", "2026-07-19T00:00:00+00:00")
    await _seed_run(temp_db, "run-new", "2026-07-21T00:00:00+00:00")

    runs = await RunRepository().list_runs()

    assert [r.run_id for r in runs] == ["run-new", "run-old"]


@pytest.mark.asyncio
async def test_list_runs_respects_limit(temp_db):
    await _seed_run(temp_db, "run-1", "2026-07-19T00:00:00+00:00")
    await _seed_run(temp_db, "run-2", "2026-07-20T00:00:00+00:00")
    await _seed_run(temp_db, "run-3", "2026-07-21T00:00:00+00:00")

    runs = await RunRepository().list_runs(limit=2)

    assert len(runs) == 2
    assert runs[0].run_id == "run-3"


@pytest.mark.asyncio
async def test_list_runs_returns_empty_list_when_no_runs(temp_db):
    db = Database(temp_db)
    await db.init()

    runs = await RunRepository().list_runs()

    assert runs == []


@pytest.mark.asyncio
async def test_create_run_inserts_a_row_visible_via_list_runs(temp_db):
    db = Database(temp_db)
    await db.init()

    await RunRepository().create_run("run-1", "2026-07-22T00:00:00+00:00")

    runs = await RunRepository().list_runs()
    assert len(runs) == 1
    assert runs[0].run_id == "run-1"
    assert runs[0].started_at == "2026-07-22T00:00:00+00:00"
    assert runs[0].status is None


@pytest.mark.asyncio
async def test_create_run_is_idempotent_for_resume(temp_db):
    db = Database(temp_db)
    await db.init()

    await RunRepository().create_run("run-1", "2026-07-22T00:00:00+00:00")
    # Resume calls create_run again with the same run_id; must not crash or
    # duplicate the row.
    await RunRepository().create_run("run-1", "2026-07-22T00:00:00+00:00")

    runs = await RunRepository().list_runs()
    assert len(runs) == 1


@pytest.mark.asyncio
async def test_finish_run_updates_fields_visible_via_list_runs(temp_db):
    db = Database(temp_db)
    await db.init()

    await RunRepository().create_run("run-1", "2026-07-22T00:00:00+00:00")
    await RunRepository().finish_run(
        "run-1",
        finished_at="2026-07-22T01:00:00+00:00",
        total_cost=1.23,
        n_experiments=5,
        n_accepted=2,
        best_config='{"a": 1}',
        best_score=0.9,
        status="COMPLETED",
    )

    runs = await RunRepository().list_runs()
    assert len(runs) == 1
    run = runs[0]
    assert run.finished_at == "2026-07-22T01:00:00+00:00"
    assert run.total_cost == 1.23
    assert run.n_experiments == 5
    assert run.n_accepted == 2
    assert run.best_config == '{"a": 1}'
    assert run.best_score == 0.9
    assert run.status == "COMPLETED"
