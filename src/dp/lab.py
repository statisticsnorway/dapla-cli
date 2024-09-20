import json
import logging
from collections.abc import Callable
from datetime import datetime
from enum import Enum
from typing import Annotated, Any

import typer
from pydantic import BaseModel
from rich import print
from rich.console import Console
from typer import Typer

from .annotations import dryrunnable
from .utils import RunResult, green, hours_since, print_err, red, run

app = Typer()
err = Console(stderr=True, force_terminal=True)
logger = logging.getLogger(__name__)

dt_format = "2006-01-02T15:04:05.999999999Z"


class Env(str, Enum):
    """Denotes the environment to operate on."""

    prod = "prod"
    test = "test"
    dev = "dev"


class OperationType(str, Enum):
    """Denotes the operation type to perform on services when processing services."""

    suspend = "suspend"
    unsuspend = "unsuspend"
    kill = "kill"
    prune = "prune"


class Service(BaseModel):
    """A Dapla Lab service."""

    name: str
    namespace: str
    revision: str | None = None
    updated: datetime | None = None
    status: str | None = None
    suspended: bool | None = None
    chart: str | None = None
    app_version: str | None = None
    chart_version: str | None = None
    created: datetime | None = None


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
        res = run(f"helm repo add {name} {url}", verbose=verbose)
        if res.returncode != 0:
            print_err(res.stderr)


@app.command()
def doctor() -> None:
    """Check if required tooling and environment is ok."""
    try:
        _assert_successful_command(
            "which kubectl", "kubectl is not installed", "kubectl"
        )
        _assert_successful_command("which helm", "helm is not installed", "helm")
    except ValueError as e:
        print(red(e))

    print(green("You're aye okay 🎉"))


@app.command()
def list_services(
    env: env_option,
    namespace: namespace_option,
    verbose: verbose_option = False,
) -> None:
    """List all services in the specified namespace."""
    _validate_env(env)
    res = run(f"helm list --namespace {namespace}", verbose=verbose)
    print(res.stdout)


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
    _validate_env(env)
    _kill(Service(name=service_name, namespace=namespace), dryrun, verbose)


@app.command()
@dryrunnable
def kill_services(
    env: env_option,
    namespace: namespace_option,
    dryrun: dryrun_option = False,
    verbose: verbose_option = False,
) -> None:
    """Kill all services in the specified namespace.

    If the namespace is set to 'all', all user namespaces will be affected.
    """
    _process_services(env, namespace, OperationType.kill, dryrun, verbose)


@app.command()
@dryrunnable
def suspend_services(
    env: env_option,
    namespace: namespace_option,
    dryrun: dryrun_option = False,
    verbose: verbose_option = False,
) -> None:
    """Suspend user services.

    All services in the specified namespace will be suspended or unsuspended. If the namespace is set to 'all', all
    user namespaces will be affected.
    """
    _process_services(env, namespace, OperationType.suspend, dryrun, verbose)


@app.command()
@dryrunnable
def unsuspend_services(
    env: env_option,
    namespace: namespace_option,
    dryrun: dryrun_option = False,
    verbose: verbose_option = False,
) -> None:
    """Unsuspend user services.

    All services in the specified namespace will be unsuspended. If the namespace is set to 'all', all user namespaces
    will be affected.
    """
    _process_services(env, namespace, OperationType.unsuspend, dryrun, verbose)


@app.command()
@dryrunnable
def prune_services(
    env: env_option,
    namespace: namespace_option,
    dryrun: dryrun_option = False,
    verbose: verbose_option = False,
) -> None:
    """Prune services."""
    _process_services(env, namespace, OperationType.prune, dryrun, verbose)


