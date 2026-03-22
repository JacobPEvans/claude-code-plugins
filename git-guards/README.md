# git-guards

Git security and workflow protection via PreToolUse hooks.

See [ARCHITECTURE.md](ARCHITECTURE.md) for integration diagrams.

## Features

- **git-permission-guard**: Blocks dangerous git/gh commands (force push, hard reset, destructive operations)
- **main-branch-guard**: Prevents file edits on main branch (enforces worktree workflow)

## Usage

No manual invocation required. All three hooks activate automatically:

- **worktree-reminder** — fires on every user prompt, reminds if not in a worktree
- **git-permission-guard** — fires on every Bash call, blocks dangerous git/gh commands
- **main-branch-guard** — fires on every file edit, blocks edits on main branch

## Installation

```bash
claude plugins add jacobpevans-cc-plugins/git-guards
```

## License

Apache-2.0
