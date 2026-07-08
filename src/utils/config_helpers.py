"""Configuration utilities for filtering and processing config dicts."""


def logical_config(config: dict) -> dict:
    """Filter out private (underscore-prefixed) keys from a config dict."""
    return {k: v for k, v in config.items() if not k.startswith("_")}
