from typer.testing import CliRunner

from shellforgeai.cli import app

runner = CliRunner()


def test_doctor_runs() -> None:
    assert runner.invoke(app, ["doctor"]).exit_code == 0


def test_version_runs() -> None:
    assert runner.invoke(app, ["--version"]).exit_code == 0


def test_inspect_host_runs() -> None:
    assert runner.invoke(app, ["inspect", "host"]).exit_code == 0


def test_tools_list_runs() -> None:
    assert runner.invoke(app, ["tools", "list"]).exit_code == 0


def test_tools_describe() -> None:
    assert runner.invoke(app, ["tools", "describe", "systemd.status"]).exit_code == 0
