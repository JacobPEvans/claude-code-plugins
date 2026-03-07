#!/usr/bin/env bats
# Test suite for content-guards/scripts/validate-token-limits.py
#
# Tests tool filtering, binary-file skipping, fail-open behavior when atc is
# unavailable, and block/allow decisions based on token counts.
#
# atc is mocked via a fake executable placed earlier in PATH so tests are
# fully hermetic and do not require the real tool to be installed.
#
# Run with: bats tests/content-guards/token-limits/validate-token-limits.bats

setup() {
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/../../.." && pwd)"
  SCRIPT="$REPO_ROOT/content-guards/scripts/validate-token-limits.py"
  FAKE_BIN_DIR="$(mktemp -d)"

  if [[ ! -f "$SCRIPT" ]]; then
    echo "ERROR: Script not found at $SCRIPT" >&2
    return 1
  fi

  export FAKE_BIN_DIR
  export PATH="$FAKE_BIN_DIR:$PATH"
}

teardown() {
  rm -rf "$FAKE_BIN_DIR"
}

# Install a fake atc that emits a specific token count on stdout.
# Usage: install_fake_atc <count>
install_fake_atc() {
  local count="$1"
  cat > "$FAKE_BIN_DIR/atc" <<EOF
#!/usr/bin/env bash
echo "${count} tokens"
EOF
  chmod +x "$FAKE_BIN_DIR/atc"
}

run_hook() {
  run python3 "$SCRIPT" <<< "$1"
}

# ---------------------------------------------------------------------------
# TC1: Non-Write/Edit tools are allowed silently (exit 0, no output)
# ---------------------------------------------------------------------------

@test "TC1: Read tool is allowed silently" {
  run_hook '{"tool_name":"Read","tool_input":{"file_path":"/some/file.py","content":"x = 1"}}'
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "TC1b: Bash tool is allowed silently" {
  run_hook '{"tool_name":"Bash","tool_input":{"command":"echo hello","content":"echo hello"}}'
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

# ---------------------------------------------------------------------------
# TC2: Invalid/missing JSON input fails open (exit 0)
# ---------------------------------------------------------------------------

@test "TC2: invalid JSON input is allowed (fail open)" {
  run python3 "$SCRIPT" <<< "not valid json"
  [ "$status" -eq 0 ]
}

@test "TC2b: empty file_path is allowed" {
  run_hook '{"tool_name":"Write","tool_input":{"file_path":"","content":"hello"}}'
  [ "$status" -eq 0 ]
}

@test "TC2c: missing content field is allowed" {
  run_hook '{"tool_name":"Write","tool_input":{"file_path":"/some/file.py"}}'
  [ "$status" -eq 0 ]
}

# ---------------------------------------------------------------------------
# TC3: Binary file extensions are skipped (exit 0)
# ---------------------------------------------------------------------------

@test "TC3: .png file is skipped" {
  install_fake_atc 99999
  run_hook '{"tool_name":"Write","tool_input":{"file_path":"/some/image.png","content":"binary"}}'
  [ "$status" -eq 0 ]
}

@test "TC3b: .pdf file is skipped" {
  install_fake_atc 99999
  run_hook '{"tool_name":"Write","tool_input":{"file_path":"/some/doc.pdf","content":"binary"}}'
  [ "$status" -eq 0 ]
}

# ---------------------------------------------------------------------------
# TC4: atc unavailable -> fail open (exit 0)
# ---------------------------------------------------------------------------

@test "TC4: Write allowed when atc is not installed (fail open)" {
  # No fake atc installed; real atc likely absent in test environment too
  rm -f "$FAKE_BIN_DIR/atc"
  run_hook '{"tool_name":"Write","tool_input":{"file_path":"/some/file.py","content":"x = 1"}}'
  [ "$status" -eq 0 ]
}

# ---------------------------------------------------------------------------
# TC5: Token count within default limit (2000) -> allow (exit 0)
# ---------------------------------------------------------------------------

@test "TC5: Write allowed when token count is within the default 2000 limit" {
  install_fake_atc 500
  run_hook '{"tool_name":"Write","tool_input":{"file_path":"/some/file.py","content":"x = 1"}}'
  [ "$status" -eq 0 ]
}

@test "TC5b: Edit allowed when token count is within limit" {
  install_fake_atc 1999
  run_hook '{"tool_name":"Edit","tool_input":{"file_path":"/some/file.py","content":"x = 1"}}'
  [ "$status" -eq 0 ]
}

# ---------------------------------------------------------------------------
# TC6: Token count exceeds default limit (2000) -> block (exit 2)
# ---------------------------------------------------------------------------

@test "TC6: Write blocked when token count exceeds 2000" {
  install_fake_atc 2001
  run_hook '{"tool_name":"Write","tool_input":{"file_path":"/some/big.py","content":"x = 1"}}'
  [ "$status" -eq 2 ]
  [[ "$output" =~ "Token limit violation" ]]
  [[ "$output" =~ "big.py" ]]
}

@test "TC6b: block message includes token count and limit values" {
  install_fake_atc 3000
  run_hook '{"tool_name":"Write","tool_input":{"file_path":"/some/large.py","content":"x = 1"}}'
  [ "$status" -eq 2 ]
  [[ "$output" =~ "3000" ]]
  [[ "$output" =~ "2000" ]]
}
