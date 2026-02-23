---
name: resolve-pr-threads
description: >-
  Orchestrates resolution of GitHub PR review threads AND reads recent non-thread
  PR comments (top-level + review bodies) by grouping related feedback,
  dispatching sub-agents that invoke superpowers:receiving-code-review,
  and resolving threads via GraphQL. Use when you need to batch-process
  review feedback to unblock a PR merge.
argument-hint: "[PR_NUMBER|all]"
allowed-tools: Read, Edit, Write, Grep, Glob, Bash(gh:*), Bash(git:*), Task
---

<!-- cspell:words PRRT oneline databaseId -->
<!-- markdownlint-disable MD013 -->

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

## DO NOT

- DO NOT use `addPullRequestReviewComment` — wrong mutation, creates new comments not replies
- DO NOT use `resolvePullRequestReviewThread` — wrong name, does not exist
- DO NOT use `gh pr comment` for thread replies — creates top-level comments, not threaded replies
- DO NOT use multi-line queries with backslash `\` continuations
- DO NOT use GraphQL `$variable` syntax (e.g., `$owner`, `$threadId`)
- DO NOT use `-f query=` with separate variable flags
- DO NOT use printf piping or heredoc for GraphQL queries
- DO NOT write Python/shell scripts to /tmp/ or anywhere. Run gh/git/jq commands directly via Bash.

**Context inference**: Infer owner/repo/PR from current git context, then substitute
these values for `{owner}`, `{repo}`, and `{number}` placeholders in all commands below:

```bash
owner=$(gh repo view --json owner --jq '.owner.login')
repo=$(gh repo view --json name --jq '.name')
number=$(gh pr view --json number --jq '.number')
```

## Workflow

### Step 1: Fetch Unresolved Threads and Recent Comments

**Run 1a and 1b in parallel.**

#### Step 1a: Fetch Unresolved Threads

```bash
gh api graphql --raw-field 'query=query { repository(owner: "{owner}", name: "{repo}") { pullRequest(number: {number}) { reviewThreads(last: 100) { nodes { id isResolved path line startLine comments(last: 100) { nodes { id databaseId body author { login } createdAt } } } } } } }'
```

Filter to `isResolved == false`. Extract: `id` (PRRT_* node ID), `path`, `line`, `comments.nodes[].databaseId`, `comments.nodes[].body`, `comments.nodes[].author.login`.

#### Step 1b: Get Last Commit Date

```bash
gh pr view {number} --json commits --jq '.commits[-1].committedDate'
```

**Then run 1c and 1d in parallel.**

#### Step 1c: Fetch Top-Level PR Comments Since Last Commit

```bash
gh api "repos/{owner}/{repo}/issues/{number}/comments?since={lastCommitDate}"
```

#### Step 1d: Fetch Review Body Comments Since Last Commit

```bash
gh api "repos/{owner}/{repo}/pulls/{number}/reviews" --jq '[.[] | select(.submitted_at > "{lastCommitDate}" and .body != "") | {id, body, author: .user.login, submitted_at}]'
```

### Step 2a: Group Related Threads

- **Same file + within 30 lines** → group together (max 5 threads per group)
- **Different file or >30 lines apart** → singleton groups
- Output numbered group list before dispatching

### Step 2b: Group Recent Comments

- **Group by reviewer** — combine each reviewer's comments into one group (max 5 per group)
- Skip entirely when Steps 1c and 1d both returned zero comments

### Step 3a: Dispatch Thread Group Sub-Agents

For each thread group, launch a `general-purpose` sub-agent. **Launch all groups in parallel.**

Sub-agent prompt:

```text
You are resolving PR review threads for PR #{number} in {owner}/{repo}.

Step 1 (MANDATORY): Invoke `superpowers:receiving-code-review` via the Skill tool.
Read and follow its full pattern before proceeding. Skipping this is a skill violation.

Step 2: Apply receiving-code-review to each thread below. Read the code at the
referenced location, evaluate the feedback, and decide: implement fix, push back
with rationale, or flag as needs-human.

