---
name: squash-merge-pr
description: >-
  Review and update PR title/description to match final changes, recommend merge
  strategy (squash vs rebase), and generate release-note-friendly commit message.
  Use after /finalize-pr reports ready, when preparing any PR for merge, or when
  you want to clean up PR metadata before merging. Handles single PR from argument
  or current branch.
argument-hint: "[PR_NUMBER]"
---

# Squash Merge PR

Reviews PR metadata after all checks pass, updates title/description to match final changes, and recommends merge strategy with release-note-friendly commit message.

## Workflow

### Step 1: Generate Full Diff

Compare PR branch to origin/main (ignore individual commit history):

```bash
git fetch origin main
git diff origin/main...HEAD
```

Analyze the complete changeset (not back-and-forth commits).

### Step 2: Update PR Title

Review current PR title:

```bash
gh pr view <PR> --json title --jq '.title'
```

Generate accurate title based on full diff:
- Use conventional commit format: `<type>: <description>`
- Types: feat, fix, refactor, docs, test, chore
- Keep concise (under 70 characters)
- Reflect the actual final changes

Update if needed:

```bash
gh pr edit <PR> --title "new title"
```

### Step 3: Update PR Description

Review current PR body:

```bash
gh pr view <PR> --json body --jq '.body'
```

Generate comprehensive description based on full diff:
- **Summary** section with 2-5 bullet points of key changes
- **Changes** section listing all major modifications
- **Breaking Changes** section (if applicable)
- **Test Plan** section with validation steps

Update if needed:

```bash
gh pr edit <PR> --body "$(cat <<'EOF'
## Summary
- Key change 1
- Key change 2

## Changes
...
EOF
)"
```

### Step 4: Recommend Merge Strategy

Analyze the changeset and recommend:

**Recommend squash merge** when:
- Single logical change (even if multiple commits)
- Commits contain back-and-forth fixes
- Work-in-progress commit messages
- Experimental changes that were refined

Provide release-note-friendly commit message:

```
<type>: <concise description>

<2-3 line explanation of what changed and why>
```

**Recommend `/rebase-pr`** when:
- Multiple distinct logical changes
- Clean, meaningful commit messages
- Each commit is independently valuable
- Preserving commit history adds context

### Step 5: Report Final Status

Report ready status with merge recommendation:

```
PR #XX is ready to merge!

Recommendation: Squash merge
Suggested commit message:
---
feat: add authentication system

Implements JWT-based authentication with refresh tokens,
secure password hashing, and role-based access control.
---

Command: gh pr merge <PR> --squash
```

The merge command requires explicit user execution. Pause and wait after reporting recommendation.

## Integration

Invoke manually after `/finalize-pr` reports ready:
```
/squash-merge-pr          # Current branch PR
/squash-merge-pr 42       # Specific PR number
```
