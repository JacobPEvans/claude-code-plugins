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

1. Record the current branch and worktree path.
2. Fetch origin with stale remote branch pruning, but without tag updates:
   `git fetch origin --no-tags --prune --force`
3. Determine the default branch from `origin/HEAD`, falling back to `main` or `master`.
4. Sync the default branch from its existing worktree with a fast-forward only merge:
   `git merge --ff-only origin/<default>`.
   If the default worktree is dirty or divergent, report it and skip instead of resetting.
5. Delete local branches already merged into the default branch with `git branch -d`.
   Never delete main/master/develop/current branches, worktree-checked-out branches, or branches
   with open PRs.
6. Switch back to the original branch if it still exists.

Do not use `git fetch --tags`, `git fetch --prune-tags`, or `git pull --tags` during the
normal refresh. Tags are audited separately in Step 4 so local-only non-release tags and
tag rewrites are not deleted by a broad fetch refspec.

### 4. Tag Audit And Cleanup

Treat `origin` as authoritative for release tags only.

Use native Git commands to compare local tags to remote tags:

```bash
git for-each-ref '--format=%(refname:short)' refs/tags
git show-ref --tags
git ls-remote --tags --refs origin
```

For local-only tags:

1. If the tag name matches the release tag pattern `v[0-9]*`, delete it with
   `git tag -d <tag>`.
2. If the tag name does not match the release tag pattern, report it and do not delete it.

For tags that exist both locally and on origin but point at different objects, report the
mismatch and do not force-update it automatically. Never delete or rewrite remote tags.

### 5. Worktree Cleanup

Only remove a worktree if it is confirmed stale.

**Stale definition**: No open PR, no uncommitted changes, and either:

- The branch has a merged PR whose `headRefOid` matches the local branch `HEAD`
  (`gh pr list --state merged --head <branch> --json number,headRefOid,mergedAt`)
- Its remote tracking branch was deleted (`[gone]` in `git branch -vv`) and it has no commits
  ahead of the default branch (`git log origin/<default>..HEAD --oneline` is empty)

Branches with open PRs, local-only branches without PRs, and worktrees with uncommitted
changes are **NEVER** stale.

For each worktree from `git worktree list`:

1. Skip the default branch (main/master), the current branch, and bare repo entries
2. If the branch has an open PR, skip — it is **never** stale
3. Check if stale using the definition above
4. If not stale, skip
5. Run `git worktree remove <path>` — **NEVER use `--force`**
6. If Git blocks removal (dirty worktree), report it and skip
7. If removed, also delete the branch: `git branch -d <branch>`.
   If this fails only because a squash-merged branch is not reachable from local default,
   use `git branch -D <branch>` only when the merged PR `headRefOid` matched the local
   branch `HEAD` before removing the worktree.

Finish with `git worktree prune`.

### 6. Summary

Report: PRs assessed as merge-ready (if any), tags deleted or reported, branches cleaned up,
worktrees removed, current branch, and sync status.

## Common Mistake to Avoid

**DO NOT** skip the PR check just because you're on main. The user may have multiple open PRs from different branches.

Always run `gh pr list --author @me --state open` to find work that needs merging.

Do not use `--prune-tags` as a shortcut for tag cleanup. Git treats tag pruning as an
explicit refspec prune and can delete local-only tags that are not release artifacts.

## Related Skills

- **sync-main** (git-workflows) — Syncs main and merges into current or all PR branches
- **rebase-pr** (git-workflows) — Rebase-merge workflow for merging individual PRs
- **git-workflow-standards** (git-standards) — Worktree structure and branch hygiene conventions
