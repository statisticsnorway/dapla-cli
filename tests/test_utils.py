import io
from unittest import mock

from dp import utils


def test_colors() -> None:
    assert utils.red("Hello World") == "[bold red]Hello World[/bold red]"
    assert utils.green("Hello World") == "[bold green]Hello World[/bold green]"
    assert utils.grey("Hello World") == "[grey50]Hello World[/grey50]"


def test_print_err() -> None:
    text = "This is an error message"

    with mock.patch("sys.stderr", new=io.StringIO()) as fake_stderr:
        utils.print_err(text)
        assert fake_stderr.getvalue().strip() == text
