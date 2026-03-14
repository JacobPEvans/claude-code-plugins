#!/usr/bin/env python3
"""
Claude Code PreToolUse hook for git branch limit enforcement.
Blocks branch creation commands when total branches (local + remote)
exceed the configured limit.

Trigger commands:
  - git branch <name> (not -d/-D)
  - git checkout -b
  - git switch -c
  - git worktree add

Limit: 100 total unique branches (local + remote deduplicated)

Exit codes:
  0 = allow the command
  2 = block the command (shows stderr to Claude)

Input: JSON from stdin with tool_input.command containing the Bash command
"""

import json
import shlex
import subprocess
import sys

BRANCH_LIMIT = 100


def _is_branch_create(command: str) -> bool:
    """Return True if the command creates a new branch."""
    try:
        tokens = shlex.split(command)
    except ValueError:
        return False

    if not tokens:
        return False

    # Find the git command start (skip env vars, prefixes like cd && ...)
    git_idx = None
    for i, tok in enumerate(tokens):
        if tok == "git":
            git_idx = i
            break

    if git_idx is None:
        return False

    rest = tokens[git_idx + 1 :]
    if not rest:
        return False

    subcmd = rest[0]

    # git branch <name> — but not delete operations
    if subcmd == "branch":
        # If any delete flag is present, not a create
        if any(f in rest for f in ("-d", "-D", "--delete", "--list", "-l", "-a", "-r", "--merged", "--no-merged", "--contains", "--sort")):
            return False
        # git branch (no args) just lists — need at least one non-flag arg
        non_flag_args = [a for a in rest[1:] if not a.startswith("-")]
        return len(non_flag_args) >= 1

    # git checkout -b <name>
    if subcmd == "checkout" and ("-b" in rest or "-B" in rest):
        return True

    # git switch -c <name> / git switch --create <name>
    if subcmd == "switch" and ("-c" in rest or "-C" in rest or "--create" in rest or "--force-create" in rest):
        return True

    # git worktree add <path> [<branch>]
    if subcmd == "worktree" and len(rest) >= 2 and rest[1] == "add":
        return True

    return False


def _count_unique_branches() -> int:
    """Count unique branches across local and remote (deduplicated)."""
    branches: set[str] = set()

    # Local branches
    try:
        result = subprocess.run(
            ["git", "branch", "--list", "--format=%(refname:short)"],
            capture_output=True, text=True, check=True, timeout=10,
        )
        for line in result.stdout.strip().splitlines():
            name = line.strip()
            if name:
                branches.add(name)
    except (subprocess.SubprocessError, ValueError):
        return 0  # fail-open

    # Remote branches
    try:
        result = subprocess.run(
            ["git", "branch", "-r", "--list", "--format=%(refname:short)"],
            capture_output=True, text=True, check=True, timeout=10,
        )
        for line in result.stdout.strip().splitlines():
            name = line.strip()
            if not name or name.endswith("/HEAD"):
                continue
            # Strip remote prefix (e.g. origin/main -> main)
            short = name.split("/", 1)[1] if "/" in name else name
            branches.add(short)
    except (subprocess.SubprocessError, ValueError):
        return 0  # fail-open

    return len(branches)


def _block_branch_limit(count: int) -> None:
    """Print branch limit block message and exit with code 2."""
    print(
        f"\n{'=' * 64}\n"
        f"BLOCKED: Branch limit exceeded\n"
        f"{'=' * 64}\n\n"
        f"  {count}/{BRANCH_LIMIT} unique branches (limit reached).\n\n"
        "Required actions:\n"
        "  1. Delete merged or stale branches\n"
        "  2. Run: git branch --merged main | xargs git branch -d\n"
        "  3. Run: git fetch --prune\n\n"
        f"{'=' * 64}\n",
        file=sys.stderr,
        flush=True,
    )
    sys.exit(2)


def main() -> None:
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_input = hook_input.get("tool_input", {})
    command = tool_input.get("command", "")

    if not _is_branch_create(command):
        sys.exit(0)

    count = _count_unique_branches()
    if count >= BRANCH_LIMIT:
        _block_branch_limit(count)


if __name__ == "__main__":
    main()
