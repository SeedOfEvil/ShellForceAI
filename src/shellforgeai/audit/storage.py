import json
from pathlib import Path


class AuditStorage:
    def __init__(self, base: Path):
        self.base = base.expanduser()
        for d in ["sessions", "artifacts", "cache"]:
            (self.base / d).mkdir(parents=True, exist_ok=True)

    def append(self, record: dict) -> None:
        p = self.base / "sessions" / f"{record['session_id']}.jsonl"
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    def list_sessions(self) -> list[str]:
        return [p.stem for p in (self.base / "sessions").glob("*.jsonl")]

    def show(self, sid: str) -> str | None:
        p = self.base / "sessions" / f"{sid}.jsonl"
        return p.read_text() if p.exists() else None
