import json
import logging
import subprocess
from enum import Enum
from typing import Annotated, Any

import typer
from rich import print
from rich.console import Console
from typer import Typer

from .annotations import dryrunnable
from .utils import green, grey, print_err, red

app = Typer()
err = Console(stderr=True, force_terminal=True)
logger = logging.getLogger(__name__)


class Env(str, Enum):
    """Denotes the environment to operate on."""

    prod = "prod"
    test = "test"
    dev = "dev"


# Common options
env_option = Annotated[
    Env,
    typer.Option("--env", "-e", case_sensitive=False),
]
namespace_option = Annotated[
    str,
    typer.Option(
        "--namespace",
        "-n",
        help="The namespace to operate on, such as `user-ssb-abc`.",
    ),
]
service_name_option = Annotated[str, typer.Option("--name", "-s")]
dryrun_option = Annotated[
    bool, typer.Option("--dryrun", help="Run the command without mutating any state")
]
verbose_option = Annotated[
    bool,
    typer.Option("--verbose", "-v", help="Be verbose and print extra information"),
]


@app.command()
def doctor() -> None:
    """Check if required tooling and environment is ok."""
    try:
        _assert_successful_command("kubectl version", "kubectl is not installed")
        _assert_successful_command("helm version", "helm is not installed")
    except ValueError as e:
        print(red(e))

    print(green("You're aye okay 🎉"))


@app.command()
def add_chart_repos(
    verbose: verbose_option = False,
) -> None:
    """Add required dapla-lab service helm chart repositories.

    The repositories must be added before we can modify helm releases (such as suspending services).
    """
    chart_repos = {
        "dapla-lab-standard": "https://statisticsnorway.github.io/dapla-lab-helm-charts-standard",
        "dapla-lab-experimental": "https://statisticsnorway.github.io/dapla-lab-helm-charts-experimental",
    }

    for name, url in chart_repos.items():
        res = _run_command(f"helm repo add {name} {url}", verbose=verbose)
        if res[2] != 0:
            print_err(res[1])


@app.command()
def list_services(
    env: env_option,
    namespace: namespace_option,
    verbose: verbose_option = False,
) -> None:
    """List all services in the specified namespace."""
    validate_env(env)
    res = _run_command(f"helm list --namespace {namespace}", verbose=verbose)
    print(res[0])


@app.command()
@dryrunnable
def kill_service(
    service_name: str,
    env: env_option,
    namespace: namespace_option,
    dryrun: dryrun_option = False,
    verbose: verbose_option = False,
) -> None:
    """Kill a service in the specified namespace."""
    validate_env(env)
    logger.info(f"Kill service {service_name} in namespace {namespace}")
    _run_command(
        f"helm delete {service_name} --namespace {namespace}",
        dryrun=dryrun,
        verbose=verbose,
    )


@app.command()
@dryrunnable
def kill_services(
    env: env_option,
    namespace: namespace_option,
    dryrun: dryrun_option = False,
    verbose: verbose_option = False,
) -> None:
    """Kill all services in the specified namespace."""
    validate_env(env)
    services = _get_helm_releases(namespace)

    if len(services) == 0:
        print("No services found in namespace {namespace}")
    else:
        for svc in services:
            logger.info(f"Kill service {svc['name']} in namespace {namespace}")
            if not dryrun:
                _run_command(
                    f"helm delete --namespace {namespace} {svc['name']}",
                    dryrun=dryrun,
                    verbose=verbose,
                )


