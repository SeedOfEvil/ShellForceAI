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
        name="host.resources",
        description="Host load/resources",
        risk=RiskTier.read,
        category="host",
        examples=["inspect host"],
    ),
    ToolDefinition(
        name="host.uptime",
        description="Host uptime",
        risk=RiskTier.read,
        category="host",
        examples=["inspect host"],
    ),
    ToolDefinition(
        name="systemd.status",
        description="systemctl status",
        risk=RiskTier.read,
        category="service",
        examples=["inspect service nginx"],
    ),
    ToolDefinition(
        name="systemd.list_failed",
        description="systemctl --failed",
        risk=RiskTier.read,
        category="service",
        examples=["diagnose nginx"],
    ),
    ToolDefinition(
        name="journal.unit",
        description="journalctl unit",
        risk=RiskTier.read,
        category="logs",
        examples=["logs nginx --since 30m"],
    ),
    ToolDefinition(
        name="files.read",
        description="Read file",
        risk=RiskTier.read,
        category="files",
        examples=["tools describe files.read"],
    ),
    ToolDefinition(
        name="files.stat",
        description="Stat file",
        risk=RiskTier.read,
        category="files",
        examples=["tools describe files.stat"],
    ),
    ToolDefinition(
        name="files.grep",
        description="Grep file",
        risk=RiskTier.read,
        category="files",
        examples=["tools describe files.grep"],
    ),
    ToolDefinition(
        name="network.listeners",
        description="Listening sockets",
        risk=RiskTier.read,
        category="network",
        examples=["diagnose network"],
    ),
    ToolDefinition(
        name="network.routes",
        description="Routes",
        risk=RiskTier.read,
        category="network",
        examples=["diagnose network"],
    ),
    ToolDefinition(
        name="network.dns",
        description="DNS resolver config",
        risk=RiskTier.read,
        category="network",
        examples=["diagnose network"],
    ),
    ToolDefinition(
        name="network.connect_test_readonly",
        description="Safe DNS/TCP connect test",
        risk=RiskTier.read,
        category="network",
        examples=["research connectivity"],
    ),
    ToolDefinition(
        name="packages.list",
        description="List packages",
        risk=RiskTier.read,
        category="packages",
        examples=["diagnose host"],
    ),
    ToolDefinition(
        name="disk.usage",
        description="Filesystem usage",
        risk=RiskTier.read,
        category="disk",
        examples=["diagnose disk"],
    ),
    ToolDefinition(
        name="disk.inodes",
        description="Filesystem inode usage",
        risk=RiskTier.read,
        category="disk",
        examples=["diagnose disk"],
    ),
    ToolDefinition(
        name="process.top",
        description="Top processes",
        risk=RiskTier.read,
        category="process",
        examples=["diagnose host"],
    ),
]


def list_tools() -> list[ToolDefinition]:
    return TOOLS


def get_tool(name: str) -> ToolDefinition | None:
    return next((t for t in TOOLS if t.name == name), None)
