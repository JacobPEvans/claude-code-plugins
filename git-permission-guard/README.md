# Git Permission Guard

A Claude Code plugin that provides centralized git and gh permission
management via PreToolUse hooks with detailed warning messages.

## Overview

This plugin replaces scattered permission rules with a single, intelligent
hook that:

- Parses git and gh commands to understand their intent
- Applies allow/ask/deny logic based on command risk level
- Provides detailed explanations for blocked commands
- Handles `git -C <path>` by analyzing the actual subcommand

## Installation

Add to your Claude Code settings:

```json
{
  "plugins": [
    "/path/to/git-permission-guard"
  ]
}
```

## Permission Categories

### DENY (Never Allowed)

Commands that bypass safety mechanisms are blocked with strong warnings:

| Pattern                        | Reason                      |
| ------------------------------ | --------------------------- |
| `git commit --no-verify / -n`  | Bypasses pre-commit hooks   |
| `git merge --no-verify`        | Bypasses merge hooks        |
| `git cherry-pick --no-verify`  | Bypasses commit hooks       |
| `git rebase --no-verify`       | Bypasses commit hooks       |
| `git config core.hooksPath`    | Changes hook directory      |
| `git -c core.hooksPath=...`    | Temporarily bypasses hooks  |
| `pre-commit uninstall`         | Removes pre-commit hooks    |
| `rm .git/hooks/*`              | Deletes hooks               |
| `chmod -x .git/hooks/`         | Disables hooks              |

### ASK (Require Confirmation)

Potentially dangerous commands are blocked with detailed warnings:

**Git Commands:**

| Command                    | Risk                                   |
| -------------------------- | -------------------------------------- |
| `git merge`                | Can create merge commits or conflicts  |
| `git reset`                | Can lose uncommitted work permanently  |
| `git restore`              | Can discard local changes              |
| `git rm`                   | Removes files from tree and index      |
| `git cherry-pick`          | Rewrites commit history                |
| `git worktree remove`      | Removes worktree directory             |
| `git gc`                   | May remove unreferenced objects        |
| `git prune`                | Removes unreferenced objects           |
| `git rebase`               | Rewrites commit history                |
| `git commit --amend`       | Rewrites the last commit               |
| `git push --force`         | Overwrites remote history              |
| `git push --force-w-lease` | Overwrites remote history              |
| `git clean`                | Removes untracked files permanently    |

**GitHub CLI Commands:**

| Command             | Risk                                        |
| ------------------- | ------------------------------------------- |
| `gh repo delete`    | Permanently deletes a repository            |
| `gh issue close`    | Closes issues (could be accidental)         |
| `gh pr close`       | Closes pull requests (could be accidental)  |
| `gh pr merge`       | Merges PR - ONLY when user requests         |
| `gh release delete` | Deletes releases permanently                |

### ALLOW (Safe Commands)

All other git/gh commands pass through silently:

- `git status`, `git log`, `git diff`, `git add`
- `git commit` (without `--no-verify`)
- `git push` (without `--force`)
- `git pull`, `git fetch`, `git branch`
- `git checkout`, `git switch`, `git stash`
- `git tag`, `git remote`, `git show`
- `git blame`, `git bisect`, `git reflog`
- `git worktree add`, `git worktree list`
- `gh pr list`, `gh issue list`, `gh repo view`
- `gh auth`, `gh api`, etc.

## Special Handling

### `git -C <path>` Commands

The hook intelligently handles `git -C <path>` by extracting the actual
subcommand:

```bash
git -C /some/path merge main    # Triggers ASK (same as "git merge")
git -C /some/path status        # Passes through (safe command)
git -C /path commit -n          # Triggers DENY (bypasses hooks)
```

### `git -c <key=value>` Commands

Configuration options are parsed to find the actual subcommand:

```bash
git -c user.name="Test" commit -m "msg"  # Passes through
git -c core.hooksPath=/dev/null commit   # Triggers DENY
```

## Warning Message Examples

### DENY Message

```text
======================================================================
BLOCKED: Prohibited Git Command
======================================================================

Command: git commit --no-verify

THIS COMMAND IS NEVER ALLOWED because it bypasses pre-commit hooks
that enforce code quality and security.

WHY THIS IS BLOCKED:
  - Pre-commit hooks catch security vulnerabilities
  - Hooks enforce consistent code formatting
  - Bypassing hooks violates development standards

WHAT TO DO INSTEAD:
  - Fix the issues that pre-commit hooks identify
  - Run: pre-commit run --all-files

======================================================================
```

### ASK Message

```text
======================================================================
CAUTION: Potentially Dangerous Git Command
======================================================================

Command: git reset --hard HEAD~1

RISK: Can permanently lose uncommitted work and rewrite local history

WHY THIS MATTERS:
  - Uncommitted changes may be discarded forever
  - Cannot be undone without reflog knowledge
  - May cause confusion if you forget what was lost

SAFER ALTERNATIVES:
  - git stash (saves changes temporarily)
  - git reset --soft (keeps changes staged)
  - git revert (preserves history)

To proceed, you must explicitly confirm this operation.
======================================================================
```

## Configuration

Configuration files are in the `config/` directory:

- `deny.json` - Patterns that are never allowed
- `ask.json` - Patterns requiring confirmation

### Adding Custom Rules

**To deny a command:**

```json
{
  "patterns": [
    {
      "match": "your-regex-pattern",
      "reason": "why this is blocked",
      "alternative": "what to do instead"
    }
  ]
}
```

**To require confirmation:**

```json
{
  "git": [
    {
      "cmd": "subcommand",
      "risk": "description of the risk",
      "safer": ["alternative 1", "alternative 2"]
    }
  ]
}
```

## Exit Codes

| Code             | Meaning | Behavior                       |
| ---------------- | ------- | ------------------------------ |
| 0 (no output)    | ALLOW   | Command executes normally      |
| 2 (with message) | BLOCK   | Command is blocked with warning|

## Testing

Test the hook manually:

```bash
# Should pass (exit 0, no output)
echo '{"tool_name":"Bash","tool_input":{"command":"git status"}}' \
  | python3 scripts/git-permission-guard.py

# Should block (exit 2, deny message)
echo '{"tool_name":"Bash","tool_input":{"command":"git commit -n"}}' \
  | python3 scripts/git-permission-guard.py

# Should block (exit 2, ask message)
echo '{"tool_name":"Bash","tool_input":{"command":"git reset --hard"}}' \
  | python3 scripts/git-permission-guard.py

# Should pass (non-git command)
echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}' \
  | python3 scripts/git-permission-guard.py
```

## License

MIT
