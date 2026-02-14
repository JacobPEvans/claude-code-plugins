<!-- cspell:words PRRT databaseId -->

# GitHub REST API Patterns for PR Review Threads

REST API commands for replying to GitHub pull request review threads.
Complements the GraphQL operations in [graphql-queries.md](graphql-queries.md).

## Why REST API for Replies?

GitHub's GraphQL API for review threads is **read-only**. To reply to review
comments while maintaining native threading, you must use the REST API.

**Key distinction**:

- **GraphQL**: Fetch threads, resolve threads (read + state changes)
- **REST API**: Reply to threads (write operations within threads)

## Reply to Review Thread

Use GitHub REST API to add a threaded reply to a review comment.

```bash
gh api repos/{OWNER}/{REPO}/pulls/{NUMBER}/comments/{COMMENT_ID}/replies \
  -f body="{REPLY_TEXT}"
```

### Required Parameters

| Parameter | Type | Source | Notes |
|-----------|------|--------|-------|
| `OWNER` | string | `gh repo view --json owner` | Repository owner |
| `REPO` | string | `gh repo view --json name` | Repository name |
| `NUMBER` | integer | `gh pr view --json number` | PR number |
| `COMMENT_ID` | integer | GraphQL `databaseId` | **Must be numeric** |
| `body` | string | Your reply text | Multi-line markdown supported |

### Critical: Use databaseId, NOT Node ID

The `COMMENT_ID` parameter **MUST** be the numeric `databaseId` from GraphQL,
**NOT** the node ID (like `PRRT_*` or `PRRC_*`).

**Wrong**:

```bash
# ❌ This will fail - node IDs don't work with REST API
COMMENT_ID="PRRT_kwDOABCDEF"  # GraphQL node ID
gh api repos/owner/repo/pulls/123/comments/$COMMENT_ID/replies -f body="..."
```

**Correct**:

```bash
# ✅ This works - numeric databaseId from GraphQL response
COMMENT_ID=987654321  # From comments.nodes[0].databaseId
gh api repos/owner/repo/pulls/123/comments/$COMMENT_ID/replies -f body="..."
```

## Extract Comment Database ID from GraphQL

When you fetch threads via GraphQL (see [graphql-queries.md](graphql-queries.md)),
each comment has both a node ID and a databaseId.

### GraphQL Response Structure

```json
{
  "data": {
    "repository": {
      "pullRequest": {
        "reviewThreads": {
          "nodes": [
            {
              "id": "PRRT_kwDOABCDEF",
              "comments": {
                "nodes": [
                  {
                    "id": "PRRC_kwDOABCDEF",
                    "databaseId": 987654321,
                    "body": "Original review comment",
                    "author": {"login": "reviewer"}
                  }
                ]
              }
            }
          ]
        }
      }
    }
  }
}
```

### Extract databaseId with jq

```bash
# Extract database ID for a specific thread
COMMENT_ID=$(echo "$THREADS_JSON" | jq -r \
  '.data.repository.pullRequest.reviewThreads.nodes[] |
   select(.id == "PRRT_xxx") |
   .comments.nodes[0].databaseId')

# Verify it's numeric
[[ "$COMMENT_ID" =~ ^[0-9]+$ ]] || { echo "Error: Invalid COMMENT_ID"; exit 1; }
```

## Complete Example

