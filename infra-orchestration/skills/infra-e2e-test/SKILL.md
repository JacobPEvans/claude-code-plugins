---
name: infra-e2e-test
description: End-to-end infrastructure pipeline validation across Terraform and Ansible repos
---

# Infrastructure End-to-End Test

Full pipeline validation across every infrastructure repo in dependency order.
Validates syntax, plans changes, exports inventory, and dry-runs Ansible playbooks.

## Pipeline Stages

### Stage 1: Terraform Validate

```bash
cd ~/git/terraform-proxmox/main
doppler run -- terragrunt validate
```

### Stage 2: Terraform Plan

```bash
cd ~/git/terraform-proxmox/main
doppler run -- terragrunt plan
```

### Stage 3: Export Inventory

Run `/infra-sync-inventory` to export Terraform outputs and distribute to Ansible repos.

### Stage 4: Ansible Syntax Check

Run in parallel across all Ansible repos:

```bash
doppler run -- ansible-playbook --syntax-check -i inventory/hosts.yml playbooks/site.yml
```

Target repos: ansible-proxmox, ansible-proxmox-apps, ansible-splunk

### Stage 5: Ansible Check Mode (Dry Run)

Run in parallel across all Ansible repos:

```bash
doppler run -- ansible-playbook --check -i inventory/hosts.yml playbooks/site.yml
```

### Stage 6: Ansible Diff

Run in parallel across all Ansible repos:

```bash
doppler run -- ansible-playbook --check --diff -i inventory/hosts.yml playbooks/site.yml
```

## Results

Report per-stage, per-repo pass/fail status:

| Stage | terraform-proxmox | ansible-proxmox | ansible-proxmox-apps | ansible-splunk |
| --- | --- | --- | --- | --- |
| Validate | PASS/FAIL | - | - | - |
| Plan | PASS/FAIL | - | - | - |
| Syntax Check | - | PASS/FAIL | PASS/FAIL | PASS/FAIL |
| Check Mode | - | PASS/FAIL | PASS/FAIL | PASS/FAIL |
| Diff | - | PASS/FAIL | PASS/FAIL | PASS/FAIL |

## Error Handling

Stage failures in Terraform block all subsequent stages. Ansible stage failures are independent per-repo.
