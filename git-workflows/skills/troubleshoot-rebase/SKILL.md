---
name: troubleshoot-rebase
description: Diagnose and recover from git rebase failures
---

# Git Rebase Troubleshoot

Diagnose and recover from rebase failures. Invoke when standard rebase error handling cannot resolve the issue.

## Quick Diagnosis

Check: `pwd`, `git status`, `git branch --show-current`, `git worktree list`, `gh pr view`.

## Error: Push Rejected (Non-Fast-Forward)

Branches have diverged. First, confirm your current branch: `git branch --show-current`.

- If this is a **feature branch** (for example `feature/foo`) and the push was rejected:
  - Rebase onto the latest main: `git fetch origin && git rebase origin/main`
  - Then push your feature branch: `git push --force-with-lease origin HEAD`

- If you are on **main** and are behind `origin/main`, do **not** rebase main:
  - Update main: `git fetch origin && git reset --hard origin/main`
  - Then retry your original operation (for example, rebase your feature branch onto main and push the feature branch).

If the rebase fails because `origin/main` moved again, repeat: fetch, rebase your feature branch, then push with `--force-with-lease`.

## Error: Repository Rule Violations

GH013 error about PR/status checks. This is NOT a block if commits are from approved PR.

**Causes**: CI not passing, reviews not approved, merge conflict.

**Fix order**: Rebase feature -> push (triggers CI) -> wait for checks -> merge to main -> push.

Check: `gh pr view <branch> --json checks,reviews,statusCheckRollup`

## Error: Embedded Git Repository

Nested .git directory found. Fix: `git rm --cached <folder-name>` or add to `.gitignore`.

## Rebase Conflict

Identify: `git status`, `git diff --name-only --diff-filter=U`

Resolve: edit files, `git add <file>`, then `git rebase --continue` (or `--abort`).

## Error: Fast-Forward Merge Failed

Main was updated between rebase and merge. Run `git fetch origin && git reset --hard origin/main`, then retry.

## Error: Feature Branch Push Failed

Fix: `git push --force-with-lease origin <branch>`

## Recovery: Aborting In-Progress Rebase

`git rebase --abort && git status`

## Verification

Before retrying:

- Main synced: `git diff origin/main --stat` (should be empty)
- Branch clean: `git status`
- No rebase in progress: check `.git/rebase-{merge,apply}` doesn't exist
- PR state: `gh pr view <branch> --json state`

## Escalation

If unresolved: check `git reflog`, review `git log -10 --oneline`, ask user.

**DO NOT**: Use `--force` (use `--force-with-lease`), use `gh pr merge`, run `git rebase -i`.
