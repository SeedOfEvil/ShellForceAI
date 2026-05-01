from __future__ import annotations

import platform
import sys
from pathlib import Path
from typing import Annotated

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
from shellforgeai.llm.manager import build_provider
from shellforgeai.llm.prompts import build_model_prompt
from shellforgeai.llm.schemas import ModelRequest
from shellforgeai.tools import host, journal, registry, systemd
from shellforgeai.version import __version__

app = typer.Typer(no_args_is_help=True)
inspect_app = typer.Typer()
tools_app = typer.Typer()
audit_app = typer.Typer()
model_app = typer.Typer()
app.add_typer(inspect_app, name="inspect")
app.add_typer(tools_app, name="tools")
app.add_typer(audit_app, name="audit")
app.add_typer(model_app, name="model")
console = Console()


def _ctx(ctx: typer.Context) -> RuntimeContext:
    return ctx.obj["runtime"]


@app.callback()
def main(
    ctx: typer.Context,
    version: Annotated[bool, typer.Option("--version")] = False,
    config: Path | None = None,
    profile: str = "inspect",
    mode: str = "inspect",
    verbose: bool = False,
) -> None:
    if version:
        console.print(__version__)
        raise typer.Exit()
    settings = load_settings(config)
    prof = load_profile(profile, Path.cwd())
    session = build_session_context(settings, prof, mode, Path.cwd())
    ctx.obj = {
        "runtime": RuntimeContext(settings=settings, profile=prof, session=session, verbose=verbose)
    }


@app.command()
def doctor(ctx: typer.Context) -> None:
    runtime = _ctx(ctx)
    audit = AuditStorage(runtime.session.data_dir)
    console.print("ShellForgeAI")
    console.print(
        f"version={__version__} python={sys.version.split()[0]} platform={platform.system()}"
    )
    console.print(f"profile={runtime.profile.name} mode={runtime.session.mode}")
    console.print(f"data_dir={runtime.session.data_dir} audit_dir={audit.sessions_dir}")
    console.print(
        f"tools={len(registry.list_tools())} model={runtime.settings.model.provider}/{runtime.settings.model.model}"
    )




@model_app.command("doctor")
def model_doctor(ctx: typer.Context) -> None:
    runtime = _ctx(ctx)
    provider = build_provider(runtime.settings)
    info = provider.doctor()
    for k, v in info.items():
        console.print(f"{k}={v}")
    if not info.get("auth_cache_present"):
        console.print("Suggested login: codex login (or codex login --device-auth)")


@model_app.command("test")
def model_test(ctx: typer.Context, prompt: str = "say hello") -> None:
    runtime = _ctx(ctx)
    provider = build_provider(runtime.settings)
    req = ModelRequest(prompt=prompt, model=runtime.settings.model.model, provider=runtime.settings.model.provider, timeout_seconds=runtime.settings.model.timeout_seconds)
    resp = provider.complete(req)
    console.print(resp.text)
@inspect_app.command("host")
def inspect_host() -> None:
    for r in [host.host_info(), host.host_resources(), host.host_uptime()]:
        console.print(f"[{r.tool}] ok={r.ok} code={r.exit_code}")
        console.print((r.stdout or r.stderr).strip() or "not available")


@inspect_app.command("service")
def inspect_service(service: str) -> None:
    r = systemd.status(service)
    console.print(f"[{r.tool}] ok={r.ok} code={r.exit_code}")
    console.print((r.stdout or r.stderr).strip() or "not available")


@app.command()
def logs(service: str, since: str = "30m") -> None:
    r = journal.unit(service, since=since)
    console.print(f"[{r.tool}] ok={r.ok} code={r.exit_code}")
    console.print((r.stdout or r.stderr).strip() or "no logs")


@tools_app.command("list")
def tools_list() -> None:
    for t in sorted(registry.list_tools(), key=lambda x: x.name):
        console.print(f"{t.name}\t{t.category}\t{t.risk.value}")


@tools_app.command("describe")
def tools_describe(tool_name: str) -> None:
    t = registry.get_tool(tool_name)
    if t is None:
        raise typer.Exit(code=1)
    console.print(t.model_dump_json(indent=2))


@audit_app.command("list")
def audit_list(ctx: typer.Context) -> None:
    runtime = _ctx(ctx)
    sessions = AuditStorage(runtime.session.data_dir).list_sessions()
    if not sessions:
        console.print("No sessions.")
        return
    for sid in sessions:
        console.print(sid)


@audit_app.command("show")
def audit_show(ctx: typer.Context, session_id: str) -> None:
    runtime = _ctx(ctx)
    val = AuditStorage(runtime.session.data_dir).show(session_id)
    if val is None:
        raise typer.Exit(code=1)
    console.print(val)


