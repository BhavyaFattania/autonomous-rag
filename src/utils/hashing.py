import hashlib
import json


def get_config_hash(config_dict: dict) -> str:
    """Returns SHA-256 hash of sorted JSON config."""
    config_json = json.dumps(config_dict, sort_keys=True).encode()
    return hashlib.sha256(config_json).hexdigest()
