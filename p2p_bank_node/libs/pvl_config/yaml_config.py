import os
import yaml


class ConfigError(Exception):
    pass


def load_yaml_config(cfg_path: str) -> dict:
    """
    Reused/adapted from:
    throw-away67/portfolio database_project/src/config.py
    https://github.com/throw-away67/portfolio/blob/e39e2f5db7a140bc24f62d2430fdeac33b82d0c0/database_project/src/config.py
    """
    if not os.path.exists(cfg_path):
        raise ConfigError(f"Missing config file at {cfg_path}")
    with open(cfg_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}