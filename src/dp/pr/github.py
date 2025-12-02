"""Git functionality."""
import logging
import subprocess

import github
from git.repo import Repo
from github.Commit import Commit
from github.GithubException import UnknownObjectException
from github.Organization import Organization
from github.PullRequest import PullRequest
from github.Repository import Repository
from pydantic import BaseModel
from rich.console import Console
from rich.style import Style

from .rich_check import SKIPPING, RichFailure

log = logging.getLogger()
console = Console()
gh_ssb: Organization | None = None

styles = {
    "normal": Style(blink=True, bold=True),
    "warning": Style(color="dark_orange3", blink=True, bold=True),
    "success": Style(color="green", blink=True, bold=True),
}


class NewBranch(BaseModel):
    """Information used to create a new Git branch.

    Attributes:
        repo_path: Local path to the git repo
        branch_name: Name of the branch to create
        commit_msg: Message that describes the git commit
        files: Files included in the commit
        instruction_msg: Message that should be displayed after the branch was pushed
    """

    repo_path: str
    branch_name: str
    commit_msg: str
    files: set[str]
    instruction_msg: str


def get_decoded_string_from_shell(command: str) -> str:
    """Decodes subprocess output to string."""
    result = subprocess.run(command.split(), stdout=subprocess.PIPE, check=True)
    decoded_result = result.stdout.decode("utf-8").strip()
    return decoded_result


def get_github_org(org_name: str = "statisticsnorway") -> Organization:
    """Gets auth token from the environment and returns Github object."""
    global gh_ssb
    if gh_ssb is None:
        log.debug("Getting Github org '{org_name}'")
        token = get_decoded_string_from_shell("gh auth token")
        gh = github.Github(token)
        gh_ssb = gh.get_organization(org_name)
    return gh_ssb


def create_branch(branch: NewBranch) -> None:
    """Create a new git branch with a set of files."""
    repo = Repo(branch.repo_path)
    current = repo.create_head(branch.branch_name)
    current.checkout()

    if repo.index.diff(None) or repo.untracked_files:
        for f in branch.files:
            repo.git.add(f)
        repo.git.commit(m=branch.commit_msg)
        repo.git.push("--set-upstream", "origin", current)
        print(branch.instruction_msg)
    else:
        console.print("No changes...", style=styles["normal"])


def delete_remote_branch(branch_name: str, repo: Repository) -> None:
    """Deletes a remote branch on specified repo."""
    try:
        ref = repo.get_git_ref(f"heads/{branch_name}")
        ref.delete()
    except UnknownObjectException:
        print("No such branch", branch_name)


def get_repo(repo_name: str, gh_org: Organization | None = None) -> Repository:
    """Gets a repository object given a repository name."""
    if gh_org is None:
        gh_org = get_github_org()
    return gh_org.get_repo(repo_name)


def get_pr(pr_number: int | None, repo_name: str, gh_org: Organization | None = None) -> PullRequest | None:
    """Returns a PR given a PR number and a repository."""
    if pr_number is None:
        console.log(RichFailure(message="PR number was not set in the state file"))
        console.log(SKIPPING)
        return None
    if gh_org is None:
        gh_org = get_github_org()
    repo: Repository = gh_org.get_repo(repo_name)
    try:  # Ensure issue exists
        return repo.get_pull(pr_number)
    except UnknownObjectException:
        console.log(RichFailure(message=f"PR with number {pr_number} was not found"))
        console.log(SKIPPING)
        return None
    except TypeError:
        console.log(RichFailure(message="PR number was not registered in the state file"))
        console.log(SKIPPING)
        return None


def get_commit(sha: str, repo_name: str, gh_org: Organization | None = None) -> Commit:
    """Gets a commit given a sha."""
    if gh_org is None:
        gh_org = get_github_org()
    repo: Repository = gh_org.get_repo(repo_name)
    return repo.get_commit(sha)

def get_last_open_pr_for_user_and_title(repo_name: str, user: str, title: str) -> PullRequest | None:
    """Gets the last opened PR in a given repo by a given user and title."""
    repo = get_repo(repo_name)
    pulls = repo.get_pulls(state="open", sort="created", direction="desc", base=repo.default_branch)
    for pr in pulls:
        if pr.user.login == user and title == pr.title:
            return pr
        
    return None