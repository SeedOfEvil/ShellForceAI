# AGENTS

- Interactive UX changes must preserve:
  - no-command launch behavior
  - --help behavior
  - --version behavior
  - non-interactive command behavior
  - safety boundary
  - docs updates

PR7: ShellForgeAI interactive banner now includes rotating quotes; build metadata env vars SHELLFORGEAI_BUILD_PR/SHELLFORGEAI_BUILD_COMMIT/SHELLFORGEAI_BUILD_BRANCH/SHELLFORGEAI_BUILD_DATE supported; /status and /examples added; artifacts are created on write only; apply remains validation-only; workspace trust does not bypass policy; canonical ShellForgeAI system prompt is required for model-backed flows.
