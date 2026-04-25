#!/usr/bin/env bats
# Test suite for content-guards/scripts/validate-markdown.sh
#
# Tests the markdown validator hook behavior including:
# - File type filtering (non-markdown, missing, dotfiles)
# - Config resolution (project vs fallback)
# - Cross-repo editing scenarios
# - Unbound variable regression (PR #39, #40)
# - HOME boundary walk regression (TC9)
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
  run bash -c 'echo "{\"tool_input\":{\"file_path\":\"'"$FIXTURES"'/cross-repo-sim/feature/new-feature/README.md\"}}" | /bin/bash "$1"' _ "$SCRIPT"
  [ "$status" -eq 0 ]
  [[ ! "$output" =~ "unbound variable" ]]
}

@test "TC7: cross-repo editing finds config from file directory not CWD" {
  # Simulate being in a completely different directory (like ~/git/repo1)
  # while editing a file in ~/git/repo2/feature/branch/
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

@test "TC9: parent walk stops before HOME — does not pick up ~/.markdownlint* and OOM" {
  # Regression for: walk climbs past project root into $HOME, finds
  # ~/.markdownlint-cli2.jsonc (Nix home-manager symlink), cd $HOME, OOM.
  # Fix: $HOME and / are checked before config scan so user-level configs
  # are never treated as project configs.
  #
  # Strategy: put intentionally-broken JSON in fake $HOME/.markdownlint-cli2.jsonc.
  # If the walk incorrectly picks it up (old bug), markdownlint-cli2 fails to
  # parse it → script exits 2. If the fix is correct, the walk stops at $HOME,
  # falls back to the inline temp config, and the valid doc.md lints cleanly → exit 0.

  local fake_home
  fake_home=$(mktemp -d)
  # Ensure cleanup even on assertion failure
  trap 'rm -rf "$fake_home"' EXIT

  # Broken config that markdownlint-cli2 cannot parse — if picked up, causes failure
  printf 'NOT_VALID_JSON_OR_YAML -- TC9 HOME boundary sentinel' \
    > "$fake_home/.markdownlint-cli2.jsonc"

  # Project dir inside fake HOME: no .git, no .markdownlint*
  local project_dir="$fake_home/myproject"
  mkdir -p "$project_dir"
  printf '# Hello\n' > "$project_dir/doc.md"

  run env HOME="$fake_home" bash -c \
    'echo "{\"tool_input\":{\"file_path\":\"'"$project_dir/doc.md"'\"}}" | /bin/bash "$1"' \
    _ "$SCRIPT"

  # Correct: walk stopped at $HOME, used inline config, lint passed
  [ "$status" -eq 0 ]
}
