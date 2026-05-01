from __future__ import annotations

import json
import re

SECRET_RE = re.compile(
    r"(api_key|token|secret|password|bearer|authorization|private_key|client_secret|refresh_token|access_token)",
    re.IGNORECASE,
)


def redact_text(value: str) -> str:
    out = []
    for line in value.splitlines():
        if SECRET_RE.search(line):
            out.append("[REDACTED]")
        else:
            out.append(line)
    return "\n".join(out)


def build_model_prompt(question: str, context: dict, max_chars: int = 6000) -> str:
    payload = redact_text(json.dumps(context, indent=2, ensure_ascii=False))
    payload = payload[:max_chars]
    return (
        "You are ShellForgeAI, a CLI-first Linux operations copilot. "
        "Do not execute actions. Cite evidence IDs.\n"
        f"Question: {question}\n"
        f"Context:\n{payload}"
    )
