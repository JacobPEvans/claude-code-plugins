#!/bin/bash
set -euo pipefail

# Fail open if jq is unavailable
command -v jq >/dev/null 2>&1 || exit 0

input=$(cat)

# Extract the command that was executed
command=$(echo "$input" | jq -r '.tool_input.command // empty' 2>/dev/null) || exit 0

# Only trigger on gh pr create commands
if [[ ! "$command" =~ gh[[:space:]]+pr[[:space:]]+create ]]; then
  exit 0
fi

# Extract the tool result (stdout from the command)
result=$(echo "$input" | jq -r '.tool_result // empty' 2>/dev/null) || exit 0

# Check if PR was successfully created (output contains a PR URL)
if [[ ! "$result" =~ github\.com/.*/pull/[0-9]+ ]]; then
  exit 0
fi

# Extract PR number from URL
pr_number=$(echo "$result" | grep -oE 'pull/[0-9]+' | head -1 | cut -d/ -f2)

# Emit systemMessage — keep it referential (DRY), delegate details to the skill
cat <<EOF
{
  "systemMessage": "PR #${pr_number} created. Invoke /finalize-pr ${pr_number} now. The skill defines the complete workflow and stop conditions. SAFETY: You are FORBIDDEN from merging, auto-merging, or approving merge of any PR. Only get it to a mergeable state for human review."
}
EOF
