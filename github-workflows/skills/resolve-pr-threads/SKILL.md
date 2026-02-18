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

## DO NOT List (for sub-agents and all GraphQL operations)

- DO NOT use `addPullRequestReviewComment` — wrong mutation, creates new comments not replies
- DO NOT use `resolvePullRequestReviewThread` — wrong name, does not exist
- DO NOT use `gh pr comment` for thread replies — creates top-level comments, not threaded replies
- DO NOT use multi-line queries with backslash `\` continuations
- DO NOT use GraphQL `$variable` syntax (e.g., `$owner`, `$threadId`)
- DO NOT use `-f query=` with separate `-f owner=`/`-F number=` variable flags
- DO NOT use printf piping or heredoc for GraphQL queries

## CRITICAL: GraphQL Query Format Requirements

**ALL GraphQL queries MUST use single-line format with `--raw-field`.**

**NEVER use multi-line GraphQL queries.** Multi-line queries cause:

- Shell encoding issues with newlines
- Variable type coercion errors (e.g., "Variable $prNumber of type Int! was provided invalid value")
- Parsing failures in Claude Code
- Inconsistent behavior across invocations

**If you see or are tempted to write a multi-line GraphQL query, STOP. It is WRONG.**

**Use direct string substitution for `{placeholder}` values — never GraphQL `$variable` syntax.** The `--raw-field` flag sends queries as-is without variable processing. Always substitute values directly into the query string before execution.

**Context inference**: When no arguments provided, automatically infer owner/repo/PR from current git context:

```bash
owner=$(gh repo view --json owner --jq '.owner.login')
repo=$(gh repo view --json name --jq '.name')
number=$(gh pr view --json number --jq '.number')
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

### Step 1: Fetch Unresolved Threads and Recent Comments

Run these operations in parallel:

#### Step 1a: Fetch Unresolved Threads (GraphQL)

Run the fetch query directly:

```bash
gh api graphql --raw-field 'query=query { repository(owner: "{owner}", name: "{repo}") { pullRequest(number: {number}) { reviewThreads(last: 100) { nodes { id isResolved path line startLine comments(last: 100) { nodes { id databaseId body author { login } createdAt } } } } } } }'
```

Replace `{owner}`, `{repo}`, `{number}` with actual values from context inference above.

Filter to threads where `isResolved == false`. Extract from each:

- `id` (`PRRT_*` node ID) - needed for resolution mutation
- `path` - file being reviewed
- `line`/`startLine` - location in file
- `comments.nodes[].id` - comment node ID
- `comments.nodes[].databaseId` - numeric REST API ID for replies
- `comments.nodes[].body` - comment text
- `comments.nodes[].author.login` - who commented

#### Step 1b: Get Last Commit Date

Fetch the last commit timestamp for filtering recent comments:

```bash
gh pr view {number} --json commits --jq '.commits[-1].committedDate'
```

**Execute 1a and 1b in parallel.** Once 1b completes, proceed to 1c and 1d.

#### Step 1c: Fetch Top-Level PR Comments Since Last Commit

```bash
gh api "repos/{owner}/{repo}/issues/{number}/comments?since={lastCommitDate}"
```

Where `{lastCommitDate}` is the ISO 8601 timestamp from Step 1b.

Extract from each comment:

- `id` - comment ID
- `body` - comment text
- `user.login` - author
- `created_at` - timestamp

#### Step 1d: Fetch Review Body Comments Since Last Commit

```bash
gh api "repos/{owner}/{repo}/pulls/{number}/reviews" --jq '[.[] | select(.submitted_at > "{lastCommitDate}" and .body != "")] | .[] | {id, body, user: .user.login, submitted_at}'
```

Extract review body comments (not inline threads) submitted after the last commit.

**Execute 1c and 1d in parallel** after 1b completes.

### Step 2: Group Related Threads

Analyze threads and group by proximity:

- **Same file + within 30 lines** -> group together (max 5 threads per group)
- **Different file or >30 lines apart** -> singleton groups
- **Output numbered group list** before dispatching

Example:

```text
Thread Groups:
  Group 1: src/auth.ts (3 threads at lines 45, 52, 58)
  Group 2: src/api.ts (1 thread at line 120)
  Group 3: README.md (2 threads at lines 15, 18)
```

### Step 2b: Group Recent Comments

Group non-thread comments from Steps 1c and 1d before dispatching:

- **Group by reviewer** — combine each reviewer's comments (top-level + review body) into one group
- **Max 5 comments per group** — if a single reviewer has >5 comments, split into multiple groups
- **Output numbered group list** alongside thread groups

Example:

```text
Comment Groups:
  Group A: @reviewer1 (1 review body + 2 top-level comments)
  Group B: @reviewer2 (1 review body)
```

**Skip entirely** when Steps 1c and 1d both returned zero comments.

### Step 3: Dispatch Sub-Agents

For each group, launch a `general-purpose` sub-agent using the Task tool.

**Sub-agent prompt template:**

