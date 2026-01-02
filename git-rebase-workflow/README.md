# git-rebase-workflow

Claude Code plugin providing a local rebase-merge workflow for maintaining linear git history.

## Overview

This plugin provides the `/rebase-pr` command for merging PRs using a local rebase workflow. Unlike `gh pr merge`, this approach:

- Maintains completely linear history (no merge commits)
- Keeps control local (no GitHub merge button)
- Ensures clean rebases before merging
- Automatically syncs main before merge
- Preserves commit signatures throughout the merge process

**Bonus**: The plugin also provides canonical merge-readiness criteria used by other commands like `/ready-player-one` and `/git-refresh`.

## Installation

### From Marketplace

```bash
claude plugins add jacobpevans-cc-plugins/git-rebase-workflow
```

### Local Development

```bash
git clone https://github.com/JacobPEvans/claude-code-plugins.git
cd claude-code-plugins
claude plugins link ./git-rebase-workflow
```

## Commands

### `/rebase-pr`

Merge the current feature branch into main using a local rebase workflow:

1. **Validates PR is ready**: Checks that PR is open, mergeable, CI passes, all review threads resolved, and approved
2. **Syncs local main**: Fetches and pulls latest from origin/main
3. **Rebases feature branch**: Rebases current branch onto main (handles conflicts intelligently)
4. **Fast-forward merges**: Merges rebased branch into main using `--ff-only`
5. **Pushes to origin/main**: Pushes updated main (auto-closes PR)
6. **Cleans up**: Deletes local branch, remote branch, and worktree

**Usage**:

```bash
/rebase-pr
```

**Prerequisites**:

- Current branch must have an associated open PR
- All CI checks must pass
- All review threads must be resolved
- PR must be approved (or review not required)
- No merge conflicts with main

## Skills

### Git Rebase Workflow for Pull Requests

The canonical skill for merging PRs with signed commits:

- **PR merge-readiness validation** - Defines authoritative criteria for when a PR is ready to merge
- **Local rebase workflow** - Step-by-step process for rebasing pull requests onto main and pushing with signatures
- **Commit signing preservation** - Ensures all commits retain signatures (why we can't use `gh pr merge`)
- **Edge case handling** - Comprehensive coverage of conflicts, CI failures, approval issues, etc.

**Referenced by**:

- `/rebase-pr` - Primary consumer
- `/ready-player-one` - Uses merge-readiness criteria
- `/git-refresh` - References merge-readiness criteria and workflow

See [skills/git-rebase/SKILL.md](skills/git-rebase/SKILL.md) for full documentation.

## Why Local Rebase?

### vs `gh pr merge`

| Feature | `/rebase-pr` (this plugin) | `gh pr merge` |
| ------- | ------------------------------ | ------------- |
| History | Completely linear | Merge commit (squash optional) |
| Control | Local validation and execution | GitHub API handles merge |
| Conflict handling | Manual resolution before merge | GitHub blocks if conflicts |
| Worktree cleanup | Automatic | Manual |
| Commit signatures | Preserved throughout | Not supported |

### vs Manual Rebase

| Feature | `/rebase-pr` (this plugin) | Manual rebase |
| ------- | ------------------------------ | ------------- |
| PR validation | Automatic (CI, reviews, threads) | Manual checks |
| Main sync | Automatic | Remember to pull |
| Fast-forward check | Automatic with clear errors | Easy to miss |
| Cleanup | Automatic | Remember all steps |

## When NOT to Use

- When you need merge commits for audit trail
- When multiple people are pushing to your PR branch
- When the repository doesn't require commit signatures
- When you're not using worktree-based development

## Requirements

- `gh` CLI authenticated with repo access (for PR status queries only, NOT for merging)
- Git configured with commit signing (required for most repositories)
- Worktree-based repository structure (see `/init-worktree`)

**Note**: We use `gh` only for querying PR status via GraphQL. All merge operations use local `git` commands to preserve commit signatures.

## Merge-Readiness Criteria

This plugin defines the **canonical merge-readiness criteria** used across multiple commands.

A PR is **READY TO MERGE** when ALL of:

1. `state == "OPEN"`
2. `mergeable == "MERGEABLE"` (no conflicts)
3. `statusCheckRollup.state == "SUCCESS"` (all CI passes)
4. All `reviewThreads` have `isResolved == true`
5. `reviewDecision == "APPROVED"` or `null` (no review required)

A PR is **BLOCKED** when ANY of:

- `mergeable == "CONFLICTING"` → "merge conflicts"
- `statusCheckRollup.state != "SUCCESS"` → "CI failing: {checks}"
- Unresolved threads exist → "unresolved review comments"
- `reviewDecision == "CHANGES_REQUESTED"` → "changes requested"

## Examples

### Successful Merge

```bash
$ /rebase-pr

## Git Rebase PR Complete

PR: #123 - Add new feature
Branch: feat/new-feature
Method: Local rebase + fast-forward push with signed commits

### Actions Taken

1. ✅ Validated PR: OPEN, MERGEABLE, CI SUCCESS, APPROVED
2. ✅ Synced main: abc1234 → def5678
3. ✅ Rebased branch: 3 commit(s)
4. ✅ Fast-forward merged to main
5. ✅ Pushed to origin/main (signatures preserved)
6. ✅ PR auto-closed by GitHub

### Cleanup

- Deleted local branch: feat/new-feature
- Deleted remote branch: origin/feat/new-feature
- Removed worktree: ~/git/repo/feat/new-feature

### Result

Main branch now at: def5678
Linear history preserved with signed commits ✨
```

### Blocked by Unresolved Review Threads

```bash
$ /rebase-pr

❌ Cannot merge: PR has 2 unresolved review threads.
Use /resolve-pr-review-thread first to address all feedback.
```

### Blocked by Failing CI

```bash
$ /rebase-pr

❌ Cannot merge: PR CI checks are failing.
Fix CI issues first using /fix-pr-ci
```

## Contributing

See the main repository [Contributing Guidelines](../../README.md#contributing) for details.

General guidelines:

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Follow conventional commits: `feat(plugin): description`
4. Sign your commits (GPG required)
5. Submit a pull request

## License

MIT
