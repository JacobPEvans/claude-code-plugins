# infra-orchestration

Claude Code plugin for cross-repo infrastructure orchestration across Terraform and Ansible workflows.

## Skills

- **`/infra-orchestrate`** - Master orchestrator with dependency graph dispatch across infrastructure repos
- **`/infra-sync-inventory`** - Export Terraform inventory and distribute to Ansible repositories
- **`/infra-e2e-test`** - End-to-end pipeline validation across Terraform and Ansible repos

## Installation

```bash
claude plugins add jacobpevans-cc-plugins/infra-orchestration
```

## Usage

```text
/infra-orchestrate plan-all
/infra-orchestrate validate-all
/infra-sync-inventory
/infra-e2e-test
```

## License

MIT
