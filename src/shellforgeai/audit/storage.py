import json
from pathlib import Path


class AuditStorage:
    def __init__(self, base: Path):
        self.base = base.expanduser()
        self.sessions_dir = self.base / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        (self.base / "artifacts").mkdir(parents=True, exist_ok=True)

    def append(self, record: dict) -> None:
        sid = record["session_id"]
        p = self.sessions_dir / f"{sid}.json"
        p.write_text(json.dumps(record, indent=2), encoding="utf-8")
        with (self.sessions_dir / "sessions.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    def list_sessions(self) -> list[str]:
        return sorted([p.stem for p in self.sessions_dir.glob("*.json") if p.name != "sessions.jsonl"])

    def show(self, sid: str) -> str | None:
        p = self.sessions_dir / f"{sid}.json"
        return p.read_text() if p.exists() else None
