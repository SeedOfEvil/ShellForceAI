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
            tool=f"process.find {name}",
            command=r.command,
            exit_code=r.exit_code,
            stderr=r.stderr,
            ok=False,
        )
    needles = [name.lower()]
    if name.lower() == "docker":
        needles = ["dockerd", "containerd", "docker-proxy", "rootlesskit"]
    lines = []
    for ln in r.stdout.splitlines():
        low = ln.lower()
        if "shellforgeai" in low:
            continue
        if any(n in low for n in needles):
            lines.append(ln)
    return ToolResult(
        tool=f"process.find {name}",
        command=r.command,
        stdout="\n".join(lines[:50]),
        stderr="not found" if not lines else "",
        exit_code=0,
        ok=bool(lines),
    )
