---
name: git-refresh
description: Check PR merge readiness, sync local repo, and cleanup stale worktrees
---

# Git Refresh

Check open PR merge-readiness status, sync the local repository, and cleanup stale worktrees.
**Note**: Does not automatically merge PRs - only reports readiness status for each PR.

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

List worktrees, identify stale ones (branch merged or deleted), remove stale worktrees, prune.

A worktree is stale if its branch no longer exists or has been merged into main.

### 5. Summary

Report: PRs assessed as merge-ready (if any), branches cleaned up, worktrees removed, current branch and sync status.

## Common Mistake to Avoid

**DO NOT** skip the PR check just because you're on main. The user may have multiple open PRs from different branches.

Always run `gh pr list --author @me --state open` to find work that needs merging.
