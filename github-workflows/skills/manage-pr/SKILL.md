---
name: manage-pr
description: Create, monitor, and fix pull requests until ready to merge
---

# Manage PR

Manages YOUR PRs as author - create, monitor, fix, prepare for merge. For reviewing others' PRs, use `/review-pr`.

## Scope

**SINGLE PR** - One PR at a time, from argument or current branch.

## Critical Rules

1. **NEVER auto-merge** - Wait for explicit user approval
2. **ALL checks must pass** - Never merge with failures
3. **ALL conversations RESOLVED** - Verify all review threads resolved
4. **Run validation locally** before pushing
5. **User approves merge** - Only after checks pass AND conversations resolved
6. **Create PR immediately** when work complete - kicks off reviews
7. **Watch CI** - Run `gh pr checks <PR> --watch` after creation

## Phase 1: Create PR

1. Run local validation (`markdownlint-cli2 .`, project linters)
2. Verify clean: `git status`
3. Push: `git push -u origin $(git branch --show-current)`
4. Create PR: `gh pr create --title "<type>: <description>" --body "..."`
5. Wait for CI: `gh pr checks <PR_NUMBER> --watch`

## Phase 2: Resolution Loop

### 2.1 Health Check

`gh pr view <PR> --json state,mergeable,statusCheckRollup,reviews`

### 2.2 Fix Failed Checks

Identify -> view logs -> fix locally -> validate -> commit -> push -> wait -> loop back to 2.1

### 2.3 Resolve Conversations

Address all review thread feedback. For batch resolution: `/resolve-pr-review-thread`

## Phase 3: Pre-Handoff

Verify ALL pass before requesting review:

1. All checks pass: `gh pr checks <PR>`
2. Mergeable: `gh pr view <PR> --json mergeable`
3. All threads resolved

**Only if all three pass**: "PR #XX ready for review. All checks pass, conversations resolved."

## Phase 4: Merge (User Action)

User merges: `--squash` for small changes, `--rebase` for larger/multiple commits.

## Workflow

`/init-worktree` -> `/resolve-issues` -> `/manage-pr` -> `/review-pr` -> `/resolve-pr-review-thread` -> merge.
