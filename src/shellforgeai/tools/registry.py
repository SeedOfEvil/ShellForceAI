from shellforgeai.policy.risk import RiskTier

from .base import ToolDefinition

TOOLS = [
    ToolDefinition(
        name="host.info",
        description="Host details",
        risk=RiskTier.read,
        category="host",
        examples=["inspect host"],
    ),
    ToolDefinition(
        name="systemd.status",
        description="systemctl status",
        risk=RiskTier.read,
        category="systemd",
        examples=["inspect service nginx"],
    ),
    ToolDefinition(
        name="journal.unit",
        description="journalctl unit",
        risk=RiskTier.read,
        category="journal",
        examples=["logs nginx --since 30m"],
    ),
]


def list_tools() -> list[ToolDefinition]:
    return TOOLS


def get_tool(name: str) -> ToolDefinition | None:
    return next((t for t in TOOLS if t.name == name), None)
