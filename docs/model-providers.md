# Model providers

## openai-codex
Uses local `codex` CLI with ChatGPT sign-in (`codex login` or `codex login --device-auth`).
ShellForgeAI does not read `~/.codex/auth.json`; it only checks whether the file exists.

Config keys:
- `model.provider`: `openai-codex`
- `model.model`: default `gpt-5.5`
- `model.fallback_model`: default `gpt-5.4`
- `model.timeout_seconds`
- `model.codex_binary`
- `model.codex_sandbox` (`read-only`)
- `model.codex_json`
- `model.codex_skip_git_repo_check`
- `model.allow_model_fallback`

Env overrides:
- `SHELLFORGEAI_MODEL_PROVIDER`
- `SHELLFORGEAI_MODEL_NAME`
- `SHELLFORGEAI_MODEL_FALLBACK`
- `SHELLFORGEAI_CODEX_BINARY`
- `SHELLFORGEAI_CODEX_TIMEOUT_SECONDS`
- `SHELLFORGEAI_CODEX_SKIP_GIT_REPO_CHECK`


## OpenAI Codex CLI notes
- Codex CLI must be installed separately (or baked into image).
- Use `codex login --device-auth` for headless containers.
- ShellForgeAI does not manage auth and does not parse `~/.codex/auth.json`.
- ShellForgeAI invokes local Codex subprocess in read-only sandbox mode.

## Interactive model behavior

Interactive mode uses the same provider abstraction. If model is unavailable, it shows setup guidance (`shellforgeai model doctor`) and does not crash.

PR7: ShellForgeAI interactive banner now includes rotating quotes; build metadata env vars SHELLFORGEAI_BUILD_PR/SHELLFORGEAI_BUILD_COMMIT/SHELLFORGEAI_BUILD_BRANCH/SHELLFORGEAI_BUILD_DATE supported; /status and /examples added; artifacts are created on write only; apply remains validation-only; workspace trust does not bypass policy; canonical ShellForgeAI system prompt is required for model-backed flows.
