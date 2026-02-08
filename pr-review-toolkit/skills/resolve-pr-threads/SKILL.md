---
name: resolve-pr-threads
description: >-
  Systematically resolve all unresolved GitHub PR review threads end-to-end:
  fetch threads via GraphQL, implement fixes or write explanations, reply to
  each comment, and mark threads resolved so the PR becomes mergeable.
  Use when you need to batch-process review feedback to unblock a PR merge.
argument-hint: "[PR_NUMBER|all]"
allowed-tools: Read, Edit, Write, Grep, Glob, Bash(gh:*), Bash(git:*)
---

<!-- cspell:words PRRT oneline -->

# Resolve PR Review Threads

Systematically addresses all unresolved PR review comments by implementing
requested changes or providing explanations, then resolves threads via
GitHub's GraphQL API so the PR becomes mergeable.

## Usage

```text
/resolve-pr-threads              # Current branch PR
/resolve-pr-threads 142          # Specific PR
/resolve-pr-threads all          # All open PRs with unresolved threads (parallel)
```

## Determine PR Context

Current PR info from branch context:

```text
PR number: !`gh pr view --json number --jq .number 2>/dev/null || echo "none"`
Repo (owner/name): !`gh repo view --json nameWithOwner --jq .nameWithOwner 2>/dev/null || echo "unknown"`
OWNER: !`gh repo view --json owner --jq .owner.login 2>/dev/null || echo "unknown"`
REPO: !`gh repo view --json name --jq .name 2>/dev/null || echo "unknown"`
Branch: !`git branch --show-current 2>/dev/null || echo "detached"`
```

## Core Principle: Reply AND Resolve Are Atomic

Every thread follows exactly one of two paths. Both end with resolution.

**Path A - Technical Fix**: Implement change -> Commit -> Reply with hash -> Resolve

**Path B - Explanation Only**: Draft explanation -> Reply with reasoning -> Resolve

Never reply without resolving. Never resolve without replying.

## Workflow

### Step 1: Fetch Unresolved Threads

Use the **Fetch Unresolved Threads** query from [graphql-queries.md](graphql-queries.md).

Filter to threads where `isResolved == false`. Extract from each:

- `id` (`PRRT_*` node ID) - needed for resolution mutation
- `path` - file being reviewed
- `line`/`startLine` - location in file
- `comments.nodes[].id` - comment node ID for threading replies
- `comments.nodes[].body` - comment text
- `comments.nodes[].author.login` - who commented

### Step 2: Classify and Prioritize

Process threads in priority order:

1. **Blocking** ("BLOCKING", "must fix", "required") - Must fix before merge
2. **Bugs/Security** (identifies a defect or vulnerability) - Critical correctness
3. **Suggestion with code** (contains ` ```suggestion ` block) - Apply directly
4. **Questions** (ends with `?`, "could you explain") - Answer clearly
5. **Suggestion without code** ("should", "consider", "recommend") - Evaluate merit
6. **Nitpick** ("nit:", "minor:") - Quick fix if easy

### Step 3: Read Code Context

For each comment, use the Read tool with offset/limit to see surrounding code:

```text
offset = max(0, line - 15)
limit = 30
Read(file_path="<path>", offset=<offset>, limit=<limit>)
```

Understand what the code does, why the reviewer raised the concern, and the
impact of potential changes before acting.

### Step 4: Check If Already Addressed

Before implementing a fix, check if a subsequent commit already addressed it:

```bash
git log --oneline -- {path}
```

If the concern was already fixed in a later commit, skip to Step 5 and reply
with: "Addressed in commit {hash}" with a brief explanation of the change.

### Step 5: Implement or Explain

**Decision tree:**

```text
Already addressed?         -> Reply with commit ref, skip to Step 6
Has suggestion block?      -> Apply exact code change
Is blocking?               -> Fix immediately
Is a question?
  Needs code change?       -> Make code clearer + explain
  Answer only?             -> Explain in reply
Has merit?
  Yes                      -> Implement fix
  No                       -> Reply with respectful disagreement
  Unsure                   -> Follow project conventions
```

For code changes: use Edit tool, follow project standards, commit with
descriptive message.

### Step 6: Reply to Each Thread

Reply within the specific review thread using the comment ID from Step 1.
This ensures the reply is threaded correctly, not posted as a standalone comment.

Use `printf` to safely handle multi-line content:

```bash
printf "**Re: %s's feedback on %s:%s**\n\n%s" \
  "{reviewer}" "{path}" "{line}" "{detailed response}" | \
gh api graphql \
  -f query='mutation($threadId: ID!, $body: String!) {
    addPullRequestReviewComment(input: {
      pullRequestReviewThreadId: $threadId,
      body: $body
    }) {
      comment { id url }
    }
  }' \
  -f threadId="{THREAD_ID}" \
  -F body=-
```

Where `{THREAD_ID}` is the thread's `PRRT_*` node ID from Step 1.

**Reply guidelines:**

- If fixed: Include commit hash and specific changes made
- If question: Give clear technical answer with rationale
- If disagreeing: Acknowledge the point, explain why not with reasoning
- NEVER tag AI assistants (@gemini-code-assist, @copilot, etc.) in replies
- NEVER tag bots - only tag human reviewers when needed

### Step 7: Resolve Each Thread

Immediately after replying, use the **Resolve Thread Mutation** from
[graphql-queries.md](graphql-queries.md) with the `PRRT_*` node ID from Step 1.

### Step 8: Verify Zero Unresolved

Use the **Verify Zero Unresolved** query from
[graphql-queries.md](graphql-queries.md).

**Must return `0`**. If not, identify and address remaining threads. Do not
report completion until verification passes.

### Step 9: Commit and Push

```bash
git add <changed-files>
git commit -m "fix: address PR review feedback

- <change 1>
- <change 2>

Co-Authored-By: Claude <noreply@anthropic.com>"
git push
```

## Batch Mode ("all")

When `$ARGUMENTS` is `all`:

1. List open PRs: `gh pr list --state open --json number,headRefName`
2. For each PR, check for unresolved threads via GraphQL
3. Skip PRs with zero unresolved threads
4. Process each PR using the Task tool with this skill's workflow
5. Verify each PR independently before moving to the next

## Special Cases

### Already-Addressed Comments

If a subsequent commit already fixed the reviewer's concern, reply with the
commit reference and resolve. Do NOT re-implement the same fix.

### Multi-Reviewer Threads

Read ALL comments chronologically. If 2+ reviewers agree, follow consensus.
If no consensus, decide based on project conventions and explain reasoning.

### Contradictory Feedback

Reply to BOTH threads acknowledging the conflict. Propose a decision with
technical rationale. Tag HUMAN reviewers only (never AI bots) for consensus.

### Outdated Comments

Check git history, reply explaining what happened to the code, provide new
location if moved, and resolve the outdated thread.

### Batch Comments

If one comment lists multiple issues, address ALL items with numbered
responses. Only resolve after ALL items are addressed.

## Output Format

```text
PR #{NUMBER} - Thread Resolution Summary

Threads addressed: {N}
Technical fixes: {count} (commits: {hashes})
Explanations: {count}

Verification: {0 unresolved} / {total threads}
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
