import io

from dp import lab
from dp.lab import Env
from dp.utils import strip_ansi


def test_doctor_all_commands_successful(mocker):
    mocker.patch("dp.lab._assert_successful_command", return_value=True)
    with mocker.patch("sys.stdout", new=io.StringIO()) as mock_stdout:
        lab.doctor()
        assert "You're aye okay 🎉" in mock_stdout.getvalue()


def test_doctor_kubectl_not_installed(mocker):
    mocker.patch(
        "dp.lab._assert_successful_command",
        side_effect=[ValueError("kubectl is not installed"), None],
    )
    with mocker.patch("sys.stdout", new=io.StringIO()) as mock_stdout:
        lab.doctor()
        assert "kubectl is not installed" in mock_stdout.getvalue()


def test_doctor_helm_not_installed(mocker):
    mocker.patch(
        "dp.lab._assert_successful_command",
        side_effect=[None, ValueError("helm is not installed")],
    )
    with mocker.patch("sys.stdout", new=io.StringIO()) as mock_stdout:
        lab.doctor()
        assert "helm is not installed" in mock_stdout.getvalue()


def test_add_chart_repos_successful(mocker):
    mocker.patch("dp.lab._run_command", return_value=("", "", 0))
    lab.add_chart_repos(verbose=False)
    lab._run_command.assert_any_call(
        "helm repo add dapla-lab-standard https://statisticsnorway.github.io/dapla-lab-helm-charts-standard",
        verbose=False,
    )
    lab._run_command.assert_any_call(
        "helm repo add dapla-lab-experimental https://statisticsnorway.github.io/dapla-lab-helm-charts-experimental",
        verbose=False,
    )


def test_add_chart_repos_error(mocker):
    mocker.patch("dp.lab._run_command", return_value=("", "error", 1))
    with mocker.patch("sys.stderr", new=io.StringIO()) as mock_stderr:
        lab.add_chart_repos(verbose=False)
        assert "error" in mock_stderr.getvalue()


def test_list_services_successful(mocker):
    mocker.patch("dp.lab._run_command", return_value=("service list", "", 0))
    mocker.patch("dp.lab.validate_env")
    with mocker.patch("sys.stdout", new=io.StringIO()) as mock_stdout:
        lab.list_services(env=Env.dev, namespace="some-ns", verbose=True)
        assert "service list" in mock_stdout.getvalue()


def test_kill_service_successful(mocker):
    mocker.patch("dp.lab._run_command", return_value=("", "", 0))
    mocker.patch("dp.lab.validate_env")
    lab.kill_service(
        service_name="test-service",
        env=Env.dev,
        namespace="some-ns",
        dryrun=False,
        verbose=True,
    )
    lab._run_command.assert_called_once_with(
        "helm delete test-service --namespace some-ns", dryrun=False, verbose=True
    )


def test_kill_service_dryrun(mocker):
    mocker.patch("dp.lab._run_command", return_value=("", "", 0))
    mocker.patch("dp.lab.validate_env")
    lab.kill_service(
        service_name="test-service",
        env=Env.dev,
        namespace="some-ns",
        dryrun=True,
        verbose=True,
    )
    lab._run_command.assert_called_once_with(
        "helm delete test-service --namespace some-ns", dryrun=True, verbose=True
    )


def test_kill_services_no_services(mocker):
    mocker.patch("dp.lab._get_helm_releases", return_value=[])
    mocker.patch("dp.lab.validate_env")
    with mocker.patch("sys.stdout", new=io.StringIO()) as mock_stdout:
        lab.kill_services(env=Env.dev, namespace="some-ns", dryrun=False, verbose=True)
        assert "No services found in namespace" in mock_stdout.getvalue()


def test_kill_services_with_services(mocker):
    mocker.patch("dp.lab._get_helm_releases", return_value=[{"name": "test-service"}])
    mocker.patch("dp.lab._run_command", return_value=("", "", 0))
    mocker.patch("dp.lab.validate_env")
    lab.kill_services(env=Env.dev, namespace="some-ns", dryrun=False, verbose=True)
    lab._run_command.assert_called_once_with(
        "helm delete --namespace some-ns test-service", dryrun=False, verbose=True
    )


def test_suspend_services_successful(mocker):
    mocker.patch("dp.lab._get_all_user_namespaces", return_value=["some-ns"])
    mocker.patch(
        "dp.lab._get_helm_releases",
        return_value=[{"name": "test-service", "chart_version": "1.0.0"}],
    )
    mocker.patch("dp.lab._run_command", return_value=("", "", 0))
    mocker.patch(
        "dp.lab._determine_chart_name", return_value="dapla-lab-standard/test-service"
    )
    mocker.patch("dp.lab.validate_env")
    with mocker.patch("sys.stdout", new=io.StringIO()) as mock_stdout:
        lab.suspend_services(
            env=Env.dev,
            namespace="some-ns",
            dryrun=False,
            verbose=True,
            unsuspend=False,
        )
        output = mock_stdout.getvalue()
        assert "Suspended 1 services" in strip_ansi(output)


def test_suspend_services_error(mocker):
    mocker.patch("dp.lab._get_all_user_namespaces", return_value=["some-ns"])
    mocker.patch(
        "dp.lab._get_helm_releases",
        return_value=[{"name": "test-service", "chart_version": "1.0.0"}],
    )
    mocker.patch("dp.lab._run_command", return_value=("", "error", 1))
    mocker.patch(
        "dp.lab._determine_chart_name", return_value="dapla-lab-standard/test-service"
    )
    mocker.patch("dp.lab.validate_env")
    with mocker.patch("sys.stdout", new=io.StringIO()) as mock_stdout:
        lab.suspend_services(
            env=Env.dev,
            namespace="some-ns",
            dryrun=False,
            verbose=True,
            unsuspend=False,
        )
        assert "Error: Could not suspend service test-service" in mock_stdout.getvalue()
