<!-- cspell:words PRRT -->

# GraphQL Queries for PR Review Threads

## CRITICAL: Single-Line Format REQUIRED

**ALL GraphQL queries in this file MUST be single-line format with `--raw-field`.**

**NEVER use multi-line GraphQL queries.** Multi-line queries cause:

- Shell encoding issues with newlines
- Variable type coercion errors
- Parsing failures in Claude Code
- Inconsistent behavior

**If you see a multi-line query anywhere, it is WRONG and must be converted to single-line.**

## Additional Requirements

- GitHub's `gh pr view --json` does NOT support `reviewThreads`
- These GraphQL queries via `gh api graphql` are the only way to manage review threads
- Always use `last: 100` (not `first`)
- Pagination is capped at 100 per request

## Fetch Unresolved Threads

```bash
<!-- markdownlint-disable-next-line MD013 -->
gh api graphql --raw-field 'query=query { repository(owner: "{OWNER}", name: "{REPO}") { pullRequest(number: {NUMBER}) { reviewThreads(last: 100) { nodes { id isResolved path line startLine comments(last: 100) { nodes { id databaseId body author { login } createdAt } } } } } } }'
```

Fields: `id` (`PRRT_*` node ID), `isResolved`, `path`, `line`/`startLine`,
`comments.nodes[].body`, `comments.nodes[].author.login`, `comments.nodes[].databaseId`

**Placeholder substitution**: Replace `{OWNER}`, `{REPO}`, `{NUMBER}` with actual values before running.

**Context inference**: When no arguments provided, infer from current git/PR context:

```bash
# Smart context inference - tries current context first, then conversation context
OWNER=${OWNER:-$(gh repo view --json owner --jq -r '.owner.login' 2>/dev/null)}
REPO=${REPO:-$(gh repo view --json name --jq -r '.name' 2>/dev/null)}
NUMBER=${NUMBER:-$(gh pr view --json number --jq -r '.number' 2>/dev/null)}

# Only error if about to execute with empty values (rare - means not in repo/PR context)
if [[ -z "$OWNER" || -z "$REPO" || -z "$NUMBER" ]]; then
  echo "Error: Could not infer repo/PR context. Either:"
  echo "  1. Run from a git repo with GitHub remote, OR"
  echo "  2. Provide explicit values: OWNER=user REPO=repo NUMBER=123"
  exit 1
fi

# Run query with inferred or provided values
<!-- markdownlint-disable-next-line MD013 -->
gh api graphql --raw-field "query=query { repository(owner: \"${OWNER}\", name: \"${REPO}\") { pullRequest(number: ${NUMBER}) { reviewThreads(last: 100) { nodes { id isResolved path line startLine comments(last: 100) { nodes { id databaseId body author { login } createdAt } } } } } } }"
```

**WARNING**: This query fetches only the last 100 threads. PRs with more than
100 review threads will silently miss older threads. Run the query multiple
times after resolving visible threads, or implement pagination with
`pageInfo { hasNextPage endCursor }` and `after:` parameter.

## Resolve Thread Mutation

```bash
gh api graphql --raw-field 'query=mutation { resolveReviewThread(input: {threadId: "{THREAD_ID}"}) { thread { id isResolved } } }'
```

`{THREAD_ID}` is the `PRRT_*` node ID from the fetch query.

**Placeholder substitution**: Replace `{THREAD_ID}` with the actual thread ID from fetch query.

Example:

```bash
THREAD_ID="PRRT_kwDO..."  # From fetch query response
[[ -z "$THREAD_ID" ]] && { echo "Error: THREAD_ID required from fetch query"; exit 1; }

gh api graphql --raw-field "query=mutation { resolveReviewThread(input: {threadId: \"${THREAD_ID}\"}) { thread { id isResolved } } }"
```

## Verify Zero Unresolved

```bash
<!-- markdownlint-disable-next-line MD013 -->
gh api graphql --raw-field 'query=query { repository(owner: "{OWNER}", name: "{REPO}") { pullRequest(number: {NUMBER}) { reviewThreads(last: 100) { nodes { isResolved } } } } }' | jq '[.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved == false)] | length'
```

Must return `0`. Any non-zero value means threads remain unresolved.

**Placeholder substitution**: Replace `{OWNER}`, `{REPO}`, `{NUMBER}` with actual values.

**Context inference**: Automatically infer from current context when not provided:

```bash
# Infer from current context (works when run from git repo/PR branch)
OWNER=${OWNER:-$(gh repo view --json owner --jq -r '.owner.login' 2>/dev/null)}
REPO=${REPO:-$(gh repo view --json name --jq -r '.name' 2>/dev/null)}
NUMBER=${NUMBER:-$(gh pr view --json number --jq -r '.number' 2>/dev/null)}

# Final check before query execution (prevents GraphQL parse errors)
[[ -z "$OWNER" || -z "$REPO" || -z "$NUMBER" ]] && { echo "Error: Could not infer repo/PR context"; exit 1; }

# Run query
<!-- markdownlint-disable-next-line MD013 -->
gh api graphql --raw-field "query=query { repository(owner: \"${OWNER}\", name: \"${REPO}\") { pullRequest(number: ${NUMBER}) { reviewThreads(last: 100) { nodes { isResolved } } } } }" | jq '[.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved == false)] | length'
```

**WARNING**: This verification only checks the last 100 threads. If a PR has
more than 100 threads, older unresolved threads may exist outside the query
window. Re-run verification after each batch to ensure no threads remain.

## Reply to Review Thread

Use GitHub REST API to add a threaded reply to a review comment.

```bash
gh api repos/{OWNER}/{REPO}/pulls/{NUMBER}/comments/{COMMENT_ID}/replies -f body="{REPLY_TEXT}"
```

**Where to get COMMENT_ID:**

From the Fetch Unresolved Threads query above, use the first comment in the thread:

```bash
COMMENT_ID=$(echo "$THREADS_JSON" | jq -r '.data.repository.pullRequest.reviewThreads.nodes[] | select(.id == "PRRT_xxx") | .comments.nodes[0].databaseId')
```

**Example with placeholder substitution:**

```bash
OWNER=$(gh repo view --json owner --jq .owner.login)
REPO=$(gh repo view --json name --jq .name)
NUMBER=$(gh pr view --json number --jq .number)
COMMENT_ID=123456  # From fetch query: comments.nodes[0].databaseId

gh api repos/${OWNER}/${REPO}/pulls/${NUMBER}/comments/${COMMENT_ID}/replies \
  -f body="**Re: reviewer's feedback on path:line**

Detailed response here."
```

**Requirements:**

- Must use numeric `databaseId` (not GraphQL node ID like `PRRT_*`)
- Reply is automatically threaded under the original comment
- Maintains GitHub's native review conversation structure
- Body can be multi-line markdown
