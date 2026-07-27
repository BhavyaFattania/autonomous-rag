"""Tests for the write-serialization fix for the SQLite `database is locked` bug.

The first test reproduces the ROOT CAUSE (two write connections contending);
the rest prove WriteCoordinator serializes writers so the collision cannot occur.
"""

import asyncio
import sqlite3
from pathlib import Path

import aiosqlite
import pytest
from src.storage.write_coordinator import WriteCoordinator, write_transaction

CREATE = "CREATE TABLE t (id INTEGER PRIMARY KEY AUTOINCREMENT, v TEXT)"


@pytest.fixture
def tmp_path(request):
    """Project-local temp dir (Windows system temp is permission-blocked here)."""
    base = Path("pytest_temp") / "write_coordinator" / request.node.name
    base.mkdir(parents=True, exist_ok=True)
    for stale in base.glob("*"):
        stale.unlink()
    return base


async def _init(path: str) -> None:
    async with aiosqlite.connect(path) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute(CREATE)
        await db.commit()


@pytest.mark.asyncio
async def test_two_connections_writing_concurrently_hit_database_is_locked(tmp_path):
    """Root-cause demonstration: a second write connection contending for
    SQLite's single writer lock raises `database is locked` even under WAL --
    exactly what the concurrent persist_events + node writers were doing."""
    path = str(tmp_path / "x.sqlite")
    await _init(path)
    a = await aiosqlite.connect(path)
    b = await aiosqlite.connect(path)
    await b.execute("PRAGMA busy_timeout=50")  # short, so the collision surfaces fast
    try:
        await a.execute("INSERT INTO t (v) VALUES ('a')")  # A holds the write lock, uncommitted
        with pytest.raises(sqlite3.OperationalError) as exc:
            await b.execute("INSERT INTO t (v) VALUES ('b')")
            await b.commit()
        assert "locked" in str(exc.value).lower()
    finally:
        await a.rollback()
        await a.close()
        await b.close()


@pytest.mark.asyncio
async def test_coordinator_serializes_concurrent_writers(tmp_path):
    """The fix: many concurrent writers through the coordinator serialize onto
    one connection under the lock -> every write lands, no `database is locked`."""
    path = str(tmp_path / "x.sqlite")
    await _init(path)
    wc = WriteCoordinator(path)

    async def w(i: int) -> None:
        async with wc.transaction() as db:
            await db.execute("INSERT INTO t (v) VALUES (?)", (str(i),))
            await db.commit()

    await asyncio.gather(*[w(i) for i in range(25)])

    async with wc.transaction() as db:
        cursor = await db.execute("SELECT COUNT(*) FROM t")
        (count,) = await cursor.fetchone()
    assert count == 25
    await wc.aclose()


@pytest.mark.asyncio
async def test_coordinator_rolls_back_on_exception(tmp_path):
    path = str(tmp_path / "x.sqlite")
    await _init(path)
    wc = WriteCoordinator(path)

    with pytest.raises(ValueError):
        async with wc.transaction() as db:
            await db.execute("INSERT INTO t (v) VALUES ('x')")
            raise ValueError("boom")  # exit without commit -> rolled back

    async with wc.transaction() as db:
        cursor = await db.execute("SELECT COUNT(*) FROM t")
        (count,) = await cursor.fetchone()
    assert count == 0
    await wc.aclose()


@pytest.mark.asyncio
async def test_write_transaction_falls_back_to_standalone_connection_when_no_writer(
    tmp_path, monkeypatch
):
    """write_transaction(None) uses a fresh Database().connect() (legacy path),
    so nodes keep working when no coordinator is injected (e.g. in tests)."""
    from src.storage.database import Database

    monkey_path = str(tmp_path / "experiments.sqlite")
    monkeypatch.setattr(Database, "default_path", monkey_path)
    await Database(monkey_path).init()

    async with write_transaction(None) as db:
        await db.execute(
            "INSERT INTO config_hashes (config_hash, first_seen, score) VALUES (?, ?, ?)",
            ("h1", "2026-01-01", 0.5),
        )
        await db.commit()

    async with write_transaction(None) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM config_hashes WHERE config_hash='h1'")
        (count,) = await cursor.fetchone()
    assert count == 1
