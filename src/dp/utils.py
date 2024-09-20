import re
import subprocess
from datetime import datetime, timezone
from typing import Any

import typer
from pydantic import BaseModel
from rich import print
from rich.console import Console
from typer import Typer

err = Console(stderr=True)
ansi_escape = re.compile(r"\x1B[@-_][0-?]*[ -/]*[@-~]")
app = Typer()


class RunResult(BaseModel):
    """The result of running a shell command."""

    stdout: str
    stderr: str
    returncode: int


def red(text: Any) -> str:
    """Returns text colored in red."""
    return f"[bold red]{text}[/bold red]"


def green(text: Any) -> str:
    """Returns text colored in green."""
    return f"[bold green]{text}[/bold green]"


def grey(text: Any) -> str:
    """Returns text colored in gray."""
    return f"[grey50]{text}[/grey50]"


def print_err(text: Any) -> None:
    """Prints to standard error stream."""
    err.print(red(text))


def strip_ansi(text: str) -> str:
    """Strip ANSI escape sequences from text."""
    return ansi_escape.sub("", text)


def hours_since(dt: datetime) -> int:
    """Calculate the number of hours since a given datetime."""
    # delta = datetime.now(timezone.utc) - dateutil.parser.isoparse(dt)
    delta = datetime.now(timezone.utc) - dt
    return int(delta.total_seconds() // 3600)


def run(command: str, dryrun: bool = False, verbose: bool = False) -> RunResult:
    """Run a shell command.

    Args:
        command (str): The shell command to run.
        dryrun (bool): Whether to perform a dry run.
        verbose (bool): Whether to print the command.

    Returns:
        RunResult: The result of the command.
    """
    if verbose:
        print(grey(f"{'DRYRUN: ' if dryrun else ''}{command}"))

    if dryrun:
        return RunResult(stdout="", stderr="", returncode=0)

    result = subprocess.run(command, shell=True, text=True, capture_output=True)
    return RunResult(
        stdout=result.stdout, stderr=result.stderr, returncode=result.returncode
    )


def assert_successful_command(cmd: str, err_msg: str, success_msg: str | None) -> None:
    """Run a shell command and assert its success.

    Args:
        cmd (str): The shell command to run.
        err_msg (str): The error message to display if the command fails.
        success_msg (str): The success message to display if the command succeeds.

    Raises:
        Exit: If the command fails.
    """
    res = run(f"eval {cmd} > /dev/null")
    if res.returncode != 0:
        err.print(f"❌  {red(err_msg)}")
        raise typer.Exit(code=res.returncode)
    if success_msg:
        print(f"✔️ {success_msg}")
