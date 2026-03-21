#!/usr/bin/env bats
# Test suite for git-guards/scripts/worktree-reminder.sh
#
# Tests the UserPromptSubmit hook's systemMessage injection:
#   - Not in a git repo → empty JSON, exit 0
#   - In git repo, worktree dir named "main" → systemMessage present
#   - In git repo, branch is "main" → systemMessage present
#   - In git repo, feature branch, dir not "main" → empty JSON, exit 0
#
# Each test that needs a git repo creates a temporary one in BATS_TMPDIR
# and tears it down in teardown().
#
# Run with: bats tests/git-guards/worktree-reminder/worktree-reminder.bats

setup() {
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/../../.." && pwd)"
  SCRIPT="$REPO_ROOT/git-guards/scripts/worktree-reminder.sh"

  if [[ ! -f "$SCRIPT" ]]; then
    echo "ERROR: Script not found at $SCRIPT" >&2
    return 1
  fi

  TMPDIR_BASE="$(mktemp -d)"
  export TMPDIR_BASE
}

teardown() {
  rm -rf "$TMPDIR_BASE"
}

# Create a minimal git repo at the given path with one committed file.
# Sets the branch name to $2 (default: main).
make_repo() {
  local repo_path="$1"
  local branch="${2:-main}"

  mkdir -p "$repo_path"
  git -C "$repo_path" init -q
  git -C "$repo_path" config user.email "test@example.com"
  git -C "$repo_path" config user.name "Test"
  echo "content" > "$repo_path/tracked.txt"
  git -C "$repo_path" add tracked.txt
  git -C "$repo_path" commit -q -m "init"
  git -C "$repo_path" branch -M "$branch"
}

# Run the hook from a specific directory
run_hook_in() {
  local dir="$1"
  run bash -c "cd '$dir' && /bin/bash '$SCRIPT'"
}

# ---------------------------------------------------------------------------
# TC1: Not in a git repo → empty JSON, exit 0
# ---------------------------------------------------------------------------

@test "TC1: not in a git repo outputs empty JSON" {
  local tmpdir
  tmpdir="$TMPDIR_BASE/not-a-repo"
  mkdir -p "$tmpdir"

  run_hook_in "$tmpdir"
  [ "$status" -eq 0 ]
  [[ "$output" == "{}" ]]
}

# ---------------------------------------------------------------------------
# TC2: In git repo, worktree dir named "main" → systemMessage present
# ---------------------------------------------------------------------------

@test "TC2: worktree dir named 'main' injects systemMessage" {
  local repo_dir
  repo_dir="$TMPDIR_BASE/main"
  make_repo "$repo_dir" "feat/some-feature"

  run_hook_in "$repo_dir"
  [ "$status" -eq 0 ]
  [[ "$output" =~ "systemMessage" ]]
  [[ "$output" =~ "WARNING" ]]
  [[ "$output" =~ "init-worktree" ]]
}

# ---------------------------------------------------------------------------
# TC3: In git repo, branch is "main" → systemMessage present
# ---------------------------------------------------------------------------

@test "TC3: branch named 'main' injects systemMessage" {
  local repo_dir
  repo_dir="$TMPDIR_BASE/myrepo"
  make_repo "$repo_dir" "main"

  run_hook_in "$repo_dir"
  [ "$status" -eq 0 ]
  [[ "$output" =~ "systemMessage" ]]
  [[ "$output" =~ "WARNING" ]]
  [[ "$output" =~ "init-worktree" ]]
}

# ---------------------------------------------------------------------------
# TC4: In git repo, feature branch, dir not "main" → empty JSON
# ---------------------------------------------------------------------------

@test "TC4: feature branch in non-main dir outputs empty JSON" {
  local repo_dir
  repo_dir="$TMPDIR_BASE/myrepo"
  make_repo "$repo_dir" "main"

  # Switch to a feature branch
  git -C "$repo_dir" checkout -q -b feat/add-feature

  run_hook_in "$repo_dir"
  [ "$status" -eq 0 ]
  [[ "$output" == "{}" ]]
}

# ---------------------------------------------------------------------------
# TC5: Both dir named "main" AND branch named "main" → still works
# ---------------------------------------------------------------------------

@test "TC5: dir named 'main' with branch 'main' injects systemMessage" {
  local repo_dir
  repo_dir="$TMPDIR_BASE/main"
  make_repo "$repo_dir" "main"

  run_hook_in "$repo_dir"
  [ "$status" -eq 0 ]
  [[ "$output" =~ "systemMessage" ]]
}
