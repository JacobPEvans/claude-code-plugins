---
name: squash-merge-pr
description: Review PR metadata and recommend merge strategy with release-note-friendly commit message
---

# Squash Merge PR

Reviews PR metadata after all checks pass, updates title/description to match final changes, and recommends merge strategy with release-note-friendly commit message.

## Scope

**SINGLE PR** - One PR at a time, from argument or current branch.

## When to Use

Invoke after all PR checks pass and before final merge:
- All CI checks green
- CodeQL clean
- Review threads resolved
- Code simplified

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

Example:
feat: add dark mode support

Implements dark mode with automatic theme switching based on system
preferences. Includes color scheme updates for all components and
persistent user preference storage.
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

## Output Format

```
✅ PR #{NUMBER} Ready to Merge

Metadata Review:
- Title: {updated/unchanged}
- Description: {updated/unchanged}

Merge Strategy: {Squash merge | Rebase merge}

Reasoning: {why this strategy was chosen}

Release-Note-Friendly Commit:
---
{type}: {description}

{explanation}
---

Execute: gh pr merge {NUMBER} --{squash|rebase}
```

## Integration

This skill is automatically invoked by `/finalize-pr` after all checks pass (Phase 4).

Can also be invoked manually:
```
/squash-merge-pr          # Current branch PR
/squash-merge-pr 42       # Specific PR number
```
