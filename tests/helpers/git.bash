# Shared BATS helpers for git-based tests.
# Usage: load '../../helpers/git'

# Create a minimal git repo at the given path with one committed file.
# Sets the branch name to $2 (default: main).
# Prints the absolute path to the committed test file.
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

  echo "$repo_path/tracked.txt"
}
