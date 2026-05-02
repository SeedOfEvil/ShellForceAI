from __future__ import annotations

import json
import os
from pathlib import Path

from shellforgeai.util.subprocess import run_command

from .base import ToolResult


def os_release() -> ToolResult:
    p = Path("/etc/os-release")
    if not p.exists():
        return ToolResult(tool="system.os_release", ok=False, exit_code=1, stderr="unavailable")
    data = {}
    for ln in p.read_text(errors="ignore").splitlines():
        if "=" in ln:
            k, v = ln.split("=", 1)
            data[k.lower()] = v.strip().strip('"')
    out = {k: data.get(k) for k in ["name", "version", "id", "pretty_name"]}
    return ToolResult(tool="system.os_release", stdout=json.dumps(out))


def cpu_memory() -> ToolResult:
    mem = {}
    meminfo = Path("/proc/meminfo")
    if meminfo.exists():
        for ln in meminfo.read_text(errors="ignore").splitlines():
            if ":" in ln:
                k, v = ln.split(":", 1)
                mem[k.strip()] = v.strip()
    loadavg = (
        Path("/proc/loadavg").read_text().split()[:3] if Path("/proc/loadavg").exists() else []
    )
    out = {
        "cpu_count": os.cpu_count(),
        "loadavg": loadavg,
        "mem_total": mem.get("MemTotal"),
        "mem_free": mem.get("MemFree"),
        "mem_available": mem.get("MemAvailable"),
        "swap_total": mem.get("SwapTotal"),
        "swap_free": mem.get("SwapFree"),
    }
    return ToolResult(tool="system.cpu_memory", stdout=json.dumps(out))


def container_detect() -> ToolResult:
    hints = []
    if Path("/.dockerenv").exists():
        hints.append("docker")
    if Path("/run/.containerenv").exists():
        hints.append("podman")
    cgroup = (
        Path("/proc/1/cgroup").read_text(errors="ignore") if Path("/proc/1/cgroup").exists() else ""
    )
    for runtime in ["docker", "containerd", "podman", "lxc"]:
        if runtime in cgroup:
            hints.append(runtime)
    is_container = "yes" if hints else "unknown"
    runtime = hints[0] if hints else "unknown"
    return ToolResult(
        tool="system.container_detect",
        stdout=json.dumps({"is_container": is_container, "runtime_hint": runtime}),
    )


def kernel_messages_tail() -> ToolResult:
    r = run_command(["dmesg", "-T", "--level=err,warn"], timeout_seconds=5)
    ok = r.exit_code == 0
    return ToolResult(
        tool="system.kernel_messages_tail",
        command=r.command,
        exit_code=r.exit_code,
        stdout=r.stdout[-16000:],
        stderr=r.stderr,
        duration_ms=r.duration_ms,
        ok=ok,
    )
