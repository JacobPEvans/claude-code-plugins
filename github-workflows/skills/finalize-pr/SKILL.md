---
name: finalize-pr
description: >-
  Automatically finalize pull requests for merge by resolving CodeQL violations,
  review threads, merge conflicts, and CI failures. Use when a PR is ready for
  final checks, when you want to prepare a PR for merge, or after completing
  feature work on a branch. Handles single PR from argument or current branch.
argument-hint: "[PR_NUMBER]"
---

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
8. **Check CI last** - Monitor GitHub Actions after other checks (longest running)
9. **Report ready and pause** - Instruct user to invoke `/squash-merge-pr` when ready
10. **Take direct action** - Identify issues and fix them automatically (except merge decisions)

## Phase 1: Create PR

1. Run local validation (`markdownlint-cli2 .`, project linters)
2. Verify clean: `git status`
3. Push: `git push -u origin $(git branch --show-current)`
4. Create PR: `gh pr create --title "<type>: <description>" --body "..."`
5. Begin Resolution Loop immediately and proceed automatically

## Phase 2: Resolution Loop (AUTOMATIC)

### 2.1 CodeQL Check (FIRST - Local Repo)

Check for CodeQL violations in the repository itself (not just GitHub Actions):

```bash
# Infer OWNER and REPO from the current git context if not already set
OWNER=${OWNER:-$(gh repo view --json owner --jq '.owner.login')}
REPO=${REPO:-$(gh repo view --json name --jq '.name')}

gh api repos/${OWNER}/${REPO}/code-scanning/alerts \
  --jq '[.[] | select(.state == "open")] | length'
```

**If violations found**:
1. Automatically invoke `/resolve-codeql fix` and wait for completion
2. **ALWAYS invoke code-simplifier agent** to simplify any fixes (if code-simplifier is unavailable, continue with fail-open philosophy)
3. Validate locally before committing

### 2.2 Review Threads (SECOND)

Check for unresolved review comments:

```bash
gh pr view <PR> --json reviewThreads --jq '[.reviewThreads[] | select(.isResolved | not)] | length'
```

**If unresolved threads exist**:
1. Automatically invoke `/resolve-pr-threads` to batch-resolve all threads
2. **ALWAYS invoke code-simplifier agent** after implementing review feedback
3. Validate locally before committing

### 2.3 Merge Conflicts (THIRD)

Check mergeable status:

```bash
gh pr view <PR> --json mergeable
```

**If merge conflicts**: Report conflict details and files, then automatically:
1. Fetch latest main: `git fetch origin main`
2. Attempt merge: `git merge origin/main`
3. If conflicts exist, identify files and report for user resolution
4. After user resolves, **ALWAYS invoke code-simplifier agent** on updated files
5. Validate locally, then commit and push automatically

### 2.4 Health Check (CONTINUOUS)

Monitor PR status continuously:

```bash
gh pr view <PR> --json state,mergeable,statusCheckRollup
```

### 2.5 Fix Failed Checks (AUTOMATIC)

When checks fail:
1. Identify failure from logs: `gh run view <RUN_ID> --log-failed`
2. Fix locally (invoke appropriate agent/skill)
3. **ALWAYS invoke code-simplifier agent** to simplify the fix
4. Validate before pushing
5. Commit and push: `git add . && git commit -m "fix: <description>" && git push`
6. Loop back to Health Check

### 2.6 GitHub Actions (LAST - Longest Running)

Only after ALL other checks pass, monitor GitHub Actions:

```bash
gh pr checks <PR> --watch
```

Wait for all checks to complete. If any fail, go to 2.5.

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

```
✅ PR #{NUMBER} ready for final review!

All checks passed. To prepare for merge, invoke:
  /squash-merge-pr
```

Wait for explicit user invocation of `/squash-merge-pr`.

## Workflow

```
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
