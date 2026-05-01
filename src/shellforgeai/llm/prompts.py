from __future__ import annotations

import json
import re

from shellforgeai.llm.system_prompt import SHELLFORGE_SYSTEM_PROMPT

SECRET_RE = re.compile(
    r"(api_key|token|secret|password|bearer|authorization|private_key|client_secret|refresh_token|access_token|auth\.json)",
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


def build_model_prompt(question: str, context: dict, max_chars: int = 2000) -> str:
    payload = redact_text(json.dumps(context, indent=2, ensure_ascii=False))[:max_chars]
    return f"{SHELLFORGE_SYSTEM_PROMPT}\nQuestion: {question}\nContext:\n{payload}"


def build_contextual_prompt(question: str, context: dict, mode: str = "standard") -> str:
    max_chars = 800 if mode == "minimal" else 2500 if mode == "standard" else 5000
    return build_model_prompt(question, context, max_chars=max_chars)
