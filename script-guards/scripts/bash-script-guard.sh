#!/bin/bash
# bash-script-guard.sh - PreToolUse hook to prevent script creation via Bash tool
#
# Detects patterns where Bash is used to write script files (redirects, heredocs)
# and blocks them, directing to the Write tool instead.
#
# Exit codes: 0=allow, 2=deny

set -euo pipefail

# Read JSON input from stdin
input=$(cat)

# Extract command using jq (fail-open if jq fails)
command=$(echo "$input" | jq -r '.tool_input.command // empty' 2>/dev/null) || { exit 0; }

# If no command, allow
if [[ -z "$command" ]]; then
    exit 0
fi

# Check for file-writing patterns to script files
if echo "$command" | grep -qE '(cat|tee|echo|printf)\s+>>?\s+\S+\.(sh|py|rb|pl|js|bash)'; then
    jq -n '{
        hookSpecificOutput: {
            hookEventName: "PreToolUse",
            permissionDecision: "deny",
            permissionDecisionReason: "BLOCKED: Use the Write tool for file creation, not Bash redirects.\n\nThe Write tool provides proper file creation with atomic writes. Bash redirects to script files are not allowed."
        }
    }' >&2
    exit 2
fi

# Check for heredoc patterns (cat <<)
if echo "$command" | grep -qE 'cat\s+<<'; then
    jq -n '{
        hookSpecificOutput: {
            hookEventName: "PreToolUse",
            permissionDecision: "deny",
            permissionDecisionReason: "BLOCKED: Use the Write tool for file creation, not heredocs.\n\nThe Write tool provides proper file creation with atomic writes. Heredoc-based file creation via Bash is not allowed."
        }
    }' >&2
    exit 2
fi

# Check for chmod +x on non-existent files
if echo "$command" | grep -qE 'chmod\s+\+x\s+'; then
    # Extract the file path after chmod +x
    target_file=$(echo "$command" | grep -oE 'chmod\s+\+x\s+\S+' | head -1 | sed 's/chmod\s\+\+x\s\+//')
    if [[ -n "$target_file" ]] && [[ ! -f "$target_file" ]]; then
        jq -n '{
            hookSpecificOutput: {
                hookEventName: "PreToolUse",
                permissionDecision: "deny",
                permissionDecisionReason: "BLOCKED: Scripts must be placed in scripts/ directory.\n\nUse the Write tool to create scripts in the appropriate directory (scripts/, hooks/, .github/, or tests/)."
            }
        }' >&2
        exit 2
    fi
fi

# All checks passed, allow operation
exit 0
