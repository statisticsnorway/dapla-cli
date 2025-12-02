"""Commands for cleaning up PRs."""
import sys

import typer

from ..close.close_all import close_all
from ..state.state_utils import state_object_handler

app = typer.Typer(name="janitor", help="Collection of commands that cleans up PRs", no_args_is_help=True)


@app.command("close-prs")
def close_prs(
    keep_remote_branches: bool = typer.Option(False, is_flag=True, help="Does not delete remote branches")
) -> None:
    # Optional argument for deleting branches as well
    """Closes all pull requests."""
    if state := state_object_handler.get_user_state():
        close_all(state, keep_remote_branches)
    else:
        sys.exit(1)
