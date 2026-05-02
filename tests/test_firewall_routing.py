from shellforgeai.interactive.repl import _is_firewall_question


def test_firewall_question_detection() -> None:
    assert _is_firewall_question("can you find if the firewall is on or off?")
    assert _is_firewall_question("check firewall")
    assert _is_firewall_question("ufw status")
    assert not _is_firewall_question("diagnose disk")
