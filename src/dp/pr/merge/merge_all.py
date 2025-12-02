"""Functions for merge command."""

import sys

import questionary
from rich import print

from ..batch_handler import batch_handler
from ..const import RepoState, State, Status
from ..github import delete_remote_branch, get_pr, get_repo
from ..rich_check import SKIPPING, RichFailure, RichSuccess, RichWarning


@batch_handler
def merge_all(state: State, override: bool) -> None:  # noqa: 3901
    """Merges all open Pull requests in state file."""
    # probe_atlantis_apply(state)

    answer = questionary.confirm("Do you want to proceed with merge?").ask()
    if not answer:
        sys.exit(1)

    """
    valid_repos = [
        r for r in state.repos.values() if r.workflow.merged == Status.NOT_STARTED and r.workflow.atlantis_apply == Status.STARTED
    ]
    """

    print("\n\n[cyan]Merging all repositories")
    for repo in state.repos.values():
        print(f"[bold magenta]{repo.name}")
        if _check_override(repo, override):
            _do_merge(repo)


def _check_override(repo: RepoState, override: bool) -> bool:
    """Checks if PR has been merged with optional override."""
    if repo.workflow.merged == Status.SUCCESS:
        print(RichWarning(message="Repository has been merged"))
        if not override:
            print(SKIPPING)
            return False
        else:
            answer = questionary.confirm("Do you want to attempt a merge anyway?").ask()
            if not answer:
                print(SKIPPING)
                return False

    return True


def _do_merge(repo: RepoState) -> None:
    """Performs a merge given a single repository."""
    if not (pr := get_pr(repo.pr.number, repo.name)):
        return

    gh_repo = get_repo(repo.name)

    if pr.mergeable_state != "clean":
        print(RichFailure(message="PR is not mergeable"))
        print(RichFailure(message="Skipping.."))
        return
    try:
        merge_status = pr.merge(merge_method="squash")
    except Exception as e:
        repo.workflow.merged = Status.FAIL
        raise e
    if merge_status.merged:
        repo.workflow.merged = Status.SUCCESS
        branch = repo.pr.branch_name
        print(RichSuccess(message="Merged branch"))
        if branch is not None:
            delete_remote_branch(branch, gh_repo)
        print(RichSuccess(message="Deleted remote branch"))
    else:
        print(RichFailure(message=f"Merge failed with message: {merge_status.message}"))
        repo.workflow.merged = Status.FAIL
