<!-- cspell:words PRRT PRRC DOABCDEF databaseId -->
<!-- markdownlint-disable MD013 -->

# REST API Patterns for PR Review Thread Replies

## When to Use REST vs GraphQL

| Operation | Use | Why |
|-----------|-----|-----|
| Fetch threads | GraphQL | Only way to access `reviewThreads` |
| Reply (simple text) | Either | GraphQL `addPullRequestReviewThreadReply` works for plain text |
| Reply (special chars) | REST | `-f body=` handles encoding automatically |
| Resolve thread | GraphQL | Only way to resolve |

REST is recommended for replies with complex body text (newlines, markdown, quotes) because `-f body=` handles encoding automatically. For simple plain-text replies, the GraphQL `addPullRequestReviewThreadReply` mutation also works — see [graphql-queries.md](graphql-queries.md).

## Reply Command

```bash
gh api repos/{owner}/{repo}/pulls/{number}/comments/{commentId}/replies -f body="your reply text here"
```

| Parameter | Type | Source | Notes |
|-----------|------|--------|-------|
| `{owner}` | string | `gh repo view --json owner --jq '.owner.login'` | Repository owner |
| `{repo}` | string | `gh repo view --json name --jq '.name'` | Repository name |
| `{number}` | integer | `gh pr view --json number --jq '.number'` | PR number |
| `{commentId}` | integer | GraphQL `databaseId` field | **Must be numeric** |

## Critical: databaseId NOT Node ID

The `{commentId}` parameter **MUST** be the numeric `databaseId` from the GraphQL response, **NOT** the node ID (like `PRRT_*` or `PRRC_*`).

```bash
# WRONG - node IDs don't work with REST API
gh api repos/owner/repo/pulls/123/comments/PRRT_kwDOABCDEF/replies -f body="..."

# CORRECT - numeric databaseId from GraphQL response
gh api repos/owner/repo/pulls/123/comments/987654321/replies -f body="..."
```

## Extract databaseId from GraphQL Response

After fetching threads via the GraphQL query in [graphql-queries.md](graphql-queries.md), extract the numeric `databaseId` for the first comment in the target thread:

```bash
commentId=$(echo "$THREADS_JSON" | jq -r '.data.repository.pullRequest.reviewThreads.nodes[] | select(.id == "PRRT_xxx") | .comments.nodes[0].databaseId')
```

The `databaseId` is always an integer (e.g., `987654321`). If you get `null` or a non-numeric value, the thread ID is wrong or the comment was deleted.

## Fallback: Top-Level PR Comment

If the REST reply endpoint fails (invalid IDs, permissions), fall back to a top-level PR comment. This loses threading but still documents your response.

```bash
gh pr comment {number} --body "Re: reviewer feedback on path:line - your response here"
```

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `404 Not Found` | Invalid `{commentId}` | Verify you're using `databaseId` (numeric), not node ID |
| `422 Validation Failed` | Comment doesn't exist | Re-fetch threads, comment may have been deleted |
| `403 Forbidden` | Permission issue | Check `gh auth status`, need repo write access |
| `Resource not accessible` | Token lacks permissions | Use fallback to top-level comment |
| Empty body error | Missing `-f body=` | Ensure `-f body="text"` is included |

See [graphql-queries.md](graphql-queries.md) for the full GraphQL query reference.
