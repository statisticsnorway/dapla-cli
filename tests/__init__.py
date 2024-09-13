"""Test suite for the dp package."""
import os

from rich.console import Console

os.environ["NO_COLOR"] = "1"
Console(force_terminal=False)  # Disable ANSI colors during testing
