from __future__ import annotations

from shellforgeai.core.evidence import EvidenceBundle, EvidenceCategory, EvidenceItem, TargetType
from shellforgeai.knowledge.search import search_local
from shellforgeai.tools import disk, host, journal, network, systemd
from shellforgeai.util.text import truncate_text


def _to_item(result, category: EvidenceCategory, title: str) -> EvidenceItem:
    content, truncated = truncate_text(result.stdout or result.stderr)
    return EvidenceItem(source=result.tool, category=category, command=result.command, ok=result.ok, exit_code=result.exit_code, title=title, summary=("ok" if result.ok else "error"), content=content, truncated=truncated)


def collect_host_evidence(context) -> list[EvidenceItem]:
    return [
        _to_item(host.host_info(), EvidenceCategory.host, "Host information"),
        _to_item(host.host_resources(), EvidenceCategory.host, "Host resources"),
        _to_item(host.host_uptime(), EvidenceCategory.host, "Host uptime"),
    ]


def collect_service_evidence(context, service_name: str, since: str = "30m") -> list[EvidenceItem]:
    return [
        _to_item(systemd.status(service_name), EvidenceCategory.service, f"systemd status {service_name}"),
        _to_item(journal.unit(service_name, since=since), EvidenceCategory.logs, f"Journal for {service_name}"),
        _to_item(systemd.list_failed(), EvidenceCategory.service, "Failed systemd units"),
    ]


def collect_disk_evidence(context) -> list[EvidenceItem]:
    return [_to_item(disk.usage(), EvidenceCategory.host, "Disk usage"), _to_item(disk.inodes(), EvidenceCategory.host, "Inode usage")]


def collect_network_evidence(context) -> list[EvidenceItem]:
    return [_to_item(network.listeners(), EvidenceCategory.network, "Listeners"), _to_item(network.routes(), EvidenceCategory.network, "Routes"), _to_item(network.dns(), EvidenceCategory.network, "DNS config")]


def collect_local_knowledge_evidence(context, query: str) -> list[EvidenceItem]:
    hits = search_local(context.settings.knowledge.local_paths, query)
    text = "\n".join(f"{h.path}:{h.line} {h.snippet}" for h in hits) or "No local knowledge hits"
    return [EvidenceItem(source="knowledge.search_local", category=EvidenceCategory.knowledge, title=f"Local knowledge: {query}", summary=f"{len(hits)} hits", content=text)]
