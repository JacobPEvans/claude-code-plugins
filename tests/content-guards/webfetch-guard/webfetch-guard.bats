#!/usr/bin/env bats
# Test suite for content-guards/scripts/webfetch-guard.py
#
# Tests tool name filtering, blocked year detection, and current year warnings.
# Blocked years are computed dynamically relative to the current date to match
# the grace-period logic in the script (Jan-Mar: block 2+ years ago;
# Apr-Dec: block 1+ years ago).
#
# Run with: bats tests/content-guards/webfetch-guard/webfetch-guard.bats

setup() {
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/../../.." && pwd)"
  SCRIPT="$REPO_ROOT/content-guards/scripts/webfetch-guard.py"

  if [[ ! -f "$SCRIPT" ]]; then
    echo "ERROR: Script not found at $SCRIPT" >&2
    return 1
  fi

  # Compute years relative to current date (mirrors the script's logic)
  CURRENT_YEAR=$(python3 -c "from datetime import datetime; print(datetime.now().year)")
  BLOCKED_YEAR=$(python3 -c "from datetime import datetime; now=datetime.now(); print(now.year - 2)")
}

run_hook() {
  run python3 "$SCRIPT" <<< "$1"
}

# ---------------------------------------------------------------------------
# TC1: Non-WebFetch/WebSearch tools are silently allowed (exit 0, no output)
# ---------------------------------------------------------------------------

@test "TC1: Bash tool is allowed silently" {
  run_hook '{"tool_name":"Bash","tool_input":{"command":"echo hello 2020"}}'
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "TC1b: Read tool is allowed silently" {
  run_hook '{"tool_name":"Read","tool_input":{"file_path":"/some/file.md"}}'
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

# ---------------------------------------------------------------------------
# TC2: Invalid JSON exits with code 1
# ---------------------------------------------------------------------------

@test "TC2: invalid JSON input exits with code 1" {
  run python3 "$SCRIPT" <<< "not valid json"
  [ "$status" -eq 1 ]
}

# ---------------------------------------------------------------------------
# TC3: WebSearch with blocked year is denied
# ---------------------------------------------------------------------------

@test "TC3: WebSearch with blocked year is denied" {
  run_hook '{"tool_name":"WebSearch","tool_input":{"query":"best practices '"$BLOCKED_YEAR"'"}}'
  [ "$status" -eq 0 ]
  [[ "$output" =~ "deny" ]]
  [[ "$output" =~ "outdated" ]]
}

# ---------------------------------------------------------------------------
# TC4: WebFetch URL with blocked year is denied
# ---------------------------------------------------------------------------

@test "TC4: WebFetch URL with blocked year is denied" {
  run_hook '{"tool_name":"WebFetch","tool_input":{"url":"https://example.com/report-'"$BLOCKED_YEAR"'","prompt":"summarize"}}'
  [ "$status" -eq 0 ]
  [[ "$output" =~ "deny" ]]
}

# ---------------------------------------------------------------------------
# TC5: WebSearch with current year gives allow with warning
# ---------------------------------------------------------------------------

@test "TC5: WebSearch with current year gives allow with warning" {
  run_hook '{"tool_name":"WebSearch","tool_input":{"query":"best practices '"$CURRENT_YEAR"'"}}'
  [ "$status" -eq 0 ]
  [[ "$output" =~ "allow" ]]
  [[ "$output" =~ "WARNING" ]]
}

# ---------------------------------------------------------------------------
# TC6: WebSearch with no year reference is allowed silently
# ---------------------------------------------------------------------------

@test "TC6: WebSearch with no year reference is allowed silently" {
  run_hook '{"tool_name":"WebSearch","tool_input":{"query":"best practices for python testing"}}'
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

# ---------------------------------------------------------------------------
# TC7: WebFetch with no year in URL or prompt is allowed silently
# ---------------------------------------------------------------------------

@test "TC7: WebFetch with no year is allowed silently" {
  run_hook '{"tool_name":"WebFetch","tool_input":{"url":"https://docs.python.org/3/","prompt":"explain decorators"}}'
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}
