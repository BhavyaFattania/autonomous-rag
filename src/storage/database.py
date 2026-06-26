"""
SQLite connection manager and schema initialisation.
WAL mode is MANDATORY for safe async access.

Usage:
    db = Database()
    await db.init()

    # Shared connection for transactional consistency:
    async with db.connect() as conn:
        repo = ExperimentRepository(conn)
        await repo.insert(experiment)
        await conn.commit()

    # Or let repositories create their own connections (uses Database.default_path):
    repo = ExperimentRepository()
    await repo.find_last_run_id()

    # Override default path (e.g. in tests):
    Database.default_path = "/tmp/test.sqlite"
"""

import aiosqlite
from contextlib import asynccontextmanager


class Database:
    default_path: str = "experiments.sqlite"

    def __init__(self, path: str | None = None):
        self.path = path if path is not None else Database.default_path

    async def init(self):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("PRAGMA journal_mode=WAL;")
            await db.execute("PRAGMA synchronous=NORMAL;")
            await db.execute("PRAGMA temp_store=MEMORY;")
            await db.execute("PRAGMA foreign_keys=ON;")
            await db.execute(self.CREATE_EXPERIMENTS_TABLE)
            await db.execute(self.CREATE_CONFIG_HASHES_TABLE)
            await db.execute(self.CREATE_RUNS_TABLE)
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_config_hashes_hash "
                "ON config_hashes (config_hash)"
            )
            await db.execute(
                """
                INSERT OR IGNORE INTO config_hashes (config_hash, first_seen, score)
                SELECT config_hash, MIN(started_at), MAX(proposed_score)
                FROM experiments
                WHERE config_hash IS NOT NULL AND config_hash != ''
                GROUP BY config_hash
                """
            )
            await db.commit()

    @asynccontextmanager
    async def connect(self):
        async with aiosqlite.connect(self.path) as db:
            yield db

    CREATE_EXPERIMENTS_TABLE = """
    CREATE TABLE IF NOT EXISTS experiments (
        experiment_id    INTEGER PRIMARY KEY AUTOINCREMENT,
        experiment_uuid  TEXT NOT NULL UNIQUE,
        run_id           TEXT NOT NULL,
        config_hash      TEXT NOT NULL,
        config_json      TEXT NOT NULL,
        hypothesis       TEXT,
        status           TEXT NOT NULL,
        failure_reason   TEXT,
        metrics_json     TEXT,
        baseline_score   REAL,
        proposed_score   REAL,
        cost_usd         REAL DEFAULT 0.0,
        started_at       TEXT NOT NULL,
        finished_at      TEXT,
        duration_sec     REAL
    )
    """

    CREATE_CONFIG_HASHES_TABLE = """
    CREATE TABLE IF NOT EXISTS config_hashes (
        config_hash  TEXT PRIMARY KEY,
        first_seen   TEXT NOT NULL,
        score        REAL
    )
    """

    CREATE_RUNS_TABLE = """
    CREATE TABLE IF NOT EXISTS runs (
        run_id        TEXT PRIMARY KEY,
        started_at    TEXT NOT NULL,
        finished_at   TEXT,
        total_cost    REAL DEFAULT 0.0,
        n_experiments INTEGER DEFAULT 0,
        n_accepted    INTEGER DEFAULT 0,
        best_config   TEXT,
        best_score    REAL,
        status        TEXT
    )
    """
