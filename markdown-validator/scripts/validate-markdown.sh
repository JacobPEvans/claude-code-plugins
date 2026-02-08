#!/bin/bash
# PostToolUse hook: Validate markdown files after Write/Edit operations
#
# This hook runs automatically after Write or Edit tool calls.
# It validates .md files with markdownlint-cli2 and cspell.
#
# Exit codes:
#   0 - Success (validation passed or not a markdown file)
#   2 - Blocking error (validation failed, stops Claude)

set -euo pipefail

# Extract the file path from stdin, which contains the hook input JSON
file_path=$(jq -r '.tool_input.file_path // empty')

# Exit silently if no file path
if [[ -z "$file_path" ]]; then
  exit 0
fi

# Only validate markdown files
if [[ ! "$file_path" =~ \.md$ ]]; then
  exit 0
fi

# Skip if file doesn't exist (might have been deleted)
if [[ ! -f "$file_path" ]]; then
  exit 0
fi

# Collect validation errors
errors=()

# Run markdownlint-cli2
if command -v markdownlint-cli2 &>/dev/null; then
  # Config resolution: project config > user home config > plugin default
  config_flag=()
  has_project_config=false

  # Walk up from the file's directory looking for project-level config
  search_dir="$(dirname -- "$file_path")"
  while true; do
    if [[ -f "$search_dir/.markdownlint-cli2.yaml" ]] ||
       [[ -f "$search_dir/.markdownlint-cli2.jsonc" ]] ||
       [[ -f "$search_dir/.markdownlint-cli2.cjs" ]] ||
       [[ -f "$search_dir/.markdownlint-cli2.mjs" ]] ||
       [[ -f "$search_dir/.markdownlint.json" ]] ||
       [[ -f "$search_dir/.markdownlint.jsonc" ]] ||
       [[ -f "$search_dir/.markdownlint.yaml" ]] ||
       [[ -f "$search_dir/.markdownlint.yml" ]] ||
       [[ -f "$search_dir/.markdownlint.cjs" ]] ||
       [[ -f "$search_dir/.markdownlint.mjs" ]]; then
      has_project_config=true
      break
    fi

    parent_dir="$(dirname -- "$search_dir")"
    if [[ "$parent_dir" == "$search_dir" ]]; then
      break
    fi
    search_dir="$parent_dir"
  done

  if [[ "$has_project_config" == "true" ]]; then
    # Let markdownlint-cli2 discover the project config naturally
    config_flag=()
  elif [[ -f "$HOME/.markdownlint-cli2.yaml" ]]; then
    config_flag=(--config "$HOME/.markdownlint-cli2.yaml")
  else
    config_flag=(--config "${CLAUDE_PLUGIN_ROOT}/config/.markdownlint-cli2.yaml")
  fi

  if ! markdownlint_output=$(markdownlint-cli2 "${config_flag[@]}" "$file_path" 2>&1); then
    errors+=("markdownlint-cli2 failed:")
    errors+=("$markdownlint_output")
  fi
fi

# Run cspell for spell checking
if command -v cspell &>/dev/null; then
  if ! cspell_output=$(cspell --no-progress "$file_path" 2>&1); then
    errors+=("cspell failed:")
    errors+=("$cspell_output")
  fi
fi

# Report errors if any
if [[ ${#errors[@]} -gt 0 ]]; then
  {
    echo "Markdown validation failed for: $file_path"
    echo ""
    printf '%s\n' "${errors[@]}"
    echo ""
    echo "Please fix these issues before continuing."
  } >&2
  exit 2
fi

exit 0
