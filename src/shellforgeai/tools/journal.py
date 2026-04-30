from shellforgeai.util.subprocess import run_command

from .base import ToolResult


def unit(service: str, since: str = "30m", lines: int = 200) -> ToolResult:
    r = run_command(["journalctl", "-u", service, "--since", since, "-n", str(lines), "--no-pager"])
    return ToolResult(
        tool="journal.unit",
        command=r.command,
        exit_code=r.exit_code,
        stdout=r.stdout,
        stderr=r.stderr,
        duration_ms=r.duration_ms,
        ok=r.exit_code == 0,
    )
