#!/usr/bin/env python3
"""
pre-commit-sign-guard.py - PreToolUse hook that refuses unsigned `git commit`.

JacobPEvans repos enforce `required_signatures` org-wide. Local config drift
(missing GPG/SSH key, `commit.gpgsign=false`, signing key not loadable) used
to silently produce unsigned commits that landed on PR branches and blocked
merges. This hook makes the failure loud and immediate — `git commit` is
denied at hook time when the signing config is incomplete.

Architecture: ai-assistant-instructions/agentsmd/rules/git-signing.md
Local config schema: ~/.config/nix-home/local.nix (per nix-home README)

Test bypass: set GIT_GUARD_SIGN_OVERRIDE=1 (mirrors the
GIT_GUARD_BRANCH_OVERRIDE pattern in main-branch-guard).
"""

import json
import os
import re
import shlex
import subprocess
import sys


def deny(reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"BLOCKED: {reason}",
        }
    }))
    sys.exit(0)


def _is_git_commit(command: str) -> bool:
    """True iff this Bash command invokes `git commit` (and not `gh ...` or
    `git commit-tree` etc. that share the prefix).

    Strips inline `-c key=value` overrides and `-C <path>` redirections so
    `git -c commit.gpgsign=false commit` is still recognised as commit.
    """
    rest = command.lstrip()
    if not (rest.startswith("git ") or rest == "git"):
        return False
    rest = rest[4:] if rest.startswith("git ") else ""
    while rest:
        m = re.match(r"^-C\s+(\"[^\"]+\"|'[^']+'|\S+)\s*(.*)", rest)
        if m:
            rest = m.group(2)
            continue
        m = re.match(r"^-c\s+\S+\s*(.*)", rest)
        if m:
            rest = m.group(1)
            continue
        break
    # Match `commit` as the actual subcommand; reject `commit-tree`, `commit-graph`
    return bool(re.match(r"^commit(\s|$)", rest))


def _commit_only_amends_no_edit(command: str) -> bool:
    """`git commit --amend --no-edit -S` is the rebase --exec resign pattern.
    Allow it through — even though `commit.gpgsign` may not be set, the
    explicit -S flag forces signing on this command.
    """
    if "--amend" not in command:
        return False
    return bool(re.search(r"(^|\s)-S(\s|$)", command) or
                re.search(r"(^|\s)--gpg-sign(\s|=|$)", command))


def _git_config_get(key: str) -> str:
    try:
        result = subprocess.run(
            ["git", "config", "--get", key],
            capture_output=True, text=True, timeout=2,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return ""


def _signing_key_is_loadable(key_value: str, fmt: str) -> bool:
    """Verify the configured signing key is actually present on this machine.

    For GPG: `gpg --list-secret-keys <id>` exits 0 when the key is in the keyring.
    For SSH: the key value is a path; the file must exist and be readable.
    """
    if not key_value:
        return False
    if fmt == "ssh":
        try:
            return os.access(os.path.expanduser(key_value), os.R_OK)
        except OSError:
            return False
    # Default to GPG (git's `gpg.format` defaults to `openpgp`)
    try:
        result = subprocess.run(
            ["gpg", "--list-secret-keys", key_value],
            capture_output=True, text=True, timeout=3,
        )
        return result.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def main() -> None:
    if os.environ.get("GIT_GUARD_SIGN_OVERRIDE") == "1":
        sys.exit(0)

    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    if data.get("tool_name") != "Bash":
        sys.exit(0)

    command = data.get("tool_input", {}).get("command", "").strip()
    if not command:
        sys.exit(0)

    # Fast path: bail out for anything that isn't `git commit`
    if not _is_git_commit(command):
        sys.exit(0)

    # `git commit --amend --no-edit -S` is signing explicitly via flag;
    # let it through even if the global config is incomplete.
    if _commit_only_amends_no_edit(command):
        sys.exit(0)

    # `git -c commit.gpgsign=false commit` would slip past a config check
    # but be caught here — anything that explicitly disables signing is denied.
    if re.search(r"-c\s+commit\.gpgsign\s*=\s*false", command):
        deny(
            "git commit invoked with `-c commit.gpgsign=false`. "
            "JacobPEvans repos enforce required_signatures — unsigned commits "
            "will be rejected on push. If you genuinely need to bypass for a "
            "test, set GIT_GUARD_SIGN_OVERRIDE=1 in the environment."
        )

    # Check the effective signing config
    gpgsign = _git_config_get("commit.gpgsign").lower()
    signingkey = _git_config_get("user.signingkey")
    fmt = (_git_config_get("gpg.format") or "openpgp").lower()

    missing = []
    if gpgsign != "true":
        missing.append("commit.gpgsign is not set to true")
    if not signingkey:
        missing.append("user.signingkey is empty")
    elif not _signing_key_is_loadable(signingkey, fmt):
        if fmt == "ssh":
            missing.append(
                f"user.signingkey points at '{signingkey}' but the file is not readable"
            )
        else:
            missing.append(
                f"user.signingkey is '{signingkey}' but `gpg --list-secret-keys {shlex.quote(signingkey)}` "
                "did not find a matching secret key"
            )

    if missing:
        deny(
            "git commit refused — signing config is incomplete:\n  - "
            + "\n  - ".join(missing)
            + "\n\nJacobPEvans repos enforce required_signatures org-wide; an unsigned "
            "commit would land on the PR branch and block the merge.\n\n"
            "Fix the local config (typically by populating ~/.config/nix-home/local.nix "
            "and rebuilding home-manager with --impure), then retry. See:\n"
            "  - ai-assistant-instructions/agentsmd/rules/git-signing.md\n"
            "  - ~/git/nix-home/main/local.nix.example"
        )

    sys.exit(0)


if __name__ == "__main__":
    main()
