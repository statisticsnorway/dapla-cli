"""Helper decorator to catch exceptions and save the state before exiting."""

from collections.abc import Callable
from typing import Any

from ..pr.state.state_utils import state_object_handler


def batch_handler(batch_function: Callable[..., Any]) -> Callable[..., Any]:
    """Provides the state to the batch function and ensures the state is saved if an exception is thrown."""

    def exception_handler(*args: Any, **kwargs: Any) -> None:
        try:
            batch_function(*args, **kwargs)
        finally:
            if state := state_object_handler.current_state:
                state_object_handler.set_state(state=state)

    return exception_handler
