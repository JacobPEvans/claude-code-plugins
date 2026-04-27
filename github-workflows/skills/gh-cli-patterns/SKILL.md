---
name: gh-cli-patterns
description: >-
  Canonical reference for all gh CLI command shapes used by skills in this
  plugin. Defines the placeholder convention, allowed --json fields, GraphQL
  fallback rules, -f/-F/--raw-field flag semantics, the PR-readiness gate,
  code-scanning alert query, review-thread fetch/count/resolve mutations, and
  heredoc bodies. Prevents Unknown JSON field errors and divergent query shapes.
---

# gh CLI Canonical Patterns — github-workflows

## Placeholder Convention

Two visually distinct notations — never mix them up:

| Notation | Meaning | Example |
|---|---|---|
| `$varName` | GraphQL variable name — **keep as literal text** in the query body | `$prNumber` |
| `<UPPER_NAME>` | Shell template — **replace before running** | `<PR_NUMBER>` |

Standard replacements:

```text
<OWNER>       → $(gh repo view --json owner --jq '.owner.login')
<REPO>        → $(gh repo view --json name  --jq '.name')
<PR_NUMBER>   → $(gh pr view  --json number --jq '.number')  (integer)
<THREAD_ID>   → PRRT_* node ID from the fetch-threads query (string)
<DATABASE_ID> → numeric comment ID from the fetch-threads query
```

## `gh pr view --json` — REST-Only

`reviewThreads` is **not** a valid `--json` field — it is GraphQL-only. Any
`gh pr view --json reviewThreads` call fails with `Unknown JSON field: "reviewThreads"`.

Other GraphQL-only fields: inline thread structure, resolution status, full
`mergeStateStatus` enum.

**Rule**: if the field isn't returned by `gh pr view --json` (no value), use `gh api graphql`.

## REST vs GraphQL

| Operation | Use |
|---|---|
| Fetch unresolved threads | GraphQL — see Canonical Review-Thread Queries |
| Verify thread resolution count | GraphQL — see Canonical Review-Thread Queries |
| Resolve a thread | GraphQL — `resolveReviewThread` mutation |
| Reply to a thread | GraphQL (`addPullRequestReviewThreadReply`) or REST (simpler for markdown/special chars) |
| Reply to a PR-level comment | REST `repos/<OWNER>/<REPO>/issues/<PR_NUMBER>/comments` |
| PR state fields (`state`, `mergeable`, `mergeStateStatus`, etc.) | `gh pr view --json` if listed; else GraphQL |

## Flag Semantics

| Flag | Use |
|---|---|
| `-f key=value` | String — for the `-f query='...'` GraphQL body and string variables |
| `-F key=value` | Auto-typed — for `Int!` and `Boolean!` GraphQL variables |
| `--raw-field 'key=value'` | Literal string, no `$var` expansion — for queries using inline `<PLACEHOLDER>` substitution |

**Never interpolate shell `$VARS` inside a GraphQL query string.** Declare typed variables
with `-f`/`-F` instead.

## Canonical PR-Readiness Gate

Use `first: 100` (never `first: 25` or `last: 100`). Always include `pageInfo`.

Replace `<OWNER>`, `<REPO>`, `<PR_NUMBER>` before running (see Placeholder Convention above).

```bash
gh api graphql -f query='
  query($owner:String!,$repo:String!,$prNumber:Int!){
    repository(owner:$owner,name:$repo){
      pullRequest(number:$prNumber){
        state mergeable mergeStateStatus isDraft reviewDecision
        commits(last:1){nodes{commit{statusCheckRollup{state}}}}
        reviewThreads(first:100){nodes{isResolved} pageInfo{hasNextPage}}
      }
    }
  }' -f owner=<OWNER> -f repo=<REPO> -F prNumber=<PR_NUMBER>
```

Inside the `-f query='...'` body, `$owner`/`$repo`/`$prNumber` are GraphQL variable names —
keep them literal. After the closing `'`, `-f owner=<OWNER>` etc. bind values — replace the
`<ANGLE_BRACKET>` placeholders with actual strings.

Required values — abort if any fail:

