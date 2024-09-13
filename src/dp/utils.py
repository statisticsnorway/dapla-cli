from typing import Any

from rich.console import Console
from typer import Typer

err = Console(stderr=True, force_terminal=False)

app = Typer()


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
