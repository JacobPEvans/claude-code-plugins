<!-- cspell:words PRRT -->

# GraphQL Queries for PR Review Threads

GitHub's `gh pr view --json` does NOT support `reviewThreads`. These GraphQL
queries via `gh api graphql` are the only way to manage review threads.

Always use `last: 100` (not `first`). Pagination is capped at 100 per request.

## Fetch Unresolved Threads

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

Fields: `id` (`PRRT_*` node ID), `isResolved`, `path`, `line`/`startLine`,
`comments.nodes[].body`, `comments.nodes[].author.login`

## Resolve Thread Mutation

```bash
gh api graphql --raw-field 'query=mutation {
  resolveReviewThread(input: {threadId: "{THREAD_ID}"}) {
    thread { id isResolved }
  }
}'
```

`{THREAD_ID}` is the `PRRT_*` node ID from the fetch query.

## Verify Zero Unresolved

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

Must return `0`. Any non-zero value means threads remain unresolved.