def _process_services(
    env: Env, namespace: str, operation: OperationType, dryrun: bool, verbose: bool
) -> None:
    """Process user services.

    Processing means either suspending, unsuspending or killing services, possibly based on a time condition.
    The supplied operation type determines what action to take.

    All services in the specified namespace will be processed. If the namespace is set to 'all', all
    user namespaces will be affected.
    """
    _validate_env(env)
    processed_count = 0
    skipped_count = 0
    namespaces = _get_all_user_namespaces() if namespace == "all" else [namespace]

    for ns in namespaces:
        # We don't need detailed info such as history for kill operations
        comprehensive_search = operation not in [OperationType.kill]
        services = _find_services(ns, verbose, comprehensive=comprehensive_search)
        if not services:
            print_err(f"No services found in {ns} namespace")
            raise typer.Exit(code=1)

        for service in services:
            try:
                action = _actions(service, dryrun, verbose)[operation]
                res = action()
                if res.returncode != 0:
                    skipped_count += 1
                    print(
                        red(
                            f"Error: Could not {operation.value} service {service.name} in namespace {ns}. {res.stderr}"
                        )
                    )
                else:
                    processed_count += 1

            except ValueError as e:
                print(red(f"{e}. Skipping this service."))
                skipped_count += 1
                continue

    print(
        f"{_conjugate(operation, capitalize=True)} {processed_count} services, skipped {skipped_count} (total: {processed_count+skipped_count}) from {len(namespaces)} namespaces"
    )


def _actions(
    service: Service, dryrun: bool, verbose: bool
) -> dict[OperationType, Callable[[], RunResult]]:
    return {
        OperationType.suspend: lambda: _suspend(service, dryrun, verbose),
        OperationType.unsuspend: lambda: _unsuspend(service, dryrun, verbose),
        OperationType.kill: lambda: _kill(service, dryrun, verbose),
        OperationType.prune: lambda: _prune(service, dryrun, verbose),
    }


def _suspend(service: Service, dryrun: bool, verbose: bool) -> RunResult:
    logger.info(f"Suspend {service.name} in namespace {service.namespace}")
    chart_name = _determine_chart_name(service.name)

    if not service.suspended:
        return run(
            f"helm upgrade {service.name} {chart_name} --namespace {service.namespace} --reuse-values --set global.suspend=True --version {service.chart_version} --history-max 0 --timeout 10m",
            dryrun=dryrun,
            verbose=verbose,
        )
    else:
        logger.info(
            f"Ignoring {service.name} in namespace {service.namespace} as it has already been suspended"
        )
        return RunResult(stdout="Not suspended", stderr="", returncode=0)


def _unsuspend(service: Service, dryrun: bool, verbose: bool) -> RunResult:
    logger.info(f"Unsuspend {service.name} in namespace {service.namespace}")
    chart_name = _determine_chart_name(service.name)

    if service.suspended:
        return run(
            f"helm upgrade {service.name} {chart_name} --namespace {service.namespace} --reuse-values --set global.suspend=False --version {service.chart_version} --history-max 0 --timeout 10m",
            dryrun=dryrun,
            verbose=verbose,
        )
    else:
        logger.info(
            f"Ignoring {service.name} in namespace {service.namespace} as it is not suspended"
        )
        return RunResult(stdout="Not suspended", stderr="", returncode=0)


def _kill(service: Service, dryrun: bool, verbose: bool) -> RunResult:
    logger.info(f"Kill service {service.name} in namespace {service.namespace}")
    return run(
        f"helm delete {service.name} --namespace {service.namespace}",
        dryrun=dryrun,
        verbose=verbose,
    )


def _prune(
    service: Service,
    dryrun: bool,
    verbose: bool,
    kill_threshold: int = 168,
    kill_suspended_threshold: int = 48,
    suspend_threshold: int = 0,
) -> RunResult:
    """Prune services based on a time threshold.

    * Kill a service if it has been running for more than kill_threshold hours (defaults to 1 week).
    * Kill a service if it has been suspended for more than kill_suspended_threshold hours (defaults to 2 days).
    * Kill a service if its status is failed.
    * Suspend a service if it has not been updated in the last suspend_threshold hours (defaults to immediately).
    """
    hours_since_started = hours_since(service.created) if service.created else 0
    hours_since_updated = hours_since(service.updated) if service.updated else 0
    if service.status == "failed":
        logger.info(
            f"Service {service.name} in namespace {service.namespace} has status failed. Terminating..."
        )
        return _kill(service, dryrun, verbose)

    if hours_since_started >= kill_threshold:
        logger.info(
            f"Service {service.name} in namespace {service.namespace} was started {hours_since_started} hours ago. Terminating..."
        )
        return _kill(service, dryrun, verbose)
    elif service.suspended and hours_since_updated >= kill_suspended_threshold:
        logger.info(
            f"Service {service.name} in namespace {service.namespace} was suspended {hours_since_updated} hours ago. Terminating..."
        )
        return _kill(service, dryrun, verbose)

    elif hours_since_updated >= suspend_threshold:
        return _suspend(service, dryrun, verbose)

    else:
        logger.info(
            f"Ignoring service {service.name} in namespace {service.namespace} as it was updated less than {suspend_threshold} hours ago"
        )
        return RunResult(stdout="Ignored", stderr="", returncode=0)


