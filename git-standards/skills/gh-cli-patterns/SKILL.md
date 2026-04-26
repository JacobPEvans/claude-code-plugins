---
name: gh-cli-patterns
description: >-
  Canonical reference for all gh CLI command shapes. Use when authoring or
  invoking gh commands — defines allowed --json fields, GraphQL fallback rules,
  -f/-F/--raw-field flag semantics, the PR-readiness gate, code-scanning alert
  query, review-thread mutations, heredoc bodies, and owner/repo extraction.
  Prevents Unknown JSON field errors and divergent query shapes across skills.
---

# gh CLI Canonical Patterns

Single source of truth for every `gh` command shape used across skills.

## `gh pr view --json` — REST-only fields

`gh pr view --json` exposes **REST fields only**. The full allowed list:

```text
additions, assignees, author, autoMergeRequest, baseRefName, baseRefOid,
body, changedFiles, closed, closedAt, closingIssuesReferences, comments,
commits, createdAt, deletions, files, fullDatabaseId, headRefName,
headRefOid, headRepository, headRepositoryOwner, id, isCrossRepository,
isDraft, labels, latestReviews, maintainerCanModify, mergeCommit,
mergeStateStatus, mergeable, mergedAt, mergedBy, milestone, number,
potentialMergeCommit, projectCards, projectItems, reactionGroups,
reviewDecision, reviewRequests, reviews, state, statusCheckRollup,
title, updatedAt, url
```

**`reviewThreads` is NOT in this list.** It is a GraphQL-only concept. Any
`gh pr view --json reviewThreads` call will fail with `Unknown JSON field: "reviewThreads"`.

Other data that requires GraphQL (not available via `--json`):

- Inline review thread structure and resolution status
- Full `mergeStateStatus` reason details beyond the enum value

Rule: if the field isn't in the allowlist above, use `gh api graphql`.

## REST vs GraphQL Decision Table

| Operation | Use |
|---|---|
| Fetch review threads + resolution status | GraphQL — see below |
| Reply to a thread | REST `…/pulls/{n}/comments/{databaseId}/replies -f body=` |
| Reply to a thread with markdown/newlines | REST — special chars safer than GraphQL mutations |
| Resolve a thread | GraphQL — `resolveReviewThread` mutation |
| Verify zero unresolved threads | GraphQL — see below |
| Code-scanning alert count | REST — `gh api` with `?state=open` |
| PR field (state, mergeable, etc.) | `gh pr view --json` if in allowlist, else GraphQL |
| Issue/top-level PR comments | REST — `…/issues/{n}/comments` |

## Flag Semantics

| Flag | Use | Notes |
|---|---|---|
| `-f key=value` | String parameter | Passes value as string; also used for `-f query='...'` |
| `-F key=value` | Auto-typed parameter | Converts integers, booleans — use for `Int!` GraphQL variables |
| `--raw-field 'key=value'` | Literal string, no template expansion | Preferred for the query body with `{placeholder}` substitution — prevents `$var` from being treated as shell variables |

**Never interpolate shell `$VARS` inside a GraphQL query body.** Use either
literal `{placeholder}` substitution before running, or GraphQL variables
with `-f`/`-F` flags.

## Owner / Repo / Number Extraction

```bash
owner=$(gh repo view --json owner --jq '.owner.login')
repo=$(gh repo view --json name --jq '.name')
number=$(gh pr view --json number --jq '.number')
```

Replace `{owner}`, `{repo}`, `{number}` in all command placeholders with these values.

## Canonical PR-Readiness Gate (GraphQL)

Single authoritative shape. Use `first: 100` (not `25`, not `last: 100`).
Always include `pageInfo { hasNextPage }` — signal if threads exceed 100.

```bash
gh api graphql -f query='
  query($owner:String!,$repo:String!,$pr:Int!){
    repository(owner:$owner,name:$repo){
      pullRequest(number:$pr){
        state mergeable mergeStateStatus isDraft reviewDecision
        commits(last:1){nodes{commit{statusCheckRollup{state}}}}
        reviewThreads(first:100){nodes{isResolved} pageInfo{hasNextPage}}
      }
    }
  }' -f owner="{owner}" -f repo="{repo}" -F pr={PR_NUMBER}
```

**Abort conditions** — if any hit, fix and re-run the gate:

