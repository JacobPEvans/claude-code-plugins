---
name: infra-orchestrate
description: Master orchestrator for cross-repo infrastructure with dependency graph dispatch
---

# Infrastructure Orchestrator

Master orchestrator for cross-repo infrastructure operations. Manages the dependency graph
between Terraform and Ansible repositories and dispatches Task subagents for each phase.

## Dependency Graph

```text
terraform-proxmox
  -> ansible-proxmox (host configuration)
  -> ansible-proxmox-apps (application configuration)
     -> ansible-splunk (Splunk Enterprise)
```

Terraform provisions infrastructure first. Ansible configures it in dependency order.

## Supported Operations

### plan-all

Run `terragrunt plan` in terraform-proxmox, then `ansible-playbook --check` across all Ansible repos in dependency order.

### validate-all

Run `terragrunt validate` in terraform-proxmox, then `ansible-playbook --syntax-check` across all Ansible repos.

### sync-inventory

Export Terraform outputs as Ansible inventory and distribute to all Ansible repos. See `/infra-sync-inventory` for details.

### e2e-test

Full pipeline validation: validate, plan, export inventory, syntax-check, check, diff. See `/infra-e2e-test` for details.

## Execution Pattern

1. **Resolve repo paths**: All repos at `~/git/<repo-name>/main/`
2. **Dispatch Terraform phase**: Launch subagent for terraform-proxmox operations
3. **Await completion**: Terraform must complete before Ansible phases
4. **Dispatch Ansible phases**: Launch parallel subagents for independent Ansible repos
5. **Collect results**: Aggregate success/failure from all subagents
6. **Report**: Summary with per-repo status

## Secret Injection

All repos use Doppler for runtime secrets: `doppler run -- <command>`. Never hardcode credentials.

## Error Handling

If any phase fails, report the failure and stop dependent phases. Independent repos continue in parallel.
