from __future__ import annotations

from . import files, host, logs, network, process
from .base import ToolResult


def nginx_detect() -> list[ToolResult]:
    return [
        host.command_exists("nginx"),
        process.find("nginx"),
        network.listeners_filtered(":80"),
        network.listeners_filtered(":443"),
        files.exists("/etc/nginx/nginx.conf"),
        logs.find_common("nginx"),
        logs.file_tail("/var/log/nginx/error.log"),
    ]


def ssh_detect() -> list[ToolResult]:
    return [
        host.command_exists("sshd"),
        process.find("sshd"),
        network.listeners_filtered(":22"),
        files.exists("/etc/ssh/sshd_config"),
        logs.find_common("ssh"),
    ]


def docker_detect() -> list[ToolResult]:
    return [
        host.command_exists("docker"),
        process.find("dockerd"),
        files.exists("/var/run/docker.sock"),
    ]
