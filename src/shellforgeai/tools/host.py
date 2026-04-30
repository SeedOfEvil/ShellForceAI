import os
import platform
import socket
import sys

from shellforgeai.util.subprocess import run_command

from .base import ToolResult


def host_info() -> ToolResult:
    return ToolResult(
        tool="host.info",
        stdout=str(
            {
                "hostname": socket.gethostname(),
                "fqdn": socket.getfqdn(),
                "platform": platform.system(),
                "kernel": platform.release(),
                "arch": platform.machine(),
                "python": sys.version.split()[0],
            }
        ),
    )


def host_resources() -> ToolResult:
    load = os.getloadavg() if hasattr(os, "getloadavg") else None
    return ToolResult(tool="host.resources", stdout=str({"loadavg": load}))


def host_uptime() -> ToolResult:
    r = run_command(["uptime"])
    return ToolResult(tool="host.uptime", command=r.command, exit_code=r.exit_code, stdout=r.stdout, stderr=r.stderr, duration_ms=r.duration_ms, ok=r.exit_code == 0)
