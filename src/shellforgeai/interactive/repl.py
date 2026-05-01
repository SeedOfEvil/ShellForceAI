from __future__ import annotations

import os
import platform
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from shellforgeai.audit.storage import AuditStorage
from shellforgeai.core.context import RuntimeContext
from shellforgeai.core.diagnose import diagnose_target
from shellforgeai.knowledge.search import search_local
from shellforgeai.llm.manager import build_provider
from shellforgeai.llm.prompts import build_contextual_prompt, build_model_prompt
from shellforgeai.llm.schemas import ModelRequest
from shellforgeai.tools import registry
from shellforgeai.version import __version__

from .commands import route_input
from .streaming import StreamRenderer
from .workspace import WorkspaceTrustStore


def _banner(console: Console, runtime: RuntimeContext, trusted: bool) -> None:
    console.print(
        Panel.fit(
            "ShellForgeAI :: CLI-first AI Ops for Linux\n"
            f"Version: {__version__}\n"
            f"Mode/Profile: {runtime.session.mode}/{runtime.profile.name}\n"
            f"Model: {runtime.settings.model.provider}/{runtime.settings.model.model}\n"
            f"Workspace: {Path.cwd()}\n"
            f"Trust: {'trusted' if trusted else 'untrusted'}"
        )
    )


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
        store.trust(workspace, __version__)
    console.print(f"Workspace trusted: {workspace}")
    return True


def start_interactive(runtime: RuntimeContext, no_trust_cache: bool = False) -> None:
    console = Console()
    trusted = WorkspaceTrustStore(runtime.session.data_dir).is_trusted(Path.cwd())
    _banner(console, runtime, trusted)
    if not _confirm_workspace(console, runtime, no_trust_cache=no_trust_cache):
        return

    raw_mode = False
    context_mode = "standard"
    renderer = StreamRenderer(console)
    console.print("Type /help for commands. Type /exit to quit.")
    while True:
        try:
            user_input = input("sfai> ").strip()
        except EOFError:
            console.print("Goodbye.")
            break
        except KeyboardInterrupt:
            console.print("\nGoodbye.")
            break

        routed = route_input(user_input)
        if routed.name in {"noop"}:
            continue
        if routed.name in {"/exit", "/quit"}:
            console.print("Goodbye.")
            break
        if routed.name == "/help":
            console.print(
                "/help /exit /quit /doctor /model /tools /audit /workspace /mode /profile /clear /raw on|off /context minimal|standard|full"
            )
            continue
        if routed.name == "/doctor":
            console.print(
                f"version={__version__} profile={runtime.profile.name} mode={runtime.session.mode}"
            )
            continue
        if routed.name == "/model":
            info = build_provider(runtime.settings).doctor()
            for k, v in info.items():
                console.print(f"{k}={v}")
            continue
        if routed.name == "/tools":
            for t in sorted(registry.list_tools(), key=lambda x: x.name):
                console.print(f"{t.name}\t{t.category}\t{t.risk.value}")
            continue
        if routed.name == "/workspace":
            console.print(f"workspace={Path.cwd()} trusted=yes")
            continue
        if routed.name == "/mode":
            console.print(runtime.session.mode)
            continue
        if routed.name == "/profile":
            console.print(runtime.profile.name)
            continue
        if routed.name == "/clear":
            os.system("clear")
            continue
        if routed.name == "/raw":
            raw_mode = routed.args.lower() == "on"
            renderer.raw = raw_mode
            console.print(f"raw={raw_mode}")
            continue
        if routed.name == "/context":
            if routed.args in {"minimal", "standard", "full"}:
                context_mode = routed.args
            console.print(f"context={context_mode}")
            continue

        with console.status("Thinking..."):
            if routed.name == "diagnose":
                result = diagnose_target(runtime, routed.args, online=False, since="30m")
                console.print(
                    f"Diagnose {routed.args}: {len(result.findings)} finding(s), {len(result.evidence.items)} evidence item(s)"
                )
            elif routed.name == "research":
                hits = search_local(
                    runtime.settings.knowledge.local_paths + [str(Path.cwd() / "SHELLFORGE.md")],
                    routed.args,
                )
                if hits:
                    for h in hits[:5]:
                        console.print(f"{h.path}:{h.line} {h.snippet}")
                else:
                    console.print("No local knowledge hits.")
            else:
                provider = build_provider(runtime.settings)
                prompt = build_contextual_prompt(
                    routed.args,
                    {
                        "host": platform.platform(),
                        "mode": runtime.session.mode,
                        "identity": "CLI-first Linux ops harness with read-only safety boundaries.",
                        "workspace_trusted": True,
                    },
                    mode=context_mode,
                )
                resp = provider.complete(
                    ModelRequest(
                        prompt=prompt,
                        model=runtime.settings.model.model,
                        provider=runtime.settings.model.provider,
                        timeout_seconds=runtime.settings.model.timeout_seconds,
                        metadata={"raw": raw_mode},
                    )
                )
                if not resp.ok:
                    console.print("Model unavailable. Run: shellforgeai model doctor")
                else:
                    renderer.render(resp.text, resp.raw.get("stdout_jsonl") if resp.raw else None)
                    u = resp.usage or {}
                    console.print(
                        f"Usage: input={u.get('input_tokens')}, cached={u.get('cached_input_tokens')}, output={u.get('output_tokens')}, reasoning={u.get('reasoning_output_tokens')}"
                    )

                AuditStorage(runtime.session.data_dir).append(
                    {
                        "session_id": runtime.session.session_id,
                        "command": "interactive.ask",
                        "summary": routed.args,
                    }
                )
