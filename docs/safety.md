placeholder

## Interactive trust boundary

Workspace trust allows reading workspace docs and writing artifacts/audit under data dir. It does not enable destructive actions, arbitrary shell, service restarts, package installs, or auto-apply.

PR7: ShellForgeAI interactive banner now includes rotating quotes; build metadata env vars SHELLFORGEAI_BUILD_PR/SHELLFORGEAI_BUILD_COMMIT/SHELLFORGEAI_BUILD_BRANCH/SHELLFORGEAI_BUILD_DATE supported; /status and /examples added; artifacts are created on write only; apply remains validation-only; workspace trust does not bypass policy; canonical ShellForgeAI system prompt is required for model-backed flows.

- Note: In restricted containers, Codex may emit bwrap/namespace errors; treat as provider sandbox limitation, not host failure. ShellForgeAI still collects evidence via typed read-only tools.
