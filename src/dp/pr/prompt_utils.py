"""Utils for prompting the user."""

from typing import Any

import questionary


def confirm_input(question: str, validator: Any = None) -> str:
    """Confirms the answer from input on a questionary question."""
    answer = questionary.text(question, validate=validator).ask()
    while not questionary.confirm(f"Are you sure '{answer}' is correct?").ask():
        answer = questionary.text(question).ask()
    return str(answer)