```text
You are resolving PR review threads for PR #{number} in {owner}/{repo}.

CRITICAL — Step 1 is mandatory. Do NOT skip it. Do NOT start implementing
fixes or replying to threads until Step 1 is complete.

**FAILURE TO INVOKE receiving-code-review IS A SKILL VIOLATION. This is not optional.**

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

Reply to threads using REST API:
gh api repos/{owner}/{repo}/pulls/{number}/comments/{databaseId}/replies -f body="your reply"

Where {databaseId} is the NUMERIC databaseId from the fetch response (NOT the PRRT_ node ID).

DO NOT use addPullRequestReviewComment — it is the WRONG mutation.
DO NOT use gh pr comment — it creates top-level comments, not threaded replies.
DO NOT use multi-line GraphQL queries or backslash continuations.

For REST API details: read rest-api-patterns.md in the resolve-pr-threads skill directory.

Output ONE line per thread:
PRRT_xxx: handled [commit:abc1234]
PRRT_xxx: needs-human [reason]

Commit changes but DO NOT push.
```

**Launch groups in parallel** - use a single message with multiple Task calls.

Sub-agents commit their own changes but do NOT push.

### Step 3b: Dispatch Comment Group Sub-Agents

Launch comment group sub-agents **in parallel with thread group sub-agents** (Step 3). One sub-agent per comment group.

**Comment sub-agent prompt template:**

```text
You are processing PR review comments for PR #{number} in {owner}/{repo}.

CRITICAL — Step 1 is mandatory. Do NOT skip it. Do NOT start responding
to comments until Step 1 is complete.

**FAILURE TO INVOKE receiving-code-review IS A SKILL VIOLATION. This is not optional.**

Step 1: FIRST — Invoke the `superpowers:receiving-code-review` skill via the
        Skill tool. This skill governs how you evaluate and respond to ALL
        review feedback. Read and follow its full pattern.

Step 2: THEN — Apply the receiving-code-review pattern to evaluate each comment below.
        Determine if each is: actionable feedback requiring implementation,
        a question needing a response, or general acknowledgment.

Step 3: ONLY AFTER Steps 1-2 — For actionable items, implement fixes and commit.
        For questions, reply via `gh pr comment {number} --body "..."`.
        For needs-human items, flag with reason.

Review comments to address:
{for each comment in group}
- Author: {author}
- Date: {created_at or submitted_at}
- Comment: {body}
{end for}

Output ONE line per comment:
COMMENT({author}, {date}): actionable [commit:abc1234]
COMMENT({author}, {date}): acknowledged [replied]
COMMENT({author}, {date}): needs-human [reason]

Commit changes but DO NOT push.
```

**Skip entirely** when Steps 1c and 1d both returned zero comments.

### Step 4: Parse Sub-Agent Output and Resolve Threads

After all sub-agents complete (both thread and comment sub-agents):

1. Parse each **thread sub-agent's** output for `handled` vs `needs-human` status
2. Parse each **comment sub-agent's** output for `actionable`, `acknowledged`, `needs-human` statuses
   - Comments are not resolvable threads — collect statuses for summary only
3. For each `handled` thread, run the resolve mutation (replace `{threadId}` with the `PRRT_*` node ID):

   ```bash
   gh api graphql --raw-field 'query=mutation { resolveReviewThread(input: {threadId: "{threadId}"}) { thread { id isResolved } } }'
   ```

4. For `needs-human` threads, skip resolution and flag for manual attention

### Step 5: Verify, Push, and Report

1. Run the verify query:

   ```bash
   gh api graphql --raw-field 'query=query { repository(owner: "{owner}", name: "{repo}") { pullRequest(number: {number}) { reviewThreads(last: 100) { nodes { isResolved } } } } }' --jq '[.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved == false)] | length'
   ```

2. **Must return `0`**. If not, identify remaining threads and report
3. Push all commits: `git push`
4. Output summary report including both thread and comment digests (see Output Format below)

## Batch Mode ("all")

When `$ARGUMENTS` is `all`:

1. List open PRs: `gh pr list --state open --json number,headRefName`
2. For each PR, check for unresolved threads via GraphQL AND recent comments via REST
3. Skip PRs with **zero unresolved threads AND zero recent comments** (both must be empty)
4. For each PR with feedback to process, run this skill's standard workflow
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
PR #{number} - Review Feedback Summary
Threads: {groupCount} groups ({threadCount} threads total)
  Handled: {count} | Needs human: {count}
  Resolved via GraphQL: {count}
  Verification: {0 unresolved} / {total}
Comments: {commentCount} since last commit
  Actionable: {count} | Acknowledged: {count} | Needs human: {count}
Status: COMPLETE | PARTIAL ({remaining} need attention)
```

**Notes**:

- Omit "Threads:" block when zero threads
- Omit "Comments:" block when zero comments
- Exit cleanly if BOTH threads and comments are zero

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `Could not resolve to a node` | Invalid thread ID | Re-fetch threads, IDs may have changed |
| `Resource not accessible` | Permission issue | Check `gh auth status`, need repo write access |
| Verification shows >0 | Thread not resolved | Re-run mutation for remaining threads |
| Empty reviewThreads | No reviews yet | Nothing to resolve, exit cleanly |
| Exactly 100 threads returned | Pagination cap hit | Resolve visible threads first, then re-run |
| REST reply fails | See rest-api-patterns.md troubleshooting | Check databaseId format, permissions |
| `since` filter returns all comments | Invalid date format | Verify `{lastCommitDate}` is ISO 8601 |
| Reviews endpoint returns empty | No reviews submitted | Proceed with threads only |
