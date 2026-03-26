#!/bin/bash
# inline-script-guard.sh - PreToolUse hook to prevent inline scripts in .nix and .yml files
#
# Detects complex inline shell logic in Nix files and GitHub Actions workflows,
# enforcing extraction to separate script files.
#
# Exit codes: 0=allow, 2=deny

set -euo pipefail

# Read JSON input from stdin
input=$(cat)

# Extract file_path and new_string using jq (fail-open if jq fails)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty' 2>/dev/null) || { exit 0; }
new_string=$(echo "$input" | jq -r '.tool_input.new_string // empty' 2>/dev/null) || { exit 0; }

# If no file path or no new content, allow
if [[ -z "$file_path" ]] || [[ -z "$new_string" ]]; then
    exit 0
fi

# Extract file extension (lowercase)
extension="${file_path##*.}"
extension=$(echo "$extension" | tr '[:upper:]' '[:lower:]')

# --- Check .nix files for inline shell scripts ---
if [[ "$extension" == "nix" ]]; then
    # Count lines containing shell keywords
    shell_keyword_count=0
    while IFS= read -r line; do
        if echo "$line" | grep -qE '\b(if|then|else|fi|for|while|do|done|case|esac)\b|&&|\|\||[^|]\|[^|]'; then
            shell_keyword_count=$((shell_keyword_count + 1))
        fi
    done <<< "$new_string"

    if [[ "$shell_keyword_count" -gt 3 ]]; then
        jq -n --arg fp "$file_path" '{
            hookSpecificOutput: {
                hookEventName: "PreToolUse",
                permissionDecision: "deny",
                permissionDecisionReason: ("BLOCKED: Inline script detected in Nix file \(.fp).\n\nExtract to scripts/ directory and reference via builtins.readFile or writeShellApplication.\n\nShell scripts must NEVER be inline in .nix files. Use separate files in scripts/ with proper extensions.")
            }
        }' >&2
        exit 2
    fi
fi

# --- Check .yml/.yaml files for complex inline bash ---
if [[ "$extension" == "yml" ]] || [[ "$extension" == "yaml" ]]; then
    # Check for multiline run blocks (run: | or run: >)
    if echo "$new_string" | grep -qE 'run:\s*[|>]'; then
        # Count lines after the run: | or run: > marker
        run_block_lines=$(echo "$new_string" | sed -n '/run:\s*[|>]/,/^[^ ]/p' | wc -l)

        if [[ "$run_block_lines" -gt 5 ]]; then
            jq -n --arg fp "$file_path" '{
                hookSpecificOutput: {
                    hookEventName: "PreToolUse",
                    permissionDecision: "deny",
                    permissionDecisionReason: ("BLOCKED: Complex inline bash in workflow YAML \(.fp).\n\nExtract to .github/scripts/ or scripts/ and call from the workflow step.\n\nNever embed complex bash logic inline in GitHub Actions workflow YAML.")
                }
            }' >&2
            exit 2
        fi
    fi
fi

# All checks passed, allow operation
exit 0
