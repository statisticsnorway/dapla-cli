"""Commands for approving open PRs."""

import sys

import questionary
from github.GithubException import GithubException
from rich import print  # noqa: A004

from ..batch_handler import batch_handler
from ..const import RepoState, State, Status
from ..github import get_commit, get_pr
from ..probe.probe_workflows import probe_workflows
from ..rich_check import RichFailure, RichSuccess


@batch_handler
def approve_prs(state: State) -> None:
    """Approves all open PRs in state file."""
    print("Probing existing PRs..")
    probe_workflows(state)

    answer = questionary.confirm("Do you want to continue and approve PRs?").ask()
    if not answer:
        sys.exit(1)
    
    if any(r.workflow.approved == Status.SUCCESS for r in state.repos.values()):
        answer = questionary.confirm("Some PRs have been approved previously. Do you want to re-approve these PRs?").ask()
        if not answer:
            print("[yellow]Removed previously approved PRs")
            repos = [r for r in state.repos.values() if r.workflow.approved != Status.SUCCESS and r.workflow.checks == Status.SUCCESS]
            
    repos = [r for r in state.repos.values() if r.workflow.checks == Status.SUCCESS]

    print("\n\n[cyan]Approving PRs..")
    for repo in repos:
        print(f"[bold magenta]{repo.name}")
        _do_approve(repo)


def _do_approve(repo: RepoState) -> None:
    """Approves PR for a single repository."""
    if pr := get_pr(repo.pr.number, repo.name):
        pr_commit = get_commit(pr.head.sha, repo.name)
        try:
            pr.create_review(commit=pr_commit, body="This is an automated approval from `dapla-cli`", event="APPROVE")
        except GithubException as e:
            print(RichFailure(message=f"Github error: {e.data['errors'][0]}"))  # type: ignore
            repo.workflow.approved = Status.FAIL
        else:
            repo.workflow.approved = Status.SUCCESS
            print(RichSuccess(message="PR approved"))
