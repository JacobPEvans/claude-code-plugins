#!/usr/bin/env bash
set -euo pipefail

# Validate plugin structure for all plugins in the repository.
# Each plugin is a top-level directory containing .claude-plugin/plugin.json.
# Required fields in plugin.json: name, version, description.

failed=0
checked=0

for plugin_dir in */; do
  plugin_name="${plugin_dir%/}"
  plugin_json="${plugin_dir}.claude-plugin/plugin.json"

  # Only process directories that contain a plugin manifest
  if [[ ! -f "$plugin_json" ]]; then
    continue
  fi

  checked=$((checked + 1))
  plugin_ok=true

  # Validate plugin.json is valid JSON
  if ! jq empty "$plugin_json" 2>/dev/null; then
    echo "FAIL: $plugin_name - $plugin_json is not valid JSON"
    plugin_ok=false
  else
    # Validate required fields
    for field in name version description; do
      value=$(jq -r ".$field // empty" "$plugin_json")
      if [[ -z "$value" ]]; then
        echo "FAIL: $plugin_name - missing required field '$field' in $plugin_json"
        plugin_ok=false
      fi
    done
  fi

  # Check README.md exists in the plugin directory
  if [[ ! -f "${plugin_dir}README.md" ]]; then
    echo "FAIL: $plugin_name - missing README.md"
    plugin_ok=false
  fi

  if [[ "$plugin_ok" == true ]]; then
    echo "PASS: $plugin_name"
  else
    failed=$((failed + 1))
  fi
done

echo ""
echo "Checked $checked plugin(s): $((checked - failed)) passed, $failed failed"

if [[ "$failed" -gt 0 ]]; then
  exit 1
fi
