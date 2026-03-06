---
name: finalize-pr
description: >-
  Automatically finalize pull requests for merge by resolving CodeQL violations,
  review threads, merge conflicts, and CI failures. Handles single PR (current
  branch or by number), all open PRs in the repo, or all open PRs across the org.
  Includes bot-authored PRs in all modes.
argument-hint: "[PR_NUMBER | all | org]"
---

<!-- cspell:words worktree oneline -->

# Finalize PR

**FULLY AUTOMATIC** - Fully automates PR finalization: monitor, fix, prepare for merge. Assumes PR already exists.
No manual intervention required. For manual review-focused workflows, use `/review-pr`.

## Critical Rules

1. **Wait for user approval to merge** - Report ready status, then pause for user merge command
2. **Verify all checks pass** - Report ready only when ALL conditions meet requirements
3. **Resolve all conversations** - Automatically invoke `/resolve-pr-threads` for review threads
4. **Fix all CodeQL violations** - Check repository and automatically fix using `/resolve-codeql`
5. **Simplify all code changes** - Invoke /simplify after ANY code modifications
6. **Validate locally before pushing** - Run project linters and tests
7. **Monitor CI early, block last** - Start CI monitoring in background immediately, but fix other issues while it runs
8. **Update PR metadata automatically** - Before reporting ready, update title, description, and linked issues via haiku subagent
9. **Take direct action** - Identify issues and fix them automatically (except merge decisions)
10. **Include bot PRs** - Never filter by author. All modes include dependabot, release-please, claude, github-actions, etc.
11. **Never cross org boundaries** - Org mode derives owner from current repo only

## Phase 1: PR Discovery and Targeting

Parse the argument to determine mode, then discover and confirm the target set.
Steps 1.1 through 1.4 run sequentially.

### 1.1 Parse Argument

| Argument | Mode | Target |
|---|---|---|
| _(none)_ | Current branch | Single PR on current branch |
| `42` (a number) | Single PR | PR #42 |
| `all` | Repo-wide | All open PRs in current repo |
| `org` | Org-wide | All open PRs across all repos in current org |

### 1.2 Discover PRs

**Single/current-branch mode**: Resolve the PR number from the current branch, then skip to Phase 2.

**Repo-wide (`all`) mode**: List all open PRs (limit 50) with number, title, author, and headRefName.

**Org-wide (`org`) mode**: Enumerate all repos in the org, then for each repo list open PRs (limit 50
per repo) including the `repository` field (needed for checkout and merge commands). Merge all results
sorted by PR number, capped at 50 total. Emit a warning and continue if any repo cannot be listed.

### 1.3 Tag Bot PRs

For each discovered PR, check if `author.login` ends with `[bot]`
(e.g., `dependabot[bot]`, `github-actions[bot]`, `claude[bot]`).
Tag these as `[bot]` in the discovery list for reporting purposes only — they are
processed identically to human-authored PRs.

### 1.4 Confirm Batch (Multi-PR Only)

For `all` and `org` modes, display the discovery list before proceeding:

```text
Found N open PRs:
  #42  feat: add user auth          (alice)
  #43  chore: bump dependencies     [bot] (dependabot[bot])
  #58  fix: resolve edge case       [bot] (claude[bot])

Proceeding to finalize all N PRs sequentially.
```

Verify the working tree is clean before proceeding. If dirty, report and ask the user to commit or
stash. Note the current branch for restoration after each PR iteration.

## Phase 2: Resolution Loop (AUTOMATIC)

**Execution strategy**: CI checks take 10+ minutes. Start monitoring them in
the background FIRST, then fix all other issues in parallel while CI runs.
Never block on CI when other work is available.

_For multi-PR modes, Phases 2-5 execute once per PR in sequence. Check out each PR branch at the
start of each iteration. For org-wide mode, use `repository.nameWithOwner` from Phase 1 as the
`--repo` argument when checking out._

Steps 2.1 and 2.2 start concurrently (2.1 is non-blocking). Steps 2.3 and 2.4 run sequentially after 2.2.

### 2.1 Start CI Monitoring (BACKGROUND)

Launch CI monitoring in a background Task agent (`run_in_background: true` on the Task tool).
Monitor CI checks using `--watch` so the agent blocks until all complete.

Do NOT wait for the agent to finish — proceed to 2.2 immediately.

### 2.2 Parallel Fixes

Run these checks simultaneously. Launch independent fixes in parallel via
Task agents when they touch different files. Invoke `superpowers:dispatching-parallel-agents` for dispatch patterns.

#### CodeQL Violations

Check for open code-scanning alerts:

```bash
gh api repos/${OWNER}/${REPO}/code-scanning/alerts --paginate \
  --jq '[.[] | select(.state == "open")] | length'
```

**If violations found**: Invoke `/resolve-codeql fix`, then /simplify, validate locally.

