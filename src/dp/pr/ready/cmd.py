"""Commands for preparing a run."""

from pathlib import Path

import typer
from rich import print  # noqa: A004

from ..ready.generate_state import generate


# Add optional arguments:
# - File path
# - Run name
def ready(
    folder_path: Path | None = typer.Option(
        None,
        "--folder-path",
        "-f",
        help="Path to root folder containing all subfolders in which pull requests are opened",
    ),
    state_file_name: str | None = typer.Option(
        None, "--state-name", "-s", help="Name of the state file to generate"
    ),
) -> None:
    """Sets up the state file and prepares the run."""
    generate(state_file_name, folder_path)
    print(
        "\n[yellow]Next step: Perhaps you would want to approve PRs with 'dpteam pr approve' next?"
    )
