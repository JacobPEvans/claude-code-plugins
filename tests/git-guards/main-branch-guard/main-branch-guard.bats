#!/usr/bin/env bats
# Test suite for git-guards/scripts/main-branch-guard.sh
#
# Tests the hook's allow/deny decisions across the following scenarios:
#   - No file path in input (fail open)
#   - File outside any git repository (fail open)
#   - Tracked file in a worktree directory named "main" (deny)
#   - Tracked file on the "main" branch (deny)
#   - Tracked file on a feature branch (allow)
#
# Each test that needs a git repo creates a temporary one in BATS_TMPDIR
# and tears it down in teardown().
#
# Run with: bats tests/git-guards/main-branch-guard/main-branch-guard.bats

setup() {
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/../../.." && pwd)"
  SCRIPT="$REPO_ROOT/git-guards/scripts/main-branch-guard.sh"
  load '../../helpers/git'

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

run_hook() {
  run bash -c 'echo "$1" | /bin/bash "$2"' _ "$1" "$SCRIPT"
}

# ---------------------------------------------------------------------------
# TC1: No file_path in JSON -> allow (exit 0)
# ---------------------------------------------------------------------------

@test "TC1: empty JSON input is allowed" {
  run_hook '{}'
  [ "$status" -eq 0 ]
}

@test "TC1b: tool_input with no file_path is allowed" {
  run_hook '{"tool_name":"Edit","tool_input":{}}'
  [ "$status" -eq 0 ]
}

# ---------------------------------------------------------------------------
# TC2: File outside any git repository -> allow (exit 0)
# ---------------------------------------------------------------------------

@test "TC2: file in /tmp (not a git repo) is allowed" {
  local tmpfile
  tmpfile="$(mktemp "$TMPDIR_BASE/testfile.XXXXXX")"
  echo "data" > "$tmpfile"
  run_hook '{"tool_name":"Edit","tool_input":{"file_path":"'"$tmpfile"'"}}'
  [ "$status" -eq 0 ]
}

# ---------------------------------------------------------------------------
# TC3: Tracked file in a worktree directory named "main" -> deny (exit 2)
# ---------------------------------------------------------------------------

@test "TC3: tracked file in worktree dir named 'main' is denied" {
  local repo_dir tracked_file
  repo_dir="$TMPDIR_BASE/main"
  tracked_file="$(make_repo "$repo_dir" "feat/some-feature")"

  run_hook '{"tool_name":"Edit","tool_input":{"file_path":"'"$tracked_file"'"}}'
  [ "$status" -eq 2 ]
  [[ "$output" =~ "BLOCKED" ]]
}

# ---------------------------------------------------------------------------
# TC4: Tracked file on the "main" branch -> deny (exit 2)
# ---------------------------------------------------------------------------

@test "TC4: tracked file on the 'main' branch is denied" {
  local repo_dir tracked_file
  repo_dir="$TMPDIR_BASE/myrepo"
  tracked_file="$(make_repo "$repo_dir" "main")"

  run_hook '{"tool_name":"Edit","tool_input":{"file_path":"'"$tracked_file"'"}}'
  [ "$status" -eq 2 ]
  [[ "$output" =~ "BLOCKED" ]]
}

# ---------------------------------------------------------------------------
# TC5: Tracked file on a feature branch -> allow (exit 0)
# ---------------------------------------------------------------------------

@test "TC5: tracked file on a feature branch is allowed" {
  local repo_dir tracked_file
  repo_dir="$TMPDIR_BASE/myrepo"
  tracked_file="$(make_repo "$repo_dir" "main")"

  # Switch to a feature branch
  git -C "$repo_dir" checkout -q -b feat/add-feature

  run_hook '{"tool_name":"Edit","tool_input":{"file_path":"'"$tracked_file"'"}}'
  [ "$status" -eq 0 ]
}

# ---------------------------------------------------------------------------
# TC6: notebook_path input is also supported
# ---------------------------------------------------------------------------

@test "TC6: notebook_path outside git repo is allowed" {
  local tmpfile
  tmpfile="$(mktemp "$TMPDIR_BASE/notebook.XXXXXX")"
  echo "data" > "$tmpfile"
  run_hook '{"tool_name":"NotebookEdit","tool_input":{"notebook_path":"'"$tmpfile"'"}}'
  [ "$status" -eq 0 ]
}

# ---------------------------------------------------------------------------
# TC7: file in bare-repo sibling (scratch dir, not a worktree) -> allow (exit 0)
# Regression: before the fix, git branch --show-current walked up to the bare
# repo and returned "main", falsely triggering the deny path.
# ---------------------------------------------------------------------------

@test "TC7: file in bare-repo sibling (not a worktree) is allowed" {
  local bare_dir seed_dir main_worktree scratch_dir scratch_file
  bare_dir="$TMPDIR_BASE/.git"
  seed_dir="$TMPDIR_BASE/_seed"
  main_worktree="$TMPDIR_BASE/main"
  scratch_dir="$TMPDIR_BASE/scratch"

  # Create bare repo
  git init --bare -q "$bare_dir"

  # Seed a commit via a temporary clone
  mkdir -p "$seed_dir"
  git -C "$seed_dir" init -q
  git -C "$seed_dir" config user.email "test@example.com"
  git -C "$seed_dir" config user.name "Test"
  echo "x" > "$seed_dir/x"
  git -C "$seed_dir" add x
  git -C "$seed_dir" commit -q -m "seed"
  git -C "$seed_dir" branch -M main
  git -C "$seed_dir" push -q "$bare_dir" main

  # Add main worktree from the bare repo
  git --git-dir="$bare_dir" worktree add -q "$main_worktree" main

  # Create scratch sibling dir (NOT a worktree)
  mkdir -p "$scratch_dir"
  scratch_file="$scratch_dir/snapshot.md"

  run_hook '{"tool_name":"Write","tool_input":{"file_path":"'"$scratch_file"'"}}'
  [ "$status" -eq 0 ]
}
