from __future__ import annotations

from shellforgeai.util.subprocess import run_command

from .base import ToolResult
from .host import command_exists


def detect() -> list[ToolResult]:
    checks = [command_exists(c) for c in ["ufw", "firewall-cmd", "nft", "iptables", "pve-firewall"]]
    out: list[ToolResult] = [*checks]
    present = {c.command[-1]: c.ok and bool((c.stdout or "").strip()) for c in checks if c.command}
    if present.get("ufw"):
        r = run_command(["ufw", "status", "verbose"], timeout=5)
        out.append(
            ToolResult(
                tool="firewall.ufw_status",
                command=r.command,
                exit_code=r.exit_code,
                stdout=r.stdout[-16000:],
                stderr=r.stderr,
                duration_ms=r.duration_ms,
                ok=r.exit_code == 0,
            )
        )
    if present.get("firewall-cmd"):
        for cmd in (["firewall-cmd", "--state"], ["firewall-cmd", "--list-all"]):
            r = run_command(cmd, timeout=5)
            out.append(
                ToolResult(
                    tool="firewall.firewalld",
                    command=r.command,
                    exit_code=r.exit_code,
                    stdout=r.stdout[-16000:],
                    stderr=r.stderr,
                    duration_ms=r.duration_ms,
                    ok=r.exit_code == 0,
                )
            )
    if present.get("nft"):
        r = run_command(["nft", "list", "ruleset"], timeout=5)
        out.append(
            ToolResult(
                tool="firewall.nft_ruleset",
                command=r.command,
                exit_code=r.exit_code,
                stdout=r.stdout[-16000:],
                stderr=r.stderr,
                duration_ms=r.duration_ms,
                ok=r.exit_code == 0,
            )
        )
    return out
