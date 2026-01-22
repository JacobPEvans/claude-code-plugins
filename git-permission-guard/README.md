# Git Permission Guard

PreToolUse hook that blocks dangerous git/gh commands with early exit
optimization for non-git commands.

## Installation

```bash
claude plugins add jacobpevans-cc-plugins/git-permission-guard
```

## How It Works

1. **Early exit** - Non-git/gh commands exit immediately (most Bash calls)
2. **DENY** - Commands bypassing safety are always blocked
3. **ASK** - Dangerous commands require user confirmation
4. **ALLOW** - Safe commands pass through silently

## Blocked Commands (DENY)

| Pattern                       | Reason                     |
| ----------------------------- | -------------------------- |
| `git commit --no-verify / -n` | Bypasses pre-commit hooks  |
| `git merge --no-verify`       | Bypasses merge hooks       |
| `git rebase --no-verify`      | Bypasses commit hooks      |
| `git config core.hooksPath`   | Changes hook directory     |
| `pre-commit uninstall`        | Removes pre-commit hooks   |
| `rm .git/hooks/*`             | Deletes git hooks          |

## Confirmation Required (ASK)

**Git:**

- `merge` - Can create conflicts
- `reset` - Can lose uncommitted work
- `restore` - Can discard changes
- `rm` - Removes from tree and index
- `cherry-pick`, `rebase` - Rewrites history
- `commit --amend` - Rewrites last commit
- `push --force`, `push --force-with-lease` - Overwrites remote
- `clean` - Removes untracked files
- `gc`, `prune` - May remove objects
- `worktree remove` - Removes worktree

**GitHub CLI:**

- `repo delete` - Permanently deletes repo
- `issue close` - Closes issues
- `pr close` - Closes pull requests
- `pr merge` - **ONLY when user EXPLICITLY requests**
- `release delete` - Deletes releases

## Special Handling

`git -C <path>` and `git -c <key=value>` are parsed to extract the actual
subcommand. `git -C /path merge` triggers the same rules as `git merge`.

## Structure

```text
git-permission-guard/
├── .claude-plugin/plugin.json
├── hooks/hooks.json
├── scripts/git-permission-guard.py
└── README.md
```

## Sources

- [Claude Code Hooks Reference](https://docs.anthropic.com/en/docs/claude-code/hooks)
