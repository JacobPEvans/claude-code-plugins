# git-workflows

Claude Code plugin for git worktree initialization, main branch synchronization, repository refresh, and PR merging.

## Skills

- **`/init-worktree`** - Initialize a clean worktree for new development work with stale cleanup and branch naming
- **`/sync-main`** - Update main from remote and merge into current branch (or all open PR branches with `all`)
- **`/refresh-repo`** - Check PR merge-readiness, sync local repo, and cleanup stale worktrees
- **`/rebase-pr`** - Merge a PR using local git rebase + signed commits + push to main
- **`/troubleshoot-rebase`** - Diagnose and recover from git rebase failures
- **`/troubleshoot-precommit`** - Troubleshoot pre-commit hook failures and auto-fixes
- **`/troubleshoot-worktree`** - Troubleshoot git worktree, branch, and refname issues

## Installation

```bash
claude plugins add jacobpevans-cc-plugins/git-workflows
```

## Usage

```text
/init-worktree fix login bug
/sync-main
/sync-main all
/refresh-repo
/rebase-pr
/rebase-pr 42
```

## License

MIT
