import json
from pathlib import Path

import typer
from rich.console import Console

from shellforgeai.audit.storage import AuditStorage
from shellforgeai.core.config import load_settings
from shellforgeai.core.profiles import load_profile
from shellforgeai.knowledge.search import search_local
from shellforgeai.tools import host, journal, registry, systemd
from shellforgeai.version import __version__

app = typer.Typer()
console = Console()


@app.callback()
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version"),
    config: Path | None = None,
    profile: str = "inspect",
    mode: str = "inspect",
    data_dir: Path | None = None,
    verbose: bool = False,
) -> None:
    if version:
        console.print(__version__)
        raise typer.Exit()
    settings = load_settings(config)
    ctx.obj = {
        "settings": settings,
        "profile": load_profile(profile, Path.cwd()),
        "mode": mode,
        "data_dir": data_dir or settings.app.data_dir,
        "verbose": verbose,
    }


@app.command()
def doctor() -> None:
    console.print("ShellForgeAI doctor OK")


inspect = typer.Typer()
app.add_typer(inspect, name="inspect")


@inspect.command("host")
def inspect_host() -> None:
    console.print(host.host_info().stdout)
    console.print(host.host_resources().stdout)


@inspect.command("service")
def inspect_service(service: str) -> None:
    r = systemd.status(service)
    console.print(r.stdout or r.stderr)


@app.command()
def logs(service: str, since: str = "30m") -> None:
    r = journal.unit(service, since=since)
    console.print(r.stdout or r.stderr)


@app.command("ask")
def ask_cmd(question: str) -> None:
    console.print(f"ask scaffold: {question}")


@app.command()
def diagnose(target: str, online: bool = False) -> None:
    console.print(f"diagnose scaffold {target} online={online}")


@app.command()
def research(query: str) -> None:
    console.print(f"research scaffold {query}")


@app.command()
def plan(goal: str, ctx: typer.Context) -> None:
    console.print(
        json.dumps(
            {
                "goal": goal,
                "mode": ctx.obj["mode"],
                "profile": ctx.obj["profile"].name,
                "proposed_steps": [],
                "safety_note": "scaffold",
            },
            indent=2,
        )
    )


@app.command()
def run(request: str) -> None:
    console.print(f"run scaffold {request}")


@app.command()
def apply(plan_file: Path) -> None:
    console.print("apply scaffold")


tools = typer.Typer()
app.add_typer(tools, name="tools")


@tools.command("list")
def tools_list() -> None:
    for t in registry.list_tools():
        console.print(f"{t.name}	{t.category}	{t.risk.value}	{t.description}")


@tools.command("describe")
def tools_describe(tool_name: str) -> None:
    t = registry.get_tool(tool_name)
    console.print(t.model_dump_json(indent=2) if t else "not found")


audit = typer.Typer()
app.add_typer(audit, name="audit")


@audit.command("list")
def audit_list(ctx: typer.Context) -> None:
    s = AuditStorage(Path(ctx.obj["data_dir"]))
    console.print("\n".join(s.list_sessions()) or "no sessions")


@audit.command("show")
def audit_show(session_id: str, ctx: typer.Context) -> None:
    s = AuditStorage(Path(ctx.obj["data_dir"]))
    console.print(s.show(session_id) or "not found")


kb = typer.Typer()
app.add_typer(kb, name="kb")


@kb.command("search")
def kb_search(query: str, ctx: typer.Context) -> None:
    console.print(
        json.dumps(search_local(ctx.obj["settings"].knowledge.local_paths, query), indent=2)
    )
