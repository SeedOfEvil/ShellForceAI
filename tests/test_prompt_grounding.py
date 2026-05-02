from shellforgeai.llm.prompts import build_model_prompt
from shellforgeai.llm.system_prompt import SHELLFORGE_SYSTEM_PROMPT


def test_system_prompt_includes_collector_rules() -> None:
    assert "CLI-first Linux operations harness" in SHELLFORGE_SYSTEM_PROMPT
    assert "Request ShellForgeAI collectors by name" in SHELLFORGE_SYSTEM_PROMPT
    assert "apply remains validation-only" in SHELLFORGE_SYSTEM_PROMPT


def test_model_prompt_includes_capabilities_and_evidence_block() -> None:
    prompt = build_model_prompt(
        "can you find if the firewall is on or off?",
        {
            "evidence": [
                {"tool": "command.exists ufw", "status": "not_found", "summary": "ufw: not found"},
                {"tool": "command.exists nft", "status": "not_found", "summary": "nft: not found"},
            ]
        },
    )
    assert "Available ShellForgeAI read-only collectors" in prompt
    assert "ShellForgeAI already collected" in prompt
    assert "command.exists ufw: not_found" in prompt
