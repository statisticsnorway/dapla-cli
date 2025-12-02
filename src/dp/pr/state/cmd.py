"""State file command implementations."""

import sys

import typer

from ..state.state_commands import remove_state, show_state
from ..state.state_utils import state_object_handler

app = typer.Typer(
    name="state", help="Reads, prints and edits state.", no_args_is_help=True
)


@app.command()
def show(
    repo_name: str | None = typer.Option(
        None,
        "--repo-name",
        "-rn",
        help="The name of the repo you want to show the state for",
    )
) -> None:
    """Visualises the state of the run."""
    if state := state_object_handler.get_user_state():
        show_state(state, repo_name)
    else:
        sys.exit(1)


@app.command()
def remove() -> None:
    """Removes the state file."""
    state_object_name = state_object_handler.user_select_run(show_other_users=True)
    if not state_object_name:
        sys.exit(1)

    remove_state(state_object_name)
