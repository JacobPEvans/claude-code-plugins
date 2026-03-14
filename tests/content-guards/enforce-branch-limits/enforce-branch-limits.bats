#!/usr/bin/env bats
# Test suite for content-guards/scripts/enforce-branch-limits.py
#
# Tests command matching, branch counting, and limit blocking.
# Mocks `git` via a fake executable placed earlier in PATH.
#
# Run with: bats tests/content-guards/enforce-branch-limits/enforce-branch-limits.bats

setup() {
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/../../.." && pwd)"
  SCRIPT="$REPO_ROOT/content-guards/scripts/enforce-branch-limits.py"
  FAKE_GIT_DIR="$(mktemp -d)"

  if [[ ! -f "$SCRIPT" ]]; then
    echo "ERROR: Script not found at $SCRIPT" >&2
    return 1
  fi

  # Write a configurable fake `git` script. Tests set GIT_LOCAL_BRANCHES
  # and GIT_REMOTE_BRANCHES before calling the script under test.
  cat > "$FAKE_GIT_DIR/git" <<'FAKEOF'
#!/usr/bin/env bash
# Configurable fake git for branch limit tests
if [[ "$1" == "branch" && "$*" == *"--format"* ]]; then
  if [[ "$*" == *"-r"* ]]; then
    echo "${GIT_REMOTE_BRANCHES:-}"
  else
    echo "${GIT_LOCAL_BRANCHES:-main}"
  fi
  exit "${GIT_EXIT_CODE:-0}"
fi
# Pass through anything else
exit 0
FAKEOF
  chmod +x "$FAKE_GIT_DIR/git"

  export PATH="$FAKE_GIT_DIR:$PATH"
  export FAKE_GIT_DIR
}

teardown() {
  rm -rf "$FAKE_GIT_DIR"
}

# Helper: generate N branch names, one per line
gen_branches() {
  local prefix="$1" count="$2"
  for i in $(seq 1 "$count"); do
    echo "${prefix}branch-${i}"
  done
}

# Helper: run the hook with the given JSON input
run_hook() {
  run python3 "$SCRIPT" <<< "$1"
}

# ---------------------------------------------------------------------------
# TC1: Unrelated commands pass through
# ---------------------------------------------------------------------------

@test "TC1: non-git command is allowed" {
  run_hook '{"tool_input":{"command":"ls -la"}}'
  [ "$status" -eq 0 ]
}

@test "TC1b: git status is allowed" {
  run_hook '{"tool_input":{"command":"git status"}}'
  [ "$status" -eq 0 ]
}

@test "TC1c: empty command is allowed" {
  run_hook '{"tool_input":{"command":""}}'
  [ "$status" -eq 0 ]
}

@test "TC1d: invalid JSON is allowed" {
  run python3 "$SCRIPT" <<< "not json"
  [ "$status" -eq 0 ]
}

# ---------------------------------------------------------------------------
# TC2: Branch delete commands pass through
# ---------------------------------------------------------------------------

@test "TC2: git branch -d is allowed" {
  run_hook '{"tool_input":{"command":"git branch -d old-branch"}}'
  [ "$status" -eq 0 ]
}

@test "TC2b: git branch -D is allowed" {
  run_hook '{"tool_input":{"command":"git branch -D old-branch"}}'
  [ "$status" -eq 0 ]
}

@test "TC2c: git branch --list is allowed" {
  run_hook '{"tool_input":{"command":"git branch --list"}}'
  [ "$status" -eq 0 ]
}

# ---------------------------------------------------------------------------
# TC3: Branch creation allowed when under limit
# ---------------------------------------------------------------------------

@test "TC3: git branch create allowed when under limit" {
  export GIT_LOCAL_BRANCHES="main"
  export GIT_REMOTE_BRANCHES="origin/main"
  run_hook '{"tool_input":{"command":"git branch new-feature"}}'
  [ "$status" -eq 0 ]
}

@test "TC3b: git checkout -b allowed when under limit" {
  export GIT_LOCAL_BRANCHES="main"
  export GIT_REMOTE_BRANCHES="origin/main"
  run_hook '{"tool_input":{"command":"git checkout -b feat/new"}}'
  [ "$status" -eq 0 ]
}

@test "TC3c: git switch -c allowed when under limit" {
  export GIT_LOCAL_BRANCHES="main"
  export GIT_REMOTE_BRANCHES="origin/main"
  run_hook '{"tool_input":{"command":"git switch -c fix/bug"}}'
  [ "$status" -eq 0 ]
}

