"""
Backward-compat re-exports from the database module.

Existing code imports from db:
    import src.storage.db as storage_db
    storage_db.DB_PATH
    await storage_db.init_db()

These still work by delegating to Database.
"""

from src.storage.database import Database

# Module-level singleton
DB_PATH = "experiments.sqlite"


def _instance(path=None):
    return Database(path or DB_PATH)


async def init_db(path=None):
    return await _instance(path).init()
