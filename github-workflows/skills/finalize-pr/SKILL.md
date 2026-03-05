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

**FULLY AUTOMATIC** - Finalizes PRs as author: monitor, fix, prepare for merge. Assumes PR already exists.
No manual intervention required. For reviewing others' PRs, use `/review-pr`.

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

## Phase 0: PR Discovery and Targeting

Parse the argument to determine mode, then discover and confirm the target set.

### 0.1 Parse Argument

| Argument | Mode | Target |
|---|---|---|
| _(none)_ | Current branch | Single PR on current branch |
| `42` (a number) | Single PR | PR #42 |
| `all` | Repo-wide | All open PRs in current repo |
| `org` | Org-wide | All open PRs across all repos in current org |

### 0.2 Discover PRs

**Single/current-branch mode**: Resolve to one PR number, then skip to Phase 1.

```bash
# If no argument — resolve from current branch
gh pr view --json number --jq '.number'
```

**Repo-wide (`all`) mode**:

```bash
gh pr list --state open --json number,title,author,headRefName
```

**Org-wide (`org`) mode**:

```bash
OWNER=$(gh repo view --json owner --jq '.owner.login')
gh repo list "$OWNER" --limit 100 --json name --jq '.[].name' | \
  xargs -I{} gh pr list --repo "$OWNER/{}" --state open \
    --json number,title,author,headRefName,repository 2>/dev/null
```

Cap at 50 PRs. If more exist, warn the user and process only the first 50.

### 0.3 Tag Bot PRs

For each discovered PR, check if `author.login` matches bot patterns
(`*[bot]`, `app/*`, `dependabot`, `release-please`, `github-actions`, `claude`).
Tag these as `[bot]` in the discovery list for reporting purposes only — they are
processed identically to human-authored PRs.

### 0.4 Confirm Batch (Multi-PR Only)

For `all` and `org` modes, display the discovery list before proceeding:

```text
Found N open PRs:
  #42  feat: add user auth          (alice)
  #43  chore: bump dependencies     [bot] (dependabot)
  #58  fix: resolve edge case       [bot] (claude)

Proceeding to finalize all N PRs sequentially.
```

Check for a clean working tree before multi-PR modes:

```bash
git status --porcelain
```

If the working tree is dirty, report and ask the user to commit or stash before proceeding.

Record the current branch for restoration after each iteration:

```bash
ORIGINAL_BRANCH=$(git branch --show-current)
```

## Phase 1: Resolution Loop (AUTOMATIC — PARALLEL)

**Execution strategy**: CI checks take 10+ minutes. Start monitoring them in
the background FIRST, then fix all other issues in parallel while CI runs.
Never block on CI when other work is available.

_For multi-PR modes, this phase and Phases 2-4 execute once per PR in sequence.
At the start of each iteration, check out the PR branch:_

```bash
# Multi-PR only — not needed for single/current-branch mode
gh pr checkout <number>
```

### 1.1 Start CI Monitoring (BACKGROUND)

Launch CI monitoring in a background Task agent (`run_in_background: true` on
the Task tool). The agent runs this blocking command in its own context:

```bash
gh pr checks <PR> --watch
```

Do NOT wait for the Task to complete — proceed to 1.2 immediately. Check the
background task's output after completing other fixes in 1.2.

### 1.2 Parallel Fixes

Run these checks simultaneously. Launch independent fixes in parallel via
Task agents when they touch different files. Invoke `superpowers:dispatching-parallel-agents` for dispatch patterns.

#### CodeQL Violations

```bash
OWNER=${OWNER:-$(gh repo view --json owner --jq '.owner.login')}
REPO=${REPO:-$(gh repo view --json name --jq '.name')}

gh api repos/${OWNER}/${REPO}/code-scanning/alerts --paginate \
  --jq '[.[] | select(.state == "open")] | length'
```

**If violations found**: Invoke `/resolve-codeql fix`, then /simplify,
validate locally.

#### Review Threads

Invoke `/resolve-pr-threads`. It exits cleanly when no threads exist.
After completion, invoke /simplify and validate locally.

#### Merge Conflicts

```bash
gh pr view <PR> --json mergeable
```

**If conflicts**: Fetch main, attempt merge, report unresolvable conflicts for
user. After resolution, invoke /simplify and validate locally.

### 1.3 CI Failure Fixes

Check background CI results from 1.1:

- **All passing**: Proceed to Phase 2
- **Failures**: Get logs via `gh run view <RUN_ID> --log-failed`, fix locally,
  invoke /simplify, validate, commit and push. Restart background CI
  monitoring and loop back to 1.2 if new issues emerged.

