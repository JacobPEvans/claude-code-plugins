---
name: sync-main
description: Update main from remote and merge into current or all PR branches
---

# Sync Main

Update the local `main` branch from remote and merge it into the current working branch,
or all open PR branches when using the `all` parameter.

## Scope Parameter

| Usage | Scope |
| ----- | ----- |
| `/sync-main` | Current branch only |
| `/sync-main all` | All open PR branches |

**CURRENT REPOSITORY ONLY** - This command never crosses into other repositories.

## Prerequisites

- You must be in a feature branch worktree (not on main itself)
- The current branch should have no uncommitted changes

## Single Branch Mode (Default)

1. **Verify state**: `git branch --show-current`, `git status --porcelain`
   - STOP if on main or uncommitted changes
2. **Find and sync main**: `cd ~/git/<repo>/main && git fetch --all --prune && git pull`
3. **Check for updates**: `git fetch origin main`
4. **Report**: Show commits behind with `git log --oneline HEAD..origin/main` (informational only)
5. **Merge**: `git merge origin/main --no-edit` — merge immediately if behind; if already up-to-date, skip and report
6. **Push**: `git push origin $(git branch --show-current)`
7. **Report**: branch, main SHA, merge status

## All Branches Mode (Orchestrator)

Report sync status for all open PR branches.

### Steps

1. **Get repo**: `gh repo view --json nameWithOwner`
2. **Update main**: CRITICAL - must happen first
3. **List open PRs**: `gh pr list --state open --json number,headRefName,title`
4. **Check each PR**: Launch subagents in parallel (invoke `superpowers:dispatching-parallel-agents`). Each checks if behind main. Do NOT merge or push.
5. **Report**: repo, main SHA, merge-readiness for each PR (current/behind/conflict)
6. **Sync all behind branches**: Merge `origin/main` into every branch that is behind — no confirmation needed
7. **Skip conflicts**: Report any branches with conflicts for manual resolution; do not attempt to merge them

## Conflict Resolution

Read files, understand both versions, combine intelligently, stage resolved files, commit.

## DO NOT

- Blindly use `--theirs` or `--ours`
- Force push unless explicitly asked
- Skip reading conflicted files
