from shellforgeai.core.evidence import TargetType, classify_target
from shellforgeai.interactive.commands import route_input


def test_slowness_phrases_route_to_performance_bundle() -> None:
    for phrase in [
        "my machine is running slow",
        "my computer is slow",
        "my PC is slow",
        "why is this machine slow?",
        "high cpu",
        "high memory",
        "high load",
        "performance issue",
    ]:
        r = route_input(phrase)
        assert r.name == "diagnose"
        assert r.args == "performance"


def test_classify_target_perf_keywords_as_host() -> None:
    assert classify_target("performance") == TargetType.host
    assert classify_target("high cpu") == TargetType.host
