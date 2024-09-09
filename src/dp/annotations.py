from functools import wraps
from typing import Any, Callable

from rich import print

from .utils import red


def dryrunnable(f: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator that prints an informative message if a command is running in dryrun mode.

    Annotate functions with this decorator to print a message if the function is running in dryrun mode. Expects
    'dryrun' boolean argument to be passed to the function.
    """

    @wraps(f)
    def wrapper(
        *args: tuple[Any], dryrun: bool = False, **kwargs: dict[str, Any]
    ) -> Any:
        if dryrun:
            print(red("Dry run enabled. No state will be mutated."))
        return f(*args, dryrun=dryrun, **kwargs)

    return wrapper
