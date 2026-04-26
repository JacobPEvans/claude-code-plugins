---
name: gh-cli-patterns
description: >-
  Canonical reference for all gh CLI command shapes. Use when authoring or
  invoking gh commands — defines allowed --json fields, GraphQL fallback rules,
  -f/-F/--raw-field flag semantics, the PR-readiness gate, code-scanning alert
  query, review-thread mutations, and heredoc bodies.
  Prevents Unknown JSON field errors and divergent query shapes across skills.
---

# gh CLI Canonical Patterns

Single source of truth for every `gh` command shape used across skills.

## `gh pr view --json` — REST-only

Run `gh pr view --json` (with no value) to list all valid fields. Key exception:
**`reviewThreads` is NOT a valid `--json` field** — it is GraphQL-only. Any
`gh pr view --json reviewThreads` call fails with `Unknown JSON field: "reviewThreads"`.

Other GraphQL-only data: inline thread structure, resolution status, `mergeStateStatus` details.

Rule: if the field isn't in the REST allowlist, use `gh api graphql`.

## REST vs GraphQL

| Operation | Use |
|---|---|
| Fetch or verify review thread resolution | GraphQL — see below |
| Resolve a thread | GraphQL — `resolveReviewThread` mutation |
| PR state fields (`state`, `mergeable`, `mergeStateStatus`, etc.) | `gh pr view --json` if listed, else GraphQL |

## Flag Semantics

| Flag | Use |
|---|---|
| `-f key=value` | String; use for `-f query='...'` GraphQL body |
| `-F key=value` | Auto-typed — use for `Int!` GraphQL variables |
| `--raw-field 'key=value'` | Literal string, no `$var` expansion — for queries with `{placeholder}` substitution |

**Never interpolate shell `$VARS` inside a GraphQL query body.** Use literal `{placeholder}`
substitution before running, or declare variables with `-f`/`-F`.

> **Placeholder extraction**: `{owner}` → `gh repo view --json owner --jq '.owner.login'`,
> `{repo}` → `gh repo view --json name --jq '.name'`,
> `{number}` → `gh pr view --json number --jq '.number'`

## Canonical PR-Readiness Gate

Use `first: 100` everywhere (not `25`, not `last: 100`). Always include `pageInfo`.

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
  }' -f owner="{owner}" -f repo="{repo}" -F pr={number}
```

**Abort if any fail:**

| Field | Required | Abort message |
|---|---|---|
| `state` | `OPEN` | "PR is not open" |
| `mergeable` | `MERGEABLE` | "PR has git conflicts" |
| `mergeStateStatus` | `CLEAN` or `HAS_HOOKS` | "PR blocked: `{value}`" |
| `isDraft` | `false` | "PR is a draft" |
| `reviewDecision` | `APPROVED` or `null` | "Review decision: `{value}`" |
| `statusCheckRollup.state` | `SUCCESS` | "CI: `{state}`" |
| All `reviewThreads.isResolved` | `true` | "Unresolved threads" |
| `reviewThreads.pageInfo.hasNextPage` | `false` | ">100 threads — paginate" |

> NOT-ready `mergeStateStatus` values: `BEHIND`, `BLOCKED`, `DIRTY`, `DRAFT`, `UNKNOWN`, `UNSTABLE`.

## Canonical Code-Scanning Alert Count

```bash
gh api 'repos/{owner}/{repo}/code-scanning/alerts?state=open&per_page=100' \
  --jq 'length' || echo "0"
```

`per_page=100` covers realistic alert counts. `|| echo "0"` handles disabled code-scanning (404).
Must return `0`; otherwise invoke `/resolve-codeql fix`.

## Canonical Review Thread Queries

Substitute `{owner}`, `{repo}`, `{number}` before running.

**Fetch unresolved threads** (`id` = `PRRT_*` node ID, used for mutations):

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

**Count unresolved** (must equal `0` before merging):

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

> If a PR may have >100 threads, use the PR-readiness gate above — it includes
> `pageInfo{hasNextPage}` and aborts if overflow is detected.

## Review-Thread Mutations

| Operation | Correct | WRONG — do not use |
|---|---|---|
| Reply | `addPullRequestReviewThreadReply` | `addPullRequestReviewComment` (creates new comment) |
| Resolve | `resolveReviewThread` | `resolvePullRequestReviewThread` (does not exist) |

```bash
# Reply
gh api graphql --raw-field 'query=mutation {
  addPullRequestReviewThreadReply(
    input: {pullRequestReviewThreadId: "{threadId}", body: "reply text"}
  ) { comment { id body } }
}'

# Resolve
gh api graphql --raw-field 'query=mutation {
  resolveReviewThread(input: {threadId: "{threadId}"}) { thread { id isResolved } }
}'
```

For replies with special characters or markdown, use REST:

```bash
gh api repos/{owner}/{repo}/pulls/{number}/comments/{databaseId}/replies -f body="reply text"
```

Failure guide: stale `{threadId}` → re-fetch threads; permission error → `gh auth status`;
wrong mutation name → check table above.

## Heredoc Body Pattern

```bash
gh pr edit {number} --body "$(cat <<'EOF'
body content here
EOF
)"
```

Same pattern for `gh pr create`, `gh pr comment`, `gh issue comment`. Never use `--body-file`.

## Related Skills

- **pr-standards** (git-standards) — PR creation guards, issue linking
- **git-workflow-standards** (git-standards) — Branch hygiene, worktree conventions