def _validate_env(env: Env) -> None:
    """Validate that the current kubernetes context is a dapla-lab context and matches the specified environment."""
    current_context_name = _get_current_cluster_name()
    if not current_context_name.startswith("gke_dapla-lab-"):
        print_err(
            f"Current context is {current_context_name}. Please switch to a dapla-lab context."
        )
        raise typer.Exit(code=1)

    if not current_context_name.endswith(env.value):
        print_err(
            f"Invalid environment {env.value}. Current context is {current_context_name}. Please switch your kubernetes context."
        )
        raise typer.Exit(code=1)


def _get_all_user_namespaces() -> list[str]:
    res = run(
        "kubectl get namespaces --no-headers -o custom-columns=':metadata.name' | grep '^user-'"
    )
    return res.stdout.strip().split("\n")


def _find_services(
    namespace: str, verbose: bool, comprehensive: bool = True
) -> list[Service]:
    """Find Dapla Lab user services in the specified namespace.

    :param namespace: the k8s namespace to search for services in
    :param verbose: if True, prints executed commands to stdout
    :param comprehensive: if True, fetches history and values for each service
    :return: a list of Service objects
    """
    res = run(
        f"helm list --namespace {namespace} --time-format {dt_format} --output json",
        verbose=verbose,
    )
    helm_releases: list[dict[str, Any]] = json.loads(res.stdout)

    for release in helm_releases:
        release_name = release["name"]
        version = release.get("chart", "").split("-")[-1]
        release["chart_version"] = version

        if comprehensive:
            history = _get_helm_release_history(release_name, namespace)
            release["created"] = history[0]["updated"]

            values = _get_helm_release_values(release_name, namespace)
            release["suspended"] = values["global"]["suspend"]

    services: list[Service] = [Service(**data) for data in helm_releases]

    return services


def _get_helm_release_values(
    helm_release_name: str, namespace: str, verbose: bool = False
) -> dict[str, Any]:
    res = run(
        f"helm get values {helm_release_name} --namespace {namespace} --output json",
        verbose=verbose,
    )
    values: dict[str, Any] = json.loads(res.stdout)
    return values


def _get_helm_release_history(
    release_name: str, namespace: str, verbose: bool = False
) -> list[dict[str, Any]]:
    res = run(
        f"helm history {release_name} --namespace {namespace} --output json",
        verbose=verbose,
    )
    values: list[dict[str, Any]] = json.loads(res.stdout)
    return values


def _get_current_cluster_name() -> str:
    res = run("kubectl config view --minify -o jsonpath='{.clusters[0].name}'")
    return res.stdout


# TODO: We should retrieve the chart name from the release values/annotations instead of guessing.
def _determine_chart_name(helm_release_name: str) -> str:
    """Guess the helm chart name based on the release name."""
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


def _assert_successful_command(cmd: str, err_msg: str, success_msg: str | None) -> None:
    res = run(f"eval {cmd} > /dev/null")
    if res.returncode != 0:
        err.print(f"❌  {red(err_msg)}")
        raise typer.Exit(code=res.returncode)
    if success_msg:
        print(f"✔️ {success_msg}")


def _conjugate(operation: OperationType, capitalize: bool = False) -> str:
    """Conjugate operations into past tense."""
    if operation.value.endswith("e"):
        past_tense = operation.value + "d"  # Don't add an extra "e"
    else:
        past_tense = operation.value + "ed"

    return past_tense.capitalize() if capitalize else past_tense
