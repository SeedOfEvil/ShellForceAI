from shellforgeai.llm.codex import CodexProvider
from shellforgeai.llm.schemas import ModelRequest


def test_command_flags(monkeypatch):
    calls = {}

    def fake_run(cmd, capture_output, text, timeout):
        calls["cmd"] = cmd

        class R:
            returncode = 0
            stdout = "ok"
            stderr = ""

        return R()

    monkeypatch.setattr("subprocess.run", fake_run)
    p = CodexProvider()
    r = p.complete(ModelRequest(prompt="hi", model="gpt-5.5", provider="openai-codex"))
    assert r.ok
    c = calls["cmd"]
    assert "exec" in c and "-m" in c and "gpt-5.5" in c
    assert "--sandbox" in c and "read-only" in c
    assert "--json" in c
    assert "--skip-git-repo-check" in c
    assert "--yolo" not in c
