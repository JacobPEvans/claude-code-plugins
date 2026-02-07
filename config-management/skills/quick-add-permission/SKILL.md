---
name: quick-add-permission
description: Quickly add always-allow permissions to all AI tool permission lists
---

# Quick Add Permission

Quickly add one or more always-allow permissions to all AI tool permission lists (Claude, Gemini, etc.) with a fresh worktree off the latest main.

## Parameters

The command accepts optional permission(s) as arguments in flexible formats:

```text
/quick-add-permission
/quick-add-permission "docker ps"
/quick-add-permission "docker ps" "docker logs" "kubectl get"
/quick-add-permission "Bash(docker ps:*)"
```

If no arguments provided, the command will prompt interactively.

### Input Format Detection

The command intelligently converts simple inputs to proper permission format:

- `"docker ps"` -> `"Bash(docker ps:*)"`
- `"git status"` -> `"Bash(git status:*)"`
- `"kubectl get pods"` -> `"Bash(kubectl get pods:*)"`
- `"Bash(docker ps:*)"` -> Used as-is (already formatted)

## Steps

### 1. Sync Main and Create Worktree

Sync main and create worktree with branch name: `chore/add-permissions-$(date +%Y%m%d-%H%M%S)`.

### 2. Gather and Format Permission Input

- Parse arguments or prompt interactively
- Convert plain text to `Bash(command:*)` format
- Use as-is if already formatted with parentheses
- Confirm format with user

### 3. Update Permission Files

Files: `agentsmd/permissions/{allow,ask,deny}.json`, `.gemini/permissions/{allow,deny}.json`

For each permission:

1. Read existing JSON, check for duplicates
2. Add new permission, maintain alphabetical order
3. Sync across all AI tools
4. Verify JSON validity with `jq empty`

### 4. Summary

Report: worktree, branch, permissions added, files modified, next steps.

## Notes

- Fresh worktree from latest main
- Sync across all AI tools
- Maintain alphabetical ordering
- Skip duplicates, verify JSON
