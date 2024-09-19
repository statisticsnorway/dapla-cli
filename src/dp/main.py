import importlib.metadata
import logging
from typing import Annotated

import typer

from . import auth, lab

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

app = typer.Typer()
app.add_typer(auth.app, name="auth", help="Authenticate dp with Keycloak")
app.add_typer(lab.app, name="lab", help="Interact with Dapla Lab services")


def version_callback(value: bool) -> None:
    """Print the version."""
    if value:
        try:
            app_version = importlib.metadata.version("dp")
        except importlib.metadata.PackageNotFoundError:
            app_version = "dev"
        print(f"Dapla CLI {app_version}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool | None, typer.Option("--version", callback=version_callback)
    ] = None,
) -> None:
    """Entrypoint for the Dapla CLI."""
    pass
