#!/usr/bin/env bats
# Test suite for content-guards/scripts/enforce-issue-limits.py
#
# Tests command matching, rate-limit logic, and hard-limit blocking.
# Mocks `gh` via a fake executable placed earlier in PATH.
#
# Run with: bats tests/content-guards/enforce-issue-limits/enforce-issue-limits.bats

setup() {
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/../../.." && pwd)"
  SCRIPT="$REPO_ROOT/content-guards/scripts/enforce-issue-limits.py"
  FAKE_GH_DIR="$(mktemp -d)"

  if [[ ! -f "$SCRIPT" ]]; then
    echo "ERROR: Script not found at $SCRIPT" >&2
    return 1
  fi

  # Write a configurable fake `gh` script. Tests set GH_RESPONSE and
  # GH_EXIT_CODE before calling the script under test.
  cat > "$FAKE_GH_DIR/gh" <<'EOF'
#!/usr/bin/env bash
echo "${GH_RESPONSE:-[]}"
exit "${GH_EXIT_CODE:-0}"
EOF
  chmod +x "$FAKE_GH_DIR/gh"

  export PATH="$FAKE_GH_DIR:$PATH"
  export FAKE_GH_DIR
}

teardown() {
  rm -rf "$FAKE_GH_DIR"
}

# Helper: run the hook with the given JSON input, capturing exit status and stderr
run_hook() {
  run python3 "$SCRIPT" <<< "$1"
}

# ---------------------------------------------------------------------------
# TC1: Unrelated commands pass through immediately (exit 0)
# ---------------------------------------------------------------------------

@test "TC1: unrelated gh command is allowed" {
  run_hook '{"tool_input":{"command":"gh repo view"}}'
  [ "$status" -eq 0 ]
}

@test "TC1b: empty command is allowed" {
  run_hook '{"tool_input":{"command":""}}'
  [ "$status" -eq 0 ]
}

@test "TC1c: invalid JSON input is allowed" {
  run python3 "$SCRIPT" <<< "not json"
  [ "$status" -eq 0 ]
}

# ---------------------------------------------------------------------------
# TC2: gh issue create - well under all limits (exit 0)
# ---------------------------------------------------------------------------

@test "TC2: gh issue create allowed when well under all limits" {
  # Few open issues, none AI-created, no recent activity
  export GH_RESPONSE='[{"number":1,"labels":[],"createdAt":"2020-01-01T00:00:00Z"}]'
  run_hook '{"tool_input":{"command":"gh issue create --title test"}}'
  [ "$status" -eq 0 ]
}

# ---------------------------------------------------------------------------
# TC3: gh issue create - total issue hard limit (exit 2)
# ---------------------------------------------------------------------------

@test "TC3: gh issue create blocked when total open issues >= 50" {
  # Build 50 open issues with no labels
  issues="["
  for i in $(seq 1 50); do
    issues+='{"number":'"$i"',"labels":[]}'
    [[ $i -lt 50 ]] && issues+=","
  done
  issues+="]"
  export GH_RESPONSE="$issues"

  run_hook '{"tool_input":{"command":"gh issue create --title test"}}'
  [ "$status" -eq 2 ]
  [[ "$output" =~ "BLOCKED: Issue creation limit exceeded" ]]
  [[ "$output" =~ "50/50" ]]
}

# ---------------------------------------------------------------------------
# TC4: gh issue create - AI-created issue hard limit (exit 2)
# ---------------------------------------------------------------------------

@test "TC4: gh issue create blocked when ai-created issues >= 25" {
  # 25 issues all with the ai-created label
  issues="["
  for i in $(seq 1 25); do
    issues+='{"number":'"$i"',"labels":[{"name":"ai-created"}]}'
    [[ $i -lt 25 ]] && issues+=","
  done
  issues+="]"
  export GH_RESPONSE="$issues"

  run_hook '{"tool_input":{"command":"gh issue create --title test"}}'
  [ "$status" -eq 2 ]
  [[ "$output" =~ "BLOCKED: Issue creation limit exceeded" ]]
  [[ "$output" =~ "25/25" ]]
}

