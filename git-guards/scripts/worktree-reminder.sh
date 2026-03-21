#!/bin/bash
# UserPromptSubmit hook - inject worktree reminder when on main branch
# Runs on every prompt submission, checks if cwd is on main branch,
# and if so, injects a systemMessage reminding Claude to create a worktree first.

set -euo pipefail

# Check if we're in a git repo
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo '{}'
    exit 0
fi

# Check if worktree directory is named "main" OR current branch is "main"
worktree_root=$(git rev-parse --show-toplevel 2>/dev/null || echo "")
current_branch=$(git branch --show-current 2>/dev/null || echo "")

if [[ "$(basename "$worktree_root")" == "main" ]] || [[ "$current_branch" == "main" ]]; then
    cat <<'ENDJSON'
{
  "systemMessage": "WARNING: You are on the main branch. You MUST first run /refresh-repo on this repo to sync main from remote origin (skip over any worktree/branch removal errors but ensure main is fully pulled), then run /init-worktree to create a feature branch worktree BEFORE making any changes. Do not read files for editing purposes or attempt any edits until you are in a worktree. This applies to ALL work — code changes, documentation, config files."
}
ENDJSON
else
    echo '{}'
fi
exit 0
