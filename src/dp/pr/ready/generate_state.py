"""Module for generating state file."""

import logging
import subprocess
from pathlib import Path
from typing import cast

import questionary
import yaml
from git import Repo
from github.PullRequest import PullRequest
from rich import print

from dp.pr.probe.probe_workflows import probe_workflows
from dp.pr.rich_check import SKIPPING, RichWarning

from ...pr.const import (
    STATE_BUCKET_NAME_URI,
    PrMetadata,
    RepoState,
    State,
    WorkflowStatus,
)
from ...pr.github import get_last_open_pr_for_user_and_title, get_repo
from ...pr.state.state_utils import state_object_handler

logger = logging.getLogger("dpteam")

GITHUB_TEMPLATE_PR_USER = "github-actions[bot]"
GITHUB_TEMPLATE_PR_TITLE = "Update team template"
GITHUB_TEAM_REPO_NAME = "terraform-ssb-dapla-teams"


def generate(state_name: str | None = None, folder_path: Path | None = None) -> None:
    """Generates a new statefile."""
    result = subprocess.run(
        ["gcloud", "config", "list", "account", "--format", "value(core.account)"],
        stdout=subprocess.PIPE,
        check=True,
    )
    # Decode the output from bytes to a string
    run_invoker = result.stdout.decode().strip().replace("@ssb.no", "")

    if not state_name:
        run_name_prompt = questionary.text(
            f"What do you want to call this run? It will be called 'pr-{run_invoker}-[your-input]. Run name:'"
        ).ask()
        state_name = f"pr-{run_invoker}-{run_name_prompt}"

    print("[yellow]Fetching team GitHub repositories")
    if folder_path is None:
        print(
            "[yellow]No folder specified, fetching all team repositories from 'terraform-ssb-dapla-teams'"
        )
        print("[yellow]This can take a minute")
        state = _generate_state_data_from_dapla_team_repo(state_name)
    else:
        state = _generate_state_data_from_path(folder_path, state_name)

    print("State generated.")
    print("Checking PRs for plans and workflows")
    probe_workflows(state)
    state_object_handler.set_state(state)
    print(
        f"\n[green]✅ state file {state_name} created and uploaded to {STATE_BUCKET_NAME_URI}"
    )


def _generate_state_data_from_dapla_team_repo(state_name: str) -> State:

    def _get_team_iac_repos() -> dict[str, str]:
        """Get the IAC repository names for all teams in the terraform-ssb-dapla-teams repository.

        Raises:
            ValueError: If a team has multiple team.yaml files.

        Returns:
            Dict[str, str]: A dictionary mapping team names to a tuple of 1) repository names and 2) newest template pull request
        """
        repo = get_repo(GITHUB_TEAM_REPO_NAME)
        teams_dir = repo.get_contents("teams")
        team_repos = {}

        if not isinstance(teams_dir, list):
            teams_dir = [teams_dir]

        for team_item in teams_dir:
            if team_item.type == "dir":  # Only process directories
                team_name = team_item.name
                try:
                    team_yaml = repo.get_contents(f"teams/{team_name}/team.yaml")
                    if isinstance(team_yaml, list):
                        raise ValueError(
                            f"Team {team_name} has multiple team.yaml files"
                        )

                    yaml_content = yaml.safe_load(team_yaml.decoded_content)
                    iac_repo_name = yaml_content.get("github", {}).get("iac_repo", {})[
                        "name"
                    ]
                    if iac_repo_name:
                        team_repos[team_name] = iac_repo_name
                except Exception as e:
                    print(f"Could not get IAC repo name for team {team_name}: {e!s}")

        return team_repos

    team_repos = _get_team_iac_repos()
    team_repo_pr_mapping = _get_template_prs_for_repos(list(team_repos.values()))
    print(f"[yellow]Found {len(team_repos.keys())} team repos with template PRs")

    repos = {
        repo_name: RepoState(
            name=repo_name,
            pr=PrMetadata(number=pr.number, url=pr.html_url, branch_name=pr.head.ref),
            workflow=WorkflowStatus(),
        )
        for repo_name, pr in team_repo_pr_mapping.items()
    }
    return State(name=state_name, repos=repos)


def _generate_state_data_from_path(path: str | Path, state_name: str) -> State:
    """Helper function to generate state file from local files."""
    root_path: Path = Path(path).absolute()
    team_repos = {}
    dot_git = ".git"
    for folder in root_path.iterdir():
        # We're interested in directories containing a .git file i.e. repositories
        if folder.is_dir() and folder / dot_git in folder.rglob(dot_git):
            # We use the ".git/config" file to get the remote repo name
            repo_remote_url: str = cast(
                str, Repo(folder).config_reader().get_value('remote "origin"', "url")
            )
            repo_name = repo_remote_url.split("/")[-1].replace(".git", "")
            # Create an entry in state so we can track this repo
            team_repos[repo_name] = repo_name

    team_repo_pr_mapping = _get_template_prs_for_repos(list(team_repos.values()))
    repos = {
        repo_name: RepoState(
            name=repo_name,
            pr=PrMetadata(number=pr.number, url=pr.html_url, branch_name=pr.head.ref),
            workflow=WorkflowStatus(),
        )
        for repo_name, pr in team_repo_pr_mapping.items()
    }

    return State(name=state_name, repos=repos)


def _get_template_prs_for_repos(team_repos: list[str]) -> dict[str, PullRequest]:
    prs = {}
    for team_repo in team_repos:
        pr = get_last_open_pr_for_user_and_title(
            repo_name=team_repo,
            user=GITHUB_TEMPLATE_PR_USER,
            title=GITHUB_TEMPLATE_PR_TITLE,
        )
        if pr is None:
            print(
                RichWarning(
                    message=f"Could not find a PR with title {GITHUB_TEMPLATE_PR_TITLE} from user {GITHUB_TEMPLATE_PR_USER} in repo {team_repo}"
                )
            )
            print(SKIPPING)
            continue
        prs[team_repo] = pr
    return prs
