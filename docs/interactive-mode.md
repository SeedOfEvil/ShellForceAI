# Interactive mode

Running `shellforgeai` with no subcommand launches interactive mode.

- Banner shows version, mode/profile, model provider/model, workspace.
- Workspace trust prompt is required unless previously trusted in data-dir cache.
- Slash commands: `/help`, `/exit`, `/quit`, `/doctor`, `/model`, `/tools`, `/audit`, `/workspace`, `/mode`, `/profile`, `/clear`, `/raw on|off`, `/context minimal|standard|full`.
- Natural routing: `diagnose ...`, `research ...`, `plan ...`, otherwise `ask`.
- Spinner/status is shown while processing model-backed and evidence-backed requests.

Safety:
- No destructive execution.
- No package install or service restart.
- Apply remains validation-only.
- Model output is advisory.

PR7: ShellForgeAI interactive banner now includes rotating quotes; build metadata env vars SHELLFORGEAI_BUILD_PR/SHELLFORGEAI_BUILD_COMMIT/SHELLFORGEAI_BUILD_BRANCH/SHELLFORGEAI_BUILD_DATE supported; /status and /examples added; artifacts are created on write only; apply remains validation-only; workspace trust does not bypass policy; canonical ShellForgeAI system prompt is required for model-backed flows.

- Note: In restricted containers, Codex may emit bwrap/namespace errors; treat as provider sandbox limitation, not host failure. ShellForgeAI still collects evidence via typed read-only tools.
