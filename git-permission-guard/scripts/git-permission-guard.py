#!/usr/bin/env python3
"""
Git Permission Guard - Blocks dangerous git/gh commands.

Exit 0 with JSON output for deny/allow decisions.
Most Bash commands are not git/gh - early exit is critical for performance.
"""

import json
import re
import sys

# Patterns that are NEVER allowed (bypass safety mechanisms)
DENY_PATTERNS = [
    (r"commit\s+.*(-n|--no-verify)", "bypasses pre-commit hooks"),
    (r"merge\s+.*--no-verify", "bypasses merge hooks"),
    (r"cherry-pick\s+.*--no-verify", "bypasses commit hooks"),
    (r"rebase\s+.*--no-verify", "bypasses commit hooks"),
    (r"config\s+.*core\.hooksPath", "changes hook directory"),
    (r"-c\s+core\.hooksPath", "bypasses configured hooks"),
    (r"pre-commit\s+uninstall", "removes pre-commit hooks"),
    (r"rm\s+(-rf?\s+)?\.git/hooks", "deletes git hooks"),
    (r"chmod\s+.*-x\s+\.git/hooks", "disables git hooks"),
]

# Commands requiring explicit user confirmation
ASK_GIT = [
    ("merge", "Can create merge commits or conflicts"),
    ("reset", "Can lose uncommitted work permanently"),
    ("restore", "Can discard local changes"),
    ("rm ", "Removes files from working tree and index"),
    ("cherry-pick", "Rewrites commit history"),
    ("worktree remove", "Removes worktree directory"),
    ("gc", "May remove unreferenced objects"),
    ("prune", "Removes unreferenced objects"),
    ("rebase", "Rewrites commit history"),
    ("commit --amend", "Rewrites the last commit"),
    ("push --force", "Overwrites remote history"),
    ("push -f", "Overwrites remote history"),
    ("clean", "Removes untracked files permanently"),
]

ASK_GH = [
    ("repo delete", "PERMANENTLY deletes repository"),
    ("issue close", "Closes issues - could be accidental"),
    ("pr close", "Closes pull requests - could be accidental"),
    ("pr merge", "Merges PR - ONLY do when user EXPLICITLY requests"),
    ("release delete", "Deletes releases permanently"),
]


def deny(reason: str) -> None:
    """Output deny decision and exit."""
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"BLOCKED: {reason}",
        }
    }))
    sys.exit(0)


def ask(command: str, risk: str) -> None:
    """Output ask decision (requires user confirmation) and exit."""
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": f"CAUTION: {risk}\nCommand: {command}",
        }
    }))
    sys.exit(0)


def main():
    # Parse input
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    # Only process Bash tool
    if data.get("tool_name") != "Bash":
        sys.exit(0)

    command = data.get("tool_input", {}).get("command", "").strip()
    if not command:
        sys.exit(0)

    # EARLY EXIT: Most commands are not git/gh - check this FIRST
    is_git = command.startswith("git ") or command == "git"
    is_gh = command.startswith("gh ") or command == "gh"
    if not is_git and not is_gh:
        sys.exit(0)

    # Extract subcommand for git (handle -C <path>, -c <key=value>)
    if is_git:
        rest = command[4:] if command.startswith("git ") else ""
        # Strip git options to find actual subcommand
        while rest:
            # -C <path>
            m = re.match(r'^-C\s+("[^"]+"|\'[^\']+\'|\S+)\s*(.*)', rest)
            if m:
                rest = m.group(2).strip()
                continue
            # -c <key=value>
            m = re.match(r'^-c\s+("[^"]+"|\'[^\']+\'|\S+)\s*(.*)', rest)
            if m:
                rest = m.group(2).strip()
                continue
            break
        subcommand = rest
    else:
        subcommand = command[3:] if command.startswith("gh ") else ""

    # Check DENY patterns (always blocked)
    for pattern, reason in DENY_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            deny(f"This command {reason}. Fix the underlying issue instead.")

    # Check ASK patterns for git
    if is_git:
        for cmd, risk in ASK_GIT:
            if subcommand.startswith(cmd) or f" {cmd}" in f" {subcommand}":
                ask(command, risk)

    # Check ASK patterns for gh
    if is_gh:
        for cmd, risk in ASK_GH:
            if subcommand.startswith(cmd):
                ask(command, risk)

    # Allow by default (exit 0, no output)
    sys.exit(0)


if __name__ == "__main__":
    main()
