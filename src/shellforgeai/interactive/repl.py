from __future__ import annotations

import os
import platform
from pathlib import Path

import typer
from rich.console import Console

from shellforgeai.core.context import RuntimeContext
from shellforgeai.interactive.banner import build_banner
from shellforgeai.llm.manager import build_provider
from shellforgeai.llm.prompts import build_contextual_prompt
from shellforgeai.llm.schemas import ModelRequest
from shellforgeai.tools import disk, host, network, process, systemd
from shellforgeai.version import get_build_info

from .commands import route_input
from .streaming import StreamRenderer
from .workspace import WorkspaceTrustStore


def _ensure_artifact_dir(runtime: RuntimeContext) -> None:
    runtime.session.artifact_dir.mkdir(parents=True, exist_ok=True)


def _is_machine_health_question(text: str) -> bool:
    t = text.lower()
    needles = [
        "issue on this machine",
        "machine healthy",
        "what's wrong with this box",
        "check this system",
        "machine look",
        "anything broken",
    ]
    return any(n in t for n in needles)


def _sanitize_provider_error(text: str) -> str:
    if "bwrap: No permissions to create a new namespace" in text:
        return (
            "Codex sandbox could not create a namespace in this container. "
            "This is a provider/container sandbox limitation, "
            "not evidence of host failure."
        )
    return text


def _confirm_workspace(console: Console, runtime: RuntimeContext, no_trust_cache: bool) -> bool:
    store = WorkspaceTrustStore(runtime.session.data_dir)
    workspace = Path.cwd()
    if not no_trust_cache and store.is_trusted(workspace):
        console.print(f"Workspace trusted: {workspace}")
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


def _collect_machine_health() -> dict[str, object]:
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
    return {
        "checks": [
            {
                "tool": c.tool,
                "ok": c.ok,
                "exit_code": c.exit_code,
                "stdout": c.stdout,
                "stderr": c.stderr,
            }
            for c in checks
        ]
    }


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
        if routed.name in {"noop"}:
            continue
        if routed.name in {"/exit", "/quit"}:
            console.print("Goodbye.")
            return
        if routed.name == "/help":
            console.print(
                "Session:\n  /help  /exit,/quit  /clear\n"
                "Status:\n  /status /doctor /model /workspace /mode /profile\n"
                "Ops:\n  diagnose <target> | research <query> | plan <goal> | ask <question>"
            )
            continue
        if routed.name in {"ask", "diagnose", "plan", "research"} or _is_machine_health_question(
            routed.args or user_input
        ):
            pass
        if routed.name == "/clear":
            os.system("clear")
            continue
        if routed.name == "/examples":
            console.print(
                "diagnose disk\nresearch nginx address already in use\n"
                "plan investigate high disk usage"
            )
            continue
        if routed.name in {"/doctor", "/status"}:
            build = get_build_info()
            console.print(
                f"version={build.display_version} profile={runtime.profile.name} "
                f"mode={runtime.session.mode} trusted=yes"
            )
            continue
        if routed.name == "/model":
            for k, v in build_provider(runtime.settings).doctor().items():
                console.print(f"{k}={v}")
            continue

        provider = build_provider(runtime.settings)
        context = {
            "host": platform.platform(),
            "mode": runtime.session.mode,
            "workspace_trusted": True,
        }
        if _is_machine_health_question(routed.args or user_input):
            with console.status("Collecting evidence..."):
                context["machine_health"] = _collect_machine_health()
            question = user_input
            kind = "diagnose"
        else:
            question = routed.args or user_input
            kind = "ask"
        with console.status("Preparing context..."):
            prompt = build_contextual_prompt(question, context, mode="standard")
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
        renderer.render(
            _sanitize_provider_error(resp.text), resp.raw.get("stdout_jsonl") if resp.raw else None
        )
