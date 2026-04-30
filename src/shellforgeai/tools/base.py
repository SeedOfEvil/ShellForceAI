from pydantic import BaseModel

from shellforgeai.policy.risk import RiskTier


class ToolDefinition(BaseModel):
    name: str
    description: str
    risk: RiskTier
    category: str
    examples: list[str] = []


class ToolResult(BaseModel):
    tool: str
    command: list[str] = []
    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""
    duration_ms: int = 0
    ok: bool = True
    timestamp: str = ""
