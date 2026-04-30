from shellforgeai.core.evidence import TargetType, classify_target
from shellforgeai.core.plans import Plan, PlanStep
from shellforgeai.tools.registry import get_tool
from shellforgeai.util.text import truncate_text


def test_target_classification():
    assert classify_target("nginx") == TargetType.service
    assert classify_target("disk space") == TargetType.disk


def test_truncate_text():
    t, truncated = truncate_text("x" * 20, max_chars=10)
    assert truncated is True
    assert len(t) == 10


def test_plan_model_serialization():
    p = Plan(
        plan_id="p1",
        goal="g",
        session_id="s1",
        steps=[PlanStep(step_id="1", title="t", description="d")],
    )
    assert '"plan_id":"p1"' in p.model_dump_json()


def test_tool_registry_new_tools():
    assert get_tool("disk.usage") is not None
    assert get_tool("network.connect_test_readonly") is not None
