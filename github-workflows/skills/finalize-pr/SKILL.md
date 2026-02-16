---
name: finalize-pr
description: Automatically finalize pull requests for merge - no human intervention needed until ready
---

# Finalize PR

**FULLY AUTOMATIC** - Finalizes YOUR PRs as author: create, monitor, fix, prepare for merge. No manual intervention required. For reviewing others' PRs, use `/review-pr`.

## Scope

**SINGLE PR** - One PR at a time, from argument or current branch.

## Critical Rules

1. **NEVER auto-merge** - Wait for explicit user approval to merge
2. **ALL checks must pass** - Never report ready with failures
3. **ALL conversations RESOLVED** - Automatically resolve using `/resolve-pr-threads`
4. **ALL CodeQL violations fixed** - Check repo and fix automatically
5. **ALWAYS simplify code** - Invoke code-simplifier after ANY code changes
6. **Run validation locally** before pushing
7. **Create PR immediately** when work complete - kicks off reviews
8. **Watch CI last** - GitHub Actions checked last (longest running)
9. **AUTOMATIC OPERATION** - Don't ask what to do, just do it

## Phase 1: Create PR

1. Run local validation (`markdownlint-cli2 .`, project linters)
2. Verify clean: `git status`
3. Push: `git push -u origin $(git branch --show-current)`
4. Create PR: `gh pr create --title "<type>: <description>" --body "..."`
5. Begin Resolution Loop immediately (don't wait for user input)

## Phase 2: Resolution Loop (AUTOMATIC)

### 2.1 CodeQL Check (FIRST - Local Repo)

Check for CodeQL violations in the repository itself (not just GitHub Actions):

```bash
gh api repos/{OWNER}/{REPO}/code-scanning/alerts \
  --jq '.[] | select(.state == "open" and .number > 0) | .number' | wc -l
```

**If violations found**:
1. Automatically invoke `/resolve-codeql fix` and wait for completion
2. **ALWAYS invoke code-simplifier agent** to simplify any fixes
3. Validate locally before committing

### 2.2 Review Threads (SECOND)

Check for unresolved review comments:

```bash
gh pr view <PR> --json reviews,reviewThreads
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
4. After user resolves, commit and push automatically

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

### 2.7 Code Simplification (ALWAYS - After Any Changes)

**CRITICAL**: After ANY code modifications in phases 2.1-2.5, invoke code-simplifier:

```text
Task tool with subagent_type: code-simplifier
Prompt: "Simplify all code changes made during PR finalization.
Focus on recently modified files. Remove unnecessary complexity
while preserving all functionality."
```

Why this matters:
- AI agents tend to over-engineer solutions
- Fixes often introduce more code than necessary
- Simpler code = easier to maintain and review
- Reduces future technical debt

**When to invoke**:
- After CodeQL fixes
- After review thread resolution
- After failed check fixes
- After merge conflict resolution
- Before final validation

## Phase 3: Pre-Handoff Verification

Verify ALL conditions automatically (no user prompts):

1. ✅ **CodeQL clean**: No open alerts in repository
2. ✅ **All threads resolved**: All review conversations addressed
3. ✅ **No merge conflicts**: PR is mergeable
4. ✅ **Code simplified**: All changes reviewed by code-simplifier
5. ✅ **All checks pass**: `gh pr checks <PR>` all green
6. ✅ **Local validation**: Project linters pass

**Only if ALL six pass**: Report "PR #XX is fully ready to merge. All checks passed."

## Phase 4: Merge (User Action Only)

**NEVER auto-merge**. Report ready status and wait for user to execute:
- `gh pr merge <PR> --squash` (for small changes, single logical commit)
- `gh pr merge <PR> --rebase` (for larger features, multiple meaningful commits)

## Automation Philosophy

**DO NOT ASK** - This skill knows what to do:
- Don't ask "should I fix this?" - fix it
- Don't ask "should I resolve threads?" - resolve them
- Don't ask "should I check CodeQL?" - check it
- Don't ask "should I simplify code?" - simplify it (ALWAYS)
- Don't report status and wait - take action

**ONLY REPORT** when:
1. PR is fully ready to merge (all checks pass)
2. User intervention required (e.g., merge conflicts needing manual resolution)
3. Unrecoverable error occurs

## Workflow

`/init-worktree` → `/resolve-issues` → `/finalize-pr` → user merges
