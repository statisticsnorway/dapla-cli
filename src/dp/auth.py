import base64
import hashlib
import json
import logging
import os
import time
from enum import Enum
from typing import Annotated

import jwt
import pyperclip
import requests
import typer
from rich import print as rich_print
from rich import print_json
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from . import config
from .utils import green, red

app = typer.Typer()
err = Console(stderr=True)
console = Console()
logger = logging.getLogger(__name__)

DAPLA_CLI_CLIENT_ID = "dapla-cli"
POLL_INTERVAL = 5  # Time to wait between polling attempts (in seconds)


class Env(str, Enum):
    """Denotes the environment to operate on."""

    prod = "prod"
    test = "test"
    dev = "dev"


keycloak_settings = {
    Env.prod: {"keycloak_url": "https://auth.ssb.no"},
    Env.test: {"keycloak_url": "https://auth.test.ssb.no"},
    Env.dev: {"keycloak_url": "https://auth-play.test.ssb.no"},
}


# Common options
env_option = Annotated[
    Env,
    typer.Option("--env", "-e", case_sensitive=False),
]

client_arg = Annotated[
    str,
    typer.Argument(
        help="The Client ID of the Keycloak client to authenticate against",
    ),
]

clipboard_option = Annotated[
    bool,
    typer.Option(
        "--to-clipboard",
        "-c",
        help="Copy access token to clipboard",
        case_sensitive=False,
    ),
]


def _get_keycloak_setting(env: Env, key: str) -> str:
    return keycloak_settings[env][key]


@app.command()
def login(env: env_option = Env.prod, client: client_arg = DAPLA_CLI_CLIENT_ID) -> None:
    """Log in to Keycloak."""
    device_info = _init_device_flow(env, client)
    _poll_for_token(
        device_info["device_code"], device_info["code_verifier"], env, client
    )


@app.command()
def logout(
    env: env_option = Env.prod, client: client_arg = DAPLA_CLI_CLIENT_ID
) -> None:
    """Log out of Keycloak."""
    refresh_token = config.get(
        "auth", "refresh_token", namespace=f"{client}-{env.value}"
    )
    if refresh_token:
        payload = {
            "client_id": DAPLA_CLI_CLIENT_ID,
            "refresh_token": refresh_token,
        }
        response = requests.post(
            _get_keycloak_setting(env.value, "keycloak_url"), data=payload
        )
        if response.status_code == 200:
            rich_print("Logged out successfully")
            config.remove("auth", namespace=f"{client}-{env.value}")
        else:
            rich_print(f"Error logging out: {response.status_code} - {response.text}")
    else:
        rich_print("Already logged out")


@app.command()
def show_access_token(
    env: env_option = Env.prod,
    client: client_arg = DAPLA_CLI_CLIENT_ID,
    decoded: Annotated[
        bool,
        typer.Option("--decoded", "-d", help="Decode the token to see its contents"),
    ] = False,
    to_clipboard: clipboard_option = False,
) -> None:
    """Print the local access token (if logged in)."""
    access_token = local_access_token(env=env, client=client, ensure_valid=True)

    if decoded:
        decoded_token = jwt.decode(access_token, options={"verify_signature": False})
        print_json(json.dumps(decoded_token))
    else:
        # Use std library python print since the print from Rich inserts undesirable newlines.
        print(access_token, end="")
        if to_clipboard:
            pyperclip.copy(access_token)


def local_access_token(env: Env, client: str, ensure_valid: bool = True) -> str:
    """Return the access token stored in the local configuration.

    If the token is not found, the user is prompted to log in.

    Args:
        env: The environment to get the access token for.
        ensure_valid: If True, the token is refreshed (if needed) before returning it.

    Returns:
        str: A valid JWT access token.

    Raises:
        Exit: If no access token is found, prompts the user to log in and exits.
    """
    access_token = config.get("auth", "access_token", namespace=f"{client}-{env.value}")
    if not access_token:
        rich_print(f"No access token found for {env.value}. Please log in.")
        raise typer.Exit(code=1)

    if ensure_valid:
        decoded_token = jwt.decode(access_token, options={"verify_signature": False})
        current_time = time.time()
        if (current_time + 300) >= decoded_token["exp"]:
            access_token = _refresh_token(env, client)

    return access_token or ""


