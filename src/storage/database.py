"""
SQLite connection manager and schema initialisation.
WAL mode is MANDATORY for safe async access.

Refactored for DI: Database implements IDatabase protocol.
"""

from contextlib import asynccontextmanager

import aiosqlite

DEFAULT_DB_PATH = "experiments.sqlite"


class Database:
    """Manages SQLite connection with WAL mode for safe async access."""

    default_path: str = DEFAULT_DB_PATH

    def __init__(self, path: str | None = None):
        """Initialize database with optional custom path."""
        self.path = path if path is not None else Database.default_path

    async def init(self):
        """Create tables, set pragma settings, and backfill config_hashes from existing experiments."""
        async with aiosqlite.connect(self.path) as db:
            await db.execute("PRAGMA journal_mode=WAL;")
            await db.execute("PRAGMA synchronous=NORMAL;")
            await db.execute("PRAGMA temp_store=MEMORY;")
            await db.execute("PRAGMA foreign_keys=ON;")
            await db.execute("PRAGMA busy_timeout=10000;")
            await db.execute(self.CREATE_EXPERIMENTS_TABLE)
            await db.execute(self.CREATE_CONFIG_HASHES_TABLE)
            await db.execute(self.CREATE_RUNS_TABLE)
            await db.execute(self.CREATE_NODE_EVENTS_TABLE)
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_config_hashes_hash "
                "ON config_hashes (config_hash)"
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_node_events_experiment_uuid "
                "ON node_events (experiment_uuid)"
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_node_events_run_id ON node_events (run_id)"
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
        """Context manager for async database connection."""
        async with aiosqlite.connect(self.path) as db:
            await db.execute("PRAGMA busy_timeout=10000;")
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

    CREATE_NODE_EVENTS_TABLE = """
    CREATE TABLE IF NOT EXISTS node_events (
        id                INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id            TEXT NOT NULL,
        experiment_uuid   TEXT NOT NULL,
        experiment_seq    INTEGER NOT NULL,
        node              TEXT NOT NULL,
        status            TEXT NOT NULL,
        timestamp         TEXT NOT NULL,
        cost_total_usd    REAL NOT NULL DEFAULT 0.0,
        message           TEXT,
        hypothesis        TEXT,
        reasoning         TEXT,
        config_json       TEXT,
        metrics_json      TEXT,
        failure_reason    TEXT,
        progress_current  INTEGER,
        progress_total    INTEGER,
        raw_event_json    TEXT
    )
    """
