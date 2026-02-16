#!/usr/bin/env bash
set -euo pipefail

# Shared test runner for Claude Code plugins
# Usage:
#   ./scripts/run-tests.sh              # Run all tests
#   ./scripts/run-tests.sh content-guards  # Run tests for specific plugin

PLUGIN_DIR="${1:-}"

if [[ -n "$PLUGIN_DIR" ]]; then
  # Validate plugin directory exists
  if [[ ! -d "$PLUGIN_DIR" ]]; then
    echo "Error: Plugin directory '$PLUGIN_DIR' does not exist" >&2
    exit 1
  fi

  # Find tests for specific plugin
  test_pattern="$PLUGIN_DIR/tests/**/*.bats"
else
  # Find all test files
  test_pattern="*/tests/**/*.bats"
fi

# Collect test files (Bash 3.2 compatible - no mapfile)
test_files=()
while IFS= read -r file; do
  test_files+=("$file")
done < <(find . -path "$test_pattern" -type f 2>/dev/null)

# Exit gracefully if no tests found
if [[ ${#test_files[@]} -eq 0 ]]; then
  echo "No test files found"
  exit 0
fi

# Run bats tests
echo "Running ${#test_files[@]} test file(s)..."
bats "${test_files[@]}"
