placeholder

## Context-first + Codex provider note (PR)
- ShellForgeAI runtime auto-runs approved typed read-only collectors for recognized ops intents (disk/performance/health/firewall/service).
- In current architecture, Codex is used as a model/provider for synthesis; ShellForgeAI tools are executed by the ShellForgeAI runtime.
- Runtime context bundles are the immediate solution; optional MCP exposure of read-only tools is a future path.
- Arbitrary shell remains blocked in interactive mode.
- Mutating/service-impacting actions remain blocked or approval-required/operator-run.
- apply remains validation-only in this alpha.
