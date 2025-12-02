"""Commands for writing 'atlantis plan' on PRs."""

import sys

from ..state.state_utils import state_object_handler
from .plan import atlantis_plan


def plan() -> None:
    """Writes 'atlantis plan' on all PRs."""
    if state := state_object_handler.get_user_state():
        atlantis_plan(state)
    else:
        sys.exit(1)
