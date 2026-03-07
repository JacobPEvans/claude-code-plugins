#!/usr/bin/env bats
# Test suite for content-guards/scripts/validate-readme.py
#
# Tests file filtering, required section validation, and code block checking.
#
# Run with: bats tests/content-guards/readme-validator/validate-readme.bats

setup() {
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/../../.." && pwd)"
  SCRIPT="$REPO_ROOT/content-guards/scripts/validate-readme.py"
  FIXTURES="$(dirname "$BATS_TEST_FILENAME")/fixtures"

  if [[ ! -f "$SCRIPT" ]]; then
    echo "ERROR: Script not found at $SCRIPT" >&2
    return 1
  fi
}

run_hook() {
  run python3 "$SCRIPT" <<< "$1"
}

# ---------------------------------------------------------------------------
# TC1: Non-README files are skipped (exit 0, no output)
# ---------------------------------------------------------------------------

@test "TC1: CONTRIBUTING.md is skipped" {
  run_hook '{"tool_input":{"file_path":"/some/path/CONTRIBUTING.md"}}'
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "TC1b: Python source file is skipped" {
  run_hook '{"tool_input":{"file_path":"/some/path/main.py"}}'
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

# ---------------------------------------------------------------------------
# TC2: Invalid/missing input fails open (exit 0)
# ---------------------------------------------------------------------------

@test "TC2: invalid JSON input is allowed (fail open)" {
  run python3 "$SCRIPT" <<< "not valid json"
  [ "$status" -eq 0 ]
}

@test "TC2b: empty file_path is allowed" {
  run_hook '{"tool_input":{"file_path":""}}'
  [ "$status" -eq 0 ]
}

@test "TC2c: nonexistent README file is allowed (file not on disk)" {
  run_hook '{"tool_input":{"file_path":"/nonexistent/path/README.md"}}'
  [ "$status" -eq 0 ]
}

# ---------------------------------------------------------------------------
# TC3: Valid README with all required sections passes (exit 0)
# ---------------------------------------------------------------------------

@test "TC3: README with all required sections passes" {
  run_hook '{"tool_input":{"file_path":"'"$FIXTURES/README-valid.md"'"}}'
  [ "$status" -eq 0 ]
}

# ---------------------------------------------------------------------------
# TC4: README missing required sections is blocked (exit 2)
# ---------------------------------------------------------------------------

@test "TC4: README missing required sections is blocked" {
  run_hook '{"tool_input":{"file_path":"'"$FIXTURES/README-missing-sections.md"'"}}'
  [ "$status" -eq 2 ]
  [[ "$output" =~ "Missing required sections" ]]
}

# ---------------------------------------------------------------------------
# TC5: README with Installation section but no code block gives warning
# ---------------------------------------------------------------------------

@test "TC5: README with Installation but no code block warns but allows" {
  run_hook '{"tool_input":{"file_path":"'"$FIXTURES/README-no-install-code.md"'"}}'
  [ "$status" -eq 0 ]
  [[ "$output" =~ "code block" ]] || [[ "$output" =~ "code blocks" ]]
}

# ---------------------------------------------------------------------------
# TC6: README name pattern matching
# ---------------------------------------------------------------------------

@test "TC6: README-ADVANCED.md file name is matched (nonexistent file skipped)" {
  run_hook '{"tool_input":{"file_path":"/tmp/README-ADVANCED.md"}}'
  [ "$status" -eq 0 ]
}
