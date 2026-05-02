#!/usr/bin/env python3
"""Tests for pre-commit-sign-guard.py decisions.

These tests use the GIT_GUARD_SIGN_OVERRIDE escape hatch is NOT enough on
its own — we also need to verify the hook's parsing logic without depending
on the local git config of whoever runs the test. Each test case below
either:
  - exercises the early-exit path (non-git, non-commit, explicit -S, etc.)
    where the hook returns silent_allow regardless of git config, or
  - sets `GIT_GUARD_SIGN_OVERRIDE=1` to bypass config inspection.

Where local git config matters (the missing-signing-config branch), we
manually invoke `_git_config_get` with a synthetic repo as cwd to exercise
the `-C <path>` propagation.
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).parent / "pre-commit-sign-guard.py"


def run(cmd: str, env_overrides: dict | None = None) -> dict:
    inp = json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}})
    env = os.environ.copy()
    if env_overrides:
        env.update(env_overrides)
    result = subprocess.run(
        ["python3", str(SCRIPT)],
        input=inp,
        capture_output=True,
        text=True,
        env=env,
    )
    if result.stdout.strip():
        return json.loads(result.stdout.strip())
    return {}


def check(label: str, cmd: str, expected: str,
          env_overrides: dict | None = None) -> bool:
    out = run(cmd, env_overrides=env_overrides)
    if not out:
        actual = "silent_allow"
    else:
        actual = out["hookSpecificOutput"]["permissionDecision"]
    ok = actual == expected
    status = "PASS" if ok else "FAIL"
    print(f"{status} [{label}]: decision={actual}")
    if not ok:
        print(f"  Expected: {expected}, Got: {actual}")
        if out:
            reason = out["hookSpecificOutput"].get("permissionDecisionReason", "")
            print(f"  Reason: {reason[:200]}")
    return ok


all_pass = True

# Non-Bash tool — silent allow
out = run("ignored")
# Synthesize a non-Bash invocation by setting tool_name to Edit
edit_input = json.dumps({"tool_name": "Edit", "tool_input": {"file_path": "x"}})
edit_result = subprocess.run(
    ["python3", str(SCRIPT)], input=edit_input,
    capture_output=True, text=True,
)
all_pass &= edit_result.stdout.strip() == ""
print(f"{'PASS' if edit_result.stdout.strip()=='' else 'FAIL'} [non-Bash tool]: silent")

# Non-git command — silent allow
all_pass &= check("non-git command", "ls -la", "silent_allow")

# Non-commit git subcommand — silent allow
all_pass &= check("git status", "git status", "silent_allow")
all_pass &= check("git log", "git log --oneline", "silent_allow")
all_pass &= check("git commit-tree (not 'commit')", "git commit-tree abc -p def", "silent_allow")
all_pass &= check("git commit-graph", "git commit-graph write", "silent_allow")

# Whitespace robustness — shlex handles tabs and multiple spaces
all_pass &= check("git\\tcommit (tab)",
                  "git\tcommit -m 'msg'",
                  "silent_allow",
                  env_overrides={"GIT_GUARD_SIGN_OVERRIDE": "1"})
all_pass &= check("git    commit (multi-space)",
                  "git    commit -m 'msg'",
                  "silent_allow",
                  env_overrides={"GIT_GUARD_SIGN_OVERRIDE": "1"})

# Override env var bypasses everything
all_pass &= check("override env",
                  "git commit -m 'msg'",
                  "silent_allow",
                  env_overrides={"GIT_GUARD_SIGN_OVERRIDE": "1"})

# Explicit -S signing flag — allow regardless of config
all_pass &= check("explicit -S", "git commit -S -m 'msg'", "silent_allow")
all_pass &= check("explicit --gpg-sign", "git commit --gpg-sign -m 'msg'", "silent_allow")
all_pass &= check("explicit --gpg-sign=KEY",
                  "git commit --gpg-sign=ABC123 -m 'msg'",
                  "silent_allow")
all_pass &= check("amend --no-edit -S (resign pattern)",
                  "git commit --amend --no-edit -S",
                  "silent_allow")
# Per the rewrite, -S alone is sufficient — --amend is no longer required
all_pass &= check("plain -S without --amend",
                  "git commit -S -m 'msg'",
                  "silent_allow")

# `-c commit.gpgsign=<falsey>` variants — all denied
all_pass &= check("-c commit.gpgsign=false",
                  "git -c commit.gpgsign=false commit -m 'msg'", "deny")
all_pass &= check("-c commit.gpgsign=no",
                  "git -c commit.gpgsign=no commit -m 'msg'", "deny")
all_pass &= check("-c commit.gpgsign=off",
                  "git -c commit.gpgsign=off commit -m 'msg'", "deny")
all_pass &= check("-c commit.gpgsign=0",
                  "git -c commit.gpgsign=0 commit -m 'msg'", "deny")
all_pass &= check("-c commit.gpgsign=FALSE (case-insensitive)",
                  "git -c commit.gpgsign=FALSE commit -m 'msg'", "deny")

# `-c commit.gpgsign=true` is NOT a falsey override — must NOT deny via that path.
# The decision then depends on the actual config; we set the override so the
# test doesn't depend on the local machine's config.
all_pass &= check("-c commit.gpgsign=true (truthy override)",
                  "git -c commit.gpgsign=true commit -m 'msg'",
                  "silent_allow",
                  env_overrides={"GIT_GUARD_SIGN_OVERRIDE": "1"})

# Quoted path with spaces in `-c user.name=` — must still recognise as commit
all_pass &= check("-c with quoted spaces",
                  'git -c "user.name=Foo Bar" commit -S -m msg',
                  "silent_allow")

# `-C <path>` is parsed and propagated. Build a synthetic git repo with
# valid signing config in a tmpdir, then invoke `git -C <tmpdir> commit`.
# The hook should query that tmpdir's config (not cwd). We can verify by
# ensuring the override path branch isn't needed when the tmpdir is set up
# correctly… but we cannot easily simulate "valid signing key" without a
# real GPG/SSH key. Instead, test the inverse: tmpdir with EMPTY config
# results in deny, even when cwd has signing configured.
with tempfile.TemporaryDirectory() as td:
    subprocess.run(["git", "init", "-q", td], check=True)
    # Explicitly clear any inherited config in this fresh repo
    subprocess.run(
        ["git", "-C", td, "config", "--local", "commit.gpgsign", "false"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", td, "config", "--local", "user.signingkey", ""],
        check=True,
    )
    all_pass &= check(
        f"-C <empty-config-repo> commit",
        f"git -C {td} commit -m 'msg'",
        "deny",
    )

if all_pass:
    print("\nAll pre-commit-sign-guard tests PASSED")
    sys.exit(0)
else:
    print("\nSome tests FAILED")
    sys.exit(1)
