import yaml
from functools import lru_cache
from src.models.rag_config import RAGConfig


@lru_cache(maxsize=1)
def load_run_settings() -> dict:
    """Load run_settings.yaml once per process. Cached after first call.
    Call invalidate_settings_cache() to force a reload (e.g. in tests)."""
    with open("config/run_settings.yaml") as f:
        return yaml.safe_load(f)


@lru_cache(maxsize=1)
def load_baseline_config() -> dict:
    """Load baseline_config.yaml once per process. Cached after first call."""
    with open("config/baseline_config.yaml") as f:
        return yaml.safe_load(f)


def invalidate_settings_cache() -> None:
    """Clear the in-process settings cache. Useful in tests and after config edits."""
    load_run_settings.cache_clear()
    load_baseline_config.cache_clear()


def write_experiment_config(config: RAGConfig):
    with open("config/experiment_config.yaml", "w") as f:
        yaml.safe_dump(config.model_dump(), f)
