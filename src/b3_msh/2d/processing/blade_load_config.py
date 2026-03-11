"""Load YAML config (blade)."""

import yaml


def blade_load_config(config_path):
    """Load YAML config."""
    with open(config_path) as f:
        return yaml.safe_load(f)
