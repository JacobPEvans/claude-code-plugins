---
name: squash-merge-pr
description: >-
  Validate PR merge-readiness and squash merge into main. Errors if PR is not
  ready — use /finalize-pr first to fix issues. Use after /finalize-pr reports
  ready. Handles single PR from argument or current branch.
metadata:
  argument-hint: "[PR_NUMBER]"
---

# Squash Merge PR

Validates PR readiness and executes squash merge. If the PR is not ready,
errors immediately and suggests `/finalize-pr` to fix issues. Never fixes
issues — only merges.

> **State warning**: Branch state, remote tracking, and PR status change between
> invocations. Re-run all git/gh commands from Step 1.

## Critical Rules

- **Never fix issues** — only merge. If PR isn't ready, error and suggest `/finalize-pr`
- **Never update PR metadata** — that's `/finalize-pr`'s job
- **Never skip validation** — always run the GraphQL check before merging

## Step 1: Validate PR Ready

Run the **canonical PR-readiness gate** from `gh-cli-patterns` (this plugin) against
`<PR_NUMBER>`. Replace `<OWNER>`, `<REPO>`, `<PR_NUMBER>` per the placeholder convention.

If any check fails, abort immediately with the field's failure message and
append: `— run /finalize-pr to fix`.

| Field | Must be | Abort message |
|-------|---------|---------------|
| `state` | `OPEN` | "PR is not open — run `/finalize-pr` to fix" |
| `mergeable` | `MERGEABLE` | "PR has merge conflicts — run `/finalize-pr` to fix" |
| `mergeStateStatus` | `CLEAN` or `HAS_HOOKS` | "PR merge state is {value} — run `/finalize-pr` to fix" |
| `isDraft` | `false` | "PR is a draft — mark ready first, then run `/finalize-pr`" |
| `reviewDecision` | `APPROVED` or `null` | "PR needs approval — run `/finalize-pr` to fix" |
| `statusCheckRollup.state` | `SUCCESS` | "CI is not passing: {state} — run `/finalize-pr` to fix" |
| All `reviewThreads.isResolved` | `true` | "Unresolved review threads — run `/finalize-pr` to fix" |
| `reviewThreads.pageInfo.hasNextPage` | `false` | ">100 threads — paginate and re-verify" |

## Step 2: Generate Squash Commit Message

Analyze the full changeset to generate a release-note-friendly commit message.
Replace `<PR_NUMBER>` before running:

```bash
git fetch origin main
git diff origin/main...HEAD
git log --oneline origin/main..HEAD
```

Generate:

- **Title**: Conventional commit format (`<type>: <description>`, under 70 chars)
- **Body**: 2-3 line explanation of what changed and why

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`

Store the title in a shell variable:

```bash
SQUASH_TITLE="<generated title>"
```

## Step 3: Execute Squash Merge

Capture the branch name before merging (needed for cleanup). Replace `<PR_NUMBER>` before running:

```bash
BRANCH=$(gh pr view <PR_NUMBER> --json headRefName --jq '.headRefName')
```

Merge without `--delete-branch` (avoids `git switch` failure in bare+worktree repos).
Use the heredoc body pattern from `gh-cli-patterns` (this plugin):

```bash
gh pr merge <PR_NUMBER> --squash --subject "$SQUASH_TITLE" --body "$(cat <<'EOF'
... generated body ...
EOF
)"
```

Single-quoted `'EOF'` prevents shell expansion. Closing `EOF` must be alone on its own line with no leading whitespace.

Delete the remote branch (GitHub may have auto-deleted it on merge — `|| true` handles that):

```bash
git push origin --delete "$BRANCH" || true
```

Find and remove the local worktree by branch name (works in any repo layout):

```bash
WORKTREE_PATH=$(git worktree list --porcelain | awk -v b="refs/heads/$BRANCH" '/^worktree/{p=$2} $0=="branch "b{print p}')
[ -n "$WORKTREE_PATH" ] && git worktree remove "$WORKTREE_PATH" || true
```

Delete the local branch ref (safe no-op if absent):

```bash
git branch -d "$BRANCH" || true
```

## Step 4: Sync Main

```bash
git switch main
git pull origin main
git worktree prune
```

## Integration

Invoke after `/finalize-pr` reports ready:

```text
/squash-merge-pr          # Current branch PR
/squash-merge-pr 42       # Specific PR number
```

## Related Skills

- finalize-pr (github-workflows) — drives PR to mergeable state before squash-merge-pr is invoked
- rebase-pr (git-workflows) — alternative merge strategy that preserves commit history
- pr-standards (git-standards) — PR authoring and review standards
- gh-cli-patterns (github-workflows) — canonical gh CLI command shapes, placeholder convention, PR-readiness gate
