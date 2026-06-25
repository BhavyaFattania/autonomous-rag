def logical_config(config: dict) -> dict:
    return {k: v for k, v in config.items() if not k.startswith("_")}
