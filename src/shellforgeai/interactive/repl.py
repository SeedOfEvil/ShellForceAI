from __future__ import annotations

import getpass
import json
import platform
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from shellforgeai.audit.storage import AuditStorage
from shellforgeai.core.context import RuntimeContext
from shellforgeai.core.diagnose import diagnose_target
from shellforgeai.core.evidence import classify_target
from shellforgeai.core.plans import Plan, PlanStep
from shellforgeai.knowledge.search import search_local
from shellforgeai.llm.manager import build_provider
from shellforgeai.llm.prompts import build_contextual_prompt, build_model_prompt
from shellforgeai.llm.schemas import ModelRequest, ModelResponse
from shellforgeai.tools import registry
from shellforgeai.version import __version__


@dataclass
class InteractiveState:
    workspace: Path
    trusted: bool
    raw: bool = False
    context_mode: str = "standard"


class TrustStore:
    def __init__(self, data_dir: Path) -> None:
        self.path = data_dir / "trust" / "workspaces.json"

    def load(self) -> dict[str, dict[str, str]]:
        if not self.path.exists():
            return {}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    def is_trusted(self, workspace: Path) -> bool:
        return str(workspace.resolve()) in self.load()

    def trust(self, workspace: Path) -> None:
        records = self.load()
        records[str(workspace.resolve())] = {
            "trusted_at": datetime.now(UTC).isoformat(),
            "hostname": platform.node(),
            "user": getpass.getuser(),
            "version": __version__,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(records, indent=2), encoding="utf-8")


def render_banner(
    runtime: RuntimeContext, console: Console, workspace: Path, trusted: bool
) -> None:
    provider = runtime.settings.model.provider
    model = runtime.settings.model.model
    console.print(
        Panel.fit(
            "ShellForgeAI :: CLI-first AI Ops for Linux\n"
            f"Version: {__version__}\n"
            f"Mode/Profile: {runtime.session.mode}/{runtime.profile.name}\n"
            f"Model: {provider}/{model}\n"
            f"Workspace: {workspace}\n"
            f"Trust: {'trusted' if trusted else 'untrusted'}"
        )
    )


def prompt_trust(
    console: Console, workspace: Path, runtime: RuntimeContext, trust_store: TrustStore
) -> bool:
    if trust_store.is_trusted(workspace):
        console.print(f"Workspace trusted: {workspace}")
        return True
    console.print("Trust this workspace?\n")
    console.print(f"Path:\n  {workspace}\n")
    console.print(
        "ShellForgeAI may:\n- read SHELLFORGE.md and local docs in this workspace\n- use read-only typed tools\n- write audit records and artifacts under the configured data directory\n- send bounded, redacted context to the configured model provider when model mode is used\n"
    )
    console.print(
        "ShellForgeAI will not:\n- execute destructive actions\n- restart services\n- install packages\n- delete files\n- bypass policy\n- auto-apply model output"
    )
    ok = input(f"\nTrust {workspace}? [y/N] ").strip().lower() in {"y", "yes"}
    if ok:
        trust_store.trust(workspace)
    return ok


def _model_call(
    runtime: RuntimeContext, question: str, context_mode: str, raw: bool
) -> ModelResponse:
    provider = build_provider(runtime.settings)
    prompt = build_contextual_prompt(
        question,
        {
            "identity": "CLI-first Linux ops harness with read-only safety boundaries.",
            "workspace_trust": "trusted",
            "cwd": str(Path.cwd()),
            "advisory_only": True,
        },
        mode=context_mode,
    )
    return provider.complete(
        ModelRequest(
            prompt=prompt,
            model=runtime.settings.model.model,
            provider=runtime.settings.model.provider,
            timeout_seconds=runtime.settings.model.timeout_seconds,
            metadata={"raw": raw},
        )
    )