### 1.4 Health Check

Verify final PR status after all fixes:

```bash
gh pr view <PR> --json state,mergeable,statusCheckRollup
```

If fixes introduced new issues, loop back to 1.2.

## Phase 2: Pre-Handoff Verification

Verify ALL conditions automatically and proceed directly:

1. ✅ **CodeQL clean**: No open alerts in repository
2. ✅ **All threads resolved**: All review conversations addressed
3. ✅ **No merge conflicts**: PR is mergeable
4. ✅ **Code simplified**: All changes reviewed by /simplify
5. ✅ **All checks pass**: `gh pr checks <PR>` all green
6. ✅ **Local validation**: Project linters pass

**Only if ALL six pass**: Proceed to Phase 3 to update PR metadata.

**Multi-PR handling**: If a PR needs human intervention (unresolvable conflict,
unrecoverable CI failure, etc.), log it with reason and continue to the next PR.
Do not stop the batch for one blocked PR.

## Phase 3: Update PR Metadata

Delegate to a **haiku subagent** to keep full diff out of main context.
Sub-steps 3.1 and 3.2 can run in parallel within the agent.

### 3.1 Update PR Title and Description

1. Run compact summary commands:

   ```bash
   git fetch origin main
   git log --oneline origin/main..HEAD
   git diff --stat origin/main...HEAD
   ```

2. Read current PR title and body:

   ```bash
   gh pr view <PR> --json title,body
   ```

3. Generate updated title (conventional commit format, <70 chars) and
   description with sections: **Summary**, **Changes**, **Test Plan**.

### 3.2 Link Related Issues and PRs

1. Extract keywords from branch name and commit messages.
2. Search for related items:

   ```bash
   gh issue list --search "<keywords>" --json number,title --limit 5
   gh pr list --search "<keywords>" --json number,title --limit 5
   ```

3. Add `Closes #X` (directly related issues) or `Related: #X` (adjacent PRs)
   to description. Only link clearly related items — no guessing.

### 3.3 Apply Updates

After 3.1 and 3.2 complete, apply using a multiline-safe pattern:

```bash
cat <<'EOF' > /tmp/pr-body.md
...
EOF

gh pr edit <PR> --title "..." --body-file /tmp/pr-body.md
```

Proceed to Phase 4.

## Phase 4: Record Result

**Single/current-branch mode**: Report ready status and wait for user:

```text
✅ PR #{NUMBER} ready for final review!

All checks passed and PR metadata is up to date.
To merge, invoke one of:
  /squash-merge-pr    # Squash all commits into one
  /rebase-pr          # Rebase commits onto main (preserves history)
```

**Multi-PR mode**: Record the per-PR result (ready / blocked / needs-human).
After recording, restore the original branch and continue to the next PR:

```bash
git switch "$ORIGINAL_BRANCH"
```

Do NOT emit a ready report here in multi-PR mode — that happens in Phase 5.

## Phase 5: Aggregate Report (Multi-PR Only)

After processing all PRs, emit a summary:

```text
PR Finalization Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✅  #42  feat: add user auth          (alice)
  ✅  #58  fix: resolve edge case       [bot] (claude)
  ⛔  #43  chore: bump dependencies     [bot] (dependabot)  — unresolvable conflict

Ready to merge (2):
  gh pr merge 42 --squash
  gh pr merge 58 --squash

Blocked — needs human (1):
  #43  chore: bump dependencies  — unresolvable conflict in package-lock.json
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Wait for explicit user merge commands.

## Workflow

```text
Single PR:
/init-worktree → [implement] → gh pr create → /finalize-pr [number]
                                                      ↓
                              Phase 0: Resolve PR number
                              Phase 1: Resolution Loop (automatic fixes)
                              Phase 2: Pre-Handoff Verification
                              Phase 3: Update PR Metadata
                              Phase 4: Report ready (wait for user)
                                                      ↓
                              User invokes: /squash-merge-pr or /rebase-pr

Repo-wide:
/finalize-pr all
  ↓
Phase 0: Discover all open PRs (including bots), confirm batch
Phase 1-4: Loop over each PR sequentially
Phase 5: Aggregate report with merge commands for ready PRs

Org-wide:
/finalize-pr org
  ↓
Phase 0: Derive org owner, enumerate repos, collect all open PRs
Phase 1-4: Loop over each PR sequentially
Phase 5: Aggregate report with merge commands for ready PRs
```