| Field | Required | Abort message |
|---|---|---|
| `state` | `OPEN` | "PR is not open" |
| `mergeable` | `MERGEABLE` | "PR has git conflicts — rebase/merge required" |
| `mergeStateStatus` | `CLEAN` or `HAS_HOOKS` | "PR merge state is `{value}` — blocked" |
| `isDraft` | `false` | "PR is a draft — mark ready for review first" |
| `reviewDecision` | `APPROVED` or `null` | "Review decision is `{value}`" |
| `statusCheckRollup.state` | `SUCCESS` | "CI rollup is `{state}`" |
| All `reviewThreads.isResolved` | `true` | "Unresolved review threads" |
| `reviewThreads.pageInfo.hasNextPage` | `false` | ">100 threads — paginate and re-verify" |

> `mergeStateStatus` values that are **NOT ready:** `BEHIND` (needs rebase),
> `BLOCKED` (branch protection), `DIRTY` (conflicts), `DRAFT`, `UNKNOWN`
> (GitHub computing), `UNSTABLE` (checks failed or pending).

## Canonical Code-Scanning Alert Count

Use the `?state=open` server-side filter — faster than client-side `select(.state=="open")`.
`|| echo "0"` handles repos with code-scanning disabled (404).

```bash
gh api 'repos/{owner}/{repo}/code-scanning/alerts?state=open&per_page=100' \
  --paginate --jq 'length' || echo "0"
```

**Required**: result must be `0`. Any open alerts → invoke `/resolve-codeql fix`.

## Canonical Fetch Unresolved Threads

Use `--raw-field` (prevents shell variable expansion in query body).
Use `first: 100` consistently. Substitute `{owner}`, `{repo}`, `{number}` before running.

```bash
gh api graphql --raw-field 'query=query {
  repository(owner: "{owner}", name: "{repo}") {
    pullRequest(number: {number}) {
      reviewThreads(first: 100) {
        nodes {
          id isResolved path line startLine
          comments(first: 100) {
            nodes { id databaseId body author { login } createdAt }
          }
        }
      }
    }
  }
}'
```

Fields returned: `id` (`PRRT_*` node ID), `isResolved`, `path`, `line`/`startLine`,
`comments.nodes[].body`, `comments.nodes[].author.login`, `comments.nodes[].databaseId`.

## Canonical Verify Zero Unresolved

```bash
gh api graphql --raw-field 'query=query {
  repository(owner: "{owner}", name: "{repo}") {
    pullRequest(number: {number}) {
      reviewThreads(first: 100) { nodes { isResolved } }
    }
  }
}' --jq '[.data.repository.pullRequest.reviewThreads.nodes[]
  | select(.isResolved == false)] | length'
```

Must return `0`. Any non-zero value means threads remain unresolved.

## Review-Thread Mutation Reference

| Operation | Correct | WRONG (do not use) |
|---|---|---|
| Reply to thread | `addPullRequestReviewThreadReply` | `addPullRequestReviewComment` (creates new comment, not reply) |
| Resolve thread | `resolveReviewThread` | `resolvePullRequestReviewThread` (does not exist) |

Reply mutation:

```bash
gh api graphql --raw-field 'query=mutation {
  addPullRequestReviewThreadReply(
    input: {pullRequestReviewThreadId: "{threadId}", body: "reply text"}
  ) { comment { id body } }
}'
```

Resolve mutation:

```bash
gh api graphql --raw-field 'query=mutation { resolveReviewThread(input: {threadId: "{threadId}"}) { thread { id isResolved } } }'
```

`{threadId}` is the `PRRT_*` node ID from the fetch query.

For replies with special characters or complex markdown, use REST instead:

```bash
gh api repos/{owner}/{repo}/pulls/{number}/comments/{databaseId}/replies \
  -f body="reply text here"
```

### When a mutation fails

1. `doesn't accept argument` — argument name wrong; use `addPullRequestReviewThreadReply` with `input: {pullRequestReviewThreadId: "...", body: "..."}`
2. `Could not resolve to a node` — thread ID stale; re-fetch threads
3. `Resource not accessible` — token permissions; run `gh auth status`
4. `Cannot query field "X" on type "Mutation"` — wrong mutation name; check table above

## Heredoc Body Pattern

Never use `--body-file` with temp files. Always inline with a heredoc:

```bash
gh pr edit {number} --body "$(cat <<'EOF'
PR body content here.

Multi-line is fine.
EOF
)"
```

Same pattern for `gh pr create`, `gh pr comment`, `gh issue comment`.

## Related Skills

- **pr-standards** (git-standards) — PR creation guards, issue linking
- **git-workflow-standards** (git-standards) — Branch hygiene, worktree conventions
