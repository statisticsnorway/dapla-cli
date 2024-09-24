import os
from collections.abc import Callable
from datetime import datetime, timedelta
from functools import wraps
from typing import Any

import typer
from rich import print

from . import config
from .utils import get_current_version, get_latest_pypi_version, print_err, red, run


def dryrunnable(f: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator that prints an informative message if a command is running in dryrun mode.

    Annotate functions with this decorator to print a message if the function is running in dryrun mode. Expects
    'dryrun' boolean argument to be passed to the function.
    """

    @wraps(f)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        dryrun = kwargs.get("dryrun", False)

        if dryrun:
            print(red("Dry run enabled. No state will be mutated."))

        return f(*args, **kwargs)

    return wrapper


def ensure_helm_repos_updated(f: Callable[..., Any]) -> Callable[..., Any]:
    """Annotation to ensure Helm repo is updated if necessary before running a helm command that relies on helm repos."""

    @wraps(f)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        config_section = "helm"
        config_key = "repos_last_updated"
        last_updated = _get_config_timestamp(config_section, config_key)

        if datetime.now() - last_updated > timedelta(hours=2):
            res = run("helm repo update")
            if res.returncode != 0:
                print_err(f"Failed to update Helm repos: {res.stderr}")
                raise typer.Exit(code=1)

            _update_config_timestamp(config_section, config_key)
        return f(*args, **kwargs)

    return wrapper


def check_version(f: Callable[..., Any]) -> Callable[..., Any]:
    """Annotation to check for newer versions from PyPI.

    This annotation checks for newer versions from PyPI and prints a message if a newer version is available.
    The check is performed once every 24 hours. You can disable this check by setting the environment
    variable DAPLA_CLI_NO_VERSION_CHECK to any value.
    """

    @wraps(f)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if os.getenv("DAPLA_CLI_NO_VERSION_CHECK"):
            return f(*args, **kwargs)

        config_section = "general"
        config_key = "last_checked_version"
        last_updated = _get_config_timestamp(config_section, config_key)

        if datetime.now() - last_updated > timedelta(hours=24):
            current_version = get_current_version()
            latest_pypi_version = get_latest_pypi_version()

            if current_version and latest_pypi_version:
                if current_version >= latest_pypi_version:
                    print(
                        f"A new version is available: {latest_pypi_version} (Installed: {current_version})"
                    )

            _update_config_timestamp(config_section, config_key)
        return f(*args, **kwargs)

    return wrapper


def _get_config_timestamp(
    section: str, key: str, default: str = "1970-01-01T00:00:00"
) -> datetime:
    """Get a timestamp from the config."""
    last_updated_str = config.get(section=section, key=key, namespace=None)
    return (
        datetime.fromisoformat(last_updated_str)
        if last_updated_str
        else datetime.fromisoformat(default)
    )


def _update_config_timestamp(section: str, key: str) -> None:
    """Update the config with the current timestamp."""
    config.put(
        section=section,
        key=key,
        value=datetime.now().isoformat(),
        namespace=None,
    )
