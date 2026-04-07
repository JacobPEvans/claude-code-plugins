#!/usr/bin/env bats
# Test suite for skill-guards/scripts/skill-reinvocation-guard.sh
#
# Tests the UserPromptSubmit hook's skill detection and systemMessage injection:
#   - No skill in prompt → empty JSON, exit 0
#   - /ship → systemMessage with "FRESH EXECUTION" and skill name
#   - /finalize-pr 42 → systemMessage with skill name
#   - Regular text → empty JSON, exit 0
#   - Filesystem path /usr/bin → empty JSON (false positive exclusion)
#   - Empty prompt → empty JSON, exit 0
#
# Run with: bats tests/skill-guards/skill-reinvocation-guard/skill-reinvocation-guard.bats

setup() {
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/../../.." && pwd)"
  SCRIPT="$REPO_ROOT/skill-guards/scripts/skill-reinvocation-guard.sh"

  if [[ ! -f "$SCRIPT" ]]; then
    echo "ERROR: Script not found at $SCRIPT" >&2
    return 1
  fi
}

# Run the hook with a given prompt string
run_hook_with_prompt() {
  local prompt="$1"
  run bash -c "echo '{\"tool_input\":{\"prompt\":\"$prompt\"}}' | /bin/bash '$SCRIPT'"
}

# ---------------------------------------------------------------------------
# TC1: No skill invocation → empty JSON, exit 0
# ---------------------------------------------------------------------------

@test "TC1: prompt without skill outputs empty JSON" {
  run_hook_with_prompt "help me fix this bug"
  [ "$status" -eq 0 ]
  [[ "$output" == "{}" ]]
}

# ---------------------------------------------------------------------------
# TC2: /ship → systemMessage with FRESH EXECUTION and skill name
# ---------------------------------------------------------------------------

@test "TC2: /ship triggers fresh execution message" {
  run_hook_with_prompt "/ship"
  [ "$status" -eq 0 ]
  [[ "$output" =~ "systemMessage" ]]
  [[ "$output" =~ "FRESH EXECUTION" ]]
  [[ "$output" =~ "ship" ]]
}

# ---------------------------------------------------------------------------
# TC3: /finalize-pr 42 → systemMessage with skill name
# ---------------------------------------------------------------------------

@test "TC3: /finalize-pr with argument triggers fresh execution message" {
  run_hook_with_prompt "/finalize-pr 42"
  [ "$status" -eq 0 ]
  [[ "$output" =~ "systemMessage" ]]
  [[ "$output" =~ "FRESH EXECUTION" ]]
  [[ "$output" =~ "finalize-pr" ]]
}

# ---------------------------------------------------------------------------
# TC4: /resolve-pr-threads all → systemMessage with skill name
# ---------------------------------------------------------------------------

@test "TC4: /resolve-pr-threads triggers fresh execution message" {
  run_hook_with_prompt "/resolve-pr-threads all"
  [ "$status" -eq 0 ]
  [[ "$output" =~ "systemMessage" ]]
  [[ "$output" =~ "resolve-pr-threads" ]]
}

# ---------------------------------------------------------------------------
# TC5: Regular text without slash → empty JSON
# ---------------------------------------------------------------------------

@test "TC5: text mentioning 'ship' without slash outputs empty JSON" {
  run_hook_with_prompt "help me ship this feature"
  [ "$status" -eq 0 ]
  [[ "$output" == "{}" ]]
}

# ---------------------------------------------------------------------------
# TC6: Filesystem path /usr/bin → empty JSON (false positive exclusion)
# ---------------------------------------------------------------------------

@test "TC6: filesystem path /usr excluded as false positive" {
  run_hook_with_prompt "check /usr/bin/python"
  [ "$status" -eq 0 ]
  [[ "$output" == "{}" ]]
}

# ---------------------------------------------------------------------------
# TC7: Filesystem path /tmp → empty JSON (false positive exclusion)
# ---------------------------------------------------------------------------

@test "TC7: filesystem path /tmp excluded as false positive" {
  run_hook_with_prompt "read /tmp/output.log"
  [ "$status" -eq 0 ]
  [[ "$output" == "{}" ]]
}

# ---------------------------------------------------------------------------
# TC8: Empty/missing prompt → empty JSON, exit 0
# ---------------------------------------------------------------------------

@test "TC8: empty input outputs empty JSON" {
  run bash -c "echo '{}' | /bin/bash '$SCRIPT'"
  [ "$status" -eq 0 ]
  [[ "$output" == "{}" ]]
}

# ---------------------------------------------------------------------------
# TC9: Malformed JSON input → empty JSON, exit 0 (fail-open)
# ---------------------------------------------------------------------------

@test "TC9: malformed JSON input outputs empty JSON" {
  run bash -c "echo 'not json at all' | /bin/bash '$SCRIPT'"
  [ "$status" -eq 0 ]
  [[ "$output" == "{}" ]]
}

# ---------------------------------------------------------------------------
# TC10: /nix path excluded as false positive
# ---------------------------------------------------------------------------

@test "TC10: filesystem path /nix excluded as false positive" {
  run_hook_with_prompt "look at /nix/store/abc123"
  [ "$status" -eq 0 ]
  [[ "$output" == "{}" ]]
}
