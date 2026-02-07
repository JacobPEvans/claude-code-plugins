# git-workflows

Claude Code plugin for git worktree initialization, main branch synchronization, and repository refresh.

## Skills

- **`/init-worktree`** - Initialize a clean worktree for new development work with stale cleanup and branch naming
- **`/sync-main`** - Update main from remote and merge into current branch (or all open PR branches with `all`)
- **`/git-refresh`** - Check PR merge-readiness, sync local repo, and cleanup stale worktrees

## Installation

```bash
claude plugins add jacobpevans-cc-plugins/git-workflows
```

## Usage

```text
/init-worktree fix login bug
/sync-main
/sync-main all
/git-refresh
```

## License

MIT
