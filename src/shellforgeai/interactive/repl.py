from __future__ import annotations

import os
import platform
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from shellforgeai.audit.storage import AuditStorage
from shellforgeai.core.context import RuntimeContext
from shellforgeai.core.diagnose import diagnose_target
from shellforgeai.core.evidence import classify_target
from shellforgeai.core.plans import Plan, PlanStep
from shellforgeai.interactive.banner import build_banner
from shellforgeai.knowledge.search import search_local
from shellforgeai.llm.manager import build_provider
from shellforgeai.llm.prompts import build_contextual_prompt
from shellforgeai.llm.schemas import ModelRequest
from shellforgeai.tools import disk, host, network, process, registry, systemd
from shellforgeai.version import get_build_info

from .commands import route_input
from .streaming import StreamRenderer
from .workspace import WorkspaceTrustStore


def _ensure_artifact_dir(runtime: RuntimeContext) -> None:
    runtime.session.artifact_dir.mkdir(parents=True, exist_ok=True)


def _is_machine_health_question(text: str) -> bool:
    t = text.lower()
    return any(
        n in t
        for n in [
            "issue on this machine",
            "machine healthy",
            "what's wrong with this box",
            "check this system",
            "machine look",
            "anything broken",
        ]
    )


def _sanitize_provider_error(text: str) -> str:
    if "bwrap: No permissions to create a new namespace" in text:
        return (
            "Codex sandbox could not create a namespace in this container. "
            "This is a provider/container sandbox limitation, not evidence of host failure."
        )
    return text


def _evidence_table(console: Console, checks: list[dict[str, str]]) -> None:
    t = Table("Tool", "Status", "Summary")
    for c in checks:
        t.add_row(c["tool"], c["status"], c["summary"])
    console.print(t)


def _confirm_workspace(console: Console, runtime: RuntimeContext, no_trust_cache: bool) -> bool:
    store = WorkspaceTrustStore(runtime.session.data_dir)
    workspace = Path.cwd()
    if not no_trust_cache and store.is_trusted(workspace):
        return True
    console.print("Trust this workspace?\n")
    console.print(f"Path:\n  {workspace}\n")
    trust = typer.confirm(f"Trust {workspace}?", default=False)
    if not trust:
        console.print("Workspace not trusted. Exiting interactive mode.")
        return False
    if not no_trust_cache:
        store.trust(workspace, get_build_info().version)
    return True


def _collect_machine_health() -> list[dict[str, str]]:
    checks = [
        host.host_info(),
        host.host_resources(),
        host.host_uptime(),
        disk.usage(),
        disk.inodes(),
        network.dns(),
        network.routes(),
        process.top(),
        systemd.list_failed(),
    ]
    return [
        {
            "tool": c.tool,
            "status": "ok" if c.ok else "unavailable",
            "summary": (c.stderr or c.stdout or "").splitlines()[0][:120],
        }
        for c in checks
    ]


