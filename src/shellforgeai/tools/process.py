from shellforgeai.util.subprocess import run_command

from .base import ToolResult


def top(limit: int = 10) -> ToolResult:
    r = run_command(["ps", "-eo", "pid,ppid,pcpu,pmem,comm", "--sort=-pcpu"])
    out = "\n".join(r.stdout.splitlines()[: limit + 1]) if r.stdout else ""
    return ToolResult(tool="process.top", command=r.command, exit_code=r.exit_code, stdout=out, stderr=r.stderr, duration_ms=r.duration_ms, ok=r.exit_code == 0)
