"""
SQLite schema. All tables are created on first run.
WAL mode is MANDATORY for safe async access.
"""

import aiosqlite

DB_PATH = "experiments.sqlite"

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
    first_seen   TEXT NOT NULL
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

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA journal_mode=WAL;")  # MANDATORY
        await db.execute("PRAGMA foreign_keys=ON;")
        await db.execute(CREATE_EXPERIMENTS_TABLE)
        await db.execute(CREATE_CONFIG_HASHES_TABLE)
        await db.execute(CREATE_RUNS_TABLE)
        await db.commit()