def run_interactive(runtime: RuntimeContext, console: Console) -> None:
    workspace = Path.cwd()
    store = TrustStore(runtime.session.data_dir)
    trusted = store.is_trusted(workspace)
    render_banner(runtime, console, workspace, trusted)
    if not trusted and not prompt_trust(console, workspace, runtime, store):
        console.print("Workspace not trusted. Exiting interactive mode.")
        return
    state = InteractiveState(workspace=workspace, trusted=True)
    console.print(f"Workspace trusted: {workspace}")
    console.print("Type /help for commands. Type /exit to quit.")
    while True:
        try:
            line = input("sfai> ").strip()
        except EOFError:
            console.print("Goodbye.")
            break
        except KeyboardInterrupt:
            console.print("\nGoodbye.")
            break
        if not line:
            continue
        if line in {"/exit", "/quit"}:
            console.print("Goodbye.")
            break
        if line == "/help":
            console.print(
                "/help /exit /quit /doctor /model /tools /audit /workspace /mode /profile /clear /raw on|off /context minimal|standard|full /diagnose <target> /ask <question> /research <query> /plan <goal>"
            )
            continue
        if line == "/doctor":
            audit = AuditStorage(runtime.session.data_dir)
            console.print(
                f"version={__version__} profile={runtime.profile.name} mode={runtime.session.mode} tools={len(registry.list_tools())} audit_dir={audit.sessions_dir}"
            )
            continue
        if line == "/model":
            info = build_provider(runtime.settings).doctor()
            for k, v in info.items():
                console.print(f"{k}={v}")
            continue
        if line == "/tools":
            for t in sorted(registry.list_tools(), key=lambda x: x.name):
                console.print(f"{t.name}\t{t.category}\t{t.risk.value}")
            continue
        if line == "/workspace":
            console.print(f"workspace={state.workspace} trusted={state.trusted}")
            continue
        if line.startswith("/raw "):
            state.raw = line.split(maxsplit=1)[1].strip() == "on"
            console.print(f"raw={'on' if state.raw else 'off'}")
            continue
        if line.startswith("/context "):
            value = line.split(maxsplit=1)[1].strip()
            if value in {"minimal", "standard", "full"}:
                state.context_mode = value
                console.print(f"context={value}")
            else:
                console.print("context must be minimal|standard|full")
            continue
        if line in {"/mode", "/profile"}:
            console.print(f"mode={runtime.session.mode} profile={runtime.profile.name}")
            continue
        if line == "/clear":
            console.clear()
            continue

        routed = line
        if line.startswith("/diagnose "):
            routed = f"diagnose {line.split(maxsplit=1)[1]}"
        elif line.startswith("/ask "):
            routed = f"ask {line.split(maxsplit=1)[1]}"
        elif line.startswith("/research "):
            routed = f"research {line.split(maxsplit=1)[1]}"
        elif line.startswith("/plan "):
            routed = f"plan {line.split(maxsplit=1)[1]}"

        if routed.startswith("diagnose "):
            target = routed.split(maxsplit=1)[1]
            with console.status("Collecting evidence..."):
                result = diagnose_target(runtime, target)
            console.print(f"Target: {target} Findings: {len(result.findings)}")
            continue
        if routed.startswith("research "):
            query = routed.split(maxsplit=1)[1]
            with console.status("Collecting evidence..."):
                hits = search_local(
                    runtime.settings.knowledge.local_paths + [str(Path.cwd() / "SHELLFORGE.md")],
                    query,
                )
            if hits:
                for h in hits[:5]:
                    console.print(f"{h.path}:{h.line} {h.snippet}")
            else:
                console.print("No local knowledge hits.")
            continue
        if routed.startswith("plan "):
            goal = routed.split(maxsplit=1)[1]
            t = classify_target(goal).value
            p = Plan(
                plan_id=f"plan_{runtime.session.session_id}",
                goal=goal,
                session_id=runtime.session.session_id,
                steps=[
                    PlanStep(
                        step_id="1", title="Collect evidence", description=f"Use diagnose for {t}"
                    )
                ],
            )
            console.print(p.model_dump_json(indent=2))
            continue

        question = routed.removeprefix("ask ") if routed.startswith("ask ") else routed
        with console.status("Asking model..."):
            resp = _model_call(runtime, question, state.context_mode, state.raw)
        if not resp.ok:
            console.print("Model unavailable. Run: shellforgeai model doctor")
            continue
        console.print(resp.text)
        if state.raw and resp.raw and resp.raw.get("stdout_jsonl"):
            console.print(resp.raw["stdout_jsonl"])
