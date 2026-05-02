#!/usr/bin/env python3
"""
pre-commit-sign-guard.py - PreToolUse hook that refuses unsigned `git commit`.

JacobPEvans repos enforce `required_signatures` org-wide. Local config drift
(missing GPG/SSH key, `commit.gpgsign=false`, signing key not loadable) used
to silently produce unsigned commits that landed on PR branches and blocked
merges. This hook makes the failure loud and immediate — `git commit` is
denied at hook time when the signing config is incomplete.

Architecture: the `git-signing` rule in JacobPEvans/ai-assistant-instructions
  https://github.com/JacobPEvans/ai-assistant-instructions/blob/main/agentsmd/rules/git-signing.md

Test bypass: set GIT_GUARD_SIGN_OVERRIDE=1 (mirrors the
GIT_GUARD_BRANCH_OVERRIDE pattern in main-branch-guard).
"""

import json
import os
import re
import shlex
import subprocess
import sys
from typing import Optional


def deny(reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"BLOCKED: {reason}",
        }
    }))
    sys.exit(0)


def _parse_git_invocation(command: str) -> tuple[Optional[list[str]], Optional[str]]:
    """Tokenize a shell command and, if it invokes git, return (rest_tokens, cwd)
    where rest_tokens are the args after stripping `git` itself plus any
    leading global options (`-C <path>`, `-c <key=value>`, `--git-dir=…`,
    `--work-tree=…`), and cwd is the effective directory for `git config`
    queries (the value passed to `-C`, or None if absent).

    Returns `(None, None)` for non-git commands or unparseable input.

    Using shlex.split (instead of regex) handles `git\\tcommit`,
    `git    commit`, `git -c "user.name=Foo Bar" commit`, etc. correctly.
    """
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        return None, None
    if not tokens or tokens[0] != "git":
        return None, None
    i = 1
    cwd: Optional[str] = None
    while i < len(tokens):
        tok = tokens[i]
        if tok == "-C" and i + 1 < len(tokens):
            cwd = tokens[i + 1]
            i += 2
        elif tok.startswith("-C"):  # -C/path form (rare but legal)
            cwd = tok[2:]
            i += 1
        elif tok == "-c" and i + 1 < len(tokens):
            i += 2  # value is opaque to us; skip it
        elif tok.startswith("-c") and "=" in tok:
            i += 1
        elif tok.startswith("--git-dir") or tok.startswith("--work-tree"):
            # Both can be `--key=val` or `--key val`
            if "=" in tok:
                i += 1
            else:
                i += 2
        else:
            break
    return tokens[i:], cwd


def _is_git_commit(rest_tokens: list[str]) -> bool:
    """Given the post-global-opts tokens from `_parse_git_invocation`, check
    if the next token is `commit` (the subcommand). Excludes `commit-tree`,
    `commit-graph`, etc.
    """
    return bool(rest_tokens) and rest_tokens[0] == "commit"


def _commit_explicitly_signs(rest_tokens: list[str]) -> bool:
    """True if the commit invocation includes an explicit signing flag (`-S`
    or `--gpg-sign[=...]`).

    The hook's job is to ensure every commit is signed; if the user passes
    `-S` explicitly, signing is forced regardless of the global config, so
    we don't need to check `commit.gpgsign`/`user.signingkey`. This covers
    the `git rebase --exec 'git commit --amend --no-edit -S'` resign pattern
    used to backfill historical unsigned PRs.

    Note: `--amend` is intentionally NOT required — `-S` alone is sufficient
    proof of intent. (Earlier versions of this hook conflated --amend with
    explicit signing; reviewers caught the mismatch with the docstring.)
    """
    for tok in rest_tokens:
        if tok == "-S":
            return True
        if tok == "--gpg-sign" or tok.startswith("--gpg-sign="):
            return True
    return False


