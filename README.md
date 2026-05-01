# ShellForgeAI

ShellForgeAI is a lean, CLI-first AI ops harness for Linux systems.

## PR2 status

Deterministic core ops runtime is now wired: diagnose collects evidence, proposes conservative plans, and writes audits/artifacts.

Examples:
- `shellforgeai diagnose nginx`
- `shellforgeai diagnose disk --save-plan`
- `shellforgeai research "nginx permission denied"`
- `shellforgeai plan "investigate high disk usage"`
- `shellforgeai audit list`

## Using OpenAI Codex / ChatGPT sign-in

1. Install Codex CLI:
   - `npm install -g @openai/codex`
   - or `brew install --cask codex`
2. Sign in:
   - `codex login`
   - headless: `codex login --device-auth`
3. Configure:
   - `export SHELLFORGEAI_MODEL_PROVIDER=openai-codex`
   - `export SHELLFORGEAI_MODEL_NAME=gpt-5.5`
   - `export SHELLFORGEAI_MODEL_FALLBACK=gpt-5.4`
   - `export SHELLFORGEAI_CODEX_TIMEOUT_SECONDS=180`
4. Verify: `shellforgeai model doctor`
5. Test: `shellforgeai ask "What is this machine doing?"`

ShellForgeAI does not read or manage ChatGPT credentials; authentication is handled by Codex CLI.
Model-backed analysis is advisory only. `apply` remains validation-only.


- Container smoke test: `docs/container-smoke-test.md`

## Interactive mode

Run `shellforgeai` (no subcommand) to start the interactive operator loop.

Example:

```text
shellforgeai
/help
diagnose disk
ask what can you see about this machine?
research nginx address already in use
plan investigate high disk usage
/exit
```

PR7: ShellForgeAI interactive banner now includes rotating quotes; build metadata env vars SHELLFORGEAI_BUILD_PR/SHELLFORGEAI_BUILD_COMMIT/SHELLFORGEAI_BUILD_BRANCH/SHELLFORGEAI_BUILD_DATE supported; /status and /examples added; artifacts are created on write only; apply remains validation-only; workspace trust does not bypass policy; canonical ShellForgeAI system prompt is required for model-backed flows.

- Note: In restricted containers, Codex may emit bwrap/namespace errors; treat as provider sandbox limitation, not host failure. ShellForgeAI still collects evidence via typed read-only tools.
