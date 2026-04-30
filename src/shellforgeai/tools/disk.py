from shellforgeai.util.subprocess import run_command

from .base import ToolResult


def usage() -> ToolResult:
    r = run_command(["df", "-hP"])
    return ToolResult(tool="disk.usage", command=r.command, exit_code=r.exit_code, stdout=r.stdout, stderr=r.stderr, duration_ms=r.duration_ms, ok=r.exit_code == 0)


def inodes() -> ToolResult:
    r = run_command(["df", "-ihP"])
    return ToolResult(tool="disk.inodes", command=r.command, exit_code=r.exit_code, stdout=r.stdout, stderr=r.stderr, duration_ms=r.duration_ms, ok=r.exit_code == 0)
