#!/usr/bin/env bash
set -euo pipefail

# Validate marketplace.json consistency.
# Checks that .claude-plugin/marketplace.json is valid JSON, that every plugin
# it references exists as a directory, and that versions match individual
# plugin.json files.

MARKETPLACE=".claude-plugin/marketplace.json"

if [[ ! -f "$MARKETPLACE" ]]; then
  echo "No marketplace.json found at $MARKETPLACE - skipping"
  exit 0
fi

# Validate marketplace.json is valid JSON
if ! jq empty "$MARKETPLACE" 2>/dev/null; then
  echo "FAIL: $MARKETPLACE is not valid JSON"
  exit 1
fi
echo "PASS: $MARKETPLACE is valid JSON"

failed=0
checked=0

# Iterate over each plugin entry in marketplace.json
plugin_count=$(jq '.plugins | length' "$MARKETPLACE")

for i in $(seq 0 $((plugin_count - 1))); do
  mp_name=$(jq -r ".plugins[$i].name" "$MARKETPLACE")
  mp_source=$(jq -r ".plugins[$i].source" "$MARKETPLACE")
  mp_version=$(jq -r ".plugins[$i].version" "$MARKETPLACE")

  checked=$((checked + 1))
  entry_ok=true

  # Resolve source path (strip leading ./)
  source_dir="${mp_source#./}"

  # Check that the referenced plugin directory exists
  if [[ ! -d "$source_dir" ]]; then
    echo "FAIL: marketplace plugin '$mp_name' references non-existent directory '$source_dir'"
    entry_ok=false
  else
    # Check that the plugin directory has a plugin.json
    plugin_json="${source_dir}/.claude-plugin/plugin.json"
    if [[ ! -f "$plugin_json" ]]; then
      echo "FAIL: marketplace plugin '$mp_name' - missing $plugin_json"
      entry_ok=false
    else
      # Validate version consistency
      local_version=$(jq -r '.version // empty' "$plugin_json")
      if [[ -n "$local_version" && "$local_version" != "$mp_version" ]]; then
        echo "FAIL: marketplace plugin '$mp_name' version mismatch - marketplace: $mp_version, plugin.json: $local_version"
        entry_ok=false
      fi

      # Validate name consistency
      local_name=$(jq -r '.name // empty' "$plugin_json")
      if [[ -n "$local_name" && "$local_name" != "$mp_name" ]]; then
        echo "FAIL: marketplace plugin '$mp_name' name mismatch - marketplace: $mp_name, plugin.json: $local_name"
        entry_ok=false
      fi
    fi
  fi

  if [[ "$entry_ok" == true ]]; then
    echo "PASS: marketplace plugin '$mp_name'"
  else
    failed=$((failed + 1))
  fi
done

echo ""
echo "Checked $checked marketplace plugin(s): $((checked - failed)) passed, $failed failed"

if [[ "$failed" -gt 0 ]]; then
  exit 1
fi
