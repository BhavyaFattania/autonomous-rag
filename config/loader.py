import os
from functools import lru_cache
from pathlib import Path

import yaml
from config.models import ModelRouting
from config.settings import Settings

_HERE = Path(__file__).resolve().parent


@lru_cache(maxsize=1)
def load_settings() -> Settings:
    path = _HERE / "run_settings.yaml"
    with open(path) as f:
        raw = yaml.safe_load(f)

    search_space_raw = raw.pop("search_space", None) or {}

    valid_search_keys = {
        "allowed_node_parsers",
        "allowed_retrievers",
        "allowed_chunk_sizes",
        "allowed_chunk_overlaps",
        "allowed_generator_models",
        "allowed_rerankers",
    }
    extra = set(search_space_raw) - valid_search_keys
    if extra:
        raise ValueError(f"Unknown search_space keys: {extra}")

    settings = Settings(**raw)
    if search_space_raw:
        from config.settings import SearchSpaceSettings

        settings.search_space = SearchSpaceSettings(**search_space_raw)
    return settings


@lru_cache(maxsize=1)
def load_model_routing() -> ModelRouting:
    path = _HERE / "model_routing.yaml"
    with open(path) as f:
        raw = yaml.safe_load(f)
    return ModelRouting(**raw["models"])


@lru_cache(maxsize=1)
def load_baseline_config() -> dict:
    path = _HERE / "baseline_config.yaml"
    with open(path) as f:
        return yaml.safe_load(f)


def load_env() -> dict[str, str]:
    return {
        "OPENROUTER_API_KEY": os.environ["OPENROUTER_API_KEY"],
    }


def invalidate_all() -> None:
    load_settings.cache_clear()
    load_model_routing.cache_clear()
    load_baseline_config.cache_clear()


def load_all() -> tuple[Settings, ModelRouting, dict, dict[str, str]]:
    return (
        load_settings(),
        load_model_routing(),
        load_baseline_config(),
        load_env(),
    )
