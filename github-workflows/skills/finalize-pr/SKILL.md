---
name: finalize-pr
description: >-
  Automatically finalize pull requests for merge by resolving CodeQL violations,
  review threads, merge conflicts, and CI failures. Use when a PR is ready for
  final checks, when you want to prepare a PR for merge, or after completing
  feature work on a branch. Handles single PR from argument or current branch.
argument-hint: "[PR_NUMBER]"
---

<!-- cspell:words worktree -->

# Finalize PR

**FULLY AUTOMATIC** - Finalizes YOUR PRs as author: create, monitor, fix, prepare for merge. No manual intervention required. For reviewing others' PRs, use `/review-pr`.

## Critical Rules

1. **Wait for user approval to merge** - Report ready status, then pause for user merge command
2. **Verify all checks pass** - Report ready only when ALL conditions meet requirements
3. **Resolve all conversations** - Automatically invoke `/resolve-pr-threads` for review threads
4. **Fix all CodeQL violations** - Check repository and automatically fix using `/resolve-codeql`
5. **Simplify all code changes** - Invoke code-simplifier after ANY code modifications
6. **Validate locally before pushing** - Run project linters and tests
7. **Create PR immediately** - Push and open PR as soon as work completes
8. **Monitor CI early, block last** - Start CI monitoring in background immediately, but fix other issues while it runs
9. **Report ready and pause** - Instruct user to invoke `/squash-merge-pr` when ready
10. **Take direct action** - Identify issues and fix them automatically (except merge decisions)

## Phase 1: Create PR

1. Run local validation (`markdownlint-cli2 .`, project linters)
2. Verify clean: `git status`
3. Push: `git push -u origin $(git branch --show-current)`
4. Create PR: `gh pr create --title "<type>: <description>" --body "..."`
5. Begin Resolution Loop immediately and proceed automatically

## Phase 2: Resolution Loop (AUTOMATIC — PARALLEL)

**Execution strategy**: CI checks take 10+ minutes. Start monitoring them in
the background FIRST, then fix all other issues in parallel while CI runs.
Never block on CI when other work is available.

### 2.1 Start CI Monitoring (BACKGROUND)

Launch CI monitoring in a background Task agent (`run_in_background: true` on
the Task tool). The agent runs this blocking command in its own context:

```bash
gh pr checks <PR> --watch
```

Do NOT wait for the Task to complete — proceed to 2.2 immediately. Check the
background task's output after completing other fixes in 2.2.

### 2.2 Parallel Fixes

Run these checks simultaneously. Launch independent fixes in parallel via
Task agents when they touch different files.

#### CodeQL Violations

```bash
OWNER=${OWNER:-$(gh repo view --json owner --jq '.owner.login')}
REPO=${REPO:-$(gh repo view --json name --jq '.name')}

gh api repos/${OWNER}/${REPO}/code-scanning/alerts --paginate \
  --jq '[.[] | select(.state == "open")] | length'
```

**If violations found**: Invoke `/resolve-codeql fix`, then code-simplifier,
validate locally.

#### Review Threads

Invoke `/resolve-pr-threads` to check for and batch-resolve all unresolved
threads. This skill fetches threads via GraphQL (since `gh pr view --json`
does not support `reviewThreads`), groups related threads, dispatches
sub-agents that follow `superpowers:receiving-code-review`, and resolves via
GraphQL. It exits cleanly when no threads exist. After completion, invoke
code-simplifier and validate locally.

#### Merge Conflicts

```bash
gh pr view <PR> --json mergeable
```

**If conflicts**: Fetch main, attempt merge, report unresolvable conflicts for
user. After resolution, invoke code-simplifier and validate locally.

### 2.3 CI Failure Fixes

Check background CI results from 2.1:

- **All passing**: Proceed to Phase 3
- **Failures**: Get logs via `gh run view <RUN_ID> --log-failed`, fix locally,
  invoke code-simplifier, validate, commit and push. Restart background CI
  monitoring and loop back to 2.2 if new issues emerged.

### 2.4 Health Check

Verify final PR status after all fixes:

```bash
gh pr view <PR> --json state,mergeable,statusCheckRollup
```

If fixes introduced new issues, loop back to 2.2.

## Phase 3: Pre-Handoff Verification

Verify ALL conditions automatically and proceed directly:

1. ✅ **CodeQL clean**: No open alerts in repository
2. ✅ **All threads resolved**: All review conversations addressed
3. ✅ **No merge conflicts**: PR is mergeable
4. ✅ **Code simplified**: All changes reviewed by code-simplifier
5. ✅ **All checks pass**: `gh pr checks <PR>` all green
6. ✅ **Local validation**: Project linters pass

**Only if ALL six pass**: Proceed to Phase 4 to report ready status.

## Phase 4: Report Ready Status

After verifying all conditions pass, report:

```text
✅ PR #{NUMBER} ready for final review!

All checks passed. To prepare for merge, invoke:
  /squash-merge-pr
```

Wait for explicit user invocation of `/squash-merge-pr`.

## Workflow

```text
/init-worktree → /resolve-issues → /finalize-pr
                                          ↓
                    Phase 1: Create PR
                    Phase 2: Resolution Loop (automatic fixes)
                    Phase 3: Pre-Handoff Verification
                    Phase 4: Report ready (wait for user)
                                          ↓
                    User invokes: /squash-merge-pr
                                          ↓
                    User executes: gh pr merge
```
