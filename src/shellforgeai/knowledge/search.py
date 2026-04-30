from pathlib import Path


def search_local(paths: list[str], query: str) -> list[dict[str, str | int]]:
    out = []
    for s in paths:
        p = Path(s)
        if not p.exists():
            continue
        files = [p] if p.is_file() else [f for f in p.rglob("*") if f.is_file()]
        for f in files:
            try:
                txt = f.read_text(errors="ignore")
            except Exception:
                continue
            for i, line in enumerate(txt.splitlines(), 1):
                if query.lower() in line.lower():
                    out.append({"path": str(f), "line": i, "snippet": line.strip()})
                    break
    return out[:20]
