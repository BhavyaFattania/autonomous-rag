import yaml
from functools import lru_cache
from src.models.rag_config import RAGConfig


@lru_cache(maxsize=1)
def load_run_settings() -> dict:
    with open("config/run_settings.yaml") as f:
        return yaml.safe_load(f)


@lru_cache(maxsize=1)
def load_baseline_config() -> dict:
    with open("config/baseline_config.yaml") as f:
        return yaml.safe_load(f)


def invalidate_settings_cache() -> None:
    load_run_settings.cache_clear()
    load_baseline_config.cache_clear()


def write_experiment_config(config: RAGConfig):
    with open("config/experiment_config.yaml", "w") as f:
        yaml.safe_dump(config.model_dump(), f)
