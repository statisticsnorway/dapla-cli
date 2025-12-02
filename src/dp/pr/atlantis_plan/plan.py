"""Functions for applying atlantis changes."""

from rich import print

from ..batch_handler import batch_handler
from ..const import RepoState, State, Status
from ..github import get_pr
from ..rich_check import RichSuccess


@batch_handler
def atlantis_plan(state: State) -> None:
    """Comments atlantis plan on all PRs where plans are failed or do not exist."""
    print("[magenta]Probing succeeded workflows and plans for repositories..")
    # probe_workflows(state)

    print("\n\n[cyan]Commenting 'atlantis plan' in unplanned repositories")
    valid_repos = [
        r
        for r in state.repos.values()
        if r.workflow.checks == Status.FAIL or r.workflow.atlantis_apply == Status.FAIL
    ]
    for repo in valid_repos:
        _do_atlantis_plan(repo)


def _do_atlantis_plan(repo: RepoState) -> bool:
    print(f"[bold magenta]{repo.name}")
    if pr := get_pr(repo.pr.number, repo.name):
        pr.create_issue_comment("atlantis plan")
        print(RichSuccess(message="Atlantis plan commented"))
        return True
    else:
        # Don't continue if we can't find the issue
        return False
