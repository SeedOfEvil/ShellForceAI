from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel


class KnowledgeResult(BaseModel):
    source: str
    path: str
    line: int
    title: str
    snippet: str
    score: float | None = None


def search_local(paths: list[str], query: str, max_results: int = 20, max_file_bytes: int = 1_000_000) -> list[KnowledgeResult]:
    out: list[KnowledgeResult] = []
    lowered = query.lower()
    for s in paths:
        p = Path(s)
        if not p.exists():
            continue
        files = [p] if p.is_file() else [f for f in p.rglob("*") if f.is_file()]
        for f in files:
            try:
                if f.stat().st_size > max_file_bytes:
                    continue
                txt = f.read_text(errors="ignore")
            except Exception:
                continue
            for i, line in enumerate(txt.splitlines(), 1):
                if lowered in line.lower():
                    out.append(KnowledgeResult(source="local", path=str(f), line=i, title=f.name, snippet=line.strip()))
                    if len(out) >= max_results:
                        return out
                    break
    return out
