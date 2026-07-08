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
    """Context manager that creates a new connection, commits on success, and always closes it."""

    async def __aenter__(self):
        self._db = await aiosqlite.connect(Database.default_path)
        return self._db

    async def __aexit__(self, typ, val, tb):
        if typ is None:
            await self._db.commit()
        await self._db.close()
