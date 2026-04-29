#!/bin/bash
# main-branch-guard.sh - PreToolUse hook to prevent Edit/Write/NotebookEdit on main branch
#
# Blocks file editing operations when the file is in a git repository on the main branch.
# Ignores files outside git repositories (like ~/.claude/plans/).
#
# Exit codes: 0=allow, 2=deny

set -euo pipefail

# Read JSON input from stdin and extract file path (handles both file_path and notebook_path)
file_path=$(jq -r '.tool_input.file_path // .tool_input.notebook_path // empty')

# If no file path found, allow operation (fail-open)
if [[ -z "$file_path" ]]; then
    exit 0
fi

# Get the directory containing the file
file_dir=$(dirname "$file_path")

# Check if the file is inside a git work tree (not a bare repo, not outside git).
# `git rev-parse --is-inside-work-tree` exits 0 even for directories adjacent
# to a bare repo — it prints "false" but the exit status is still 0 — so we
# must inspect the output, not just the exit code. Files outside git work
# trees (e.g. ~/.claude/plans/, or scratch dirs that sit next to a bare repo)
# are always allowed.
inside=$(cd "$file_dir" 2>/dev/null && git rev-parse --is-inside-work-tree 2>/dev/null || echo "false")
if [[ "$inside" != "true" ]]; then
    exit 0
fi

# Get worktree root from file's directory context
worktree_root=$(cd "$file_dir" && git rev-parse --show-toplevel 2>/dev/null || echo "")

# Check if worktree directory is named 'main'
if [[ -n "$worktree_root" ]] && [[ "$(basename "$worktree_root")" == "main" ]]; then
    jq -n --arg path "$file_path" '{
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "deny",
        permissionDecisionReason: ("BLOCKED: File '\''\($path)'\'' is in the main worktree. Editing files in the main worktree is not allowed.\n\nCreate a worktree using `/superpowers:using-git-worktrees`.")
      }
    }' >&2
    exit 2
fi

# Fallback: check current branch from file's directory
current_branch=$(cd "$file_dir" && git branch --show-current 2>/dev/null || echo "")

if [[ "$current_branch" == "main" ]]; then
    jq -n --arg path "$file_path" '{
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "deny",
        permissionDecisionReason: ("BLOCKED: File '\''\($path)'\'' is in the main worktree. Editing files in the main worktree is not allowed.\n\nCreate a worktree using `/superpowers:using-git-worktrees`.")
      }
    }' >&2
    exit 2
fi

# All checks passed, allow operation
exit 0
