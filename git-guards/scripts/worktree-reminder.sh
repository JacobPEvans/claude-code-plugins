#!/bin/bash
# UserPromptSubmit hook - inject worktree reminder when on main branch
# Runs on every prompt submission, checks if cwd is on main branch,
# and if so, injects a systemMessage reminding Claude to create a worktree first.
#
# Note: UserPromptSubmit provides user_prompt on stdin but we don't need it.

# Single git call: returns worktree root (line 1) and branch name (line 2).
# Fails with exit 128 outside a git repo, producing no output.
# Uses read instead of mapfile for bash 3.x (macOS /bin/bash) compatibility.
_git_output=$(git rev-parse --show-toplevel --abbrev-ref HEAD 2>/dev/null) || { echo '{}'; exit 0; }

worktree_root=$(echo "$_git_output" | head -1)
current_branch=$(echo "$_git_output" | tail -1)

if [[ "$(basename "$worktree_root")" == "main" ]] || [[ "$current_branch" == "main" ]]; then
    cat <<'ENDJSON'
{
  "systemMessage": "WARNING: You are on the main branch. You MUST first run /refresh-repo on this repo to sync main from remote origin (skip over any worktree/branch removal errors but ensure main is fully pulled), then create a feature branch worktree using /superpowers:using-git-worktrees BEFORE making any changes. Do not read files for editing purposes or attempt any edits until you are in a worktree. This applies to ALL work — code changes, documentation, config files."
}
ENDJSON
else
    echo '{}'
fi
