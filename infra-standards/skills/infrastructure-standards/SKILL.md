---
name: infrastructure-standards
description: Use when working on infrastructure repos (terraform, ansible, kubernetes, proxmox, nix devShells)
---

# Infrastructure Standards

## General Principles

- **Idempotency**: All IaC must produce same result on repeated runs.
- **Modularity**: Organize into reusable modules.
- **State management**: Remote state with locking (DynamoDB for AWS).
- **Security**: Least privilege, encrypt at rest and in transit.
- **Cost**: Right-size resources, tag everything, set budget alerts.

## Deployment Pipeline

```text
terraform-proxmox  ->  ansible-proxmox  ->  ansible-proxmox-apps  ->  ansible-splunk
(provision VMs)        (configure host)     (configure apps)          (configure Splunk)
```

Not every change needs the full pipeline. App config: ansible-proxmox-apps
only. Splunk config: ansible-splunk only. New VM: full pipeline.

## VMID & IP Addressing

IPs use pattern `192.168.0.{vmid}` (for VMIDs under 256).

| VMID Range | Purpose | Examples |
| --- | --- | --- |
| 100-109 | Infrastructure | ansible, pi-hole |
| 110-149 | Utilities | pve-scripts |
| 150-169 | AI Dev | claude-code, gemini |
| 170-179 | Cribl Stream | cribl-stream (171-172) |
| 180-189 | Cribl Edge | cribl-edge (181-182) |
| 190-199 | LB/Management | haproxy, splunk-mgmt |
| 200-299 | VMs | splunk-vm (200) |
| 9000-9999 | Templates | Not running, no IP |

## Dev Shell Architecture

Every repo owns its own dev shell. No central registry.

```text
repo/
├── flake.nix      <- defines devShells.default
├── flake.lock     <- pins nixpkgs independently
├── .envrc         <- `use flake` (ALWAYS committed)
└── .direnv/       <- ALWAYS in .gitignore
```

| Repo | Template | Key Tools |
| --- | --- | --- |
| ansible-proxmox | `nix-devenv?dir=shells/ansible` | ansible, molecule, sops, age |
| ansible-proxmox-apps | `nix-devenv?dir=shells/ansible` | + SOPS_AGE_KEY_FILE |
| terraform-proxmox | `nix-devenv?dir=shells/terraform` | terraform, terragrunt, tfsec, trivy |
| terraform-aws | `nix-devenv?dir=shells/terraform` | same as terraform-proxmox |
| kubernetes-monitoring | `nix-devenv?dir=shells/kubernetes` | kubectl, helm, helmfile, k9s, kind |
| splunk | `nix-devenv?dir=shells/splunk-dev` | uv (Python 3.9 on-demand) |

## Secrets Management

### SOPS vs Doppler Decision

| Scenario | Tool |
| --- | --- |
| Runtime injection (env vars) | Doppler |
| Secrets committed to git (encrypted) | SOPS |
| Terraform state encryption | SOPS |
| Ansible vault replacement | SOPS |
| CI/CD pipeline secrets | Doppler |

**Rule**: If it must exist in a git-tracked file, use SOPS. If injectable
at runtime, use Doppler.

### Doppler Usage

```bash
# Terraform
doppler run --name-transformer tf-var -- terragrunt plan
# With AWS
aws-vault exec terraform -- doppler run --name-transformer tf-var -- terragrunt apply
# Ansible
doppler run -- ansible-playbook -i inventory/hosts.yml playbooks/site.yml
```

### SOPS Configuration

`.sops.yaml` at repo root:

```yaml
creation_rules:
  - path_regex: (\.enc\.ya?ml$|secrets/.*\.ya?ml$)
    age: >-
      age1your-public-key-here
```

Naming: encrypted = `.enc.yml`, plaintext = `.yml` (in `.gitignore`).
Precedence: when both provide same secret, Doppler (runtime) wins.

## Terraform Inventory Contract

Terraform outputs feed Ansible dynamic inventory:

```json
{
  "splunk": {
    "hosts": ["192.168.0.200"],
    "vars": { "ansible_port": 22, "ansible_user": "ansible" }
  }
}
```

**Contract rules**:

- Terraform owns IP assignment (derived from VMID) and port assignment
- Ansible consumes but never overrides these values
- Changes to IPs/ports must originate in terraform-proxmox
