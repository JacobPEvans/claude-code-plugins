---
name: gh-cli-patterns
description: >-
  Canonical reference for gh CLI command shapes used by skills in this plugin.
  Defines the placeholder convention, allowed --json fields, GraphQL fallback
  rules, -f/-F/--raw-field flag semantics, and the canonical PR-readiness gate.
  Prevents Unknown JSON field errors and divergent query shapes across skills.
---

# gh CLI Canonical Patterns — git-workflows

## Placeholder Convention

Two visually distinct notations — never mix them up:

| Notation | Meaning | Example |
|---|---|---|
| `$varName` | GraphQL variable name — **keep as literal text** in the query body | `$prNumber` |
| `<UPPER_NAME>` | Shell template — **replace before running** | `<PR_NUMBER>` |

Standard replacements:

```text
<OWNER>      → $(gh repo view --json owner --jq '.owner.login')
<REPO>       → $(gh repo view --json name  --jq '.name')
<PR_NUMBER>  → $(gh pr view  --json number --jq '.number')  (integer)
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
| Review thread resolution status | GraphQL — `gh api graphql` |
| Resolve a thread | GraphQL — `resolveReviewThread` mutation |
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

## Heredoc Body Pattern

```bash
gh pr edit <PR_NUMBER> --body "$(cat <<'EOF'
body content here
EOF
)"
```

Same pattern for `gh pr create`, `gh pr comment`, `gh issue comment`. Never use `--body-file`.

## Related Skills

- **gh-cli-patterns** (github-workflows) — extends this skill with code-scanning and mutation patterns
- **pr-standards** (git-standards) — PR creation guards, issue linking