#### Review Threads

Invoke `/resolve-pr-threads`. It exits cleanly when no threads exist.
After completion, invoke /simplify and validate locally.

#### Merge Conflicts

Check if the PR is mergeable. **If conflicts**: Fetch main, attempt merge, report unresolvable
conflicts for user. After resolution, invoke /simplify and validate locally.

### 2.3 CI Failure Fixes

Check background CI results from 2.1:

- **All passing**: Proceed to Phase 3
- **Failures**: Fetch failed run logs, fix locally, invoke /simplify, validate, commit and push.
  Restart background CI monitoring and loop back to 2.2 if new issues emerged.

### 2.4 Health Check

Verify final PR state, mergeability, and check status. If fixes introduced new issues, loop back to 2.2.

## Phase 3: Pre-Handoff Verification

Verify ALL conditions automatically and proceed directly:

1. ✅ **CodeQL clean**: No open alerts in repository
2. ✅ **All threads resolved**: All review conversations addressed
3. ✅ **No merge conflicts**: PR is mergeable
4. ✅ **Code simplified**: All changes reviewed by /simplify
5. ✅ **All checks pass**: `gh pr checks <PR>` all green
6. ✅ **Local validation**: Project linters pass

**Only if ALL six pass**: Proceed to Phase 4 to update PR metadata.

**Multi-PR handling**: If a PR needs human intervention (unresolvable conflict,
unrecoverable CI failure, etc.), log it with reason and continue to the next PR.
Do not stop the batch for one blocked PR.

## Phase 4: Update PR Metadata

Delegate to a **haiku subagent** to keep full diff out of main context.
Steps 4.1 and 4.2 can run in parallel within the agent. Step 4.3 runs after both.

### 4.1 Update PR Title and Description

1. Summarize branch history and diff stats against main; read current PR title and body.
2. Generate updated title (conventional commit format, <70 chars) and description with sections:
   **Summary**, **Changes**, **Test Plan**.

### 4.2 Link Related Issues and PRs

1. Extract keywords from branch name and commit messages.
2. Search GitHub issues and PRs for related items (limit 5 each).
3. Add `Closes #X` (directly related issues) or `Related: #X` (adjacent PRs) — no guessing.

### 4.3 Apply Updates

After 4.1 and 4.2 complete, write the body to a temp file and apply with `gh pr edit --body-file`
(safer than inline for multiline content).

Proceed to Phase 5.

## Phase 5: Record Result

**Single/current-branch mode**: Report ready status and wait for user:

```text
✅ PR #{NUMBER} ready for final review!

All checks passed and PR metadata is up to date.
To merge, invoke one of:
  /squash-merge-pr    # Squash all commits into one
  /rebase-pr          # Rebase commits onto main (preserves history)
```

**Multi-PR mode**: Record the per-PR result (ready / blocked / needs-human). Restore the original
branch and continue to the next PR. Do NOT emit a ready report — that happens in Phase 6.

## Phase 6: Aggregate Report (Multi-PR Only)

After processing all PRs, emit a summary. For org-wide mode, merge commands must include `--repo`
since PR numbers are scoped per-repository; use `repository.nameWithOwner` from Phase 1 discovery.

```text
PR Finalization Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✅  #42  feat: add user auth          (alice)         [owner/repo]
  ✅  #58  fix: resolve edge case       [bot] (claude[bot])  [owner/repo]
  ⛔  #43  chore: bump dependencies     [bot] (dependabot[bot])  [owner/repo]  — unresolvable conflict

Ready to merge (2):
  gh pr merge 42 --squash --repo owner/repo
  gh pr merge 58 --squash --repo owner/repo

Blocked — needs human (1):
  #43  chore: bump dependencies  — unresolvable conflict in package-lock.json
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

For repo-wide (`all`) mode, `--repo` may be omitted since all PRs share the current repo.

Wait for explicit user merge commands.

## Workflow

Use this skill ONLY after a PR already exists. To create a PR first, use `gh pr create`.

```text
Single PR (PR already created):
/finalize-pr [number]
  ↓
Phase 1: Resolve PR number
Phase 2: Resolution Loop (automatic fixes)
Phase 3: Pre-Handoff Verification
Phase 4: Update PR Metadata
Phase 5: Report ready (wait for user)
  ↓
User invokes: /squash-merge-pr or /rebase-pr

Repo-wide:
/finalize-pr all
  ↓
Phase 1: Discover all open PRs (including bots), confirm batch
Phases 2-5: Loop over each PR sequentially
Phase 6: Aggregate report with merge commands for ready PRs

Org-wide:
/finalize-pr org
  ↓
Phase 1: Derive org owner, enumerate repos, collect and merge all open PRs
Phases 2-5: Loop over each PR sequentially
Phase 6: Aggregate report with --repo-qualified merge commands for ready PRs
```
