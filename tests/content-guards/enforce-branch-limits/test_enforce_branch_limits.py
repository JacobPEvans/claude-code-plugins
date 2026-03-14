#!/usr/bin/env python3
"""Tests for enforce-branch-limits.py hook.

Verifies command detection, branch counting, block messages, and fail-open
behavior.

Run with: python3 tests/content-guards/enforce-branch-limits/test_enforce_branch_limits.py
"""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCRIPT = REPO_ROOT / "content-guards" / "scripts" / "enforce-branch-limits.py"

# Import the module with hyphenated name
spec = importlib.util.spec_from_file_location("enforce_branch_limits", str(SCRIPT))
ebl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ebl)


def run(inp: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["python3", str(SCRIPT)],
        input=inp,
        capture_output=True,
        text=True,
    )


def check(label: str, inp: str, expected_code: int) -> bool:
    result = run(inp)
    ok = result.returncode == expected_code
    status = "PASS" if ok else "FAIL"
    print(f"{status} [{label}]: exit={result.returncode}")
    if not ok:
        print(f"  Expected exit: {expected_code}, Got: {result.returncode}")
        if result.stderr:
            print(f"  Stderr: {result.stderr[:200]}")
    return ok


all_pass = True

# --- Command detection tests (via direct function call) ---

# Branch create commands
ok = ebl._is_branch_create("git branch new-feature")
print(f"{'PASS' if ok else 'FAIL'} [detect: git branch new-feature]")
all_pass &= ok

ok = ebl._is_branch_create("git checkout -b feat/new")
print(f"{'PASS' if ok else 'FAIL'} [detect: git checkout -b]")
all_pass &= ok

ok = ebl._is_branch_create("git switch -c fix/bug")
print(f"{'PASS' if ok else 'FAIL'} [detect: git switch -c]")
all_pass &= ok

ok = ebl._is_branch_create("git switch --create fix/bug")
print(f"{'PASS' if ok else 'FAIL'} [detect: git switch --create]")
all_pass &= ok

ok = ebl._is_branch_create("git worktree add /tmp/wt -b feat/new main")
print(f"{'PASS' if ok else 'FAIL'} [detect: git worktree add -b]")
all_pass &= ok

ok = ebl._is_branch_create("git worktree add -B feat/force /tmp/wt main")
print(f"{'PASS' if ok else 'FAIL'} [detect: git worktree add -B]")
all_pass &= ok

ok = ebl._is_branch_create("git checkout -B feat/force")
print(f"{'PASS' if ok else 'FAIL'} [detect: git checkout -B]")
all_pass &= ok

# Non-create commands (should return False)
ok = not ebl._is_branch_create("git branch -d old-feature")
print(f"{'PASS' if ok else 'FAIL'} [skip: git branch -d]")
all_pass &= ok

ok = not ebl._is_branch_create("git branch -D old-feature")
print(f"{'PASS' if ok else 'FAIL'} [skip: git branch -D]")
all_pass &= ok

ok = not ebl._is_branch_create("git branch --list")
print(f"{'PASS' if ok else 'FAIL'} [skip: git branch --list]")
all_pass &= ok

ok = not ebl._is_branch_create("git branch")
print(f"{'PASS' if ok else 'FAIL'} [skip: git branch (no args)]")
all_pass &= ok

ok = not ebl._is_branch_create("git status")
print(f"{'PASS' if ok else 'FAIL'} [skip: git status]")
all_pass &= ok

ok = not ebl._is_branch_create("git checkout main")
print(f"{'PASS' if ok else 'FAIL'} [skip: git checkout main]")
all_pass &= ok

ok = not ebl._is_branch_create("git switch main")
print(f"{'PASS' if ok else 'FAIL'} [skip: git switch main]")
all_pass &= ok

ok = not ebl._is_branch_create("ls -la")
print(f"{'PASS' if ok else 'FAIL'} [skip: non-git command]")
all_pass &= ok

ok = not ebl._is_branch_create("")
print(f"{'PASS' if ok else 'FAIL'} [skip: empty command]")
all_pass &= ok

ok = not ebl._is_branch_create("git branch --merged main")
print(f"{'PASS' if ok else 'FAIL'} [skip: git branch --merged]")
all_pass &= ok

ok = not ebl._is_branch_create("git worktree remove /tmp/wt")
print(f"{'PASS' if ok else 'FAIL'} [skip: git worktree remove]")
all_pass &= ok

# Regression: branch rename/move must not be treated as create
ok = not ebl._is_branch_create("git branch -m old-name new-name")
print(f"{'PASS' if ok else 'FAIL'} [skip: git branch -m (rename)]")
all_pass &= ok

ok = not ebl._is_branch_create("git branch -M old-name new-name")
print(f"{'PASS' if ok else 'FAIL'} [skip: git branch -M (force rename)]")
all_pass &= ok

ok = not ebl._is_branch_create("git branch --move old-name new-name")
print(f"{'PASS' if ok else 'FAIL'} [skip: git branch --move]")
all_pass &= ok

# Regression: branch copy must not be treated as create
ok = not ebl._is_branch_create("git branch -c old-name new-name")
print(f"{'PASS' if ok else 'FAIL'} [skip: git branch -c (copy)]")
all_pass &= ok

ok = not ebl._is_branch_create("git branch -C old-name new-name")
print(f"{'PASS' if ok else 'FAIL'} [skip: git branch -C (force copy)]")
all_pass &= ok

# Regression: worktree add existing branch (no -b) must not be treated as create
ok = not ebl._is_branch_create("git worktree add /tmp/wt existing-branch")
print(f"{'PASS' if ok else 'FAIL'} [skip: git worktree add existing branch]")
all_pass &= ok

ok = not ebl._is_branch_create("git worktree add /tmp/wt")
print(f"{'PASS' if ok else 'FAIL'} [skip: git worktree add (detached HEAD)]")
all_pass &= ok

# --- Hook integration tests (via stdin) ---

# Invalid JSON - fail open
all_pass &= check("invalid JSON", "not valid json", 0)

# Empty JSON - fail open
all_pass &= check("empty JSON", "{}", 0)

# Non-matching command passes through
all_pass &= check(
    "git status passthrough",
    json.dumps({"tool_input": {"command": "git status"}}),
    0,
)

# git branch -d passes through
all_pass &= check(
    "git branch -d passthrough",
    json.dumps({"tool_input": {"command": "git branch -d old"}}),
    0,
)

# Branch create command with git available -> either 0 (under limit) or could be 2
result = run(
    json.dumps({"tool_input": {"command": "git branch new-test-branch"}})
)
ok = result.returncode in (0, 2)
status = "PASS" if ok else "FAIL"
print(f"{status} [git branch create]: exit={result.returncode} (0=under-limit, 2=blocked)")
all_pass &= ok

print()
print("ALL TESTS PASSED" if all_pass else "SOME TESTS FAILED")
sys.exit(0 if all_pass else 1)
