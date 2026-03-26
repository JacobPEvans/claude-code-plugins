#!/bin/bash
# research-reminder.sh - UserPromptSubmit hook to remind about research-first approach
#
# When the user's prompt contains implementation keywords, injects a system message
# reminding to check for existing tools before creating new ones.
#
# Exit codes: 0 always (never blocks user prompts)

set -euo pipefail

# Read JSON input from stdin
input=$(cat)

# Extract the user prompt (fail-open if jq fails)
prompt=$(echo "$input" | jq -r '.tool_input.prompt // .tool_input.content // .prompt // .content // empty' 2>/dev/null) || { exit 0; }

# If no prompt found, exit silently
if [[ -z "$prompt" ]]; then
    exit 0
fi

# Check for implementation keywords (case-insensitive)
prompt_lower=$(echo "$prompt" | tr '[:upper:]' '[:lower:]')

keywords="create write build implement add make generate automate script function helper utility tool wrapper"
found=false
for keyword in $keywords; do
    if echo "$prompt_lower" | grep -qw "$keyword"; then
        found=true
        break
    fi
done

if [[ "$found" == true ]]; then
    jq -n '{
        systemMessage: "Before implementing: check if a native tool, CLI, module, or existing function handles this. Use Context7 MCP for library docs. Check the direct-execution alternatives table. Script files are blocked by hooks unless placed in scripts/, hooks/, .github/, or tests/ directories."
    }'
fi

exit 0
