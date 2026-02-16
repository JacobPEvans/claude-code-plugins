#!/usr/bin/env bash
set -euo pipefail

# Shared test runner for Claude Code plugins
# Usage:
#   ./scripts/run-tests.sh              # Run all tests
#   ./scripts/run-tests.sh content-guards  # Run tests for specific plugin

PLUGIN_DIR="${1:-}"

find_paths=()
if [[ -n "$PLUGIN_DIR" ]]; then
  # Validate plugin directory exists
  if [[ ! -d "$PLUGIN_DIR" ]]; then
    echo "Error: Plugin directory '$PLUGIN_DIR' does not exist" >&2
    exit 1
  fi
  if [[ -d "$PLUGIN_DIR/tests" ]]; then
    find_paths+=("$PLUGIN_DIR/tests")
  fi
else
  # Find all test files
  for d in */; do
    if [[ -d "${d}tests" ]]; then
      find_paths+=("${d}tests")
    fi
  done
fi

# Collect test files (Bash 3.2 compatible - no mapfile)
test_files=()
if [[ ${#find_paths[@]} -gt 0 ]]; then
  while IFS= read -r file; do
    test_files+=("$file")
  done < <(find "${find_paths[@]}" -name '*.bats' -type f 2>/dev/null)
fi

# Exit gracefully if no tests found
if [[ ${#test_files[@]} -eq 0 ]]; then
  echo "No test files found"
  exit 0
fi

# Run bats tests
echo "Running ${#test_files[@]} test file(s)..."
bats "${test_files[@]}"
