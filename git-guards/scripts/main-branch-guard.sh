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

# Check if the file is tracked within a git repository.
# This correctly handles untracked files and non-repo directories.
if ! (cd "$file_dir" 2>/dev/null && git ls-files --error-unmatch "$(basename "$file_path")" >/dev/null 2>&1); then
    # Not in a git repo OR file is not tracked. Allow operation.
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
        permissionDecisionReason: ("BLOCKED: File '\''\($path)'\'' is in the main worktree. Editing files on the main branch is not allowed.\n\nRun `/init-worktree` to create a feature branch.")
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
        permissionDecisionReason: ("BLOCKED: Current branch is '\''main'\''. Editing files on the main branch is not allowed.\n\nRun `/init-worktree` to create a feature branch.")
      }
    }' >&2
    exit 2
fi

# All checks passed, allow operation
exit 0
