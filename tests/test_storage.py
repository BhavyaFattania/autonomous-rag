import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path

import aiosqlite
import pytest
from src.storage.database import Database
from src.storage.repositories._shared import db_or_connect


@pytest.fixture
def temp_db(tmp_path_factory):
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
    await temp_db.init()

    async with aiosqlite.connect(temp_db.path) as conn:
        cursor = await conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in await cursor.fetchall()]

        assert "experiments" in tables
        assert "config_hashes" in tables
        assert "runs" in tables


@pytest.mark.asyncio
async def test_wal_mode_enabled(temp_db):
    await temp_db.init()

    async with aiosqlite.connect(temp_db.path) as conn:
        cursor = await conn.execute("PRAGMA journal_mode;")
        mode = (await cursor.fetchone())[0]
        assert mode.lower() == "wal"


@pytest.mark.asyncio
async def test_connect_sets_busy_timeout(temp_db):
    await temp_db.init()

    async with temp_db.connect() as conn:
        cursor = await conn.execute("PRAGMA busy_timeout;")
        timeout_ms = (await cursor.fetchone())[0]
        assert timeout_ms == 10000


@pytest.mark.asyncio
async def test_auto_commit_context_sets_busy_timeout(temp_db, monkeypatch):
    await temp_db.init()
    monkeypatch.setattr(Database, "default_path", temp_db.path)

    async with db_or_connect(None) as conn:
        cursor = await conn.execute("PRAGMA busy_timeout;")
        timeout_ms = (await cursor.fetchone())[0]
        assert timeout_ms == 10000


@pytest.mark.asyncio
async def test_concurrent_writes_no_longer_raise_database_locked(temp_db, monkeypatch):
    """Reproduces the exact race observed in a real overnight run:
    persist_events() and recorder_node() each open their own ad-hoc
    connection to the same file and can write at the same moment. Before the
    busy_timeout fix, the second writer's INSERT raised
    sqlite3.OperationalError: database is locked immediately instead of
    waiting for the first writer's transaction to finish."""
    await temp_db.init()
    monkeypatch.setattr(Database, "default_path", temp_db.path)

    holder = await aiosqlite.connect(temp_db.path)
    await holder.execute("PRAGMA busy_timeout=5000;")
    await holder.execute("BEGIN IMMEDIATE")
    await holder.execute(
        "INSERT INTO runs (run_id, started_at) VALUES ('holder-run', '2026-01-01T00:00:00+00:00')"
    )

    async def release_after_delay():
        await asyncio.sleep(0.3)
        await holder.commit()
        await holder.close()

    async def contending_write():
        async with db_or_connect(None) as conn:
            await conn.execute(
                "INSERT INTO runs (run_id, started_at) VALUES ('other-run', '2026-01-01T00:00:01+00:00')"
            )

    release_task = asyncio.create_task(release_after_delay())
    await contending_write()  # must not raise, even while `holder` holds the write lock
    await release_task

    async with aiosqlite.connect(temp_db.path) as conn:
        cursor = await conn.execute("SELECT run_id FROM runs ORDER BY run_id")
        rows = [row[0] for row in await cursor.fetchall()]
    assert rows == ["holder-run", "other-run"]


@pytest.mark.asyncio
async def test_insert_and_read_experiment(temp_db):
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
