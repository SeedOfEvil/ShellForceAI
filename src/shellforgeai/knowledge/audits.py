from __future__ import annotations

import json
from pathlib import Path


def search_recent_audits(data_dir: Path, query: str, limit: int = 5) -> list[dict]:
    records_path = data_dir / "audit.jsonl"
    if not records_path.exists():
        return []
    rows: list[dict] = []
    q = query.lower()
    for line in reversed(records_path.read_text(encoding="utf-8").splitlines()):
        try:
            obj = json.loads(line)
        except Exception:
            continue
        text = f"{obj.get('target', '')} {obj.get('summary', '')}".lower()
        if q and not any(token in text for token in q.split()):
            continue
        rows.append(
            {
                "session_id": obj.get("session_id", ""),
                "target": obj.get("target", ""),
                "summary": obj.get("summary", ""),
            }
        )
        if len(rows) >= limit:
            break
    return rows
