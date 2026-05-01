# Interactive Mode

`shellforgeai` now launches an interactive operator loop when run without subcommands.

Flow:
1. Banner with version/mode/provider/workspace
2. Workspace trust check
3. REPL prompt (`sfai>`)

Natural language routing maps `diagnose ...`, `research ...`, and `plan ...` prefixes to their workflows; all other text routes to `ask`.
