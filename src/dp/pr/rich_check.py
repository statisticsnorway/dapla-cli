"""Helper classes for rich pretty printing checks."""

from enum import Enum

from pydantic import BaseModel
from rich.padding import Padding


class Status(Enum):
    """Enum for pretty checks."""

    Success = 1
    Failure = 2
    Warning = 3


class Check(BaseModel):
    """Holds a success status and a message for an error check."""

    status: Status
    message: str

    def get_status(self) -> Status:
        """Return the current status."""
        return self.status

    def __rich__(self) -> Padding:
        """Help Rich print with correct font colors and emojis."""
        if self.status is Status.Success:
            result = "✅[green]"
        elif self.status is Status.Failure:
            result = "❌[red] ERROR: "
        elif self.status is Status.Warning:
            result = "⚠️[yellow]  WARNING: "

        return Padding.indent(f"{result} {self.message}", 4)


class RichSuccess(Check):
    """A successful check."""

    status: Status = Status.Success


class RichFailure(Check):
    """A failed check."""

    status: Status = Status.Failure


class RichWarning(Check):
    """A warning check."""

    status: Status = Status.Warning


SKIPPING = RichWarning(message="Skipping..")
