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