def start_interactive(runtime: RuntimeContext, no_trust_cache: bool = False) -> None:
    console = Console()
    trusted = WorkspaceTrustStore(runtime.session.data_dir).is_trusted(Path.cwd())
    console.print(build_banner(runtime, trusted))
    if not _confirm_workspace(console, runtime, no_trust_cache=no_trust_cache):
        return
    renderer = StreamRenderer(console)
    while True:
        user_input = input("sfai> ").strip()
        routed = route_input(user_input)
        if routed.name == "noop":
            continue
        if routed.name in {"/exit", "/quit"}:
            console.print("Goodbye.")
            return
        if routed.name == "/clear":
            os.system("clear")
            continue
        if routed.name == "/help":
            console.print(
                "Session:\n  /help /exit /clear\n"
                "Status:\n  /status /doctor /model /workspace /mode /profile\n"
                "Ops:\n  diagnose <target> research <query> plan <goal> ask <question>"
            )
            continue
        if routed.name == "/examples":
            console.print(
                "diagnose disk\nresearch nginx address already in use\n"
                "plan investigate high disk usage"
            )
            continue
        if routed.name in {"/doctor", "/status"}:
            b = get_build_info()
            console.print(
                f"version={b.display_version} profile={runtime.profile.name} "
                f"mode={runtime.session.mode}"
            )
            continue
        if routed.name == "/profile":
            p = runtime.profile
            console.print(
                f"Profile: {p.name}\n"
                f"Online allowed: {p.online_allowed}\n"
                f"Raw shell allowed: {p.raw_shell_allowed}\n"
                f"Mode: {runtime.session.mode}\n"
                "Apply: validation-only"
            )
            continue
        if routed.name == "/mode":
            console.print(
                f"Mode: {runtime.session.mode}\n"
                "Execution: no destructive actions\n"
                "Apply: validation-only"
            )
            continue
        if routed.name == "/audit":
            sessions = AuditStorage(runtime.session.data_dir).list_sessions()
            console.print(
                "No audit sessions found."
                if not sessions
                else "Recent audit sessions:\n" + "\n".join(sessions[:10])
            )
            continue
        if routed.name == "/tools":
            t = Table("Name", "Category", "Risk", "Description")
            for tool in sorted(registry.list_tools(), key=lambda x: x.name):
                t.add_row(tool.name, tool.category, tool.risk.value, tool.description)
            console.print(t)
            continue
        if routed.name == "research":
            with console.status("Searching local knowledge..."):
                hits = search_local(
                    runtime.settings.knowledge.local_paths + [str(Path.cwd() / "SHELLFORGE.md")],
                    routed.args,
                )
            if not hits:
                console.print(
                    f"No local knowledge hits for: {routed.args}\n"
                    "Suggestions:\n"
                    "- Add SHELLFORGE.md guidance in this workspace.\n"
                    "- Add local runbooks under configured knowledge paths.\n"
                    "- Use ask for model-backed general reasoning.\n"
                    "- Use diagnose nginx to collect live service evidence."
                )
            else:
                for h in hits[:5]:
                    console.print(f"{h.path}:{h.line} {h.snippet}")
            continue
        if routed.name in {"diagnose"}:
            with console.status("Collecting evidence..."):
                res = diagnose_target(runtime, routed.args, online=False, since="30m")
            checks = [
                {"tool": i.source, "status": "ok" if i.ok else "unavailable", "summary": i.summary}
                for i in res.evidence.items
            ]
            console.print(f"Collected {len(checks)} evidence item(s)")
            _evidence_table(console, checks)
            with console.status("Building findings..."):
                pass
            with console.status("Writing artifacts..."):
                _ensure_artifact_dir(runtime)
                ep = runtime.session.artifact_dir / "evidence.json"
                ep.write_text(res.evidence.model_dump_json(indent=2), encoding="utf-8")
                pp = runtime.session.artifact_dir / "plan.json"
                pp.write_text(res.proposed_plan.model_dump_json(indent=2), encoding="utf-8")
                sp = runtime.session.artifact_dir / "summary.md"
                sp.write_text(
                    f"Session: {res.session_id}\n"
                    f"Target: {routed.args}\n"
                    f"Type: {res.target_type.value}\n"
                    f"Mode: {runtime.session.mode}\n"
                    f"Profile: {runtime.profile.name}\n"
                    "Collectors:\n"
                    + "\n".join([f"- {c['tool']}: {c['status']} ({c['summary']})" for c in checks])
                    + "\nDeterministic findings:\n"
                    + "\n".join([f"- {f.title}" for f in res.findings])
                    + (
                        f"\nArtifacts:\n- evidence: {ep}\n"
                        f"- plan: {pp}\n- summary: {sp}\n"
                        "Safety: apply remains validation-only."
                    ),
                    encoding="utf-8",
                )
            console.print(
                f"Diagnose {routed.args}\n"
                f"Session: {res.session_id}\nTarget: {routed.args}\n"
                f"Type: {res.target_type.value}\n"
                f"Evidence: {len(res.evidence.items)} item(s)\n"
                f"Findings: {len(res.findings)}\n"
                f"Artifacts:\n- evidence: {ep}\n- plan: {pp}\n- summary: {sp}"
            )
            continue
        if routed.name in {"plan", "/plan"}:
            with console.status("Building plan..."):
                t = classify_target(routed.args).value
                p = Plan(
                    plan_id=f"plan_{runtime.session.session_id}",
                    goal=routed.args,
                    session_id=runtime.session.session_id,
                    steps=[
                        PlanStep(
                            step_id="1",
                            title="Collect evidence",
                            description=f"Use diagnose for {t}",
                        ),
                        PlanStep(
                            step_id="2",
                            title="Review findings",
                            description="Review evidence and prioritize safe checks",
                        ),
                    ],
                )
            with console.status("Writing plan artifact..."):
                _ensure_artifact_dir(runtime)
                pp = runtime.session.artifact_dir / "plan.json"
                pp.write_text(p.model_dump_json(indent=2), encoding="utf-8")
                (runtime.session.artifact_dir / "summary.md").write_text(
                    f"Session: {runtime.session.session_id}\n"
                    f"Goal: {routed.args}\nPlan: {pp}\n"
                    "Safety: apply remains validation-only.",
                    encoding="utf-8",
                )
            console.print(
                f"Plan created\nGoal: {routed.args}\nRisk: read\n"
                f"Steps: {len(p.steps)}\nPlan: {pp}\n"
                "Apply: validation-only in this alpha"
            )
            continue

        provider = build_provider(runtime.settings)
        kind = "ask"
        context = {
            "host": platform.platform(),
            "mode": runtime.session.mode,
            "workspace_trusted": True,
        }
        if _is_machine_health_question(user_input):
            with console.status("Collecting evidence..."):
                checks = _collect_machine_health()
            console.print(f"Collected {len(checks)} evidence item(s)")
            _evidence_table(console, checks)
            context["machine_health"] = checks
            kind = "diagnose"
        with console.status("Preparing context..."):
            prompt = build_contextual_prompt(
                user_input if routed.name != "ask" else routed.args, context, mode="standard"
            )
        try:
            with console.status("Asking model..."):
                resp = provider.complete(
                    ModelRequest(
                        prompt=prompt,
                        model=runtime.settings.model.model,
                        provider=runtime.settings.model.provider,
                        timeout_seconds=runtime.settings.model.timeout_seconds,
                        metadata={
                            "command_kind": kind,
                            "profile": runtime.profile.name,
                            "mode": runtime.session.mode,
                        },
                    )
                )
        except Exception as exc:
            console.print(_sanitize_provider_error(str(exc)))
            continue
        with console.status("Writing artifacts..."):
            _ensure_artifact_dir(runtime)
            (runtime.session.artifact_dir / "model-response.md").write_text(
                resp.text, encoding="utf-8"
            )
        renderer.render(_sanitize_provider_error(resp.text), None)
