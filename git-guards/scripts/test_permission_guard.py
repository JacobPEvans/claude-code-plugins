#!/usr/bin/env python3
"""Tests for git-permission-guard.py ASK/DENY decisions."""

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).parent / "git-permission-guard.py"


def run(cmd: str) -> dict:
    inp = json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}})
    result = subprocess.run(
        ["python3", str(SCRIPT)],
        input=inp,
        capture_output=True,
        text=True,
    )
    if result.stdout.strip():
        return json.loads(result.stdout.strip())
    return {}


def check(label: str, cmd: str, expected_decision: str) -> bool:
    out = run(cmd)
    if not out:
        actual = "silent_allow"
    else:
        actual = out["hookSpecificOutput"]["permissionDecision"]

    ok = actual == expected_decision
    status = "PASS" if ok else "FAIL"
    print(f"{status} [{label}]: decision={actual}")
    if not ok:
        print(f"  Expected: {expected_decision}, Got: {actual}")
    return ok


all_pass = True

# git rm (plain) - silent allow: git protects uncommitted changes by default
all_pass &= check("git rm plain", "git rm some/file.txt", "silent_allow")

# git rm --cached - silent allow: only removes from index, working tree untouched
all_pass &= check("git rm --cached", "git rm --cached some/file.txt", "silent_allow")

# git rm -f - must ask: permanently discards uncommitted changes
all_pass &= check("git rm -f", "git rm -f some/file.txt", "ask")

# git rm --force - must ask: permanently discards uncommitted changes
all_pass &= check("git rm --force", "git rm --force some/file.txt", "ask")

# git rm -r - must ask: recursive deletion
all_pass &= check("git rm -r", "git rm -r some/directory/", "ask")

# git rm -rf - must ask: combined short flags, force-removes recursively
all_pass &= check("git rm -rf", "git rm -rf some/directory/", "ask")

# git rm -r -f - must ask: matches -r first (more specific would need ordering)
all_pass &= check("git rm -r -f", "git rm -r -f some/directory/", "ask")

# git restore - must ask: discards local changes
all_pass &= check("git restore", "git restore some/file.txt", "ask")

# git clean - must ask: removes untracked files
all_pass &= check("git clean", "git clean -fd", "ask")

# git reset - must ask: can lose uncommitted work
all_pass &= check("git reset", "git reset --hard HEAD", "ask")

# git push --force - must ask
all_pass &= check("git push --force", "git push --force origin main", "ask")

# DENY: commit --no-verify
all_pass &= check("git commit --no-verify", "git commit -m msg --no-verify", "deny")

# DENY: remove hooks
all_pass &= check("rm .git/hooks", "rm .git/hooks/pre-commit", "deny")

# Non-git command: silent allow
all_pass &= check("ls command", "ls -la", "silent_allow")

print()
print("ALL TESTS PASSED" if all_pass else "SOME TESTS FAILED")
sys.exit(0 if all_pass else 1)
