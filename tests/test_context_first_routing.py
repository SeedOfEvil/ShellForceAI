from shellforgeai.interactive.commands import route_input
from shellforgeai.llm.prompts import build_model_prompt


def test_disk_intents_route_to_diagnose_disk() -> None:
    for phrase in [
        "how much disk space do we have left?",
        "free disk space",
        "is disk full",
    ]:
        routed = route_input(phrase)
        assert routed.name == "diagnose"
        assert routed.args == "disk"


def test_health_intents_route_to_diagnose_health() -> None:
    for phrase in ["my system is glitchy", "machine is acting weird", "any issue on this machine"]:
        routed = route_input(phrase)
        assert routed.name == "diagnose"
        assert routed.args == "health"


def test_prompt_includes_collected_evidence_instruction() -> None:
    prompt = build_model_prompt(
        "how much disk space left",
        {"evidence": [{"tool": "disk.usage", "status": "ok", "summary": "/ 70% used"}]},
    )
    assert "already collected evidence" in prompt
    assert "Do not ask operators to rerun collectors already collected" in prompt
