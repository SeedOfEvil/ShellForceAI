from pathlib import Path

from shellforgeai.audit.storage import AuditStorage


def test_audit_storage(tmp_path: Path):
    s = AuditStorage(tmp_path)
    s.append({"session_id": "s1"})
    assert "s1" in s.list_sessions()
