import pytest
import aiosqlite
import os
import tempfile
import json
from datetime import datetime, timezone

from src.storage import db

@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)

    # Patch DB_PATH
    old_path = db.DB_PATH
    db.DB_PATH = path

    yield path

    db.DB_PATH = old_path
    if os.path.exists(path):
        os.remove(path)

@pytest.mark.asyncio
async def test_init_db_creates_tables(temp_db):
    await db.init_db()

    async with aiosqlite.connect(temp_db) as conn:
        cursor = await conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in await cursor.fetchall()]

        assert "experiments" in tables
        assert "config_hashes" in tables
        assert "runs" in tables

@pytest.mark.asyncio
async def test_wal_mode_enabled(temp_db):
    await db.init_db()

    async with aiosqlite.connect(temp_db) as conn:
        cursor = await conn.execute("PRAGMA journal_mode;")
        mode = (await cursor.fetchone())[0]
        assert mode.lower() == "wal"

@pytest.mark.asyncio
async def test_insert_and_read_experiment(temp_db):
    await db.init_db()

    async with aiosqlite.connect(temp_db) as conn:
        await conn.execute(
            """
            INSERT INTO experiments
            (experiment_uuid, run_id, config_hash, config_json, hypothesis, status, started_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ("uuid-123", "run-456", "hash789", '{"chunk_size": 512}', "test hyp", "PENDING", datetime.now(timezone.utc).isoformat())
        )
        await conn.commit()

        cursor = await conn.execute("SELECT experiment_uuid, config_json FROM experiments WHERE experiment_uuid='uuid-123'")
        row = await cursor.fetchone()

        assert row is not None
        assert row[0] == "uuid-123"
        assert json.loads(row[1])["chunk_size"] == 512
