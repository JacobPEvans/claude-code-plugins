---
name: refresh-repo
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

Only remove a worktree if it is confirmed stale.

**Stale definition**: The branch has a merged PR (`gh pr list --state merged --head <branch>`)
OR its remote tracking branch was deleted (`[gone]` in `git branch -vv`).

Branches with open PRs, local-only branches without PRs, and worktrees with uncommitted
changes are **NEVER** stale.

For each worktree from `git worktree list`:

1. Skip `main` and bare repo entries
2. Check if stale (merged PR or `[gone]`)
3. Run `git worktree remove <path>` — **NEVER use `--force`**
4. If Git blocks removal (dirty worktree), report it and skip
5. If removed, also delete the branch: `git branch -d <branch>`

Finish with `git worktree prune`.

### 5. Summary

Report: PRs assessed as merge-ready (if any), branches cleaned up, worktrees removed, current branch and sync status.

## Common Mistake to Avoid

**DO NOT** skip the PR check just because you're on main. The user may have multiple open PRs from different branches.

Always run `gh pr list --author @me --state open` to find work that needs merging.
