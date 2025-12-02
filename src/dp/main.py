import logging
from typing import Annotated

import typer

from . import auth, lab, team_api
from .annotations import check_version
from .pr import cmd as pr
from .utils import get_current_version

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

app = typer.Typer(no_args_is_help=True)
app.add_typer(auth.app, name="auth", help="Authenticate dp with Keycloak")
app.add_typer(lab.app, name="lab", help="Interact with Dapla Lab services")
app.add_typer(team_api.app, name="team-api", help="Interact with Dapla Team API")
app.add_typer(pr.app, name="pr", help="Approve and merge template PRs")


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
