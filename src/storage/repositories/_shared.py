import aiosqlite

from src.storage.database import Database


def db_or_connect(db: aiosqlite.Connection | None):
    """Return a context manager over *db* if given, or a fresh connection.

    When a fresh connection is created, it auto-commits on success
    (no exception).  Caller-provided connections are never committed
    here — the caller manages the transaction."""
    if db is not None:
        return _NoopContext(db)
    return _AutoCommitContext()


class _NoopContext:
    """Context manager that returns a provided connection without closing it."""

    def __init__(self, db: aiosqlite.Connection):
        self._db = db

    async def __aenter__(self):
        return self._db

    async def __aexit__(self, *exc):
        pass


class _AutoCommitContext:
    """Context manager that creates a new connection, commits on success, and always closes it.

    Sets busy_timeout explicitly (Python's sqlite3 already defaults new
    connections to a 5s timeout, but a longer, explicit value here is cheap
    insurance against a writer that's still slow to release the lock after
    that window -- see src/storage/event_log.py's _insert_with_lock_retry()
    for the actual fix for the "database is locked" collision observed
    between this context and recorder_node()'s own connection in a real run;
    a bare timeout bump alone did not make that error stop occurring)."""

    async def __aenter__(self):
        self._db = await aiosqlite.connect(Database.default_path)
        await self._db.execute("PRAGMA busy_timeout = 10000")
        return self._db

    async def __aexit__(self, typ, val, tb):
        if typ is None:
            await self._db.commit()
        await self._db.close()
