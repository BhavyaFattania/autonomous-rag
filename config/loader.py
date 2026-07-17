"""Load configuration from YAML files with caching.

Provides functions to load and cache settings, model routing, and baseline config.
All loaders use LRU caching to avoid re-parsing YAML on repeated calls.
"""

import os
from functools import lru_cache
from pathlib import Path

import yaml
from config.models import ModelRouting
from config.settings import Settings

_HERE = Path(__file__).resolve().parent


@lru_cache(maxsize=1)
def load_settings() -> Settings:
    """Load run_settings.yaml and return validated Settings with optional search_space config."""
    path = _HERE / "run_settings.yaml"
    with open(path) as f:
        raw = yaml.safe_load(f)

    search_space_raw = raw.pop("search_space", None) or {}

    from config.settings import SearchSpaceSettings

    # Derived from the model rather than hand-maintained, so a new
    # SearchSpaceSettings field is automatically accepted here instead of
    # silently rejected by a duplicate list that drifted out of sync (as
    # happened with allowed_embedding_models).
    valid_search_keys = set(SearchSpaceSettings.model_fields)
    extra = set(search_space_raw) - valid_search_keys
    if extra:
        raise ValueError(f"Unknown search_space keys: {extra}")

    settings = Settings(**raw)
    if search_space_raw:
        settings.search_space = SearchSpaceSettings(**search_space_raw)
    return settings


@lru_cache(maxsize=1)
def load_model_routing() -> ModelRouting:
    """Load model_routing.yaml and return validated ModelRouting with role-to-model mappings."""
    path = _HERE / "model_routing.yaml"
    with open(path) as f:
        raw = yaml.safe_load(f)
    return ModelRouting(**raw["models"])


@lru_cache(maxsize=1)
def load_baseline_config() -> dict:
    path = _HERE / "baseline_config.yaml"
    with open(path) as f:
        return yaml.safe_load(f)


@lru_cache(maxsize=1)
def load_openai_pricing() -> dict[str, tuple[float, float]]:
    """Load openai_pricing.yaml: model_id -> (usd_per_million_input, usd_per_million_output).

    OpenAI's API has no pricing endpoint, so this table is maintained by hand
    (see the file header) rather than fetched live.
    """
    path = _HERE / "openai_pricing.yaml"
    with open(path) as f:
        raw = yaml.safe_load(f)
    return {model_id: tuple(prices) for model_id, prices in raw["models"].items()}


def load_env() -> dict[str, str]:
    """Extract API keys from environment variables.

    OPENROUTER_API_KEY is required today because it's still the only
    provider every other subsystem (embeddings, reranker, Ragas judge)
    depends on regardless of settings.run.llm_provider. OPENAI_API_KEY is
    included when present so an "openai" llm_provider can be resolved by
    src.core.provider_factory.build_provider — it is not yet required
    unconditionally since nothing else in the pipeline needs it.
    """
    env = {"OPENROUTER_API_KEY": os.environ["OPENROUTER_API_KEY"]}
    if "OPENAI_API_KEY" in os.environ:
        env["OPENAI_API_KEY"] = os.environ["OPENAI_API_KEY"]
    return env


def invalidate_all() -> None:
    """Clear all cached configuration loaders (for testing/reloading)."""
    load_settings.cache_clear()
    load_model_routing.cache_clear()
    load_baseline_config.cache_clear()
    load_openai_pricing.cache_clear()


def load_all() -> tuple[Settings, ModelRouting, dict, dict[str, str]]:
    """Load and return all config: (settings, model_routing, baseline_config, env_vars)."""
    return (
        load_settings(),
        load_model_routing(),
        load_baseline_config(),
        load_env(),
    )
