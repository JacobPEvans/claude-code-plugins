#!/usr/bin/env bats
# Test suite for content-guards/scripts/validate-markdown.sh
#
# Tests the markdown validator hook behavior including:
# - File type filtering (non-markdown, missing, dotfiles)
# - Config resolution (project vs fallback)
# - Cross-repo editing scenarios
# - Unbound variable regression (PR #39, #40)
#
# Run with: bats tests/content-guards/markdown-validator/validate-markdown.bats

setup() {
  # Path to the script under test (relative to repo root)
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/../../.." && pwd)"
  SCRIPT="$REPO_ROOT/content-guards/scripts/validate-markdown.sh"
  FIXTURES="$(dirname "$BATS_TEST_FILENAME")/fixtures"

  # Verify script exists
  if [[ ! -f "$SCRIPT" ]]; then
    echo "ERROR: Script not found at $SCRIPT" >&2
    return 1
  fi
}

@test "TC1: non-markdown file is skipped" {
  run bash -c 'echo "{\"tool_input\":{\"file_path\":\"test.py\"}}" | /bin/bash "$1"' _ "$SCRIPT"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "TC2: missing file is skipped" {
  run bash -c 'echo "{\"tool_input\":{\"file_path\":\"/nonexistent/file.md\"}}" | /bin/bash "$1"' _ "$SCRIPT"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "TC3: home dotfile is skipped" {
  run bash -c 'echo "{\"tool_input\":{\"file_path\":\"~/.config/foo.md\"}}" | /bin/bash "$1"' _ "$SCRIPT"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "TC4: .claude directory file is skipped" {
  run bash -c 'echo "{\"tool_input\":{\"file_path\":\"/path/to/.claude/foo.md\"}}" | /bin/bash "$1"' _ "$SCRIPT"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "TC5: empty config_flag with project config does not cause unbound variable" {
  run bash -c 'echo "{\"tool_input\":{\"file_path\":\"'"$FIXTURES"'/project-with-config/doc.md\"}}" | /bin/bash "$1"' _ "$SCRIPT"
  [ "$status" -eq 0 ]
  [[ ! "$output" =~ "unbound variable" ]]
}

@test "TC6: non-empty config_flag with fallback config" {
  # File without ancestor config should use fallback (temp config or plugin default)
  run bash -c 'echo "{\"tool_input\":{\"file_path\":\"'"$FIXTURES"'/cross-repo-sim/feat/new-feature/README.md\"}}" | /bin/bash "$1"' _ "$SCRIPT"
  [ "$status" -eq 0 ]
  [[ ! "$output" =~ "unbound variable" ]]
}

@test "TC7: cross-repo editing finds config from file directory not CWD" {
  # Simulate being in a completely different directory (like ~/git/repo1)
  # while editing a file in ~/git/repo2/feat/branch/
  original_dir=$(pwd)
  cd /tmp

  run bash -c 'echo "{\"tool_input\":{\"file_path\":\"'"$FIXTURES"'/project-with-config/doc.md\"}}" | /bin/bash "$1"' _ "$SCRIPT"

  # Restore original directory
  cd "$original_dir"

  [ "$status" -eq 0 ]
  [[ ! "$output" =~ "unbound variable" ]]
}

@test "TC8: empty JSON input is handled gracefully" {
  run bash -c 'echo "{}" | /bin/bash "$1"' _ "$SCRIPT"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}
