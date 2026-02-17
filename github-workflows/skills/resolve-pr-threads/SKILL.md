---
name: resolve-pr-threads
description: >-
  Orchestrates resolution of GitHub PR review threads by grouping related
  comments, dispatching sub-agents that invoke superpowers:receiving-code-review,
  and resolving threads via GraphQL. Use when you need to batch-process
  review feedback to unblock a PR merge.
argument-hint: "[PR_NUMBER|all]"
allowed-tools: Read, Edit, Write, Grep, Glob, Bash(gh:*), Bash(git:*), Task
---

<!-- cspell:words PRRT oneline databaseId -->

# Resolve PR Review Threads (Orchestrator)

Orchestrates resolution of all unresolved PR review comments by grouping
related threads, dispatching sub-agents to implement fixes or provide
explanations, then resolving threads via GitHub's GraphQL API.

## Usage

```text
/resolve-pr-threads              # Current branch PR
/resolve-pr-threads 142          # Specific PR
/resolve-pr-threads all          # All open PRs with unresolved threads (parallel)
```

## CRITICAL: GraphQL Query Format Requirements

**ALL GraphQL queries MUST use single-line format with `--raw-field`.**

**NEVER use multi-line GraphQL queries.** Multi-line queries cause:

- Shell encoding issues with newlines
- Variable type coercion errors (e.g., "Variable $prNumber of type Int! was provided invalid value")
- Parsing failures in Claude Code
- Inconsistent behavior across invocations

**If you see or are tempted to write a multi-line GraphQL query, STOP. It is WRONG.**

<!-- markdownlint-disable-next-line MD013 -->
**Use direct string substitution for `{placeholder}` values — never GraphQL `$variable` syntax.** The `--raw-field` flag sends queries as-is without variable processing. Always substitute values directly into the query string before execution.

**Context inference**: When no arguments provided, automatically infer owner/repo/PR from current git context:

```bash
# Smart inference - uses current context when available
OWNER=${OWNER:-$(gh repo view --json owner --jq -r '.owner.login' 2>/dev/null)}
REPO=${REPO:-$(gh repo view --json name --jq -r '.name' 2>/dev/null)}
NUMBER=${NUMBER:-$(gh pr view --json number --jq -r '.number' 2>/dev/null)}
```

All GraphQL patterns are documented in [graphql-queries.md](graphql-queries.md) in correct single-line format.

## Determine PR Context

Current PR info from branch context:

```text
PR number: !`gh pr view --json number --jq .number 2>/dev/null || echo "none"`
Repo (owner/name): !`gh repo view --json nameWithOwner --jq .nameWithOwner 2>/dev/null || echo "unknown"`
OWNER: !`gh repo view --json owner --jq .owner.login 2>/dev/null || echo "unknown"`
REPO: !`gh repo view --json name --jq .name 2>/dev/null || echo "unknown"`
Branch: !`git branch --show-current 2>/dev/null || echo "detached"`
```

## Workflow

### Step 1: Fetch Unresolved Threads

Use the **Fetch Unresolved Threads** query from [graphql-queries.md](graphql-queries.md).

Filter to threads where `isResolved == false`. Extract from each:

- `id` (`PRRT_*` node ID) - needed for resolution mutation
- `path` - file being reviewed
- `line`/`startLine` - location in file
- `comments.nodes[].id` - comment node ID
- `comments.nodes[].databaseId` - REST API ID for replies
- `comments.nodes[].body` - comment text
- `comments.nodes[].author.login` - who commented

### Step 2: Group Related Comments

Analyze threads and group by proximity:

- **Same file + within 30 lines** → group together (max 5 threads per group)
- **Different file or >30 lines apart** → singleton groups
- **Output numbered group list** before dispatching

Example:

```text
Group 1: src/auth.ts (3 threads at lines 45, 52, 58)
Group 2: src/api.ts (1 thread at line 120)
Group 3: README.md (2 threads at lines 15, 18)
```

### Step 3: Dispatch Sub-Agents

For each group, launch a `general-purpose` sub-agent using the Task tool.

