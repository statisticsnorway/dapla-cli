"""Probes repositories for 'atlantis plan'."""

from github.PullRequest import PullRequest
from rich import print  # noqa: A004

from ..batch_handler import batch_handler
from ..const import RepoState, State, Status
from ..github import get_commit, get_pr
from ..rich_check import RichFailure, RichSuccess, RichWarning


@batch_handler
def probe_workflows(state: State) -> None:
    """Probes workflows for atlantis plan and checks in repositories."""
    print("\n\n[cyan]Probing repositories for GitHub checks..")
    for repo in state.repos.values():
        print(f"[bold magenta]{repo.name}")
        if pr := get_pr(repo.pr.number, repo.name):
                _probe_commit_statuses(repo, pr)
        else:
            print(RichWarning(message="Removing repo from state"))
            del state.repos[repo.name]

def _probe_commit_statuses(repo: RepoState, pr: PullRequest) -> None:
    """Probes commit statuses for success or failure."""
    commit = get_commit(pr.head.sha, repo.name)
    
    status = commit.get_combined_status()
    match status.state:
        case "pending":
            print(RichWarning(message='Checks are pending'))
            repo.workflow.checks = Status.FAIL
        case "failure":
            print(
                RichFailure(message='Checks failed')
            )
            repo.workflow.checks = Status.FAIL
        case "success":
            print(RichSuccess(message='Checks succeeded'))
            repo.workflow.checks = Status.SUCCESS
    
