"""Tests for Database schema creation, WAL mode, and basic experiment row insert/read."""

import json
from datetime import UTC, datetime
from pathlib import Path

import aiosqlite
import pytest
from src.storage.database import Database


@pytest.fixture
def temp_db(tmp_path_factory):
    """Database backed by a project-local temp sqlite file, cleaned up after the test."""
    base = Path("pytest_temp")
    base.mkdir(exist_ok=True)
    d = base / "storage_test"
    d.mkdir(exist_ok=True)
    path = str(d / "experiments.sqlite")
    db = Database(path)
    yield db
    for f in d.iterdir():
        f.unlink(missing_ok=True)
    d.rmdir()


@pytest.mark.asyncio
async def test_init_db_creates_tables(temp_db):
    """Database.init() creates the experiments, config_hashes, and runs tables."""
    await temp_db.init()

    async with aiosqlite.connect(temp_db.path) as conn:
        cursor = await conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in await cursor.fetchall()]

        assert "experiments" in tables
        assert "config_hashes" in tables
        assert "runs" in tables


@pytest.mark.asyncio
async def test_wal_mode_enabled(temp_db):
    """The sqlite connection runs in WAL journal mode (needed for concurrent readers/writers)."""
    await temp_db.init()

    async with aiosqlite.connect(temp_db.path) as conn:
        cursor = await conn.execute("PRAGMA journal_mode;")
        mode = (await cursor.fetchone())[0]
        assert mode.lower() == "wal"


@pytest.mark.asyncio
async def test_insert_and_read_experiment(temp_db):
    """A round-tripped experiment row preserves its JSON-encoded config."""
    await temp_db.init()

    async with aiosqlite.connect(temp_db.path) as conn:
        await conn.execute(
            """
            INSERT INTO experiments
            (experiment_uuid, run_id, config_hash, config_json, hypothesis, status, started_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "uuid-123",
                "run-456",
                "hash789",
                '{"chunk_size": 512}',
                "test hyp",
                "PENDING",
                datetime.now(UTC).isoformat(),
            ),
        )
        await conn.commit()

        cursor = await conn.execute(
            "SELECT experiment_uuid, config_json FROM experiments WHERE experiment_uuid='uuid-123'"
        )
        row = await cursor.fetchone()

        assert row is not None
        assert row[0] == "uuid-123"
        assert json.loads(row[1])["chunk_size"] == 512