| Field | Required | Abort message |
|---|---|---|
| `state` | `OPEN` | "PR is not open" |
| `mergeable` | `MERGEABLE` | "PR has git conflicts" |
| `mergeStateStatus` | `CLEAN` or `HAS_HOOKS` | "PR blocked: {value}" |
| `isDraft` | `false` | "PR is a draft" |
| `reviewDecision` | `APPROVED` or `null` | "Review decision: {value}" |
| `statusCheckRollup.state` | `SUCCESS` | "CI: {state}" |
| All `reviewThreads.isResolved` | `true` | "Unresolved threads" |
| `reviewThreads.pageInfo.hasNextPage` | `false` | ">100 threads — paginate" |

> NOT-ready `mergeStateStatus` values: `BEHIND`, `BLOCKED`, `DIRTY`, `DRAFT`, `UNKNOWN`, `UNSTABLE`.

## Canonical Code-Scanning Alert Count

Replace `<OWNER>`, `<REPO>` before running.

```bash
gh api 'repos/<OWNER>/<REPO>/code-scanning/alerts?state=open&per_page=100' \
  --jq 'length' || echo "0"
```

`per_page=100` covers realistic alert counts. `|| echo "0"` handles disabled code-scanning (404).
Must return `0`; otherwise invoke `/resolve-codeql fix`.

## Canonical Review-Thread Queries

Replace `<OWNER>`, `<REPO>`, `<PR_NUMBER>` using inline literal substitution before running
(uses `--raw-field` — no `-f`/`-F` variable binding).

**Fetch unresolved threads** (`id` = `PRRT_*` node ID for mutations, `databaseId` = numeric ID for REST replies):

```bash
gh api graphql --raw-field 'query=query {
  repository(owner: "<OWNER>", name: "<REPO>") {
    pullRequest(number: <PR_NUMBER>) {
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

**Count unresolved** (must equal `0` before merging; checks overflow):

```bash
gh api graphql --raw-field 'query=query {
  repository(owner: "<OWNER>", name: "<REPO>") {
    pullRequest(number: <PR_NUMBER>) {
      reviewThreads(first: 100) { nodes { isResolved } pageInfo { hasNextPage } }
    }
  }
}' --jq '{unresolved: ([.data.repository.pullRequest.reviewThreads.nodes[]
  | select(.isResolved == false)] | length),
  overflow: .data.repository.pullRequest.reviewThreads.pageInfo.hasNextPage}'
```

Must return `{"unresolved": 0, "overflow": false}`. Non-zero `unresolved` or `overflow: true`
means threads remain.

## Review-Thread Mutations

| Operation | Correct | WRONG — do not use |
|---|---|---|
| Reply | `addPullRequestReviewThreadReply` | `addPullRequestReviewComment` (creates new comment, not a reply) |
| Resolve | `resolveReviewThread` | `resolvePullRequestReviewThread` (does not exist) |

Replace `<THREAD_ID>` and `<DATABASE_ID>` before running.

```bash
# Reply via GraphQL (use REST below for markdown/special characters)
gh api graphql --raw-field 'query=mutation {
  addPullRequestReviewThreadReply(
    input: {pullRequestReviewThreadId: "<THREAD_ID>", body: "reply text"}
  ) { comment { id body } }
}'

# Reply via REST (simpler for markdown and special characters)
gh api repos/<OWNER>/<REPO>/pulls/<PR_NUMBER>/comments/<DATABASE_ID>/replies -f body="reply text"

# Resolve
gh api graphql --raw-field 'query=mutation {
  resolveReviewThread(input: {threadId: "<THREAD_ID>"}) { thread { id isResolved } }
}'
```

Failure guide: stale `<THREAD_ID>` → re-fetch threads; permission error → `gh auth status`;
wrong mutation name → check table above.

## Heredoc Body Pattern

```bash
gh pr edit <PR_NUMBER> --body "$(cat <<'EOF'
body content here
EOF
)"
```

Same pattern for `gh pr create`, `gh pr comment`, `gh issue comment`. Never use `--body-file`.

## Related Skills

- **pr-standards** (git-standards) — PR creation guards, issue linking