# ---------------------------------------------------------------------------
# TC5: gh issue create - 24h rate limit (exit 2)
# ---------------------------------------------------------------------------

@test "TC5: gh issue create blocked when 15 issues created in last 24h" {
  # Fake gh returns 15 issues all created within the last hour
  now="$(python3 -c 'from datetime import datetime, timezone; print(datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))')"
  issues="["
  for i in $(seq 1 15); do
    issues+='{"number":'"$i"',"labels":[],"createdAt":"'"$now"'"}'
    [[ $i -lt 15 ]] && issues+=","
  done
  issues+="]"
  export GH_RESPONSE="$issues"

  run_hook '{"tool_input":{"command":"gh issue create --title test"}}'
  [ "$status" -eq 2 ]
  [[ "$output" =~ "BLOCKED: Rate limit exceeded" ]]
  [[ "$output" =~ "issues" ]]
}

# ---------------------------------------------------------------------------
# TC6: gh pr create - 24h rate limit (exit 2)
# ---------------------------------------------------------------------------

@test "TC6: gh pr create blocked when 15 PRs created in last 24h" {
  now="$(python3 -c 'from datetime import datetime, timezone; print(datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))')"
  prs="["
  for i in $(seq 1 15); do
    prs+='{"createdAt":"'"$now"'"}'
    [[ $i -lt 15 ]] && prs+=","
  done
  prs+="]"
  export GH_RESPONSE="$prs"

  run_hook '{"tool_input":{"command":"gh pr create --title test"}}'
  [ "$status" -eq 2 ]
  [[ "$output" =~ "BLOCKED: Rate limit exceeded" ]]
  [[ "$output" =~ "PRs" ]]
}

# ---------------------------------------------------------------------------
# TC7: gh pr edit - 24h rate limit (exit 2)
# ---------------------------------------------------------------------------

@test "TC7: gh pr edit blocked when 15 PRs created in last 24h" {
  now="$(python3 -c 'from datetime import datetime, timezone; print(datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))')"
  prs="["
  for i in $(seq 1 15); do
    prs+='{"createdAt":"'"$now"'"}'
    [[ $i -lt 15 ]] && prs+=","
  done
  prs+="]"
  export GH_RESPONSE="$prs"

  run_hook '{"tool_input":{"command":"gh pr edit 42 --title new-title"}}'
  [ "$status" -eq 2 ]
  [[ "$output" =~ "BLOCKED: Rate limit exceeded" ]]
  [[ "$output" =~ "creating or updating" ]]
}

# ---------------------------------------------------------------------------
# TC8: gh pr create - under limit is allowed
# ---------------------------------------------------------------------------

@test "TC8: gh pr create allowed when under rate limit" {
  now="$(python3 -c 'from datetime import datetime, timezone; print(datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))')"
  export GH_RESPONSE='[{"createdAt":"'"$now"'"}]'

  run_hook '{"tool_input":{"command":"gh pr create --title test"}}'
  [ "$status" -eq 0 ]
}

# ---------------------------------------------------------------------------
# TC9: gh failure - fail open
# ---------------------------------------------------------------------------

@test "TC9: gh failure causes fail-open (exit 0)" {
  export GH_EXIT_CODE=1
  export GH_RESPONSE=""

  run_hook '{"tool_input":{"command":"gh issue create --title test"}}'
  [ "$status" -eq 0 ]
}

# ---------------------------------------------------------------------------
# TC10: block message includes correct remediation language (no bad references)
# ---------------------------------------------------------------------------

@test "TC10: hard-limit block message does not reference missing skill path" {
  issues="["
  for i in $(seq 1 50); do
    issues+='{"number":'"$i"',"labels":[]}'
    [[ $i -lt 50 ]] && issues+=","
  done
  issues+="]"
  export GH_RESPONSE="$issues"

  run_hook '{"tool_input":{"command":"gh issue create --title test"}}'
  [ "$status" -eq 2 ]
  [[ ! "$output" =~ "agentsmd/skills/consolidate-issues" ]]
}
