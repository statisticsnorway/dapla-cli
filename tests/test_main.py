"""Test cases for the __main__ module."""

import pytest
from typer.testing import CliRunner

from dp.main import app

runner = CliRunner()


@pytest.fixture
def cli_runner() -> CliRunner:
    """Fixture for invoking command-line interfaces."""
    return runner


def test_main_succeeds(cli_runner: CliRunner) -> None:
    """It exits with a status code of zero."""
    result = cli_runner.invoke(app, ["--help"])
    assert result.exit_code == 0
