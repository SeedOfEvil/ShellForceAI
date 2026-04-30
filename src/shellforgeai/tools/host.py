import os
import platform
import socket
import sys

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
