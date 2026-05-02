# Codex integration (current + future)

## Current architecture (provider mode)
- ShellForgeAI can call Codex as a model/provider for analysis text generation.
- ShellForgeAI typed tools/collectors are executed by the ShellForgeAI runtime.
- Therefore, ShellForgeAI must collect context first for known intents before sending prompts.

## Why context-first routing is required
Passing collector names in a prompt is not equivalent to tool availability. Without runtime collection (or an exposed tool interface), the model cannot reliably execute those collectors.

## Immediate approach
- Use runtime intent routing + context bundles (`disk`, `performance`, `health`, `firewall`, service diagnostics).
- Provide already-collected evidence block in model prompts.
- Keep arbitrary shell blocked.
- Keep mutation blocked/approval-required.
- Keep `apply` validation-only in alpha.

## Future optional approach (experimental, disabled by default)
Proposed command: `shellforgeai mcp serve --readonly`

Proposed read-only MCP tools:
- `shellforgeai_health`
- `shellforgeai_diagnose_disk`
- `shellforgeai_diagnose_performance`
- `shellforgeai_diagnose_firewall`
- `shellforgeai_diagnose_service`
- `shellforgeai_audit_recent`

Mutating tools are explicitly excluded from the initial MCP surface.