def _disables_signing_via_inline_c(command: str) -> bool:
    """Detect `git -c commit.gpgsign=<falsey>` (or with surrounding quotes /
    arbitrary spacing). False values per git's bool parsing: `false`, `no`,
    `off`, `0`, empty string. Anything else is truthy.
    """
    return bool(re.search(
        r"""-c\s*['"]?commit\.gpgsign\s*=\s*(false|no|off|0|['"]\s*['"])""",
        command,
        re.IGNORECASE,
    ))


def _git_config_get(key: str, *, cwd: Optional[str] = None,
                    bool_type: bool = False) -> str:
    """Read git config with optional `cwd` (so `git -C <path> commit` checks
    the right repo) and optional bool normalisation.

    `bool_type=True` runs `git config --type=bool --get`, which converts
    `yes`/`on`/`1`/`true` (and case variants) to the literal string `true`,
    and `no`/`off`/`0`/`false`/empty to `false`. Without this, callers comparing
    the raw value against `"true"` would incorrectly reject `commit.gpgsign=yes`.
    """
    args = ["git", "config"]
    if bool_type:
        args.extend(["--type", "bool"])
    args.extend(["--get", key])
    try:
        result = subprocess.run(
            args, capture_output=True, text=True, timeout=2,
            cwd=cwd if cwd else None,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return ""


def _signing_key_is_loadable(key_value: str, fmt: str) -> bool:
    """Verify the configured signing key is actually present.

    GPG: `gpg --list-secret-keys -- <id>` exits 0 when the key is in the
    keyring. The `--` prevents `key_value` (config-derived) from being
    interpreted as an option if it starts with a hyphen.

    SSH: the key value is a path; the file must exist and be readable.
    """
    if not key_value:
        return False
    if fmt == "ssh":
        try:
            return os.access(os.path.expanduser(key_value), os.R_OK)
        except OSError:
            return False
    try:
        result = subprocess.run(
            ["gpg", "--list-secret-keys", "--", key_value],
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

    rest_tokens, cwd = _parse_git_invocation(command)
    if rest_tokens is None or not _is_git_commit(rest_tokens):
        sys.exit(0)

    if _commit_explicitly_signs(rest_tokens):
        sys.exit(0)

    if _disables_signing_via_inline_c(command):
        deny(
            "git commit invoked with `-c commit.gpgsign=<falsey>`. "
            "JacobPEvans repos enforce required_signatures — unsigned commits "
            "will be rejected on push. If you genuinely need to bypass for a "
            "test, set GIT_GUARD_SIGN_OVERRIDE=1 in the environment."
        )

    gpgsign = _git_config_get("commit.gpgsign", cwd=cwd, bool_type=True)
    signingkey = _git_config_get("user.signingkey", cwd=cwd)
    fmt = (_git_config_get("gpg.format", cwd=cwd) or "openpgp").lower()

    missing = []
    if gpgsign != "true":
        missing.append("commit.gpgsign is not set to a truthy value")
    if not signingkey:
        missing.append("user.signingkey is empty")
    elif not _signing_key_is_loadable(signingkey, fmt):
        if fmt == "ssh":
            missing.append(
                f"user.signingkey points at '{signingkey}' but the file is not readable"
            )
        else:
            missing.append(
                f"user.signingkey is '{signingkey}' but `gpg --list-secret-keys -- {shlex.quote(signingkey)}` "
                "did not find a matching secret key"
            )

    if missing:
        deny(
            "git commit refused — signing config is incomplete:\n  - "
            + "\n  - ".join(missing)
            + "\n\nJacobPEvans repos enforce required_signatures org-wide; an unsigned "
            "commit would land on the PR branch and block the merge.\n\n"
            "Architecture and per-context setup:\n"
            "  https://github.com/JacobPEvans/ai-assistant-instructions/blob/main/agentsmd/rules/git-signing.md"
        )

    sys.exit(0)


if __name__ == "__main__":
    main()