**Sub-agent prompt template:**

```text
You are resolving PR review threads for PR #{number} in {owner}/{repo}.

CRITICAL — Step 1 is mandatory. Do NOT skip it. Do NOT start implementing
fixes or replying to threads until Step 1 is complete.

Step 1: FIRST — Invoke the `superpowers:receiving-code-review` skill via the
        Skill tool. This skill governs how you evaluate and respond to ALL
        review feedback. Read and follow its full pattern.

Step 2: THEN — Apply the receiving-code-review pattern to each thread below.
        Read the code at the referenced location, evaluate the reviewer's
        feedback through the lens of that skill, and decide: implement the
        fix, push back with rationale, or flag as needs-human.

Step 3: ONLY AFTER Steps 1-2 — Reply to each thread and commit changes.

Review threads to address:
{for each thread in group}
- Thread ID: {PRRT_xxx}
- File: {path}:{line}
- Reviewer: {author}
- Comment: {body}
- Database ID: {databaseId}
{end for}

Reply to threads using:
gh api repos/{owner}/{repo}/pulls/{number}/comments/{databaseId}/replies -f body="..."

For REST API details: read rest-api-patterns.md in the resolve-pr-threads skill directory.

Output ONE line per thread:
PRRT_xxx: handled [commit:abc1234]
PRRT_xxx: needs-human [reason]

Commit changes but DO NOT push.
```

**Launch groups in parallel** - use a single message with multiple Task calls.

Sub-agents commit their own changes but do NOT push.

### Step 4: Resolve Threads

After all sub-agents complete:

1. Parse each sub-agent's output for `handled` vs `needs-human` status
2. For each `handled` thread, run the **Resolve Thread Mutation** from
   [graphql-queries.md](graphql-queries.md) using the `PRRT_*` node ID
3. For `needs-human` threads, skip resolution and flag for manual attention

### Step 5: Verify and Push

1. Run the **Verify Zero Unresolved** query from
   [graphql-queries.md](graphql-queries.md)
2. **Must return `0`**. If not, identify remaining threads and report
3. Push all commits: `git push`
4. Output summary report

## Batch Mode ("all")

When `$ARGUMENTS` is `all`:

1. List open PRs: `gh pr list --state open --json number,headRefName`
2. For each PR, check for unresolved threads via GraphQL
3. Skip PRs with zero unresolved threads
4. For each PR with unresolved threads, run this skill's standard workflow
5. Verify each PR independently before moving to the next

## Special Cases for Sub-Agents

Sub-agents handle these via `superpowers:receiving-code-review`, but these
GitHub-specific edge cases need explicit attention:

- **Already addressed**: Check `git log --oneline -- {path}` before re-implementing.
  Reply with commit ref if already fixed.
- **Multi-reviewer threads**: Read ALL comments chronologically. Follow consensus
  if 2+ reviewers agree; otherwise decide by project conventions.
- **Contradictory feedback**: Reply to both threads acknowledging the conflict.
  Propose a decision with technical rationale.
- **Outdated comments**: Check git history, explain what changed, provide new
  location if code moved.
- **Batch comments**: Address ALL items with numbered responses. Only mark
  `handled` after ALL items are addressed.

## Output Format

```text
PR #{number} - Thread Resolution Summary
Groups: {groupCount} ({threadCount} threads total)
Handled: {count} | Needs human: {count}
Resolved via GraphQL: {count}
Verification: {0 unresolved} / {total}
Status: COMPLETE | PARTIAL ({remaining} need attention)
```

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `Could not resolve to a node` | Invalid thread ID | Re-fetch threads, IDs may have changed |
| `Resource not accessible` | Permission issue | Check `gh auth status`, need repo write access |
| Verification shows >0 | Thread not resolved | Re-run mutation for remaining threads |
| Empty reviewThreads | No reviews yet | Nothing to resolve, exit cleanly |
| Exactly 100 threads returned | Pagination cap hit | Resolve visible threads first, then re-run |
| REST reply fails | See rest-api-patterns.md troubleshooting | Check databaseId format, permissions |
