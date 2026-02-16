---
name: finalize-pr
description: Automatically finalize pull requests for merge - no human intervention needed until ready
---

# Finalize PR

**FULLY AUTOMATIC** - Finalizes YOUR PRs as author: create, monitor, fix, prepare for merge. No manual intervention required. For reviewing others' PRs, use `/review-pr`.

## Scope

**SINGLE PR** - One PR at a time, from argument or current branch.

## Prerequisites

**Required plugins:**
- **code-simplifier** (official Anthropic plugin) - Automatically simplifies code after changes

Install code-simplifier:
```bash
# The code-simplifier is an official Anthropic plugin
# It is invoked via Task tool with subagent_type: code-simplifier
```

If code-simplifier is not available, the skill will continue but skip simplification steps (fail-open philosophy).

## Critical Rules

1. **Wait for user approval to merge** - Report ready status, then pause for user merge command
2. **Verify all checks pass** - Report ready only when ALL conditions meet requirements
3. **Resolve all conversations** - Automatically invoke `/resolve-pr-threads` for review threads
4. **Fix all CodeQL violations** - Check repository and automatically fix using `/resolve-codeql`
5. **Simplify all code changes** - Invoke code-simplifier after ANY code modifications
6. **Validate locally before pushing** - Run project linters and tests
7. **Create PR immediately** - Push and open PR as soon as work completes
8. **Check CI last** - Monitor GitHub Actions after other checks (longest running)
9. **Review PR metadata** - Update title and description to match final diff before merge
10. **Take direct action** - Identify issues and fix them automatically

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
2. **ALWAYS invoke code-simplifier agent** to simplify any fixes
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

### 2.7 Code Simplification (ALWAYS - After Any Changes)

**CRITICAL**: After ANY code modifications in phases 2.1-2.6 (including fixes triggered by 2.6 failures that loop back through 2.5), invoke code-simplifier:

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

Verify ALL conditions automatically and proceed directly:

1. ✅ **CodeQL clean**: No open alerts in repository
2. ✅ **All threads resolved**: All review conversations addressed
3. ✅ **No merge conflicts**: PR is mergeable
4. ✅ **Code simplified**: All changes reviewed by code-simplifier
5. ✅ **All checks pass**: `gh pr checks <PR>` all green
6. ✅ **Local validation**: Project linters pass

**Only if ALL six pass**: Proceed to Phase 4 for final PR metadata review.

## Phase 4: PR Metadata Review and Merge Strategy

After all checks pass, review and update PR metadata to accurately reflect final changes.

### 4.1 Generate Full Diff

Compare PR branch to origin/main (ignore individual commit history):

```bash
git fetch origin main
git diff origin/main...HEAD
```

Analyze the complete changeset (not back-and-forth commits).

### 4.2 Update PR Title

Review current PR title:

```bash
gh pr view <PR> --json title --jq '.title'
```

Generate accurate title based on full diff:
- Use conventional commit format: `<type>: <description>`
- Types: feat, fix, refactor, docs, test, chore
- Keep concise (under 70 characters)
- Reflect the actual final changes

Update if needed:

```bash
gh pr edit <PR> --title "new title"
```

### 4.3 Update PR Description

Review current PR body:

```bash
gh pr view <PR> --json body --jq '.body'
```

Generate comprehensive description based on full diff:
- **Summary** section with 2-5 bullet points of key changes
- **Changes** section listing all major modifications
- **Breaking Changes** section (if applicable)
- **Test Plan** section with validation steps

Update if needed:

```bash
gh pr edit <PR> --body "$(cat <<'EOF'
## Summary
- Key change 1
- Key change 2

## Changes
...
EOF
)"
```

### 4.4 Recommend Merge Strategy

Analyze the changeset and recommend:

**Recommend squash merge** when:
- Single logical change (even if multiple commits)
- Commits contain back-and-forth fixes
- Work-in-progress commit messages
- Experimental changes that were refined

Provide release-note-friendly commit message:

```
<type>: <concise description>

<2-3 line explanation of what changed and why>

Example:
feat: add dark mode support

Implements dark mode with automatic theme switching based on system
preferences. Includes color scheme updates for all components and
persistent user preference storage.
```

**Recommend `/rebase-pr`** when:
- Multiple distinct logical changes
- Clean, meaningful commit messages
- Each commit is independently valuable
- Preserving commit history adds context

## Phase 5: Merge (User Action Only)

Report final status with merge recommendation:

```
PR #XX is ready to merge!

Recommendation: Squash merge
Suggested commit message:
---
feat: add authentication system

Implements JWT-based authentication with refresh tokens,
secure password hashing, and role-based access control.
---

Command: gh pr merge <PR> --squash
```

The merge command requires explicit user execution. Pause and wait after reporting recommendation.

## Automation Philosophy

**Take direct action** - This skill operates autonomously:
- Fix issues immediately when detected
- Resolve review threads automatically using `/resolve-pr-threads`
- Check and fix CodeQL violations using `/resolve-codeql`
- Simplify code after every change using code-simplifier
- Continue to next check after completing each step

**Report to user** in these specific cases:
1. PR is fully ready to merge (all checks pass) - pause for merge approval
2. User intervention required (e.g., merge conflicts needing manual resolution)
3. Unrecoverable error occurs requiring human decision

## Workflow

```
/init-worktree → /resolve-issues → /finalize-pr → user merges
                                          ↓
                    Phase 1: Create PR
                    Phase 2: Resolution Loop (automatic fixes)
                    Phase 3: Pre-Handoff Verification
                    Phase 4: PR Metadata Review (update title/description)
                    Phase 5: Merge Recommendation → user executes
```
