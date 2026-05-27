import aiosqlite
import src.storage.db as storage_db

def _logical_config(config: dict) -> dict:
    return {k: v for k, v in config.items() if not k.startswith("_")}

async def deduplicator_node(state) -> dict:
    from src.utils.hashing import get_config_hash
    from datetime import datetime, timezone

    config_hash = get_config_hash(_logical_config(state["validated_config"]))

    async with aiosqlite.connect(storage_db.DB_PATH) as db:
        cursor = await db.execute(
            """
            SELECT experiment_id FROM experiments
            WHERE config_hash=?
              AND status NOT IN ('FAILED_VALIDATION')
            LIMIT 1
            """,
            (config_hash,),
        )
        row = await cursor.fetchone()

        if row:
            return {"status": "FAILED_DUPLICATE", "failure_reason": "Config was already completed"}

        try:
            await db.execute(
                """
                INSERT INTO config_hashes (config_hash, first_seen)
                VALUES (?, ?)
                """,
                (config_hash, datetime.now(timezone.utc).isoformat()),
            )
            await db.commit()
        except aiosqlite.IntegrityError:
            return {"status": "FAILED_DUPLICATE", "failure_reason": "Config was already proposed"}

    return {"status": "RUNNING"}
