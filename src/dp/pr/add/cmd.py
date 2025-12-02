"""Functions for creating state file for existing PR´s."""

import datetime
import re
import sys
from pathlib import Path

import typer
from rich import print  # noqa: A004

from ..const import (
    STATE_BUCKET_NAME_URI,
    PrMetadata,
    RepoState,
    State,
    Status,
    WorkflowStatus,
)
from ..state.state_utils import state_object_handler

app = typer.Typer(name="add", help="Create state file for existing PR´s", no_args_is_help=True)


@app.command()
def urls(
    target_branch_name: str = typer.Option("update/template", "--target-branch-name", "-tbn", help="Branch name used in PR´s"),
    pr_urls: list[str] = typer.Argument(None, help="List of PR urls to create state file for."),
) -> None:
    """Creates a state for a list of existing PR´s."""
    if len(pr_urls) == 0:
        print("No repository specified.")
        sys.exit(1)
    for pr_url in pr_urls:
        if not is_valid_github_pr_url(pr_url):
            print(f"Exiting because of invalid GitHub PR URL: {pr_url}")
            sys.exit(1)
    state_name = f"batch-{target_branch_name}-{datetime.datetime.now()}"
    state = create_state(pr_urls, state_name, target_branch_name)
    state_object_handler.set_state(state)
    print(f"[green]✅ state file {state_name} created and uploaded to {STATE_BUCKET_NAME_URI}")


def is_valid_github_pr_url(url: str) -> bool:
    """Validates that a string is a valid GitHub PR url."""
    # Pattern to match only a GitHub pull request URL
    pattern = re.compile(r"^https?://github\.com/[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+/pull/[0-9]+$")
    return bool(pattern.match(url))


def extract_repo_name(pr_url: str) -> str:
    """Extracts the repo name from a GitHub PR url."""
    # Split the URL to get the path segments after 'github.com'
    path_segments = pr_url.split("github.com/")[-1].split("/")
    # path_segments[0] is the user or organization, and path_segments[1] is the repository name
    repo_name = path_segments[1] if len(path_segments) > 1 else None
    if repo_name is None:
        raise ValueError(f"Invalid GitHub PR URL: {pr_url}")
    return repo_name


def get_pr_metadata(pr_url: str, target_branch_name: str) -> PrMetadata:
    """Creates a PrMetadata object from a GitHub PR url."""
    pr_number = int(pr_url.split("/")[-1])
    return PrMetadata(number=pr_number, url=pr_url, branch_name=target_branch_name)


def create_state(repo_list: list[str], state_name: str, target_branch_name: str) -> State:
    """Creates a State object from a list of GitHub PR urls."""
    repos_map = {}
    for pr_url in repo_list:
        repo_name = extract_repo_name(pr_url)
        repos_map[repo_name] = RepoState(
            name=repo_name,
            local_path=Path(""),
            pr=get_pr_metadata(pr_url, target_branch_name),
            workflow=WorkflowStatus(opened=Status.SUCCESS),
        )
    return State(name=state_name, repos=repos_map)
