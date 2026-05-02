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
    perf_intents = [
        "my machine is running slow",
        "my computer is slow",
        "my pc is slow",
        "pc feels slow",
        "system feels slow",
        "machine feels sluggish",
        "server is slow",
        "host is slow",
        "why is this machine slow",
        "why is my server slow",
        "high cpu",
        "high memory",
        "high load",
        "performance issue",
        "high io",
        "laggy",
        "hanging",
        "system is crawling",
        "everything is slow",
    ]
    if any(p in lowered for p in perf_intents):
        return RoutedCommand(name="diagnose", args="performance")
    disk_intents = [
        "how much disk space do we have left",
        "disk space left",
        "free disk space",
        "are we running out of disk",
        "is disk full",
        "disk usage",
        "storage left",
        "how full is the disk",
        "out of space",
        "inode usage",
        "are inodes full",
    ]
    if any(p in lowered for p in disk_intents):
        return RoutedCommand(name="diagnose", args="disk")
    health_intents = [
        "my system is glitchy",
        "computer is acting weird",
        "machine is acting weird",
        "something is wrong with this machine",
        "system health",
        "check this machine",
        "any issue on this machine",
        "is this host healthy",
        "things are unstable",
        "weird behavior",
        "glitches",
    ]
    if any(p in lowered for p in health_intents):
        return RoutedCommand(name="diagnose", args="health")
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
