#!/bin/bash
# research-reminder.sh - UserPromptSubmit hook to remind about research-first approach
#
# When the user's prompt contains implementation keywords, injects a system message
# reminding to check for existing tools before creating new ones.
#
# Exit codes: 0 always (never blocks user prompts)

set -euo pipefail

# Read JSON input from stdin (fail-open if jq fails)
input=$(cat)
prompt=$(echo "$input" | jq -r '.tool_input.prompt // .tool_input.content // .prompt // .content // empty' 2>/dev/null) || exit 0

# If no prompt found, exit silently
if [[ -z "$prompt" ]]; then
    exit 0
fi

# Check for implementation keywords (case-insensitive via grep -i)
if echo "$prompt" | grep -qiwE 'create|write|build|implement|add|make|generate|automate|script|function|helper|utility|tool|wrapper'; then
    jq -n '{
        systemMessage: "Before implementing: check if a native tool, CLI, module, or existing function handles this. Use Context7 MCP for library docs. Check the direct-execution alternatives table. Script files are blocked by hooks unless placed in scripts/, hooks/, .github/, or tests/ directories."
    }'
fi

exit 0
