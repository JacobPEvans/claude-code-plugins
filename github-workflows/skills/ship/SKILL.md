---
name: ship
description: >-
  Commit, push, create PR(s), and auto-finalize — full automation pipeline.
  Handles uncommitted changes and recently created PRs. Never merges.
allowed-tools: Bash(git:*), Bash(gh:*), Agent, Read, Grep, Glob, Skill
model: sonnet
---

# Ship

**Single command to commit, push, create PR(s), and auto-finalize everything.**
Orchestrates `/commit-push-pr` and `/finalize-pr` into one pipeline. Never merges.

## Step 1: Detect Scope

Identify all PRs that need finalization.

### 1.1 Check for Uncommitted Changes

```bash
git status --porcelain
```

**If changes exist** (staged or unstaged):

1. Dispatch a **sonnet subagent** to run `/commit-push-pr`
2. The subagent handles: branch creation, commit, push, and `gh pr create`
3. Capture the PR number from the subagent's output (look for `pull/NUMBER` pattern)
4. Add it to the PR list

**If no changes**: Skip to 1.2.

### 1.2 Scan for Recently Created/Mentioned PRs

Check conversation context for PR numbers that were recently created or mentioned.
Also check the current branch:

```bash
gh pr view --json number --jq '.number' 2>/dev/null
```

Add any found PRs to the list.

### 1.3 Deduplicate

Remove duplicate PR numbers from the combined list (Step 1.1 + Step 1.2).

**If list is empty**: Report "Nothing to ship — no uncommitted changes and no open PRs
on this branch." and stop.

## Step 2: Dispatch Finalization

For **each PR** in the deduplicated list, dispatch a separate **sonnet subagent**
running `/finalize-pr <PR_NUMBER>`.

**All agents run in parallel** — use the Agent tool with `run_in_background: true`
for all but the last, or dispatch all at once if the runtime supports it.

Each `/finalize-pr` agent independently handles:

- CodeQL violation resolution
- Review thread resolution (via `/resolve-pr-threads`)
- Merge conflict resolution
- CI failure fixes
- Code simplification (via `/simplify`)
- PR metadata updates

**Do NOT run `/resolve-pr-threads` separately** — `/finalize-pr` already invokes it
internally. Running both causes race conditions on GraphQL mutations and git pushes.

## Step 3: Aggregate Results

Wait for all `/finalize-pr` agents to complete. Collect their results and report:

```text
Ship Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✅  #42  Ready for review
  ✅  #43  Ready for review
  ⛔  #44  Blocked — [reason]

Ready to merge (2):
  /squash-merge-pr 42
  /squash-merge-pr 43

Blocked — needs human (1):
  #44 — [detailed reason]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Safety

- **NEVER merge** — only prepare PRs for human review
- **NEVER approve** — no auto-approval of PRs
- Each `/finalize-pr` agent enforces its own merge prohibition
- This command inherits all safety constraints from `/finalize-pr`

## Examples

```text
# Ship uncommitted changes (commit + PR + finalize)
/ship

# Ship when PR already exists on current branch
/ship

# Multi-PR: uncommitted changes create new PR, existing PR also finalized
/ship
```
