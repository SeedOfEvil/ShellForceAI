from __future__ import annotations

import socket
from urllib.parse import urlparse

from shellforgeai.util.subprocess import run_command

from .base import ToolResult


def listeners() -> ToolResult:
    r = run_command(["ss", "-lntup"])
    return ToolResult(
        tool="network.listeners",
        command=r.command,
        exit_code=r.exit_code,
        stdout=r.stdout,
        stderr=r.stderr,
        duration_ms=r.duration_ms,
        ok=r.exit_code == 0,
    )


def routes() -> ToolResult:
    r = run_command(["ip", "route", "show"])
    return ToolResult(
        tool="network.routes",
        command=r.command,
        exit_code=r.exit_code,
        stdout=r.stdout,
        stderr=r.stderr,
        duration_ms=r.duration_ms,
        ok=r.exit_code == 0,
    )


def dns() -> ToolResult:
    r = run_command(["cat", "/etc/resolv.conf"])
    return ToolResult(
        tool="network.dns",
        command=r.command,
        exit_code=r.exit_code,
        stdout=r.stdout,
        stderr=r.stderr,
        duration_ms=r.duration_ms,
        ok=r.exit_code == 0,
    )


def connect_test_readonly(target: str, port: int = 443, timeout_seconds: int = 3) -> ToolResult:
    host = urlparse(target).hostname or target
    try:
        ip = socket.gethostbyname(host)
        s = socket.create_connection((host, port), timeout=timeout_seconds)
        s.close()
        out = f"resolved={ip}; tcp_connect_ok={host}:{port}"
        return ToolResult(tool="network.connect_test_readonly", stdout=out)
    except Exception as exc:
        return ToolResult(
            tool="network.connect_test_readonly", ok=False, exit_code=1, stderr=str(exc)
        )


def listeners_filtered(pattern: str) -> ToolResult:
    base = listeners()
    if not base.ok:
        return ToolResult(
            tool="network.listeners.filtered",
            command=base.command,
            ok=False,
            exit_code=base.exit_code,
            stderr=base.stderr,
        )
    lines = [ln for ln in base.stdout.splitlines() if pattern.lower() in ln.lower()]
    return ToolResult(
        tool="network.listeners.filtered", command=base.command, stdout="\n".join(lines), ok=True
    )
