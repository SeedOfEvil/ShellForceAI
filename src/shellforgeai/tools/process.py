from shellforgeai.util.subprocess import run_command

from .base import ToolResult


def top(limit: int = 10) -> ToolResult:
    r = run_command(["ps", "-eo", "pid,ppid,pcpu,pmem,comm", "--sort=-pcpu"])
    out = "\n".join(r.stdout.splitlines()[: limit + 1]) if r.stdout else ""
    return ToolResult(
        tool="process.top",
        command=r.command,
        exit_code=r.exit_code,
        stdout=out,
        stderr=r.stderr,
        duration_ms=r.duration_ms,
        ok=r.exit_code == 0,
    )


def find(name: str) -> ToolResult:
    r = run_command(["ps", "-eo", "pid,comm,args"])
    if r.exit_code != 0:
        return ToolResult(
            tool="process.find", command=r.command, exit_code=r.exit_code, stderr=r.stderr, ok=False
        )
    lines = [ln for ln in r.stdout.splitlines() if name.lower() in ln.lower()]
    return ToolResult(
        tool="process.find", command=r.command, stdout="\n".join(lines[:50]), exit_code=0, ok=True
    )
