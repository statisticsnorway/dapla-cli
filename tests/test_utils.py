import importlib.metadata
import io
from datetime import datetime, timedelta, timezone
from unittest import mock

import pytest
import requests
import typer
from packaging.version import Version
from rich.console import Console

from dp import utils


def test_colors() -> None:
    assert utils.red("Hello World") == "[bold red]Hello World[/bold red]"
    assert utils.green("Hello World") == "[bold green]Hello World[/bold green]"
    assert utils.grey("Hello World") == "[grey50]Hello World[/grey50]"


def test_print_err() -> None:
    text = "This is an error message"

    patch_err = mock.patch("dp.utils.err", Console(stderr=True, force_terminal=False))
    patch_stderr = mock.patch("sys.stderr", new=io.StringIO())

    with patch_err, patch_stderr as fake_stderr:
        utils.print_err(text)
        assert fake_stderr.getvalue().strip() == text


def test_strip_ansi_removes_escape_sequences():
    text_with_ansi = "\x1B[31mHello World\x1B[0m"
    result = utils.strip_ansi(text_with_ansi)
    assert result == "Hello World"


def test_strip_ansi_no_escape_sequences():
    plain_text = "Hello World"
    result = utils.strip_ansi(plain_text)
    assert result == "Hello World"


def test_strip_ansi_mixed_content():
    mixed_text = "Hello \x1B[31mWorld\x1B[0m!"
    result = utils.strip_ansi(mixed_text)
    assert result == "Hello World!"


def test_strip_ansi_empty_string():
    empty_text = ""
    result = utils.strip_ansi(empty_text)
    assert result == ""


def test_hours_since_valid_datetime():
    dt = datetime.now(timezone.utc) - timedelta(hours=5)
    result = utils.hours_since(dt)
    assert result == 5


def test_hours_since_future_datetime():
    dt = datetime.now(timezone.utc) + timedelta(hours=5)
    result = utils.hours_since(dt)
    assert result == -5


def test_run_command_successful(mocker):
    mocker.patch(
        "subprocess.run",
        return_value=mocker.Mock(stdout="output", stderr="", returncode=0),
    )
    result = utils.run("echo 'Hello World'")
    assert result.stdout == "output"
    assert result.stderr == ""
    assert result.returncode == 0


def test_run_command_failure(mocker):
    mocker.patch(
        "subprocess.run",
        return_value=mocker.Mock(stdout="", stderr="error", returncode=1),
    )
    result = utils.run("invalid_command")
    assert result.stdout == ""
    assert result.stderr == "error"
    assert result.returncode == 1


def test_run_command_dryrun(mocker):
    result = utils.run("echo 'Hello World'", dryrun=True)
    assert result.stdout == ""
    assert result.stderr == ""
    assert result.returncode == 0


def test_assert_successful_command_success(mocker):
    mocker.patch(
        "dp.utils.run", return_value=utils.RunResult(stdout="", stderr="", returncode=0)
    )
    with mocker.patch("sys.stdout", new=io.StringIO()) as mock_stdout:
        utils.assert_successful_command(
            "echo 'Hello World'", "Error message", "Success message"
        )
        assert "✔️ Success message" in mock_stdout.getvalue()


def test_assert_successful_command_failure(mocker):
    mocker.patch(
        "dp.utils.run",
        return_value=utils.RunResult(stdout="", stderr="error", returncode=1),
    )
    with mocker.patch("sys.stderr", new=io.StringIO()) as mock_stderr:
        with pytest.raises(typer.Exit):
            utils.assert_successful_command("invalid_command", "Error message", None)
            assert "❌  Error message" in mock_stderr.getvalue()


def test_get_current_version_installed(mocker):
    mocker.patch("importlib.metadata.version", return_value="1.0.0")
    result = utils.get_current_version()
    assert result == Version("1.0.0")


def test_get_current_version_not_installed(mocker):
    mocker.patch(
        "importlib.metadata.version",
        side_effect=importlib.metadata.PackageNotFoundError,
    )
    result = utils.get_current_version()
    assert result is None


def test_get_latest_pypi_version_successful(mocker):
    mocker.patch(
        "requests.get",
        return_value=mocker.Mock(
            status_code=200, json=lambda: {"info": {"version": "1.0.0"}}
        ),
    )
    result = utils.get_latest_pypi_version()
    assert result == Version("1.0.0")


def test_get_latest_pypi_version_request_failure(mocker):
    mocker.patch("requests.get", side_effect=requests.RequestException)
    result = utils.get_latest_pypi_version()
    assert result is None


def test_get_latest_pypi_version_invalid_response(mocker):
    mocker.patch(
        "requests.get", return_value=mocker.Mock(status_code=200, json=lambda: {})
    )
    result = utils.get_latest_pypi_version()
    assert result is None
