<!-- cspell:words PRRT PRRC DOABCDEF databaseId -->
<!-- markdownlint-disable MD013 -->

# REST API Patterns for PR Review Thread Replies

REST is recommended for replies with complex body text (newlines, markdown, quotes) because `-f body=` handles encoding automatically. For simple plain-text replies, the GraphQL `addPullRequestReviewThreadReply` mutation also works — see [graphql-queries.md](graphql-queries.md).

## Reply Command

```bash
gh api repos/{owner}/{repo}/pulls/{number}/comments/{databaseId}/replies -f body="your reply text here"
```

| Parameter | Type | Source | Notes |
|-----------|------|--------|-------|
| `{owner}` | string | `gh repo view --json owner --jq '.owner.login'` | Repository owner |
| `{repo}` | string | `gh repo view --json name --jq '.name'` | Repository name |
| `{number}` | integer | `gh pr view --json number --jq '.number'` | PR number |
| `{databaseId}` | integer | GraphQL `databaseId` field | **Must be numeric** |

## Critical: databaseId NOT Node ID

The `{databaseId}` parameter **MUST** be the numeric `databaseId` from the GraphQL response, **NOT** the node ID (like `PRRT_*` or `PRRC_*`).

```bash
# WRONG - node IDs don't work with REST API
gh api repos/owner/repo/pulls/123/comments/PRRT_kwDOABCDEF/replies -f body="..."

# CORRECT - numeric databaseId from GraphQL response
gh api repos/owner/repo/pulls/123/comments/987654321/replies -f body="..."
```

## Extract databaseId from GraphQL Response

After fetching threads via GraphQL, extract the numeric `databaseId` for the first comment in the target thread:

```bash
commentId=$(echo "$THREADS_JSON" | jq -r '.data.repository.pullRequest.reviewThreads.nodes[] | select(.id == "PRRT_xxx") | .comments.nodes[0].databaseId')
```

The `databaseId` is always an integer (e.g., `987654321`). If you get `null` or a non-numeric value, the thread ID is wrong or the comment was deleted.

## Fallback: Top-Level PR Comment

If the REST reply endpoint fails (invalid IDs, permissions), fall back to a top-level PR comment. This loses threading but still documents your response.

```bash
gh pr comment {number} --body "Re: reviewer feedback on path:line - your response here"
```

## Read Non-Thread Comments

### Get Last Commit Date

```bash
gh pr view {number} --json commits --jq '.commits[-1].committedDate'
```

Returns ISO 8601 timestamp (e.g., `2026-02-17T12:34:56Z`). Used to filter comments since the last code push.

### Fetch Top-Level PR Comments Since Last Commit

```bash
gh api "repos/{owner}/{repo}/issues/{number}/comments?since={lastCommitDate}"
```

Returns array of comments posted after the specified timestamp.

### Fetch Review Body Comments Since Last Commit

```bash
gh api "repos/{owner}/{repo}/pulls/{number}/reviews" --jq '[.[] | select(.submitted_at > "{lastCommitDate}" and .body != "") | {id, body, author: .user.login, submitted_at}]'
```

The `--jq` filter is required because the reviews endpoint does not support server-side `?since=` filtering.

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `404 Not Found` | Invalid `{databaseId}` | Verify you're using `databaseId` (numeric), not node ID |
| `422 Validation Failed` | Comment doesn't exist | Re-fetch threads, comment may have been deleted |
| `403 Forbidden` | Permission issue | Check `gh auth status`, need repo write access |
| `Resource not accessible` | Token lacks permissions | Use fallback to top-level comment |
| Empty body error | Missing `-f body=` | Ensure `-f body="text"` is included |
