placeholder

## Interactive CLI mode

`shellforgeai` with no subcommand starts interactive mode with workspace trust confirmation, slash commands, natural routing, status spinner, and clean model output.

PR7: ShellForgeAI interactive banner now includes rotating quotes; build metadata env vars SHELLFORGEAI_BUILD_PR/SHELLFORGEAI_BUILD_COMMIT/SHELLFORGEAI_BUILD_BRANCH/SHELLFORGEAI_BUILD_DATE supported; /status and /examples added; artifacts are created on write only; apply remains validation-only; workspace trust does not bypass policy; canonical ShellForgeAI system prompt is required for model-backed flows.
\n## Interactive guardrails update\n- Interactive mode is not a shell; shell-looking pasted input is blocked unless explicitly prefixed with ask explain/review.
- Multiline shell paste recovery uses a short-lived quarantine: subsequent shell fragments are blocked without model calls, while /help and /exit still work.\n- Slash commands are deterministic and unknown slash commands do not call the model.\n- Added /health and /audit latest interactive commands.\n- Apply remains validation-only; workspace trust does not bypass mutation policy.\n- Service-impacting commands must be described as approval-required/operator-run.\n
