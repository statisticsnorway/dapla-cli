import os

import pytest


@pytest.fixture(autouse=True)
def no_color_env():
    """Setting NO_COLOR=1 for all tests to disable ANSI colors."""
    os.environ["NO_COLOR"] = "1"
