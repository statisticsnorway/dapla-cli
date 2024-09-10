import configparser
from configparser import ConfigParser
from pathlib import Path
from typing import Any

import typer


def put(section: str, key: str, value: Any, namespace: str | None) -> None:
    """Set a config value for a key in a section."""
    config = _load_config(namespace)
    if section not in config:
        config[section] = {}
    config[section][key] = value
    _save_config(config, namespace)


def get(section: str, key: str, namespace: str | None) -> Any:
    """Retrieve the config value of a key in a section."""
    config = _load_config(namespace)
    if section in config and key in config[section]:
        return config[section][key]

    return None


def remove(section: str, namespace: str | None) -> None:
    """Remove a section from the config."""
    config = _load_config(namespace)
    if section in config:
        config.remove_section(section)
        _save_config(config, namespace)


def _config_file(namespace: str | None) -> Path:
    config_dir = Path(typer.get_app_dir("dapla-cli"))
    config_dir.mkdir(parents=True, exist_ok=True)  # Ensure the directory exists
    filename = "config.ini" if namespace is None else f"config-{namespace}.ini"
    return config_dir / filename


def _load_config(namespace: str | None) -> ConfigParser:
    """Load the config file."""
    config = configparser.ConfigParser()
    config_file = _config_file(namespace)
    if config_file.exists():
        config.read(config_file)
    return config


def _save_config(config: ConfigParser, namespace: str | None) -> None:
    """Save the config file."""
    with open(_config_file(namespace), "w") as f:
        config.write(f)