@test "TC3d: git worktree add allowed when under limit" {
  export GIT_LOCAL_BRANCHES="main"
  export GIT_REMOTE_BRANCHES="origin/main"
  run_hook '{"tool_input":{"command":"git worktree add /tmp/wt feat/new"}}'
  [ "$status" -eq 0 ]
}

# ---------------------------------------------------------------------------
# TC4: Branch creation blocked when at limit
# ---------------------------------------------------------------------------

@test "TC4: git branch create blocked when at 100 branches" {
  export GIT_LOCAL_BRANCHES="$(gen_branches '' 100)"
  export GIT_REMOTE_BRANCHES=""
  run_hook '{"tool_input":{"command":"git branch new-feature"}}'
  [ "$status" -eq 2 ]
  [[ "$output" =~ "BLOCKED: Branch limit exceeded" ]]
  [[ "$output" =~ "100/100" ]]
}

@test "TC4b: git checkout -b blocked when at 100 branches" {
  export GIT_LOCAL_BRANCHES="$(gen_branches '' 100)"
  export GIT_REMOTE_BRANCHES=""
  run_hook '{"tool_input":{"command":"git checkout -b feat/new"}}'
  [ "$status" -eq 2 ]
  [[ "$output" =~ "BLOCKED: Branch limit exceeded" ]]
}

@test "TC4c: git switch -c blocked when at 100 branches" {
  export GIT_LOCAL_BRANCHES="$(gen_branches '' 100)"
  export GIT_REMOTE_BRANCHES=""
  run_hook '{"tool_input":{"command":"git switch -c fix/bug"}}'
  [ "$status" -eq 2 ]
  [[ "$output" =~ "BLOCKED: Branch limit exceeded" ]]
}

@test "TC4d: git worktree add blocked when at 100 branches" {
  export GIT_LOCAL_BRANCHES="$(gen_branches '' 100)"
  export GIT_REMOTE_BRANCHES=""
  run_hook '{"tool_input":{"command":"git worktree add /tmp/wt feat/new"}}'
  [ "$status" -eq 2 ]
  [[ "$output" =~ "BLOCKED: Branch limit exceeded" ]]
}

# ---------------------------------------------------------------------------
# TC5: Deduplication - same branch local and remote counts once
# ---------------------------------------------------------------------------

@test "TC5: local+remote deduplication keeps count correct" {
  # 50 local + 50 remote with same names = 50 unique (under limit)
  export GIT_LOCAL_BRANCHES="$(gen_branches '' 50)"
  export GIT_REMOTE_BRANCHES="$(gen_branches 'origin/' 50)"
  run_hook '{"tool_input":{"command":"git branch new-feature"}}'
  [ "$status" -eq 0 ]
}

# ---------------------------------------------------------------------------
# TC6: Over limit with mixed local and remote
# ---------------------------------------------------------------------------

@test "TC6: blocked when local+remote unique branches >= 100" {
  # 60 local + 60 remote (40 overlap) = 80 unique local + 20 unique remote = still under
  # Let's use 100 unique: 50 local-only + 50 remote-only
  export GIT_LOCAL_BRANCHES="$(gen_branches 'local-' 50)"
  export GIT_REMOTE_BRANCHES="$(gen_branches 'origin/remote-' 50)"
  run_hook '{"tool_input":{"command":"git branch new-feature"}}'
  [ "$status" -eq 2 ]
  [[ "$output" =~ "BLOCKED: Branch limit exceeded" ]]
}

# ---------------------------------------------------------------------------
# TC7: git failure causes fail-open
# ---------------------------------------------------------------------------

@test "TC7: git failure causes fail-open (exit 0)" {
  export GIT_EXIT_CODE=1
  run_hook '{"tool_input":{"command":"git branch new-feature"}}'
  [ "$status" -eq 0 ]
}

# ---------------------------------------------------------------------------
# TC8: Block message includes remediation advice
# ---------------------------------------------------------------------------

@test "TC8: block message suggests pruning" {
  export GIT_LOCAL_BRANCHES="$(gen_branches '' 100)"
  export GIT_REMOTE_BRANCHES=""
  run_hook '{"tool_input":{"command":"git branch new-feature"}}'
  [ "$status" -eq 2 ]
  [[ "$output" =~ "Delete merged or stale branches" ]]
  [[ "$output" =~ "git fetch --prune" ]]
}
