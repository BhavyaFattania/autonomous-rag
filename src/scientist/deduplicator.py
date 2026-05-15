import aiosqlite
from src.storage.db import DB_PATH

async def deduplicator_node(state) -> dict:
    from src.utils.hashing import get_config_hash
    config_hash = get_config_hash(state["validated_config"])
    
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT config_hash FROM config_hashes WHERE config_hash=?", (config_hash,))
        row = await cursor.fetchone()
        
        if row:
            return {"status": "FAILED_DUPLICATE", "failure_reason": "Config hash already exists in DB"}
            
        await db.execute("INSERT INTO config_hashes (config_hash, first_seen) VALUES (?, datetime('now'))", (config_hash,))
        await db.commit()
        
    return {"status": "RUNNING"}
