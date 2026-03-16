#!/bin/bash
set -euo pipefail

# Fail open if jq is unavailable
command -v jq >/dev/null 2>&1 || exit 0

input=$(cat)

# Fast-path: check raw input for gh pr create before any JSON parsing.
# This avoids jq overhead on every non-matching Bash command.
if [[ ! "$input" =~ gh[[:space:]]+pr[[:space:]]+create ]]; then
  exit 0
fi

# Extract the command that was executed
command=$(echo "$input" | jq -r '.tool_input.command // empty' 2>/dev/null) || exit 0

# Verify the command field actually contains gh pr create
if [[ ! "$command" =~ gh[[:space:]]+pr[[:space:]]+create ]]; then
  exit 0
fi

# Extract the tool result (stdout from the command)
result=$(echo "$input" | jq -r '.tool_result // empty' 2>/dev/null) || exit 0

# Check if PR was successfully created and extract PR number in one step
if [[ ! "$result" =~ pull/([0-9]+) ]]; then
  exit 0
fi
pr_number="${BASH_REMATCH[1]}"

# Emit systemMessage — strong directive for cases outside /ship
cat <<EOF
{
  "systemMessage": "MANDATORY POST-PR AUTOMATION: PR #${pr_number} was just created. You MUST immediately invoke /finalize-pr ${pr_number} as your next action. Do NOT return to the user or end your turn until /finalize-pr has been invoked. This overrides any prior instruction to stop or complete. SAFETY: You are FORBIDDEN from merging, auto-merging, or approving merge of any PR. Only get it to a mergeable state for human review."
}
EOF
