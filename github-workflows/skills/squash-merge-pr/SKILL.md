---
name: squash-merge-pr
description: >-
  Validate PR merge-readiness and squash merge into main. Errors if PR is not
  ready — use /finalize-pr first to fix issues. Use after /finalize-pr reports
  ready. Handles single PR from argument or current branch.
argument-hint: "[PR_NUMBER]"
---

# Squash Merge PR

Validates PR readiness and executes squash merge. If the PR is not ready,
errors immediately and suggests `/finalize-pr` to fix issues. Never fixes
issues — only merges.

## Critical Rules

- **Never fix issues** — only merge. If PR isn't ready, error and suggest `/finalize-pr`
- **Never update PR metadata** — that's `/finalize-pr`'s job
- **Never skip validation** — always run the GraphQL check before merging

## Step 1: Validate PR Ready

Read `@git-workflows/skills/rebase-pr/SKILL.md` Step 1 — use its GraphQL query,
fields, and abort conditions as the single source of truth.

If any check fails, abort immediately with the field's failure message and
append: `— run /finalize-pr to fix`.

## Step 2: Generate Squash Commit Message

Analyze the full changeset to generate a release-note-friendly commit message:

```bash
git fetch origin main
git diff origin/main...HEAD
git log --oneline origin/main..HEAD
```

Generate:

- **Title**: Conventional commit format (`<type>: <description>`, under 70 chars)
- **Body**: 2-3 line explanation of what changed and why

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`

## Step 3: Execute Squash Merge

```bash
gh pr merge <PR> --squash --subject "<title>" --body "<body>"
```

## Step 4: Cleanup

Delete local branch if it exists and sync main:

```bash
git branch -d <branch> 2>/dev/null || true
git fetch origin main
git pull origin main
```

## Integration

Invoke after `/finalize-pr` reports ready:

```text
/squash-merge-pr          # Current branch PR
/squash-merge-pr 42       # Specific PR number
```
