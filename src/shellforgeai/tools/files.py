from pathlib import Path

from .base import ToolResult


def read(path: str, max_bytes: int = 65536) -> ToolResult:
    p = Path(path)
    if not p.exists():
        return ToolResult(tool="files.read", ok=False, exit_code=1, stderr="missing file")
    if p.is_dir():
        return ToolResult(tool="files.read", ok=False, exit_code=1, stderr="path is directory")
    return ToolResult(tool="files.read", stdout=p.read_text(errors="ignore")[:max_bytes])


def stat(path: str) -> ToolResult:
    p = Path(path)
    e = p.exists()
    return ToolResult(
        tool="files.stat",
        stdout=str(
            {
                "path": str(p),
                "exists": e,
                "is_file": p.is_file() if e else False,
                "is_dir": p.is_dir() if e else False,
            }
        ),
    )
