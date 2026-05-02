from __future__ import annotations

import os
import platform
from ast import literal_eval
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
from shellforgeai.tools import disk, firewall, host, network, process, registry, systemd
from shellforgeai.version import get_build_info

from .commands import route_input
from .guards import is_multiline_shell_fragment, is_shell_fragment_line, looks_like_shell_command
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
            "firewall is on or off",
            "firewall status",
            "firewall enabled",
            "check firewall",
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


def _summary_for_check(c) -> str:
    first = (c.stderr or c.stdout or "").splitlines()[0] if (c.stderr or c.stdout) else ""
    if c.tool == "host.info" and "hostname" in c.stdout:
        payload = literal_eval(c.stdout)
        return (
            f"hostname={payload.get('hostname', 'unknown')} "
            f"kernel={payload.get('kernel', 'unknown')} "
            f"arch={payload.get('arch', 'unknown')}"
        )
    if c.tool == "host.resources":
        return (c.stdout or "").replace("{'loadavg': ", "loadavg=").replace("}", "")
    if c.tool == "host.uptime":
        return first or "uptime unavailable"
    if c.tool in {"disk.usage", "disk.inodes"}:
        lines = (c.stdout or "").splitlines()[1:3]
        vals = []
        for ln in lines:
            parts = ln.split()
            if len(parts) >= 6:
                vals.append(f"{parts[5]} {parts[4]} used")
        return ", ".join(vals) if vals else (first or "disk summary unavailable")
    if c.tool == "network.dns" and "nameserver" in (c.stdout or ""):
        ns = [ln.split()[1] for ln in c.stdout.splitlines() if ln.startswith("nameserver")]
        return f"docker resolver {ns[0]}" if ns else "dns configured"
    if c.tool == "network.routes":
        return first or "route summary unavailable"
    if c.tool == "process.top":
        return (
            "top process summary available"
            if c.ok
            else f"unavailable — {first or 'command failed'}"
        )
    if c.tool.startswith("systemd") and not c.ok:
        return f"unavailable — {first or 'systemctl not found'}"
    return first[:120] if first else ("ok" if c.ok else "unavailable")


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
        *firewall.detect(),
    ]
    return [
        {
            "tool": c.tool,
            "status": "ok" if c.ok else "unavailable",
            "summary": _summary_for_check(c),
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
    paste_guard_active = False
    paste_guard_remaining_lines = 0
    paste_guard_non_shell_lines = 0
    paste_guard_first_notice = False
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
            paste_guard_active = False
            continue
        if routed.name == "/help":
            console.print("""Session:
  /help              Show this help
  /exit, /quit       Exit ShellForgeAI
  /clear             Clear the screen

Status:
  /status            Show runtime summary
  /doctor            Show ShellForgeAI health
  /health            Run machine health checks
  /model             Show model provider status
  /workspace         Show workspace trust/status
  /mode              Show current mode
  /profile           Show active profile

Ops:
  diagnose <target>  Collect evidence and diagnose targets
  research <query>   Search local knowledge first
  plan <goal>        Create a conservative read-only plan
  ask <question>     Ask the configured model

Debug:
  /raw on|off        Toggle raw provider events
  /context <mode>    Set context mode: minimal, standard, full

Examples:
  diagnose disk
  research nginx address already in use
  plan investigate high disk usage
  ask explain this command: systemctl status nginx --no-pager

Shell paste guard:
  ShellForgeAI is not a shell. Run host/container commands outside sfai>.
  To review a command, prefix it with:
  ask explain this command: ...""")
            continue
        if routed.name == "/examples":
            console.print("""Diagnostics:
  diagnose disk
  diagnose network
  diagnose nginx
Research:
  research nginx address already in use
  research docker dns resolution
Planning:
  plan investigate high disk usage
  plan troubleshoot nginx 502 errors
Ask:
  ask what can you inspect here?
  ask explain this command: systemctl status nginx --no-pager
  ask review this shell snippet: df -h && du -xhd1 /var
Safety:
  Can you restart nginx for me?
  What would you check before restarting nginx?
Commands:
  /health
  /audit latest""")
            continue
        if routed.name in {"/doctor", "/status", "/health"}:
            b = get_build_info()
            if routed.name == "/health":
                checks = _collect_machine_health()
                console.print("Collected evidence:")
                _evidence_table(console, checks)
                console.print(
                    "Health summary:\n"
                    "Read-only checks completed. Review unavailable rows "
                    "and investigate as needed."
                )
            else:
                console.print(
                    f"version={b.display_version} "
                    f"profile={runtime.profile.name} "
                    f"mode={runtime.session.mode}"
                )
            continue
        if routed.name == "/model":
            info = build_provider(runtime.settings).doctor()
            for k, v in info.items():
                console.print(f"{k}={v}")
            continue
        if routed.name == "/profile":
            p = runtime.profile
            console.print(
                f"Profile: {p.name}\n"
                f"Online allowed: {p.online_allowed}\n"
                f"Raw shell allowed: {getattr(p, 'allow_shell_raw', False)}\n"
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
            if routed.args.strip().lower() == "latest":
                if not sessions:
                    console.print("No audit sessions found.")
                else:
                    latest = sessions[-1]
                    console.print(
                        f"Latest audit session: {latest}\n"
                        f"Session file: "
                        f"{runtime.session.data_dir / 'sessions' / (latest + '.json')}\n"
                        f"Artifacts dir: {runtime.session.data_dir / 'artifacts'}"
                    )
                continue
            console.print(
                "No audit sessions found."
                if not sessions
                else "Recent audit sessions:\n" + "\n".join(sessions[:10])
            )
            continue
        if routed.name == "/workspace":
            trusted_now = WorkspaceTrustStore(runtime.session.data_dir).is_trusted(Path.cwd())
            console.print(
                f"Workspace: {Path.cwd()}\n"
                f"Trusted: {'yes' if trusted_now else 'no'}\n"
                f"Data dir: {runtime.session.data_dir}\n"
                f"Artifacts dir: {runtime.session.data_dir / 'artifacts'}\n"
                f"Sessions dir: {runtime.session.data_dir / 'sessions'}\n"
                f"Mode/Profile: {runtime.session.mode}/{runtime.profile.name}\n"
                "Safety: workspace trust allows bounded read context only."
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
                {
                    "tool": i.source,
                    "status": str(i.metadata.get("status", "ok" if i.ok else "unavailable")),
                    "summary": i.summary,
                }
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

        if user_input.startswith("/"):
            console.print(f"Unknown command: {routed.name}")
            console.print("Type /help for available commands.")
            continue
        is_explicit_ask = routed.name == "ask" and routed.args.lower().startswith(
            ("explain this command:", "review this shell snippet:", "what does this command do?")
        )
        raw_for_guard = routed.args if routed.name == "ask" else user_input
        shell_like = is_multiline_shell_fragment(raw_for_guard) or looks_like_shell_command(
            raw_for_guard
        )
        if paste_guard_active and not is_explicit_ask:
            if shell_like or is_shell_fragment_line(raw_for_guard):
                if not paste_guard_first_notice:
                    console.print("""Multiline shell paste detected.

ShellForgeAI interactive mode does not execute shell snippets.

Run it in your shell, or ask me to review it with:

ask review this shell snippet: ...

No command was executed.""")
                    paste_guard_first_notice = True
                else:
                    console.print("Blocked shell paste fragment. No command was executed.")
                paste_guard_remaining_lines -= 1
                if raw_for_guard.strip().lower() in {"done", "fi", "esac", "'"}:
                    paste_guard_active = False
                if paste_guard_remaining_lines <= 0:
                    paste_guard_active = False
                continue
            paste_guard_non_shell_lines += 1
            if paste_guard_non_shell_lines >= 3:
                paste_guard_active = False
            else:
                paste_guard_remaining_lines -= 1
                if paste_guard_remaining_lines <= 0:
                    paste_guard_active = False
        if not is_explicit_ask and shell_like:
            paste_guard_active = True
            paste_guard_remaining_lines = 20
            paste_guard_non_shell_lines = 0
            paste_guard_first_notice = False
            console.print("""Multiline shell paste detected.

ShellForgeAI interactive mode does not execute shell snippets.

Run it in your shell, or ask me to review it with:

ask review this shell snippet: ...

No command was executed.""")
            paste_guard_first_notice = True
            continue
        if not is_explicit_ask and is_shell_fragment_line(raw_for_guard):
            console.print(
                "This looks like a shell command pasted into ShellForgeAI interactive mode.\n\n"
                "ShellForgeAI is not a shell and will not execute it.\n\n"
                "Run this in your host/container shell instead, or ask ShellForgeAI to "
                "explain/review it with:\n\nask explain this command: <command>\n\n"
                "No command was executed."
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
