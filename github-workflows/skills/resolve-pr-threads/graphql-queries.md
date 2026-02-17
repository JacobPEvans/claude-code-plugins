<!-- cspell:words PRRT DOABCDEF databaseId -->
<!-- markdownlint-disable MD013 -->

# GraphQL Queries for PR Review Threads

## Golden Rules

1. **Single-line only** — no backslash `\` continuations in any `gh api` command
2. **`--raw-field` with direct substitution** — no GraphQL `$variable` syntax, no `-f`/`-F` variable flags
3. **`--jq` over `| jq`** — avoids shell pipe issues in Claude Code

## Get Context

Run these three commands to get substitution values:

```bash
owner=$(gh repo view --json owner --jq '.owner.login')
repo=$(gh repo view --json name --jq '.name')
number=$(gh pr view --json number --jq '.number')
```

## Placeholder Convention

All queries use **camelCase placeholders** for string substitution.

| Placeholder | Type | Example Value | Source |
|-------------|------|---------------|--------|
| `{owner}` | string | `"JacobPEvans"` | `gh repo view --json owner --jq '.owner.login'` |
| `{repo}` | string | `"claude-code-plugins"` | `gh repo view --json name --jq '.name'` |
| `{number}` | integer | `123` | `gh pr view --json number --jq '.number'` |
| `{threadId}` | string | `"PRRT_kwDOABCDEF"` | From GraphQL fetch query response |

Replace placeholders with actual values before running any command.

## Fetch Unresolved Threads

```bash
gh api graphql --raw-field 'query=query { repository(owner: "{owner}", name: "{repo}") { pullRequest(number: {number}) { reviewThreads(last: 100) { nodes { id isResolved path line startLine comments(last: 100) { nodes { id databaseId body author { login } createdAt } } } } } } }'
```

Fields returned: `id` (`PRRT_*` node ID), `isResolved`, `path`, `line`/`startLine`,
`comments.nodes[].body`, `comments.nodes[].author.login`, `comments.nodes[].databaseId`

**WARNING**: Fetches only the last 100 threads. Re-run after resolving visible threads if the PR has more.

## Reply to Thread (GraphQL)

```bash
gh api graphql --raw-field 'query=mutation { addPullRequestReviewThreadReply(input: {pullRequestReviewThreadId: "{threadId}", body: "reply text here"}) { comment { id body } } }'
```

For replies with special characters, newlines, or complex markdown, use the REST API instead — see [rest-api-patterns.md](rest-api-patterns.md).

## Resolve Thread

```bash
gh api graphql --raw-field 'query=mutation { resolveReviewThread(input: {threadId: "{threadId}"}) { thread { id isResolved } } }'
```

`{threadId}` is the `PRRT_*` node ID from the fetch query.

## Verify Zero Unresolved

```bash
gh api graphql --raw-field 'query=query { repository(owner: "{owner}", name: "{repo}") { pullRequest(number: {number}) { reviewThreads(last: 100) { nodes { isResolved } } } } }' --jq '[.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved == false)] | length'
```

Must return `0`. Any non-zero value means threads remain unresolved.

## Mutation Reference Table

| Operation | Correct Mutation | WRONG (do NOT use) |
|-----------|------------------|--------------------|
| Reply to thread | `addPullRequestReviewThreadReply` | `addPullRequestReviewComment` |
| Resolve thread | `resolveReviewThread` | `resolvePullRequestReviewThread` |

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Could not resolve to a node` | Invalid thread ID | Re-fetch threads, IDs may have changed |
| `Variable $x was provided invalid value` | Used GraphQL `$variable` syntax | Remove all `$variables`, substitute values directly |
| `Parse error on ... near $` | Shell corrupted `$` sign | Use single quotes around `--raw-field` value |
| `Resource not accessible` | Permission issue | Check `gh auth status`, need repo write access |
| Exactly 100 threads returned | Pagination cap hit | Resolve visible threads first, then re-run |

See [rest-api-patterns.md](rest-api-patterns.md) for REST API reply patterns.
