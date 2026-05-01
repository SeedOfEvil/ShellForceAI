from pathlib import Path

from typer.testing import CliRunner

from shellforgeai.cli import app
from shellforgeai.interactive import repl

runner = CliRunner()


def test_no_args_starts_interactive(monkeypatch) -> None:
    called = {"ok": False}

    def _fake(runtime, console) -> None:
        called["ok"] = True

    monkeypatch.setattr("shellforgeai.cli.run_interactive", _fake)
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert called["ok"]


def test_workspace_trust_no_exits(tmp_path: Path, monkeypatch) -> None:
    class DummyConsole:
        def print(self, *_args, **_kwargs):
            return None

        def status(self, *_args, **_kwargs):
            raise AssertionError("should not run status")

    monkeypatch.setattr("builtins.input", lambda _p="": "n")
    store = repl.TrustStore(tmp_path)
    ok = repl.prompt_trust(DummyConsole(), Path.cwd(), None, store)  # type: ignore[arg-type]
    assert not ok


def test_trust_store_persist(tmp_path: Path) -> None:
    store = repl.TrustStore(tmp_path)
    ws = tmp_path / "repo"
    ws.mkdir()
    assert not store.is_trusted(ws)
    store.trust(ws)
    assert store.is_trusted(ws)


def test_help_and_exit_commands(monkeypatch) -> None:
    inputs = iter(["/help", "/exit"])
    monkeypatch.setattr("builtins.input", lambda _p="": next(inputs))

    class DummyStatus:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    class DummyConsole:
        def print(self, *_args, **_kwargs):
            return None

        def clear(self):
            return None

        def status(self, *_args, **_kwargs):
            return DummyStatus()

    from shellforgeai.core.config import load_settings
    from shellforgeai.core.profiles import load_profile
    from shellforgeai.core.session import build_session_context
    from shellforgeai.core.context import RuntimeContext

    settings = load_settings(None)
    profile = load_profile("inspect", Path.cwd())
    session = build_session_context(settings, profile, "inspect", Path.cwd())
    runtime = RuntimeContext(settings=settings, profile=profile, session=session, verbose=False)
    monkeypatch.setattr(repl.TrustStore, "is_trusted", lambda *_: True)

    repl.run_interactive(runtime, DummyConsole())
