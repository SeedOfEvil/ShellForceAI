placeholder

## Interactive mode safety

Workspace trust in interactive mode allows local workspace reading and audit/artifact writes under the ShellForgeAI data directory only. It does not allow destructive actions, service restart/reload, package installs, arbitrary shell execution, or auto-apply. Apply remains validation-only and model output is advisory.
