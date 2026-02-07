---
name: sync-permissions
description: Merge local AI permission settings into repository-wide permissions
---

# Sync Permissions

Scan local AI settings across all repos/worktrees, analyze permissions, and merge approved changes into repository permissions.

## Supported Tools

| AI Tool | Config Location | Sync Status |
| --- | --- | --- |
| Claude | `agentsmd/permissions/` | Fully supported |
| Gemini | `.gemini/permissions/` | Fully supported |
| Copilot | `.github/copilot-instructions.md` | Not yet supported |

## Workflow

### Phase 1: Discovery and Analysis

Scan home directory for AI permission settings, classify permissions, and deduplicate against existing patterns.

**Currently scans:**

- Claude settings from `~/.claude/settings.local.json` in all repos/worktrees
- Gemini settings from `~/.gemini/settings.json` in all repos/worktrees

### Phase 2: User Approval

Review analysis report. Ask user to approve, modify, or cancel.

### Phase 3: Execution

**Only after approval**, apply changes, sync across tools, and cleanup local files.

**Sync strategy:**

- Merge permissions using a union approach
- When same permission exists in both tools with different classifications, prioritize Claude classification
- When permission exists only in Gemini, preserve and propagate to Claude
- Result: identical permission sets across all supported tools

## Architecture

Command -> Agent -> Skill pattern:

- Agents: `permissions-analyzer`, `permissions-syncer`
- Skill: `permission-patterns` (safety classification, deduplication, token-efficient extraction)
