"""Tests for ExperimentRepository's historical-browsing queries, added for
the web dashboard's REST history API."""

import os
from pathlib import Path

import pytest
from src.storage.database import Database
from src.storage.models import Experiment
from src.storage.repositories.experiment_repository import ExperimentRepository


@pytest.fixture
def temp_db():
    # Project-local temp dir -- pytest's own tmp_path fixture hits a
    # PermissionError on this machine (see tests/test_storage.py for the
    # established workaround this fixture copies).
    base = Path("pytest_temp")
    base.mkdir(exist_ok=True)
    d = base / "experiment_repository_history_test"
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


async def _seed(path: str, **overrides) -> None:
    db = Database(path)
    await db.init()
    experiment_uuid = f"uuid-{overrides.pop('experiment_uuid', '1')}"
    defaults = dict(
        experiment_uuid=experiment_uuid,
        run_id="run-1",
        config_hash="hash-1",
        config_json="{}",
        status="ACCEPTED",
        started_at="2026-07-21T00:00:00+00:00",
    )
    defaults.update(overrides)
    await ExperimentRepository().insert(Experiment(**defaults))


@pytest.mark.asyncio
async def test_find_by_run_id_returns_only_matching_run(temp_db):
    await _seed(temp_db, experiment_uuid="a", run_id="run-1")
    await _seed(temp_db, experiment_uuid="b", run_id="run-2")
    await _seed(temp_db, experiment_uuid="c", run_id="run-1")

    results = await ExperimentRepository().find_by_run_id("run-1")

    assert len(results) == 2
    assert {r.experiment_uuid for r in results} == {"uuid-a", "uuid-c"}


@pytest.mark.asyncio
async def test_find_by_run_id_returns_empty_list_for_unknown_run(temp_db):
    await _seed(temp_db, experiment_uuid="a", run_id="run-1")

    results = await ExperimentRepository().find_by_run_id("no-such-run")

    assert results == []


@pytest.mark.asyncio
async def test_find_by_id_returns_matching_experiment(temp_db):
    await _seed(temp_db, experiment_uuid="a", hypothesis="larger chunks help")

    all_rows = await ExperimentRepository().find_by_run_id("run-1")
    experiment_id = all_rows[0].experiment_id

    found = await ExperimentRepository().find_by_id(experiment_id)

    assert found is not None
    assert found.hypothesis == "larger chunks help"


@pytest.mark.asyncio
async def test_find_by_id_returns_none_for_unknown_id(temp_db):
    await _seed(temp_db, experiment_uuid="a")

    found = await ExperimentRepository().find_by_id(999999)

    assert found is None
