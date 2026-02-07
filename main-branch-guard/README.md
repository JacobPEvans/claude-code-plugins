# Main Branch Guard

PreToolUse hook that blocks file editing operations when working on the main branch or
in the main worktree.

## Installation

```bash
claude plugins add jacobpevans-cc-plugins/main-branch-guard
```

## How It Works

The hook performs two checks before allowing editing:

1. **Path Check** - Determines if the file path is in a main branch worktree (path
   contains `/main/`)
2. **Git Branch Check** - Verifies the current git branch is not `main`

If either check indicates you're on main, the operation is blocked with a clear error
message.

## Fail-Open Behavior

If git commands are unavailable or directory traversal fails, the hook allows the
operation to proceed. This ensures development isn't blocked when git tools are
inaccessible.

## Structure

```text
main-branch-guard/
├── .claude-plugin/plugin.json
├── hooks/hooks.json
├── scripts/main-branch-guard.py
└── README.md
```

## License

MIT
