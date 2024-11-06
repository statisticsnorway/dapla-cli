import logging
from enum import Enum
from typing import Annotated

import requests
import typer

from .auth import local_access_token

app = typer.Typer()
logger = logging.getLogger(__name__)


class Env(str, Enum):
    """Denotes the environment to operate on."""

    prod = "prod"
    test = "test"


env_config = {
    Env.prod: {"team_api_url": "https://dapla-team-api-v2.prod-bip-app.ssb.no"},
    Env.test: {"team_api_url": "https://dapla-team-api-v2.staging-bip-app.ssb.no"},
}

env_option = Annotated[
    Env,
    typer.Option("--env", "-e", case_sensitive=False),
]


@app.command()
def get(
    path: Annotated[
        str,
        typer.Argument(help="The api path to request i.e. /teams/play-enhjoern-a"),
    ],
    env: env_option = Env.prod,
) -> None:
    """Make an authenticated GET request to the dapla-team-api."""
    resp = requests.get(
        env_config[env]["team_api_url"] + path,
        headers={"Authorization": f"Bearer {local_access_token(env)}"},
    )
    print(resp.text)
