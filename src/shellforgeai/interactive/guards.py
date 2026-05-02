from __future__ import annotations

import re

_SHELL_PREFIXES = (
    "sudo ",
    "docker ",
    "kubectl ",
    "systemctl ",
    "journalctl ",
    "apt ",
    "apt-get ",
    "dnf ",
    "yum ",
    "apk ",
    "pacman ",
    "rm ",
    "mv ",
    "cp ",
    "chmod ",
    "chown ",
    "cat ",
    "grep ",
    "find ",
    "sed ",
    "awk ",
    "tail ",
    "head ",
    "ps ",
    "ss ",
    "ip ",
    "nft ",
    "iptables ",
    "bash -lc",
    "sh -lc",
    "for ",
    "while ",
    "if ",
    "do",
    "done",
    "then",
    "fi",
)


def _has_unmatched_quote(text: str, quote: str) -> bool:
    return text.count(quote) % 2 == 1


def is_multiline_shell_fragment(text: str) -> bool:
    raw = text.strip()
    if not raw:
        return False
    lowered = raw.lower()
    if raw.endswith("\\"):
        return True
    if _has_unmatched_quote(raw, "'") or _has_unmatched_quote(raw, '"'):
        return True
    if re.match(r"^(for|if|while|do|done|then|fi)\b", lowered):
        return True
    return ("$(" in raw or "`" in raw) and any(
        x in lowered for x in ("for ", "do", "done", "ls", "find", "echo")
    )


def looks_like_shell_command(text: str) -> bool:
    raw = text.strip()
    if not raw:
        return False
    if is_multiline_shell_fragment(raw):
        return True
    lowered = raw.lower()
    if lowered.startswith(_SHELL_PREFIXES):
        return True
    return " docker exec " in lowered or " docker compose " in lowered
