"""Functions for applying atlantis changes."""

import sys

import questionary
from rich import print  # noqa: A004

from ..batch_handler import batch_handler
from ..const import RepoState, State, Status
from ..github import get_pr
from ..rich_check import SKIPPING, RichSuccess, RichWarning


@batch_handler
def atlantis_apply(state: State) -> None:  # noqa: 3901
    """Comments atlantis apply on all uncommented and open PRs."""
    print("[magenta]Probing successful workflows in repositories..")
    # probe_workflows(state)

    answer = questionary.confirm("Do you want to proceed with 'atlantis apply'?").ask()
    if not answer:
        sys.exit(1)

    print("\n\n[cyan]Commenting 'atlantis apply' in repositories")

    for repo in state.repos.values():
        print(f"[bold magenta]{repo.name}")
        _do_atlantis_apply(repo)


def _do_atlantis_apply(repo: RepoState) -> None:
    """Comments 'atlantis apply' on a single repository."""
    # Should check if issue exists
    pr = get_pr(repo.pr.number, repo.name)
    if pr and _should_run_atlantis_apply(repo):
        pr.create_issue_comment("atlantis apply")
        repo.workflow.atlantis_apply = Status.STARTED
        print(RichSuccess(message="Atlantis apply comment created"))


def _should_run_atlantis_apply(repo: RepoState) -> bool:
    """Checks whether atlantis apply should be run."""
    if (
        repo.workflow.checks == Status.NOT_STARTED
        or repo.workflow.checks == Status.FAIL
    ):
        print(RichWarning(message="Checks failed or haven't been recorded for PR"))
        print(SKIPPING)
        return False

    if repo.workflow.approved == Status.NOT_STARTED:
        print(RichWarning(message="PR was found but not approved"))
        print(SKIPPING)
        return False

    match repo.workflow.atlantis_apply:
        case Status.FAIL:
            print(
                RichWarning(
                    message="Apply has been ran previously but failed, commenting apply again"
                )
            )
        case Status.STARTED:
            print(
                RichWarning(
                    message="Have commented 'atlantis apply' previously, but no response by atlantis has been recorded."
                )
            )
            print(SKIPPING)
            return False
        case Status.SUCCESS:
            print(RichWarning(message="Successful apply found in this repository"))
            print(SKIPPING)
            return False
    return True
