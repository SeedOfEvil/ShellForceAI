from __future__ import annotations

import re


def truncate_text(text: str, max_chars: int = 12000) -> tuple[str, bool]:
    if len(text) <= max_chars:
        return text, False
    return text[:max_chars], True


def extract_lines_matching(text: str, patterns: list[str], max_matches: int = 20) -> list[str]:
    compiled = [re.compile(p, re.IGNORECASE) for p in patterns]
    matches: list[str] = []
    for line in text.splitlines():
        if any(p.search(line) for p in compiled):
            matches.append(line.strip())
            if len(matches) >= max_matches:
                break
    return matches
