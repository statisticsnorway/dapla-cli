import io
from unittest.mock import patch

from dp import lab


def test_doctor():
    with patch("dp.lab._assert_successful_command") as mock_command:

        # Test when all commands are successful
        mock_command.return_value = True
        with patch("sys.stdout", new=io.StringIO()) as mock_stdout:
            lab.doctor()
            assert "You're aye okay 🎉" in mock_stdout.getvalue()

        # Test when kubectl is not installed
        mock_command.side_effect = [ValueError("kubectl is not installed"), None, None]
        with patch("sys.stdout", new=io.StringIO()) as mock_stdout:
            lab.doctor()
            assert "kubectl is not installed" in mock_stdout.getvalue()

        # Test when helm is not installed
        mock_command.side_effect = [None, ValueError("helm is not installed"), None]
        with patch("sys.stdout", new=io.StringIO()) as mock_stdout:
            lab.doctor()
            assert "helm is not installed" in mock_stdout.getvalue()


def test_add_chart_repos(mocker):
    _run_command_spy = mocker.spy(lab, "_run_command")

    lab.add_chart_repos()

    expected_calls = [
        mocker.call(
            "helm repo add dapla-lab-standard https://statisticsnorway.github.io/dapla-lab-helm-charts-standard",
            verbose=False,
        ),
        mocker.call(
            "helm repo add dapla-lab-experimental https://statisticsnorway.github.io/dapla-lab-helm-charts-experimental",
            verbose=False,
        ),
    ]

    assert _run_command_spy.call_args_list == expected_calls


def test_list_services(mocker):
    mocker.patch("dp.lab._run_command", return_value=("service list", None))
    mocker.patch("dp.lab.validate_env")

    lab.list_services("dev", "some-ns", True)

    lab._run_command.assert_called_once_with(
        "helm list --namespace some-ns", verbose=True
    )
    lab.validate_env.assert_called_once_with("dev")