Step 3: Reply to each thread and commit changes.

Threads:
{for each thread in group}
- Thread ID: {PRRT_xxx} | File: {path}:{line} | Reviewer: {author}
- Comment: {body}
- Database ID: {databaseId}
{end for}

Reply command (run directly via Bash — do NOT write a script):
gh api repos/{owner}/{repo}/pulls/{number}/comments/{databaseId}/replies -f body="your reply"

{databaseId} is the NUMERIC value from the fetch response, NOT the PRRT_ node ID.

Output ONE line per thread:
PRRT_xxx: handled [commit:abc1234]
PRRT_xxx: needs-human [reason]

Commit changes but DO NOT push.
```

### Step 3b: Dispatch Comment Group Sub-Agents

Launch **in parallel with Step 3a**. One sub-agent per comment group. Skip if no comments.

Sub-agent prompt:

```text
You are processing PR review comments for PR #{number} in {owner}/{repo}.

Step 1 (MANDATORY): Invoke `superpowers:receiving-code-review` via the Skill tool.
Read and follow its full pattern before proceeding. Skipping this is a skill violation.

Step 2: Apply receiving-code-review to each comment below. Determine if each is:
actionable feedback, a question needing response, or general acknowledgment.

Step 3: Implement fixes and commit, or reply via `gh pr comment {number} --body "..."`.
Do NOT write scripts — run gh commands directly via Bash.

Comments:
{for each comment in group}
- Author: {author} | Date: {created_at or submitted_at}
- Comment: {body}
{end for}

Output ONE line per comment:
COMMENT({author}, {date}): actionable [commit:abc1234]
COMMENT({author}, {date}): acknowledged [replied]
COMMENT({author}, {date}): needs-human [reason]

Commit changes but DO NOT push.
```

### Step 4: Resolve Threads Sequentially

After all sub-agents complete, resolve each `handled` thread **one at a time** (not in parallel) to avoid cascade failures:

```bash
gh api graphql --raw-field 'query=mutation { resolveReviewThread(input: {threadId: "{threadId}"}) { thread { id isResolved } } }'
```

Skip `needs-human` threads; flag for manual attention.

### Step 5: Verify, Push, and Report

```bash
gh api graphql --raw-field 'query=query { repository(owner: "{owner}", name: "{repo}") { pullRequest(number: {number}) { reviewThreads(last: 100) { nodes { isResolved } } } } }' --jq '[.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved == false)] | length'
```

Must return `0`. Then push: `git push`.

## Batch Mode ("all")

1. `gh pr list --state open --json number,headRefName`
2. For each PR, check for unresolved threads and recent comments
3. Skip PRs with zero threads AND zero comments
4. Run standard workflow for each PR with feedback
5. Verify each PR independently before moving to the next

## Output Format

```text
PR #{number} - Review Feedback Summary
Threads: {groupCount} groups ({threadCount} total) | Handled: {n} | Needs human: {n}
  Resolved via GraphQL: {n} | Verification: {0 unresolved}/{total}
Comments: {n} since last commit | Actionable: {n} | Acknowledged: {n} | Needs human: {n}
Status: COMPLETE | PARTIAL ({n} need attention)
```

Omit "Threads:" when zero threads; omit "Comments:" when zero comments.

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `Could not resolve to a node` | Invalid thread ID | Re-fetch threads, IDs may have changed |
| `Resource not accessible` | Permission issue | Check `gh auth status`, need repo write access |
| Verification shows >0 | Thread not resolved | Re-run mutation for remaining threads |
| Empty reviewThreads | No reviews yet | Exit cleanly |
| Exactly 100 threads returned | Pagination cap hit | Resolve visible threads first, then re-run |
| REST reply fails | Invalid `databaseId` or permissions | Verify numeric databaseId (not node ID) and ensure token has required repo permissions (403 = permission issue) |
| `since` filter returns all comments | Invalid date format | Verify ISO 8601 format |
| Reviews endpoint returns empty | No reviews submitted | Proceed with threads only |
