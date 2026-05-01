from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RoutedCommand:
    name: str
    args: str = ""


def route_input(text: str) -> RoutedCommand:
    raw = text.strip()
    if not raw:
        return RoutedCommand(name="noop")
    if raw.startswith("/"):
        head, _, tail = raw.partition(" ")
        return RoutedCommand(name=head.lower(), args=tail.strip())

    lowered = raw.lower()
    for prefix, cmd in [
        ("diagnose ", "diagnose"),
        ("research ", "research"),
        ("plan ", "plan"),
        ("inspect host", "inspect_host"),
        ("inspect service ", "inspect_service"),
        ("ask ", "ask"),
    ]:
        if lowered.startswith(prefix):
            return RoutedCommand(name=cmd, args=raw[len(prefix) :].strip())
    return RoutedCommand(name="ask", args=raw)
