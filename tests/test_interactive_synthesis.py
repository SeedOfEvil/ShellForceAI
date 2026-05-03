from shellforgeai.interactive.repl import _deterministic_operator_summary


def test_deterministic_operator_summary_has_sections() -> None:
    txt = _deterministic_operator_summary(
        "health",
        [
            {"tool": "disk.usage", "status": "ok", "summary": "/ 86% used"},
            {"tool": "disk.inodes", "status": "ok", "summary": "/ 67% used"},
            {"tool": "system.container_detect", "status": "ok", "summary": "container=docker"},
            {
                "tool": "systemd.list_failed",
                "status": "unavailable",
                "summary": "systemctl not found",
            },
            {"tool": "host.resources", "status": "ok", "summary": "loadavg=2.42,2.78,3.10"},
        ],
    )
    assert "## Assessment" in txt
    assert "## Facts found" in txt
    assert "## Clues / likely causes" in txt
    assert "disk usage is elevated" in txt.lower()
