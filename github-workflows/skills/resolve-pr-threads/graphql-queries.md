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

## Placeholder Convention

All queries use **camelCase placeholders** for string substitution — matching GitHub's own `gh api` convention.

| Placeholder | Type | Example Value | Source |
|-------------|------|---------------|--------|
| `{owner}` | string | `"JacobPEvans"` | `gh repo view --json owner --jq '.owner.login'` |
| `{repo}` | string | `"claude-code-plugins"` | `gh repo view --json name --jq '.name'` |
| `{number}` | integer | `123` | `gh pr view --json number --jq '.number'` |
| `{threadId}` | string | `"PRRT_kwDOABCDEF"` | From GraphQL fetch query response |

### CRITICAL: Direct String Substitution Only

❌ **WRONG** — Using GraphQL `$variable` syntax with `--raw-field`:

```bash
# This will FAIL with variable type coercion errors
gh api graphql --raw-field 'query=mutation($threadId: ID!) {
  resolveReviewThread(input: {threadId: $threadId}) {
    thread { id isResolved }
  }
}'
```

✅ **CORRECT** — Direct string substitution into the query string:

```bash
# Substitute values directly into the query template
THREAD_ID="PRRT_kwDOABCDEF"
gh api graphql --raw-field "query=mutation { resolveReviewThread(input: {threadId: \"${THREAD_ID}\"}) { thread { id isResolved } } }"
```

<!-- markdownlint-disable-next-line MD013 -->
**Do NOT use GraphQL `$variable` syntax with `--raw-field`.** The `--raw-field` flag sends the query as-is without variable processing. Always substitute placeholder values directly into the query string before execution.

## Fetch Unresolved Threads

```bash
<!-- markdownlint-disable-next-line MD013 -->
gh api graphql --raw-field 'query=query { repository(owner: "{owner}", name: "{repo}") { pullRequest(number: {number}) { reviewThreads(last: 100) { nodes { id isResolved path line startLine comments(last: 100) { nodes { id databaseId body author { login } createdAt } } } } } } }'
```

Fields: `id` (`PRRT_*` node ID), `isResolved`, `path`, `line`/`startLine`,
`comments.nodes[].body`, `comments.nodes[].author.login`, `comments.nodes[].databaseId`

<!-- markdownlint-disable-next-line MD013 -->
**Placeholder substitution**: Replace `{owner}`, `{repo}`, `{number}` with actual values before running.

**WARNING**: This query fetches only the last 100 threads. PRs with more than
100 review threads will silently miss older threads. Run the query multiple
times after resolving visible threads, or implement pagination with
`pageInfo { hasNextPage endCursor }` and `after:` parameter.

## Resolve Thread Mutation

```bash
gh api graphql --raw-field 'query=mutation { resolveReviewThread(input: {threadId: "{threadId}"}) { thread { id isResolved } } }'
```

`{threadId}` is the `PRRT_*` node ID from the fetch query.

**Placeholder substitution**: Replace `{threadId}` with the actual thread ID from fetch query.

## Verify Zero Unresolved

```bash
<!-- markdownlint-disable-next-line MD013 -->
gh api graphql --raw-field 'query=query { repository(owner: "{owner}", name: "{repo}") { pullRequest(number: {number}) { reviewThreads(last: 100) { nodes { isResolved } } } } }' | jq '[.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved == false)] | length'
```

Must return `0`. Any non-zero value means threads remain unresolved.

**Placeholder substitution**: Replace `{owner}`, `{repo}`, `{number}` with actual values.

**WARNING**: This verification only checks the last 100 threads. If a PR has
more than 100 threads, older unresolved threads may exist outside the query
window. Re-run verification after each batch to ensure no threads remain.

**Note**: For REST API patterns (replying to review threads), see
[rest-api-patterns.md](rest-api-patterns.md).
