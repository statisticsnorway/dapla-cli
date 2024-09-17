import time

import pytest
import typer

from dp import auth
from dp.auth import Env


def test_login_successful(mocker):
    mocker.patch(
        "dp.auth._init_device_flow",
        return_value={"device_code": "device_code", "code_verifier": "code_verifier"},
    )
    mocker.patch("dp.auth._poll_for_token", return_value="access_token")
    auth.login(env=Env.prod)
    auth._init_device_flow.assert_called_once_with(Env.prod)
    auth._poll_for_token.assert_called_once_with(
        "device_code", "code_verifier", Env.prod
    )


def test_login_device_flow_error(mocker):
    mocker.patch("dp.auth._init_device_flow", side_effect=typer.Exit(code=1))
    with pytest.raises(typer.Exit):
        auth.login(env=Env.prod)


def test_logout_successful(mocker):
    mocker.patch("dp.auth.config.get", return_value="refresh_token")
    mocker.patch("dp.auth.requests.post", return_value=mocker.Mock(status_code=200))
    mocker.patch("dp.auth.config.remove")
    auth.logout(env=Env.prod)
    auth.config.get.assert_called_once_with("auth", "refresh_token", "prod")
    auth.requests.post.assert_called_once()
    auth.config.remove.assert_called_once_with("auth", namespace="prod")


def test_logout_already_logged_out(mocker):
    mocker.patch("dp.auth.config.get", return_value=None)
    auth.logout(env=Env.prod)
    auth.config.get.assert_called_once_with("auth", "refresh_token", "prod")


def test_show_access_token_prints_token(mocker):
    mocker.patch("dp.auth.local_access_token", return_value="access_token")
    auth.show_access_token(env=Env.prod)
    auth.local_access_token.assert_called_once_with(Env.prod, ensure_valid=True)


def test_show_access_token_decoded(mocker):
    mocker.patch("dp.auth.local_access_token", return_value="access_token")
    mocker.patch("dp.auth.jwt.decode", return_value={"decoded": "token"})
    auth.show_access_token(env=Env.prod, decoded=True)
    auth.local_access_token.assert_called_once_with(Env.prod, ensure_valid=True)
    auth.jwt.decode.assert_called_once_with(
        "access_token", options={"verify_signature": False}
    )


def test_show_access_token_to_clipboard(mocker):
    mocker.patch("dp.auth.local_access_token", return_value="access_token")
    mocker.patch("dp.auth.pyperclip.copy")
    auth.show_access_token(env=Env.prod, to_clipboard=True)
    auth.local_access_token.assert_called_once_with(Env.prod, ensure_valid=True)
    auth.pyperclip.copy.assert_called_once_with("access_token")


def test_local_access_token_not_found(mocker):
    mocker.patch("dp.auth.config.get", return_value=None)
    with pytest.raises(typer.Exit):
        auth.local_access_token(env=Env.prod)


def test_local_access_token_refresh_needed(mocker):
    mocker.patch("dp.auth.config.get", return_value="access_token")
    mocker.patch("dp.auth.jwt.decode", return_value={"exp": time.time() - 100})
    mocker.patch("dp.auth._refresh_token", return_value="new_access_token")
    token = auth.local_access_token(env=Env.prod)
    assert token == "new_access_token"
    auth._refresh_token.assert_called_once_with(Env.prod)
