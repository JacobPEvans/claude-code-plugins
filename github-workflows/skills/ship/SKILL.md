---
name: ship
description: >-
  Commit, push, create PR(s), and auto-finalize — full automation pipeline.
  Handles uncommitted changes and recently created PRs. Never merges.
allowed-tools: Bash(git *), Bash(gh *), Agent, Read, Grep, Glob, Skill
---

# Ship

**Single command to commit, push, create PR(s), and auto-finalize everything.**
Handles commit, push, PR creation, and `/finalize-pr` in one pipeline. Never merges.

## Step 1: Detect Scope

Identify all PRs that need finalization.

### 1.1 Check for Uncommitted Changes

```bash
git status --porcelain
```

**If changes exist** (staged or unstaged), execute inline:

1. Create branch if on main: `git checkout -b {type}/{description}` (derive from changes)
2. Stage changes: `git add <relevant files>` (no `-A` — be selective)
3. Commit with conventional commit message: `git commit -m "type: description"`
4. Push: `git push -u origin HEAD`
5. Create PR: `gh pr create --fill` (or with title/body derived from commit)
6. Capture PR number from output (look for `pull/NUMBER` pattern)
7. Add it to the PR list

> **Hook note**: After `gh pr create`, a pr-lifecycle hook may emit a system message
> directing you to invoke `/finalize-pr`. **Ignore it** — Step 2 handles finalization.

**If no changes**: Skip to 1.2.

### 1.2 Scan for Recently Created/Mentioned PRs

Check conversation context for PR numbers that were recently created or mentioned.
Also check the current branch:

```bash
gh pr view --json number --jq '.number' 2>/dev/null || true
```

Add any found PRs to the list.

### 1.3 Deduplicate

Remove duplicate PR numbers from the combined list (Step 1.1 + Step 1.2).

**If list is empty**: Report "Nothing to ship — no uncommitted changes and no open PRs
on this branch." and stop.

## Step 1.5: Build Context Brief

Before dispatching any finalization agents, construct a **context brief** that will
be included in every subagent prompt. This is critical — without it, subagents
resolving PR review threads will blindly follow reviewer suggestions instead of
making informed decisions about whether feedback is correct.

The context brief must include:

1. **What was built and why** — summarize the changes and their purpose from
   the conversation history (the user's original request, the problem being solved)
2. **Key decisions made** — any architectural choices, trade-offs, or deliberate
   patterns chosen during implementation (e.g., "chose X over Y because Z")
3. **Intentional patterns** — things that might look wrong but are correct
   (e.g., "the empty catch block is intentional because the caller handles errors")
4. **Scope boundaries** — what is explicitly out of scope for this change

Format as a concise block (aim for 10-20 lines):

```text
## Context for PR #{number}
**Purpose**: [1-2 sentence summary of what and why]
**Key decisions**:
- [decision 1 and rationale]
- [decision 2 and rationale]
**Intentional patterns**:
- [pattern that reviewers might question]
**Out of scope**: [what this PR deliberately does not address]
```

This brief is passed verbatim to each `/finalize-pr` subagent in Step 2.

## Step 2: Finalize PRs

### Single PR (1 PR in list)

Invoke `/finalize-pr {number}` directly via the Skill tool — no subagent needed.
The context brief from Step 1.5 is already in session context and will be available
when `/finalize-pr` invokes `/resolve-pr-threads`.

### Multiple PRs (2+ PRs in list)

Dispatch a separate subagent per PR. **All agents run in parallel** — dispatch all
Agent tool calls in a single response.

Subagent prompt:

```text
You are finalizing PR #{number} in {owner}/{repo}.

{context_brief from Step 1.5}

Invoke `/finalize-pr {number}`. When it invokes /resolve-pr-threads, use
the context brief above to evaluate review feedback — push back on suggestions
that contradict intentional decisions, accept genuine improvements, flag
ambiguous feedback as needs-human.

SAFETY: You are FORBIDDEN from merging, auto-merging, or approving merge of any PR.
```

### What `/finalize-pr` handles

- CodeQL violation resolution
- Review thread resolution (via `/resolve-pr-threads` → `superpowers:receiving-code-review`)
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
