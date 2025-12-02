"""Global variables for batch update commands."""

from enum import Enum, auto
from typing import TypeAlias

from pydantic import BaseModel

STATE_BUCKET_NAME_URI = "ssb-batch-update-statefiles"
BATCH_PROJECT_ID = "batch-update-p-3f"
STATE_FIELDS = [
    "workflows-success",
    "pr-approved",
    "atlantis-apply",
    "atlantis-apply-success",
    "pr-merged",
    "issue-url",
    "issue-nr",
    "branch",
]

StateObjectName: "TypeAlias" = str | None


class Status(Enum):
    """Possible statuses for a single workflow item."""

    NOT_STARTED = auto()
    STARTED = auto()
    SUCCESS = auto()
    FAIL = auto()


class PrMetadata(BaseModel):
    """Metadata for a Pull Request on Github."""

    number: int | None = None
    url: str | None = None
    branch_name: str | None = None


class WorkflowStatus(BaseModel):
    """Status of stages in the workflow for a single repo."""

    opened: Status = Status.NOT_STARTED
    checks: Status = Status.NOT_STARTED
    approved: Status = Status.NOT_STARTED
    atlantis_apply: Status = Status.NOT_STARTED
    merged: Status = Status.NOT_STARTED


class RepoState(BaseModel):
    """The state of a single repo."""

    name: str  # name of the repo, e.g. "dapla-stat-iac"
    pr: PrMetadata
    workflow: WorkflowStatus


class State(BaseModel):
    """Model representing the state of all repos in a run."""

    name: str
    repos: dict[str, RepoState] = {}
    version: str = "0.0.1"

    def get_repo_state(self, repo_name: str) -> RepoState:
        """Get the state of a single repo."""
        return self.repos[repo_name]