@app.command()
def diagnose(
    ctx: typer.Context,
    target: str,
    online: bool = False,
    since: str = "30m",
    json_output: bool = typer.Option(False, "--json"),
    save_plan: bool = False,
    model: bool = typer.Option(False, "--model"),
) -> None:
    runtime = _ctx(ctx)
    result = diagnose_target(runtime, target, online=online, since=since)
    audit = AuditStorage(runtime.session.data_dir)
    ev_path = runtime.session.artifact_dir / "evidence.json"
    ev_path.write_text(result.evidence.model_dump_json(indent=2), encoding="utf-8")
    plan_path = runtime.session.artifact_dir / "plan.json"
    if save_plan:
        plan_path.write_text(result.proposed_plan.model_dump_json(indent=2), encoding="utf-8")
    rec = {
        "session_id": runtime.session.session_id,
        "command": "diagnose",
        "target": target,
        "mode": runtime.session.mode,
        "profile": runtime.profile.name,
        "tools_called": [i.source for i in result.evidence.items],
        "artifacts": [str(ev_path)] + ([str(plan_path)] if save_plan else []),
        "warnings": result.warnings,
        "errors": result.errors,
        "summary": f"diagnosed {target}",
    }
    audit.append(rec)
    if model:
        provider = build_provider(runtime.settings)
        prompt = build_model_prompt(f"Diagnose {target}", {"findings": [f.model_dump() for f in result.findings], "evidence": [i.model_dump() for i in result.evidence.items]})
        mresp = provider.complete(ModelRequest(prompt=prompt, model=runtime.settings.model.model, provider=runtime.settings.model.provider, timeout_seconds=runtime.settings.model.timeout_seconds))
        (runtime.session.artifact_dir / "model-response.md").write_text(mresp.text, encoding="utf-8")
        console.print("Model-assisted analysis:\n" + mresp.text)
    console.print(result.model_dump_json(indent=2) if json_output else f"session={result.session_id} target={target} type={result.target_type}")


@app.command()
def research(ctx: typer.Context, query: str, model: bool = typer.Option(False, "--model")) -> None:
    runtime = _ctx(ctx)
    hits = search_local(
        runtime.settings.knowledge.local_paths + [str(Path.cwd() / "SHELLFORGE.md")], query
    )
    if not hits:
        console.print("No local knowledge hits.")
        return
    for h in hits:
        console.print(f"{h.path}:{h.line} {h.snippet}")
    if model:
        runtime = _ctx(ctx)
        provider = build_provider(runtime.settings)
        resp = provider.complete(ModelRequest(prompt=build_model_prompt(query, {"hits": [h.model_dump() for h in hits]}), model=runtime.settings.model.model, provider=runtime.settings.model.provider, timeout_seconds=runtime.settings.model.timeout_seconds))
        console.print("\nModel synthesis:\n" + resp.text)


@app.command()
def plan(ctx: typer.Context, goal: str, model: bool = typer.Option(False, "--model")) -> None:
    runtime = _ctx(ctx)
    t = classify_target(goal).value
    p = Plan(
        plan_id=f"plan_{runtime.session.session_id}",
        goal=goal,
        session_id=runtime.session.session_id,
        steps=[
            PlanStep(step_id="1", title="Collect evidence", description=f"Use diagnose for {t}"),
            PlanStep(
                step_id="2",
                title="Review",
                description="Review findings and confirm next safe steps",
            ),
        ],
    )
    out = runtime.session.artifact_dir / "plan.json"
    out.write_text(p.model_dump_json(indent=2), encoding="utf-8")
    if model:
        provider = build_provider(runtime.settings)
        resp = provider.complete(ModelRequest(prompt=build_model_prompt(goal, {"deterministic_plan": p.model_dump()}), model=runtime.settings.model.model, provider=runtime.settings.model.provider, timeout_seconds=runtime.settings.model.timeout_seconds))
        (runtime.session.artifact_dir / "model-plan-review.md").write_text(resp.text, encoding="utf-8")
    console.print(str(out))


@app.command()
def apply(plan_file: Path) -> None:
    if not plan_file.exists():
        raise typer.BadParameter("plan file missing")
    Plan.model_validate_json(plan_file.read_text(encoding="utf-8"))
    console.print(
        "Apply execution is intentionally disabled in this alpha. Plan validation is available; execution will be introduced after safety hardening."
    )


@app.command()
def ask(ctx: typer.Context, question: str) -> None:
    runtime = _ctx(ctx)
    provider = build_provider(runtime.settings)
    prompt = build_model_prompt(question, {"host": platform.platform(), "mode": runtime.session.mode})
    resp = provider.complete(ModelRequest(prompt=prompt, model=runtime.settings.model.model, provider=runtime.settings.model.provider, timeout_seconds=runtime.settings.model.timeout_seconds))
    if not resp.ok:
        console.print("Model unavailable. Install Codex CLI and login with: codex login")
        raise typer.Exit(code=1)
    console.print(resp.text)
