#!/bin/bash
# UserPromptSubmit hook — inject fresh-execution reminder on skill invocation.

input=$(cat)
prompt=$(jq -r '.tool_input.prompt // .tool_input.content // .prompt // .content // empty' <<< "$input" 2>/dev/null) || { printf '{}'; exit 0; }

[[ -z "$prompt" ]] && { printf '{}'; exit 0; }

if [[ "$prompt" =~ (^|[[:space:]])/([a-z][a-z0-9-]+)([^a-z0-9-]|$) ]]; then
    skill_name="${BASH_REMATCH[2]}"
    case "$skill_name" in
        usr|tmp|etc|var|bin|dev|opt|home|nix|proc|sys|run|lib|mnt|srv|boot|root|sbin) printf '{}'; exit 0 ;;
    esac
    jq -n --arg skill "$skill_name" '{
        systemMessage: ("FRESH EXECUTION: /" + $skill + " — Step 1 now. New invocation, new live state. All prior outputs in this session are stale. Re-run every git, gh, and API command.")
    }' || printf '{"systemMessage":"FRESH EXECUTION: /%s — Step 1 now. New invocation, new live state. All prior outputs in this session are stale. Re-run every git, gh, and API command."}' "$skill_name"
else
    printf '{}'
fi

exit 0
