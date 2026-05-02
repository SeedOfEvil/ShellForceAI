from __future__ import annotations

from pathlib import Path

from . import files
from .base import ToolResult

COMMON = {
    "nginx": ["/var/log/nginx/error.log", "/var/log/nginx/access.log"],
    "ssh": ["/var/log/auth.log", "/var/log/secure"],
    "docker": ["/var/log/docker.log"],
}


def find_common(service: str) -> ToolResult:
    paths = [p for p in COMMON.get(service.lower(), []) if Path(p).exists()]
    return ToolResult(tool="logs.find_common", stdout="\n".join(paths) or "none")


def file_tail(path: str, lines: int = 100) -> ToolResult:
    r = files.tail(path, lines=lines)
    return ToolResult(
        tool="logs.file_tail", ok=r.ok, exit_code=r.exit_code, stdout=r.stdout, stderr=r.stderr
    )


def search_errors(
    path: str, patterns: list[str] | None = None, max_matches: int = 50
) -> ToolResult:
    patterns = patterns or [
        "error",
        "failed",
        "denied",
        "refused",
        "timeout",
        "address already in use",
        "no such file",
        "permission",
    ]
    r = files.read_text(path, max_bytes=131072)
    if not r.ok:
        return ToolResult(tool="logs.search_errors", ok=False, exit_code=1, stderr=r.stderr)
    matches = []
    for ln in r.stdout.splitlines():
        low = ln.lower()
        if any(p in low for p in patterns):
            matches.append(ln)
        if len(matches) >= max_matches:
            break
    return ToolResult(tool="logs.search_errors", stdout="\n".join(matches))
