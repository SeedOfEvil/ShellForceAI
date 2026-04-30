from shellforgeai.util.subprocess import run_command

from .base import ToolResult


def status(service: str) -> ToolResult:
    r = run_command(["systemctl", "status", service, "--no-pager"])
    return ToolResult(
        tool="systemd.status",
        command=r.command,
        exit_code=r.exit_code,
        stdout=r.stdout,
        stderr=r.stderr,
        duration_ms=r.duration_ms,
        ok=r.exit_code == 0,
    )


def list_failed() -> ToolResult:
    r = run_command(["systemctl", "--failed", "--no-pager"])
    return ToolResult(
        tool="systemd.list_failed",
        command=r.command,
        exit_code=r.exit_code,
        stdout=r.stdout,
        stderr=r.stderr,
        duration_ms=r.duration_ms,
        ok=r.exit_code == 0,
    )
