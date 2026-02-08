<!-- cspell:words PRRT -->

# GraphQL Queries for PR Review Threads

GitHub's `gh pr view --json` does NOT support `reviewThreads`. These GraphQL
queries via `gh api graphql` are the only way to manage review threads.

Always use `last: 100` (not `first`). Pagination is capped at 100 per request.

## Fetch Unresolved Threads

```bash
gh api graphql \
  -f query='query($owner: String!, $repo: String!, $number: Int!) {
    repository(owner: $owner, name: $repo) {
      pullRequest(number: $number) {
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
  }' \
  -f owner="{OWNER}" \
  -f repo="{REPO}" \
  -F number={NUMBER}
```

Fields: `id` (`PRRT_*` node ID), `isResolved`, `path`, `line`/`startLine`,
`comments.nodes[].body`, `comments.nodes[].author.login`

**WARNING**: This query fetches only the last 100 threads. PRs with more than
100 review threads will silently miss older threads. Run the query multiple
times after resolving visible threads, or implement pagination with
`pageInfo { hasNextPage endCursor }` and `after:` parameter.

## Resolve Thread Mutation

```bash
gh api graphql \
  -f query='mutation($threadId: ID!) {
    resolveReviewThread(input: {threadId: $threadId}) {
      thread { id isResolved }
    }
  }' \
  -f threadId="{THREAD_ID}"
```

`{THREAD_ID}` is the `PRRT_*` node ID from the fetch query.

## Verify Zero Unresolved

```bash
gh api graphql \
  -f query='query($owner: String!, $repo: String!, $number: Int!) {
    repository(owner: $owner, name: $repo) {
      pullRequest(number: $number) {
        reviewThreads(last: 100) { nodes { isResolved } }
      }
    }
  }' \
  -f owner="{OWNER}" \
  -f repo="{REPO}" \
  -F number={NUMBER} \
  | jq '[.data.repository.pullRequest.reviewThreads.nodes[]
    | select(.isResolved == false)] | length'
```

Must return `0`. Any non-zero value means threads remain unresolved.

**WARNING**: This verification only checks the last 100 threads. If a PR has
more than 100 threads, older unresolved threads may exist outside the query
window. Re-run verification after each batch to ensure no threads remain.
