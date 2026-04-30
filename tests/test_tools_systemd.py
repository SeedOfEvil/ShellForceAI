from shellforgeai.tools.systemd import status


def test_systemd_command_construction_mocked(monkeypatch):
    class R:
        command = ["systemctl"]
        exit_code = 0
        stdout = "ok"
        stderr = ""
        duration_ms = 1

    monkeypatch.setattr("shellforgeai.tools.systemd.run_command", lambda *a, **k: R())
    assert status("nginx").ok
