"""Module for modifying and printing the state file."""

import sys
from typing import Any

import questionary
from rich import print  # noqa: A004
from rich.style import Style
from rich.table import Table
from rich.text import Text

from ..batch_handler import batch_handler
from ..const import State, StateObjectName, Status
from ..state.state_utils import state_object_handler

true_style = Style(color="green")
false_style = Style(color="red")
none_style = Style(color="yellow")


def remove_state(state_object_name: StateObjectName) -> None:
    """Removes state file."""
    if state_object_name is None:
        sys.exit(0)

    confirm = questionary.confirm(
        f"Are you sure you want to delete the statefile {state_object_name}?"
    ).ask()
    if not confirm:
        sys.exit(1)

    blob = state_object_handler.get_bucket().blob(state_object_name)
    blob.delete()
    print("State file deleted")


@batch_handler
def show_state(state: State, repo_name: str | None = None) -> None:
    """Print the state."""
    table = _initialize_table()
    if repo_name is not None:
        # The user wishes to print one specific repo
        if repo_name not in state.repos.keys():
            print(
                "The provided repository ({name}) does not exist in the selected state file."
            )
            sys.exit(0)
        repo_list = [repo_name]
    else:
        repo_list = list(state.repos.keys())

    for name in repo_list:
        repo = state.get_repo_state(name)

        row: list[str | Text] = [repo.name]
        for value in repo.workflow.dict().values():
            row.append(_get_workflow_cell(value))
        for key, value in repo.pr.model_dump().items():
            row.append(_get_pr_metadata_cell(key, value))
        table.add_row(*row)

    print(table)


def _initialize_table() -> Table:
    # The order of columns must match the order of field definition in the pydantic models.
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Repo", style="cyan", no_wrap=True)

    # Workflow status
    table.add_column("PR opened", style="magenta")
    table.add_column("Checks", style="magenta")
    table.add_column("PR approved", style="magenta")
    table.add_column("Atlantis apply", style="magenta")
    table.add_column("PR merged", style="magenta")

    # PR Metadata
    table.add_column("PR number", style="cyan")
    table.add_column("PR URL", style="cyan")
    table.add_column("Branch", style="cyan")
    return table


def _get_pr_metadata_cell(key: str, value: Any) -> Text | str:
    match key:
        case "number" | "branch_name":
            return Text(str(value), true_style)
        case "url":
            return f"[link={value}]PR[/link]" if value is not None else str(value)
        case _:
            return Text("None", none_style)


def _get_workflow_cell(value: Status) -> Text:
    match value:
        case Status.NOT_STARTED:
            cell_text = "Not started"
            cell_style = none_style
        case Status.STARTED:
            cell_text = "Started"
            cell_style = none_style
        case Status.SUCCESS:
            cell_text = "Success"
            cell_style = true_style
        case Status.FAIL:
            cell_text = "Fail"
            cell_style = false_style

    return Text(cell_text, style=cell_style)
