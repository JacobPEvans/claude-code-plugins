<!-- cspell:words PRRT DOABCDEF databaseId -->
<!-- markdownlint-disable MD013 -->

# GraphQL Queries for PR Review Threads

## Golden Rules

1. **Single-line only** — no backslash `\` continuations in any `gh api` command
2. **`--raw-field` with direct substitution** — no GraphQL `$variable` syntax, no `-f`/`-F` variable flags
3. **`--jq` over `| jq`** — avoids shell pipe issues in Claude Code

## Get Context

```bash
owner=$(gh repo view --json owner --jq '.owner.login')
repo=$(gh repo view --json name --jq '.name')
number=$(gh pr view --json number --jq '.number')
```

## Placeholder Convention

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

## When a Mutation Fails

If `addPullRequestReviewThreadReply` returns an error, follow this diagnosis flow:

1. **`doesn't accept argument`** → The mutation exists, but the argument name or `input:` shape is wrong. Use `addPullRequestReviewThreadReply` exactly as shown above, with `input: {pullRequestReviewThreadId: "...", body: "..."}`
2. **`Could not resolve to a node`** → The thread ID is stale. Re-fetch threads with the fetch query above
3. **`Resource not accessible`** → Token permissions. Run `gh auth status` and verify repo write access

The reply must always land inside the review thread. Top-level PR comments are unresolvable and break the workflow.

> **Note:** An error like `Cannot query field "addPullRequestReviewThreadReply" on type "Mutation"` usually means the mutation name itself is wrong (for example, using `addPullRequestReviewComment` instead of `addPullRequestReviewThreadReply`).
