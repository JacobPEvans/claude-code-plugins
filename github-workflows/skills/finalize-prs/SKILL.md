---
name: finalize-prs
description: Orchestrate PR finalization across all repositories and report merge-readiness
---

# Ready Player One

Finalize all open PRs across all owned repositories by fixing CI failures, resolving review threads, and reporting which PRs
are ready to merge versus blocked.

## Scope

**ALL OWNED REPOSITORIES** - Orchestrates complete PR finalization workflow across all repos.

What this command DOES:

- Execute `/fix-pr-ci all` to resolve CI failures
- Execute `/resolve-pr-review-thread all` to resolve review threads
- Scan all repos for open PRs
- Determine merge-readiness status for each PR
- Generate JSON report of ready vs blocked PRs

What this command DOES NOT:

- Merge PRs automatically (only reports readiness)
- Create new PRs
- Close or archive PRs

## Execution Steps

### Step 1: Fix CI Failures

Execute `/fix-pr-ci all`. Wait for completion.

### Step 2: Resolve Review Threads

Execute `/resolve-pr-review-thread all`. Wait for completion.

### Step 3: Scan All Open PRs

Use `gh repo list` and `gh pr list` to enumerate all open PRs across repos.

### Step 4: Determine Merge-Readiness

**Ready to merge**: OPEN, MERGEABLE, all checks SUCCESS, no unresolved threads, approved.
**Blocked**: Failing any of the above.

### Step 5: Generate JSON Report

```json
{
  "ready_to_merge": [{"repo": "owner/repo", "pr": 123, "title": "...", "url": "..."}],
  "blocked": [{"repo": "...", "pr": 456, "title": "...", "reason": "CI failing", "url": "..."}]
}
```

### Step 6: Display Summary

Report: repos scanned, PRs ready, PRs blocked with reasons. Save JSON to `/tmp/ready-player-one-{TIMESTAMP}.json`.

## Blocking Reasons

CI failing, merge conflicts, unresolved comments, changes requested, no approval, draft.

## Error Handling

Log errors, continue scanning, report partial results.

**Remember**: Orchestrate, scan, report. Never merge automatically.
