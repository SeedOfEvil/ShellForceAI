from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console

from shellforgeai.audit.storage import AuditStorage
from shellforgeai.core.config import load_settings
from shellforgeai.core.context import RuntimeContext
from shellforgeai.core.diagnose import diagnose_target
from shellforgeai.core.evidence import classify_target
from shellforgeai.core.plans import Plan, PlanStep
from shellforgeai.core.profiles import load_profile
from shellforgeai.core.session import build_session_context
from shellforgeai.knowledge.search import search_local
from shellforgeai.tools import host, journal, registry, systemd
from shellforgeai.version import __version__

app = typer.Typer()
console = Console()


def _ctx(ctx: typer.Context) -> RuntimeContext:
    return ctx.obj["runtime"]


@app.callback()
def main(ctx: typer.Context, version: bool = False, config: Path | None = None, profile: str = "inspect", mode: str = "inspect", verbose: bool = False) -> None:
    if version:
        console.print(__version__)
        raise typer.Exit()
    settings = load_settings(config)
    prof = load_profile(profile, Path.cwd())
    session = build_session_context(settings, prof, mode, Path.cwd())
    ctx.obj = {"runtime": RuntimeContext(settings=settings, profile=prof, session=session, verbose=verbose)}


@app.command()
def diagnose(ctx: typer.Context, target: str, online: bool = False, since: str = "30m", json_output: bool = typer.Option(False, "--json"), save_plan: bool = False) -> None:
    runtime = _ctx(ctx)
    result = diagnose_target(runtime, target, online=online, since=since)
    audit = AuditStorage(runtime.session.data_dir)
    ev_path = runtime.session.artifact_dir / "evidence.json"
    ev_path.write_text(result.evidence.model_dump_json(indent=2))
    plan_path = runtime.session.artifact_dir / "plan.json"
    if save_plan:
        plan_path.write_text(result.proposed_plan.model_dump_json(indent=2))
    rec = {"session_id": runtime.session.session_id, "command": "diagnose", "target": target, "mode": runtime.session.mode, "profile": runtime.profile.name, "tools_called": [i.source for i in result.evidence.items], "artifacts": [str(ev_path)] + ([str(plan_path)] if save_plan else []), "warnings": result.warnings, "errors": result.errors, "summary": f"diagnosed {target}"}
    audit.append(rec)
    if json_output:
        console.print(result.model_dump_json(indent=2))
    else:
        console.print(f"session={result.session_id} target={target} type={result.target_type}")
        console.print(f"evidence_items={len(result.evidence.items)} findings={len(result.findings)}")


@app.command()
def research(ctx: typer.Context, query: str) -> None:
    runtime = _ctx(ctx)
    hits = search_local(runtime.settings.knowledge.local_paths + [str(Path.cwd() / "SHELLFORGE.md")], query)
    for h in hits:
        console.print(f"{h.path}:{h.line} {h.snippet}")


@app.command()
def plan(ctx: typer.Context, goal: str) -> None:
    runtime = _ctx(ctx)
    t = classify_target(goal).value
    plan = Plan(plan_id=f"plan_{runtime.session.session_id}", goal=goal, session_id=runtime.session.session_id, steps=[PlanStep(step_id="1", title="Collect evidence", description=f"Use diagnose for {t}"), PlanStep(step_id="2", title="Review", description="Review findings and confirm next safe steps")])
    out = runtime.session.artifact_dir / "plan.json"
    out.write_text(plan.model_dump_json(indent=2))
    console.print(str(out))


@app.command()
def apply(plan_file: Path) -> None:
    if not plan_file.exists():
        raise typer.BadParameter("plan file missing")
    Plan.model_validate_json(plan_file.read_text())
    console.print("Apply execution is intentionally disabled in PR2. Plan validation is available; execution will be introduced after safety hardening.")