@app.command()
@dryrunnable
def suspend_services(
    env: env_option,
    namespace: namespace_option,
    dryrun: dryrun_option = False,
    verbose: verbose_option = False,
    unsuspend: Annotated[
        bool,
        typer.Option("--unsuspend", help="Unsuspend services (instead of suspend)"),
    ] = False,
) -> None:
    """Suspend or unsuspend user services.

    All services in the specified namespace will be suspended or unsuspended. If the namespace is set to 'all', all
    user namespaces will be affected.
    """
    validate_env(env)
    suspend = True if not unsuspend else False
    processed_count = 0
    skipped_count = 0
    namespaces = _get_all_user_namespaces() if namespace == "all" else [namespace]

    for ns in namespaces:
        services = _get_helm_releases(ns)
        for svc in services:
            release_name = svc["name"]
            chart_version = svc["chart_version"]
            logger.info(
                f"{'Suspend' if suspend else 'Unsuspend'} {release_name} in namespace {ns}"
            )
            try:
                chart_name = _determine_chart_name(svc["name"])
            except ValueError as e:
                print(red(f"{e}. Skipping this service."))
                skipped_count += 1
                continue

            res = _run_command(
                f"helm upgrade {release_name} {chart_name} --reuse-values --set global.suspend={suspend} --version {chart_version} --history-max 0 --timeout 10m --namespace {ns}",
                dryrun=dryrun,
                verbose=verbose,
            )
            if res[2] != 0:
                skipped_count += 1
                print(
                    red(
                        f"Error: Could not suspend service {release_name} in namespace {ns}. {res[1]}"
                    )
                )
            else:
                processed_count += 1

    print(
        f"Suspended {processed_count} services, skipped {skipped_count} (total: {processed_count+skipped_count}) from {len(namespaces)} namespaces"
    )


def validate_env(env: Env) -> None:
    """Validate that the current kubernetes context is a dapla-lab context and matches the specified environment."""
    current_context_name = _get_current_cluster_name()
    if not current_context_name.startswith("gke_dapla-lab-"):
        print_err(
            f"Current context is {current_context_name}. Please switch to a dapla-lab context."
        )
        raise typer.Exit(code=1)

    if not current_context_name.endswith(env.value):
        print_err(
            f"Invalid environment {env}. Current context is {current_context_name}. Please switch your kubernetes context."
        )
        raise typer.Exit(code=1)


def _run_command(
    command: str, dryrun: bool = False, verbose: bool = False
) -> tuple[str, str, int]:
    """Runs a shell command and returns its output and error status."""
    if verbose:
        print(grey(f"{'DRYRUN: ' if dryrun else ''}{command}"))

    if dryrun:
        return "", "", 0

    result = subprocess.run(command, shell=True, text=True, capture_output=True)
    return result.stdout, result.stderr, result.returncode


def _get_all_user_namespaces() -> list[str]:
    res = _run_command(
        "kubectl get namespaces --no-headers -o custom-columns=':metadata.name' | grep '^user-'"
    )
    return res[0].strip().split("\n")


def _get_helm_releases(namespace: str) -> list[dict[str, Any]]:
    res = _run_command(f"helm list --namespace {namespace} --output json")
    helm_releases: list[dict[str, Any]] = json.loads(res[0])

    for release in helm_releases:
        version = release.get("chart", "").split("-")[-1]
        release["chart_version"] = version

    return helm_releases


def _get_helm_release_values(helm_release_name: str, namespace: str) -> dict[str, Any]:
    res = _run_command(
        f"helm get values {helm_release_name} --namespace {namespace} --output json"
    )
    values: dict[str, Any] = json.loads(res[0])
    return values


def _get_current_cluster_name() -> str:
    res = _run_command("kubectl config view --minify -o jsonpath='{.clusters[0].name}'")
    return res[0]


def _get_all_services() -> list[dict[str, str]]:
    all_services = []
    for ns in _get_all_user_namespaces():
        services = _get_helm_releases(ns)
        all_services.extend(services)

    return all_services


def _determine_chart_name(helm_release_name: str) -> str:
    """Guess the helm chart name based on the release name.

    TODO: We should retrieve the chart name from the release values/annotations instead of guessing.
    """
    catalogs = {
        "jupyter-playground": "dapla-lab-standard",
        "jupyter": "dapla-lab-standard",
        "vscode-python": "dapla-lab-standard",
        "rstudio": "dapla-lab-standard",
        "datadoc": "dapla-lab-standard",
    }

    for service_name, catalog in catalogs.items():
        if service_name in helm_release_name.lower():
            return f"{catalog}/{service_name}"

    raise ValueError(
        f"Could not determine helm chart catalog for helm release {helm_release_name}"
    )


def _assert_successful_command(cmd: str, msg: str) -> None:
    res = _run_command(f"eval {cmd} > /dev/null")
    if res[2] != 0:
        err.print(red(msg))
        raise typer.Exit(code=1)
