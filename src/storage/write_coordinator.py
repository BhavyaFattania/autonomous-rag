"""Serializes all SQLite writes for a run onto ONE connection guarded by an
asyncio.Lock.

Root cause this fixes: the pipeline opened multiple write connections that ran
concurrently -- the background `persist_events` task writing `node_events` while
a pipeline node (recorder/deduplicator) held a read-then-write transaction on its
own connection. SQLite is single-writer; that read->write lock upgrade across two
connections is a deadlock SQLite reports as `database is locked` immediately, one
that `busy_timeout` deliberately will not wait out. Funnelling every write through
one connection under one lock means no two write transactions ever contend, so the
collision -- and the retry/timeout band-aids around it -- disappear.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

import aiosqlite


class WriteCoordinator:
    """Owns the single write connection for a run and serializes access to it.

    `transaction()` is a near drop-in for `Database().connect()`: it yields a
    connection the caller writes to and commits, but acquires the shared lock
    first and reuses one long-lived connection, so concurrent callers queue
    instead of contending. Reads are unaffected -- they keep their own
    connections and read concurrently under WAL.
    """

    def __init__(self, path: str):
        self._path = path
        self._lock = asyncio.Lock()
        self._conn: aiosqlite.Connection | None = None

    async def _ensure(self) -> aiosqlite.Connection:
        if self._conn is None:
            self._conn = await aiosqlite.connect(self._path)
            # Defense-in-depth: a lingering reader could still briefly hold the
            # snapshot; let the single writer wait rather than error.
            await self._conn.execute("PRAGMA busy_timeout=10000")
        return self._conn

    @asynccontextmanager
    async def transaction(self):
        """Acquire the write lock, yield the shared connection, roll back on
        error. The caller commits on success (matching `Database().connect()`)."""
        async with self._lock:
            conn = await self._ensure()
            try:
                yield conn
            except BaseException:
                await conn.rollback()
                raise

    async def aclose(self) -> None:
        """Close the shared connection at run end. Safe to call more than once."""
        if self._conn is not None:
            await self._conn.close()
            self._conn = None


def write_transaction(writer: WriteCoordinator | None):
    """Serialized write transaction when a coordinator is provided; otherwise a
    fresh standalone connection (legacy/test path). Caller commits on success."""
    if writer is not None:
        return writer.transaction()
    from src.storage.database import Database

    return Database().connect()
