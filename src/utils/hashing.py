"""Deterministic configuration hashing for caching and deduplication."""

import hashlib
import json


def get_config_hash(config_dict: dict) -> str:
    """Generate SHA-256 hash of a config dict (sorted JSON for determinism)."""
    config_json = json.dumps(config_dict, sort_keys=True).encode()
    return hashlib.sha256(config_json).hexdigest()
