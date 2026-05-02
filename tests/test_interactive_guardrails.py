from typer.testing import CliRunner

from shellforgeai.cli import app
from shellforgeai.interactive.guards import looks_like_shell_command

runner = CliRunner()


def test_shell_guard_detects_examples() -> None:
    assert looks_like_shell_command("sudo docker exec -it shellforgeai sh -lc 'echo hi'")
    assert looks_like_shell_command("docker compose up -d")
    assert looks_like_shell_command("for d in $(ls -td /data/artifacts/sf_*); do")
    assert looks_like_shell_command("done")


def test_blocked_shell_input_no_model_call(monkeypatch) -> None:
    def boom(*args, **kwargs):
        raise AssertionError("model should not be called")

    monkeypatch.setattr("shellforgeai.interactive.repl.build_provider", boom)
    res = runner.invoke(
        app,
        ["interactive", "--no-trust-cache"],
        input="y\nsudo docker exec -it shellforgeai sh\n/help\n/exit\n",
    )
    assert res.exit_code == 0
    assert "This looks like a shell command pasted" in res.stdout
    assert "Session:" in res.stdout


def test_explicit_ask_shell_explain_calls_model(monkeypatch) -> None:
    called = {"v": False}

    class P:
        def complete(self, req):
            called["v"] = True

            class R:
                text = "ok"

            return R()

    monkeypatch.setattr("shellforgeai.interactive.repl.build_provider", lambda *_: P())
    res = runner.invoke(
        app,
        ["interactive", "--no-trust-cache"],
        input="y\nask explain this command: sudo docker exec -it x y\n/exit\n",
    )
    assert res.exit_code == 0
    assert called["v"]


def test_audit_latest_no_model(monkeypatch) -> None:
    def boom(*args, **kwargs):
        raise AssertionError("model should not be called")

    monkeypatch.setattr("shellforgeai.interactive.repl.build_provider", boom)
    res = runner.invoke(app, ["interactive", "--no-trust-cache"], input="y\n/audit latest\n/exit\n")
    assert res.exit_code == 0
    assert "No audit sessions found." in res.stdout
