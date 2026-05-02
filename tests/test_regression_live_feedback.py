from shellforgeai.tools import firewall, host, registry


def test_tools_registry_exposes_new_collectors() -> None:
    names = {t.name for t in registry.list_tools()}
    assert "system.os_release" in names
    assert "logs.file_tail" in names
    assert "firewall.detect" in names


def test_command_exists_not_found_is_valid_evidence(monkeypatch) -> None:
    class R:
        command = ["which", "docker"]
        exit_code = 1
        stdout = ""
        stderr = ""
        duration_ms = 1

    monkeypatch.setattr("shellforgeai.tools.host.run_command", lambda *_args, **_kwargs: R())
    res = host.command_exists("docker")
    assert res.ok is True
    assert res.exit_code == 0
    assert res.stderr == "not found"


def test_firewall_detect_all_missing(monkeypatch) -> None:
    class R:
        command = ["which", "ufw"]
        exit_code = 1
        stdout = ""
        stderr = ""
        duration_ms = 1

    monkeypatch.setattr("shellforgeai.tools.host.run_command", lambda *_args, **_kwargs: R())
    results = firewall.detect()
    assert results
    assert all(r.tool == "command.exists" for r in results)
