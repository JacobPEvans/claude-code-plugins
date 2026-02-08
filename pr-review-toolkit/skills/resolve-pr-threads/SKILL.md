---
name: resolve-pr-threads
description: >-
  Resolve GitHub PR review threads by implementing fixes or explanations,
  replying, and marking resolved via GraphQL. Use when a PR has unresolved
  review comments that block merge. No other plugin does this.
argument-hint: "[PR_NUMBER|all]"
allowed-tools: Read, Edit, Write, Grep, Glob, Bash(gh:*), Bash(git:*)
---

<!-- cspell:words PRRT -->

# Resolve PR Review Threads

Addresses unresolved PR review comments by implementing requested changes or providing
explanations, then resolves threads via GitHub's GraphQL API so the PR becomes mergeable.

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
Repo: !`gh repo view --json nameWithOwner --jq .nameWithOwner 2>/dev/null || echo "unknown"`
Branch: !`git branch --show-current 2>/dev/null || echo "detached"`
```

## Core Principle: Reply AND Resolve Are Atomic

Every thread follows exactly one of two paths. Both end with resolution.

**Path A - Technical Fix**: Read comment -> Implement change -> Commit -> Reply with commit hash -> Resolve thread

**Path B - Explanation Only**: Read comment -> Draft explanation -> Reply with reasoning -> Resolve thread

Never reply without resolving. Never resolve without replying.

## Workflow

### Step 1: Fetch Unresolved Threads

**CRITICAL**: `gh pr view --json` does NOT support `reviewThreads`. Use GraphQL:

```bash
gh api graphql --raw-field 'query=query {
  repository(owner: "{OWNER}", name: "{REPO}") {
    pullRequest(number: {NUMBER}) {
      reviewThreads(last: 100) {
        nodes {
          id isResolved path line startLine
          comments(last: 100) {
            nodes { id databaseId body author { login } createdAt }
          }
        }
      }
    }
  }
}'
```

Extract from each unresolved thread (`isResolved == false`):

- `id` (starts with `PRRT_`) - needed for resolution mutation
- `path` - file being reviewed
- `line`/`startLine` - location in file
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

Understand what the code does, why the reviewer raised the concern, and the impact
of potential changes before acting.

### Step 4: Implement or Explain

**Decision tree:**

```text
Has suggestion block?  -> Apply exact code change
Is blocking?           -> Fix immediately
Is a question?
  Needs code change?   -> Make code clearer + explain
  Answer only?         -> Explain in reply
Has merit?
  Yes                  -> Implement fix
  No                   -> Reply with respectful disagreement
  Unsure               -> Follow project conventions
```

For code changes: use Edit tool, follow project standards, commit with descriptive message.

### Step 5: Reply to Each Thread

Post a reply as a PR comment referencing the specific feedback:

```bash
gh pr comment {PR_NUMBER} --body "**Re: {reviewer}'s feedback on {path}:{line}**

{detailed response}"
```

**Reply guidelines:**

- If fixed: Include commit hash and specific changes made
- If question: Give clear technical answer with rationale
- If disagreeing: Acknowledge the point, explain why not implementing with reasoning
- NEVER tag AI assistants (@gemini-code-assist, @copilot, etc.) in replies
- NEVER tag bots - only tag human reviewers when needed

### Step 6: Resolve Each Thread

Immediately after replying, resolve via GraphQL mutation:

```bash
gh api graphql --raw-field 'query=mutation { resolveReviewThread(input: {threadId: "{THREAD_ID}"}) { thread { id isResolved } } }'
```

Where `{THREAD_ID}` is the `PRRT_*` node ID from Step 1.

### Step 7: Verify Zero Unresolved

After resolving all threads, verify none remain:

```bash
gh api graphql --raw-field 'query=query {
  repository(owner: "{OWNER}", name: "{REPO}") {
    pullRequest(number: {NUMBER}) {
      reviewThreads(last: 100) { nodes { isResolved } }
    }
  }
}' | jq '[.data.repository.pullRequest.reviewThreads.nodes[]
  | select(.isResolved == false)] | length'
```

**Must return `0`**. If not, identify and address remaining threads. Do not report
completion until verification passes.

### Step 8: Commit and Push

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
4. Process each PR with unresolved threads using the Task tool with this skill's workflow
5. Verify each PR independently before moving to the next

## Special Cases

### Multi-Reviewer Threads

If multiple reviewers commented on the same thread:

1. Read ALL comments chronologically
2. If 2+ reviewers agree, follow consensus
3. If no consensus, decide based on project conventions and explain reasoning

### Contradictory Feedback

If different threads give conflicting advice:

1. Reply to BOTH threads acknowledging the conflict
2. Propose a decision with technical rationale
3. Tag HUMAN reviewers only (never AI bots) to request consensus

### Outdated Comments

If a comment references deleted or moved code:

1. Check git history for context
2. Reply explaining what happened to the code
3. Provide new location if moved
4. Resolve the outdated thread

### Batch Comments

If one comment lists multiple issues:

1. Address ALL items in the comment
2. Reply with numbered responses matching each item
3. Only resolve after ALL items are addressed

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
| Verification shows >0 | Thread not resolved | Re-run resolution mutation for remaining threads |
| Empty reviewThreads | No reviews yet | Nothing to resolve, exit cleanly |
