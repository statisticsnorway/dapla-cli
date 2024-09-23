import logging
from typing import Annotated

import typer

from . import auth, lab
from .annotations import check_version
from .utils import get_current_version

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

app = typer.Typer()
app.add_typer(auth.app, name="auth", help="Authenticate dp with Keycloak")
app.add_typer(lab.app, name="lab", help="Interact with Dapla Lab services")


def version_callback(value: bool) -> None:
    """Print the version."""
    if value:
        version = get_current_version() or "dev"
        print(f"Dapla CLI {version}")
        raise typer.Exit()


@app.callback()
@check_version
def main(
    version: Annotated[
        bool | None, typer.Option("--version", callback=version_callback)
    ] = None,
) -> None:
    """Entrypoint for the Dapla CLI."""
    pass
