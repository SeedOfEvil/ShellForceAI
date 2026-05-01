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
