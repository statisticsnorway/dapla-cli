from collections.abc import Callable
from functools import wraps
from typing import Any

from rich import print

from .utils import red


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
