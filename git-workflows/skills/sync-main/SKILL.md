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
3. **Check for updates**: `git fetch origin main && git merge-base --is-ancestor origin/main HEAD`
4. **Inform user**: Report if branch is behind main with summary of commits
5. **Request confirmation**: Ask user if they want to merge main into current branch
6. **Merge (if confirmed)**: `git merge origin/main --no-edit`
7. **Push (if confirmed)**: `git push origin $(git branch --show-current)`
8. **Report**: branch, main SHA, merge status or "merge declined by user"

## All Branches Mode (Orchestrator)

Report sync status for all open PR branches.

### Steps

1. **Get repo**: `gh repo view --json nameWithOwner`
2. **Update main**: CRITICAL - must happen first
3. **List open PRs**: `gh pr list --state open --json number,headRefName,title`
4. **Check each PR**: Launch subagents in parallel. Each checks if behind main. Do NOT merge or push.
5. **Report**: repo, main SHA, merge-readiness for each PR (current/behind/conflict)
6. **Prompt user**: Ask which PRs should be synced with main
7. **Sync only confirmed**: Only merge confirmed branches after user approval

## Conflict Resolution

Read files, understand both versions, combine intelligently, stage resolved files, commit.

## DO NOT

- Blindly use `--theirs` or `--ours`
- Force push unless explicitly asked
- Skip reading conflicted files