def _init_device_flow(env: Env, client: str) -> dict[str, str]:
    # Generate PKCE values
    code_verifier = _generate_code_verifier()
    code_challenge = _generate_code_challenge(code_verifier)

    payload = {
        "client_id": DAPLA_CLI_CLIENT_ID,
        "scope": "openid",
        "code_challenge_method": "S256",
        "code_challenge": code_challenge,
    }
    device_auth_url = f"{_get_keycloak_setting(env.value, 'keycloak_url')}/realms/ssb/protocol/openid-connect/auth/device"
    response = requests.post(device_auth_url, data=payload)

    if response.status_code == 200:
        result = response.json()
        device_code = result["device_code"]
        user_code = result["user_code"]
        verification_uri = result["verification_uri"]
        rich_print(
            f"Please visit {verification_uri} and enter the user code: {user_code}"
        )
        return {
            "device_code": device_code,
            "user_code": user_code,
            "code_verifier": code_verifier,
        }
    else:
        rich_print(
            f"Error initiating device flow: {response.status_code} - {response.text}"
        )
        raise typer.Exit(code=1)


def _poll_for_token(device_code: str, code_verifier: str, env: Env, client: str) -> str:
    """Polls the token endpoint until the user completes authentication, with a progress bar."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("Waiting for user authentication...", start=False)

        while True:
            payload = {
                "client_id": DAPLA_CLI_CLIENT_ID,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                "device_code": device_code,
                "code_verifier": code_verifier,
            }

            token_url = f"{_get_keycloak_setting(env.value, 'keycloak_url')}/realms/ssb/protocol/openid-connect/token"
            response = requests.post(token_url, data=payload)

            if response.status_code == 200:
                result = response.json()
                access_token: str = result["access_token"]
                refresh_token: str = result["refresh_token"]
                config.put(
                    section="auth",
                    key="access_token",
                    value=access_token,
                    namespace=f"{client}-{env.value}",
                )
                config.put(
                    section="auth",
                    key="refresh_token",
                    value=refresh_token,
                    namespace=f"{client}-{env.value}",
                )
                rich_print(green("OK"))
                return access_token

            elif response.status_code == 400:
                error = response.json().get("error", "")
                if error == "authorization_pending":
                    progress.update(
                        task, description="Waiting for user authentication..."
                    )
                    time.sleep(POLL_INTERVAL)
                elif error == "slow_down":
                    progress.update(
                        task,
                        description="Slowing down polling as requested by server...",
                    )
                    time.sleep(POLL_INTERVAL * 1.5)
                else:
                    rich_print(red(f"Error: {error}"))
                    raise typer.Exit(code=1)
            else:
                rich_print(
                    red(
                        f"Unexpected response: {response.status_code} - {response.text}"
                    )
                )
                raise typer.Exit(code=1)


def _generate_code_verifier() -> str:
    """Generates a secure random code verifier."""
    return base64.urlsafe_b64encode(os.urandom(32)).decode("utf-8").rstrip("=")


def _generate_code_challenge(verifier: str) -> str:
    """Generates the code challenge by hashing and encoding the code verifier."""
    challenge = hashlib.sha256(verifier.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(challenge).decode("utf-8").rstrip("=")


def _refresh_token(env: Env, client: str) -> str:
    """Refreshes the access token using the refresh token."""
    refresh_token = config.get(
        "auth", "refresh_token", namespace=f"{client}-{env.value}"
    )
    if not refresh_token:
        rich_print("No refresh token found. Please log in.")
        raise typer.Exit(code=1)

    payload = {
        "client_id": DAPLA_CLI_CLIENT_ID,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    response = requests.post(
        f"{_get_keycloak_setting(env.value, 'keycloak_url')}/realms/ssb/protocol/openid-connect/token",
        data=payload,
    )

    if response.status_code == 200:
        result = response.json()
        new_access_token: str = result["access_token"]
        new_refresh_token: str = result["refresh_token"]
        config.put(
            section="auth",
            key="access_token",
            value=new_access_token,
            namespace=f"{client}-{env.value}",
        )
        config.put(
            section="auth",
            key="refresh_token",
            value=new_refresh_token,
            namespace=f"{client}-{env.value}",
        )
        return new_access_token
    else:
        rich_print(
            red(f"Error refreshing token: {response.status_code} - {response.text}")
        )
        raise typer.Exit(code=1)
