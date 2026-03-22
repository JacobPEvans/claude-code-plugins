# git-workflows

Claude Code plugin for main branch synchronization, repository refresh, and PR merging. For worktree creation, use `superpowers:using-git-worktrees` guided by `.claude/rules/worktree-conventions.md`.

See [ARCHITECTURE.md](ARCHITECTURE.md) for integration diagrams.

## Skills

- **`/sync-main`** - Update main from remote and merge into current branch (or all open PR branches with `all`)
- **`/refresh-repo`** - Check PR merge-readiness, sync local repo, and cleanup stale worktrees
- **`/rebase-pr`** - Merge a PR using local git rebase + signed commits + push to main
- **`/wrap-up`** - Post-merge cleanup: refresh repo, quick retrospective, clean gone branches
- **`/troubleshoot-rebase`** - Diagnose and recover from git rebase failures
- **`/troubleshoot-precommit`** - Troubleshoot pre-commit hook failures and auto-fixes
- **`/troubleshoot-worktree`** - Troubleshoot git worktree, branch, and refname issues

## Installation

```bash
claude plugins add jacobpevans-cc-plugins/git-workflows
```

## Usage

```text
/sync-main
/sync-main all
/refresh-repo
/rebase-pr
/rebase-pr 42
/wrap-up                  # Post-merge cleanup + retrospective
```

## Dependencies

| Skill | Requires | Why |
|-------|----------|-----|
| `/wrap-up` | `claude-retrospective` plugin | Invokes `/retrospecting quick` for session retrospective |
| `/wrap-up` | `commit-commands` plugin | Invokes `/clean_gone` for branch cleanup |

## License

MIT
