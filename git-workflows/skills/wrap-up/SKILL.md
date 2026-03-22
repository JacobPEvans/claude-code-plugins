---
name: wrap-up
description: >-
  End-of-session cleanup after PR merge: refresh repo, run quick retrospective,
  and clean gone branches. Combines /refresh-repo, /retrospecting quick, and
  /clean_gone into a single post-merge workflow.
---

# Post-Merge Wrap-Up

Run all three steps in order. Each step is a separate skill invocation.
After completing the steps, provide a summary of the actions taken.

## Step 1: Refresh Repository

Invoke `/refresh-repo` to:

- Check merge-readiness of any remaining open PRs
- Sync local main with remote
- Clean up stale worktrees (merged PRs, `[gone]` remote branches)
- Report repository state

## Step 2: Quick Retrospective

Invoke `/retrospecting quick` to capture a brief session retrospective:

- Git history analysis (commits, files changed)
- Session efficiency metrics
- Key decisions and outcomes
- Actionable improvements

**Requires**: `claude-retrospective` plugin (external).
If not installed, skip this step and note it was skipped.

## Step 3: Clean Gone Branches

Invoke `/clean_gone` to remove any local branches whose remote tracking branch
has been deleted:

- Identify branches marked `[gone]`
- Remove associated worktrees
- Delete the local branches

**Requires**: `commit-commands` plugin (external).
If not installed, skip this step and note it was skipped.

## Summary

Report what was completed:

```text
Wrap-Up Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Refresh:        done or skipped
  Retrospective:  done or skipped
  Branch cleanup:  done or skipped
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
