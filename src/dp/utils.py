from rich.console import Console
from typer import Typer

err = Console(stderr=True)

app = Typer()


def red(text: str) -> str:
    """Returns text colored in red."""
    return f"[bold red]{text}[/bold red]"


def green(text: str) -> str:
    """Returns text colored in green."""
    return f"[bold green]{text}[/bold green]"


def gray(text: str) -> str:
    """Returns text colored in gray."""
    return f"[bright_black]{text}[/bright_black]"


def print_err(text: str) -> None:
    """Prints to standard error stream."""
    err.print(red(text))