```bash
# 1. Fetch threads via GraphQL (see graphql-queries.md)
OWNER=$(gh repo view --json owner --jq -r '.owner.login')
REPO=$(gh repo view --json name --jq -r '.name')
NUMBER=$(gh pr view --json number --jq -r '.number')

<!-- markdownlint-disable-next-line MD013 -->
THREADS_JSON=$(gh api graphql --raw-field "query=query { repository(owner: \"${OWNER}\", name: \"${REPO}\") { pullRequest(number: ${NUMBER}) { reviewThreads(last: 100) { nodes { id comments(last: 100) { nodes { databaseId body author { login } } } } } } } }")

# 2. Extract database ID for the thread you want to reply to
THREAD_ID="PRRT_kwDO..."  # The thread's GraphQL node ID
COMMENT_ID=$(echo "$THREADS_JSON" | jq -r \
  ".data.repository.pullRequest.reviewThreads.nodes[] |
   select(.id == \"${THREAD_ID}\") |
   .comments.nodes[0].databaseId")

# 3. Verify we have a valid numeric ID
if [[ ! "$COMMENT_ID" =~ ^[0-9]+$ ]]; then
  echo "Error: Could not extract valid databaseId for thread $THREAD_ID"
  exit 1
fi

# 4. Post the threaded reply
gh api repos/${OWNER}/${REPO}/pulls/${NUMBER}/comments/${COMMENT_ID}/replies \
  -f body="**Re: feedback on file.ts:42**

Thanks for the review! I've addressed this by:
- Refactoring the function for clarity
- Adding input validation
- Including unit tests

Fixed in commit abc1234."
```

## Multi-Line Reply Formatting

The REST API supports multi-line markdown in the `body` parameter.

### Using Here-Document

```bash
gh api repos/${OWNER}/${REPO}/pulls/${NUMBER}/comments/${COMMENT_ID}/replies \
  -f body="$(cat <<'EOF'
**Re: reviewer's feedback on path:line**

Detailed response here with:
- Bullet points
- Code blocks
- Multiple paragraphs

Fixed in commit abc1234.
EOF
)"
```

### Using printf

```bash
REPLY=$(printf "**Re: %s's feedback on %s:%s**\n\n%s\n\nFixed in commit %s." \
  "reviewer" "src/auth.ts" "45" "Detailed explanation here" "abc1234")

gh api repos/${OWNER}/${REPO}/pulls/${NUMBER}/comments/${COMMENT_ID}/replies \
  -f body="$REPLY"
```

## Reply Behavior

When you use this REST endpoint:

✅ **Reply appears threaded** under the original review comment in GitHub UI
✅ **Preserves conversation context** - readers see the full thread
✅ **Notifies the reviewer** - they receive a notification
✅ **Supports markdown** - formatting, code blocks, lists all work
✅ **Counted as engagement** - PR shows activity

❌ **Does NOT resolve the thread** - you must still call the GraphQL resolve mutation
❌ **Does NOT trigger review re-request** - resolution + approval required for that

## Fallback: Top-Level PR Comment

If the REST API fails (permission issues, invalid IDs), fall back to a
top-level PR comment. This loses threading but still documents your response.

```bash
gh pr comment ${NUMBER} --body "**Re: reviewer's feedback on path:line**

Detailed response here.

Note: Posted as top-level comment due to threading API limitation."
```

**Use cases for fallback**:

- Token lacks `write:discussion` permission
- Invalid or stale comment database ID
- Comment was deleted after GraphQL fetch
- Network/API errors

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `404 Not Found` | Invalid `COMMENT_ID` | Verify you're using `databaseId` (numeric), not node ID |
| `422 Validation Failed` | Comment doesn't exist | Re-fetch threads, comment may have been deleted |
| `403 Forbidden` | Permission issue | Check `gh auth status`, need repo write access |
| `Resource not accessible` | Token lacks permissions | Use fallback to top-level comment |
| Empty body error | Missing `-f body=` | Ensure `-f body="text"` is included |

## Integration with GraphQL Workflow

Typical workflow combining GraphQL and REST:

1. **Fetch threads** (GraphQL) → Get `id` (PRRT_*) and `databaseId` for each comment
2. **Read and analyze** → Understand reviewer feedback
3. **Implement changes** → Fix code, commit
4. **Reply to thread** (REST) → Post explanation using `databaseId`
5. **Resolve thread** (GraphQL) → Mark resolved using `id` (PRRT_*)
6. **Verify** (GraphQL) → Confirm zero unresolved threads

See [SKILL.md](SKILL.md) for the complete orchestration pattern.
