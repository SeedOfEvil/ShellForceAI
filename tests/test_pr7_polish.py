from typer.testing import CliRunner

from shellforgeai.cli import app
from shellforgeai.interactive.banner import QUOTES, build_banner
from shellforgeai.interactive.repl import _is_machine_health_question, _sanitize_provider_error
from shellforgeai.llm.prompts import build_model_prompt
from shellforgeai.llm.system_prompt import SHELLFORGE_SYSTEM_PROMPT
from shellforgeai.version import get_build_info

runner = CliRunner()


def test_banner_quote_deterministic(monkeypatch):
    class X: ...

    rt = X()
    rt.session = X()
    rt.profile = X()
    rt.settings = X()
    rt.settings.model = X()
    rt.session.mode = "inspect"
    rt.profile.name = "inspect"
    rt.settings.model.provider = "codex"
    rt.settings.model.model = "gpt-5.5"
    panel = build_banner(rt, True, chooser=lambda q: q[0])
    txt = str(panel.renderable)
    assert "ShellForgeAI" in txt and "CLI-first AI Ops for Linux" in txt
    assert QUOTES[0] in txt and "ShellForceAI" not in txt


def test_build_info_env(monkeypatch):
    monkeypatch.setenv("SHELLFORGEAI_BUILD_PR", "7")
    monkeypatch.setenv("SHELLFORGEAI_BUILD_COMMIT", "abc1234")
    b = get_build_info()
    assert b.github_pr == "7" and b.git_commit == "abc1234"


def test_prompt_has_system_identity():
    p = build_model_prompt("q", {"token": "x"})
    assert "You are ShellForgeAI" in p and "validation-only" in p and "[REDACTED]" in p


def test_machine_health_intent_detection():
    assert _is_machine_health_question("Any issue on this machine?")
    assert not _is_machine_health_question("tell me a joke")


def test_bwrap_error_sanitized():
    msg = _sanitize_provider_error("bwrap: No permissions to create a new namespace")
    assert "provider/container sandbox limitation" in msg


def test_system_prompt_disallows_direct_machine_inspection():
    assert "Do not run shell commands" in SHELLFORGE_SYSTEM_PROMPT


def test_interactive_reserved_commands_do_not_call_model(monkeypatch):
    def boom(*args, **kwargs):
        raise AssertionError("model should not be called")

    monkeypatch.setattr("shellforgeai.interactive.repl.build_provider", boom)
    text = "y\n/profile\n/mode\n/audit\n/tools\ndiagnose disk\n/exit\n"
    res = runner.invoke(app, ["interactive", "--no-trust-cache"], input=text)
    assert res.exit_code == 0 and "Profile:" in res.stdout and "Diagnose disk" in res.stdout
