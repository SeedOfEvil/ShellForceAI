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
from shellforgeai.core.plans import Plan, PlanStep
from shellforgeai.interactive.banner import build_banner
from shellforgeai.knowledge.search import search_local
from shellforgeai.llm.manager import build_provider
from shellforgeai.llm.prompts import build_contextual_prompt
from shellforgeai.llm.schemas import ModelRequest
from shellforgeai.tools import registry
from shellforgeai.version import get_build_info

from .commands import route_input
from .streaming import StreamRenderer
from .workspace import WorkspaceTrustStore


def _ensure_artifact_dir(runtime: RuntimeContext) -> None:
    runtime.session.artifact_dir.mkdir(parents=True, exist_ok=True)


def _confirm_workspace(console: Console, runtime: RuntimeContext, no_trust_cache: bool) -> bool:
    store = WorkspaceTrustStore(runtime.session.data_dir)
    workspace = Path.cwd()
    if not no_trust_cache and store.is_trusted(workspace):
        console.print(f"Workspace trusted: {workspace}")
        return True
    console.print("Trust this workspace?\n")
    console.print(f"Path:\n  {workspace}\n")
    console.print(
        "ShellForgeAI may read local docs, use read-only typed tools, and write audit/artifacts."
    )
    console.print(
        "No destructive actions, no service restarts, no package installs, no auto-apply."
    )
    trust = typer.confirm(f"Trust {workspace}?", default=False)
    if not trust:
        console.print("Workspace not trusted. Exiting interactive mode.")
        return False
    if not no_trust_cache:
        store.trust(workspace, get_build_info().version)
    return True


def start_interactive(runtime: RuntimeContext, no_trust_cache: bool = False) -> None:
    console = Console()
    trusted = WorkspaceTrustStore(runtime.session.data_dir).is_trusted(Path.cwd())
    console.print(build_banner(runtime, trusted))
    if not _confirm_workspace(console, runtime, no_trust_cache=no_trust_cache):
        return
    renderer = StreamRenderer(console)
    console.print("Type /help for commands. Type /exit to quit.")
    while True:
        user_input = input("sfai> ").strip()
        routed = route_input(user_input)
        if routed.name in {"noop"}:
            continue
        if routed.name in {"/exit", "/quit"}:
            console.print("Goodbye.")
            return
        if routed.name == "/clear":
            os.system("clear")
            continue
        if routed.name == "/help":
            console.print(
                "Session:\n  /help  /exit,/quit  /clear\nStatus:\n  /status /doctor /model /workspace /mode /profile\nOps:\n  diagnose <target> | research <query> | plan <goal> | ask <question>\nDebug:\n  /raw on|off /context minimal|standard|full"
            )
            continue
        if routed.name == "/examples":
            console.print(
                "diagnose disk\nresearch nginx address already in use\nplan investigate high disk usage\nask what can you inspect here?"
            )
            continue
        if routed.name in {"/doctor", "/status"}:
            build = get_build_info()
            console.print(
                f"version={build.display_version} profile={runtime.profile.name} mode={runtime.session.mode} trusted=yes"
            )
            continue
        if routed.name == "/model":
            for k, v in build_provider(runtime.settings).doctor().items():
                console.print(f"{k}={v}")
            continue
        if routed.name == "/tools":
            t = Table("name", "category", "risk", "description")
            for tool in sorted(registry.list_tools(), key=lambda x: x.name):
                t.add_row(tool.name, tool.category, tool.risk.value, tool.description)
            console.print(t)
            continue
        if routed.name == "/audit":
            sessions = AuditStorage(runtime.session.data_dir).list_sessions()
            console.print("No audit sessions found." if not sessions else "\n".join(sessions[:10]))
            continue
        if routed.name == "research":
            hits = search_local(
                runtime.settings.knowledge.local_paths + [str(Path.cwd() / "SHELLFORGE.md")],
                routed.args,
            )
            if not hits:
                console.print(
                    f"No local knowledge hits for: {routed.args}\nSuggestions:\n- Add SHELLFORGE.md guidance in this workspace.\n- Add local runbooks under configured knowledge paths.\n- Try /context full for broader context."
                )
            else:
                for h in hits[:5]:
                    console.print(f"{h.path}:{h.line} {h.snippet}")
            continue
        if routed.name == "diagnose":
            res = diagnose_target(runtime, routed.args, online=False, since="30m")
            _ensure_artifact_dir(runtime)
            ep = runtime.session.artifact_dir / "evidence.json"
            ep.write_text(res.evidence.model_dump_json(indent=2), encoding="utf-8")
            sp = runtime.session.artifact_dir / "summary.md"
            sp.write_text(f"Session: {res.session_id}\nTarget: {routed.args}\n", encoding="utf-8")
            console.print(
                f"Diagnose {routed.args}\nFindings: {len(res.findings)}\nEvidence: {len(res.evidence.items)} item(s)\nSession: {res.session_id}\nArtifacts:\n- evidence: {ep}\n- summary: {sp}"
            )
            continue
        if routed.name == "plan" or routed.name == "/plan":
            _ensure_artifact_dir(runtime)
            p = Plan(
                plan_id=f"plan_{runtime.session.session_id}",
                goal=routed.args,
                session_id=runtime.session.session_id,
                steps=[
                    PlanStep(
                        step_id="1", title="Collect evidence", description="Run read-only checks"
                    )
                ],
            )
            pp = runtime.session.artifact_dir / "plan.json"
            pp.write_text(p.model_dump_json(indent=2), encoding="utf-8")
            console.print(
                f"Plan created\nGoal: {routed.args}\nRisk: read\nSteps: {len(p.steps)}\nPlan: {pp}\nApply: validation-only in this alpha"
            )
            continue

        provider = build_provider(runtime.settings)
        prompt = build_contextual_prompt(
            routed.args,
            {"host": platform.platform(), "mode": runtime.session.mode, "workspace_trusted": True},
            mode="standard",
        )
        resp = provider.complete(
            ModelRequest(
                prompt=prompt,
                model=runtime.settings.model.model,
                provider=runtime.settings.model.provider,
                timeout_seconds=runtime.settings.model.timeout_seconds,
                metadata={
                    "command_kind": "ask",
                    "profile": runtime.profile.name,
                    "mode": runtime.session.mode,
                },
            )
        )
        renderer.render(resp.text, resp.raw.get("stdout_jsonl") if resp.raw else None)
