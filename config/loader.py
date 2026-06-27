import os
import yaml
from functools import lru_cache

from config.settings import Settings, SearchSpaceSettings
from config.models import ModelRouting


@lru_cache(maxsize=1)
def load_settings() -> Settings:
    with open("config/run_settings.yaml") as f:
        raw = yaml.safe_load(f)
    search_space_raw = raw.pop("search_space", None) or {}
    settings = Settings(**raw)
    if search_space_raw:
        settings.search_space = SearchSpaceSettings(**search_space_raw)
    return settings


@lru_cache(maxsize=1)
def load_model_routing() -> ModelRouting:
    with open("config/model_routing.yaml") as f:
        raw = yaml.safe_load(f)
    return ModelRouting(**raw["models"])


@lru_cache(maxsize=1)
def load_baseline_config() -> dict:
    with open("config/baseline_config.yaml") as f:
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
