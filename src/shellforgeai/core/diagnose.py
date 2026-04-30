from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field

from shellforgeai.core.collectors import (
    collect_disk_evidence,
    collect_host_evidence,
    collect_local_knowledge_evidence,
    collect_network_evidence,
    collect_service_evidence,
)
from shellforgeai.core.evidence import EvidenceBundle, TargetType, classify_target
from shellforgeai.core.plans import Plan, PlanStep
from shellforgeai.util.text import extract_lines_matching


class Finding(BaseModel):
    severity: str
    title: str
    detail: str
    evidence_refs: list[str] = Field(default_factory=list)
    confidence: str = "medium"


class DiagnosisResult(BaseModel):
    session_id: str
    target: str
    target_type: TargetType
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    evidence: EvidenceBundle
    findings: list[Finding]
    proposed_plan: Plan
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    audit_path: str | None = None


def diagnose_target(
    context, target: str, online: bool = False, since: str = "30m"
) -> DiagnosisResult:
    ttype = classify_target(target)
    items = collect_host_evidence(context)
    findings: list[Finding] = []
    warnings: list[str] = []
    if online and not context.session.online_enabled:
        warnings.append("Online research requested but blocked by active profile/policy.")
    if ttype == TargetType.service:
        items.extend(collect_service_evidence(context, target, since=since))
        items.extend(collect_local_knowledge_evidence(context, target))
    elif ttype == TargetType.disk:
        items.extend(collect_disk_evidence(context))
    elif ttype == TargetType.network:
        items.extend(collect_network_evidence(context))
    else:
        items.extend(collect_local_knowledge_evidence(context, target))
    for i in items:
        if not i.ok:
            findings.append(
                Finding(
                    severity="warning",
                    title=f"{i.source} reported error",
                    detail=i.summary,
                    evidence_refs=[i.source],
                    confidence="high",
                )
            )
        matches = extract_lines_matching(
            i.content,
            [
                "error",
                "failed",
                "permission denied",
                "address already in use",
                "no such file",
                "connection refused",
            ],
            5,
        )
        if matches:
            findings.append(
                Finding(
                    severity="warning",
                    title=f"Potential issues in {i.source}",
                    detail="; ".join(matches),
                    evidence_refs=[i.source],
                    confidence="medium",
                )
            )
    steps = [
        PlanStep(
            step_id="1",
            title="Review collected evidence",
            description="Inspect host/service signals and prioritize likely root cause.",
        ),
        PlanStep(
            step_id="2",
            title="Validate configuration manually",
            description="Check target-specific config files and syntax before any change.",
        ),
        PlanStep(
            step_id="3",
            title="Prepare operator-approved remediation",
            description="Document exact change/reload steps for explicit approval in later phase.",
        ),
    ]
    plan = Plan(
        plan_id=f"plan_{uuid4().hex[:8]}",
        goal=f"Diagnose {target}",
        session_id=context.session.session_id,
        steps=steps,
        notes=["Restart/reload actions are deferred and require operator approval."],
    )
    bundle = EvidenceBundle(target=target, target_type=ttype, items=items, warnings=warnings)
    return DiagnosisResult(
        session_id=context.session.session_id,
        target=target,
        target_type=ttype,
        evidence=bundle,
        findings=findings,
        proposed_plan=plan,
        warnings=warnings,
    )
