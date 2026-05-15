import yaml
from pathlib import Path
from src.models.rag_config import RAGConfig

def load_run_settings() -> dict:
    with open("config/run_settings.yaml") as f:
        return yaml.safe_load(f)

def load_baseline_config() -> dict:
    with open("config/baseline_config.yaml") as f:
        config_dict = yaml.safe_load(f)
    return config_dict

def write_experiment_config(config: RAGConfig):
    with open("config/experiment_config.yaml", "w") as f:
        yaml.safe_dump(config.model_dump(), f)
