"""Probes repositories for 'atlantis apply'."""

from github.PullRequest import PullRequest
from rich import print

from ..batch_handler import batch_handler
from ..const import RepoState, State, Status
from ..github import get_pr
from ..rich_check import RichSuccess, RichWarning


@batch_handler
def probe_atlantis_apply(state: State) -> None:
    """Probes atlantis apply."""
    print("\n\n[cyan]Probing repositories for 'atlantis apply'")
    for repo in state.repos.values():
        print(f"[bold magenta]{repo.name}")
        if pr := get_pr(repo.pr.number, repo.name):
            _do_probe_atlantis_apply(repo, pr)


def _do_probe_atlantis_apply(repo: RepoState, pr: PullRequest) -> None:
    """Probes atlantis apply for a single repository."""
    # here, we should ideally get the workflow ID and use that instead of a comment
    # however, this is not too simple with the GitHub Python library
    # https://stackoverflow.com/questions/75063703/github-api-find-status-of-required-checks-on-a-pull-request-towards-protected-b

    if pr.mergeable_state == "clean":
        print(RichSuccess(message="PR is ready to be merged"))
        repo.workflow.atlantis_apply = Status.SUCCESS

    else:
        print(RichWarning(message="PR is not mergeable"))
        print(RichWarning(message="Skipping.."))
        repo.workflow.atlantis_apply = Status.FAIL
