---
name: refresh-repo
description: Check PR merge readiness, sync local repo, and cleanup stale worktrees
---

# Git Refresh

Check open PR merge-readiness status, sync the local repository, and cleanup stale worktrees.
**Note**: Does not automatically merge PRs - only reports readiness status for each PR.

> **State warning**: Branch state, remote tracking, and PR status change between
> invocations. Re-run all git/gh commands from Step 1.

## Steps

### 1. Identify Open PRs

**CRITICAL**: Always check for open PRs, regardless of current branch.

```bash
# Check for PR from current branch
gh pr view --json state,number,title 2>/dev/null

# ALWAYS also check for any open PRs by the user
gh pr list --author @me --state open --json number,title,headRefName
```

### 2. Report Merge-Readiness Status

For each open PR, **DO NOT MERGE** - only check and report:

```bash
gh pr view NUMBER --json state,mergeable,statusCheckRollup,reviewDecision
```

**Merge-ready criteria**: State OPEN, Mergeable MERGEABLE, All checks SUCCESS, All threads resolved, Review APPROVED or not required.

### 3. Sync Workflow

1. Fetch all remotes and prune deleted remote branches
2. Switch to default branch (main or master)
3. Pull latest changes
4. Delete local branches already merged into default (never delete main/master/develop)
5. Switch back to original branch if it still exists

### 4. Worktree Cleanup

Only remove a worktree if it is confirmed stale.

**Stale definition**: The branch has a merged PR (`gh pr list --state merged --head <branch>`)
OR its remote tracking branch was deleted (`[gone]` in `git branch -vv`).

Branches with open PRs, local-only branches without PRs, and worktrees with uncommitted
changes are **NEVER** stale.

For each worktree from `git worktree list`:

1. Skip the default branch (main/master) and bare repo entries
2. If the branch has an open PR, skip — it is **never** stale
3. Check if stale: `[gone]` remote, or merged PR (`gh pr list --state merged --head <branch>`)
   AND no commits ahead of default (`git log origin/main..HEAD --oneline` is empty)
4. If not stale, skip
5. Run `git worktree remove <path>` — **NEVER use `--force`**
6. If Git blocks removal (dirty worktree), report it and skip
7. If removed, also delete the branch: `git branch -d <branch>`.
   If this fails (squash-merged branch not reachable from local main), investigate before using `git branch -D`

Finish with `git worktree prune`.

### 5. Summary

Report: PRs assessed as merge-ready (if any), branches cleaned up, worktrees removed, current branch and sync status.

## Common Mistake to Avoid

**DO NOT** skip the PR check just because you're on main. The user may have multiple open PRs from different branches.

Always run `gh pr list --author @me --state open` to find work that needs merging.

## Related Skills

- **sync-main** (git-workflows) — Syncs main and merges into current or all PR branches
- **rebase-pr** (git-workflows) — Rebase-merge workflow for merging individual PRs
- **git-workflow-standards** (git-standards) — Worktree structure and branch hygiene conventions
