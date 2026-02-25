#!/usr/bin/env python3
"""
Git Permission Guard - Blocks dangerous git/gh commands.

Exit 0 with JSON output for deny/allow decisions.
Most Bash commands are not git/gh - early exit is critical for performance.
"""

import json
import re
import sys

# Patterns checked against ALL commands (not git-specific)
DENY_ALWAYS = [
    (r"pre-commit\s+uninstall", "removes pre-commit hooks"),
    (r"rm\s+.*\.git/hooks", "deletes git hooks"),
    (r"chmod\s+.*-x\s+\.git/hooks", "disables git hooks"),
]

# Patterns checked ONLY when command starts with 'git ' to avoid false
# positives from matching substrings in gh api body text or other commands
DENY_GIT_ONLY = [
    (r"commit\s+.*(-n|--no-verify)", "bypasses pre-commit hooks"),
    (r"merge\s+.*--no-verify", "bypasses merge hooks"),
    (r"cherry-pick\s+.*--no-verify", "bypasses commit hooks"),
    (r"rebase\s+.*--no-verify", "bypasses commit hooks"),
    (r"config\s+.*core\.hooksPath", "changes hook directory"),
    (r"-c\s+core\.hooksPath", "bypasses configured hooks"),
]

# Commands requiring explicit user confirmation
# Ordered from most specific to least specific to avoid false matches
ASK_GIT = [
    ("commit --amend", "Rewrites the last commit"),
    ("push --force-with-lease", "Overwrites remote history"),
    ("push --force", "Overwrites remote history"),
    ("push -f", "Overwrites remote history"),
    ("worktree remove --force", "Removes worktree directory, discarding uncommitted changes"),
    ("worktree remove -f", "Removes worktree directory, discarding uncommitted changes"),
    ("cherry-pick", "Rewrites commit history"),
    ("merge", "Can create merge commits or conflicts"),
    ("reset", "Can lose uncommitted work permanently"),
    ("restore", "Can discard local changes"),
    ("rebase", "Rewrites commit history"),
    ("clean", "Removes untracked files permanently"),
    ("prune", "Removes unreferenced objects"),
    ("rm", "Removes files from working tree and index"),
    ("gc", "May remove unreferenced objects"),
]

ASK_GH = [
    ("repo delete", "PERMANENTLY deletes repository"),
    ("release delete", "Deletes releases permanently"),
    ("issue close", "Closes issues - could be accidental"),
    ("pr close", "Closes pull requests - could be accidental"),
    ("pr merge", "Merges PR - ONLY do when user EXPLICITLY requests"),
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

    # Check universal DENY patterns (non-git-specific)
    for pattern, reason in DENY_ALWAYS:
        if re.search(pattern, command, re.IGNORECASE):
            deny(f"This command {reason}. Fix the underlying issue instead.")

    # EARLY EXIT: Most commands are not git/gh
    is_git = command.startswith("git ") or command == "git"
    is_gh = command.startswith("gh ") or command == "gh"
    if not is_git and not is_gh:
        sys.exit(0)

    # Check git-specific DENY patterns (after early exit to avoid false
    # positives from matching substrings in non-git commands like gh api)
    if is_git:
        for pattern, reason in DENY_GIT_ONLY:
            if re.search(pattern, command, re.IGNORECASE):
                deny(f"This command {reason}. Fix the underlying issue instead.")

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

    # Check ASK patterns - use word boundaries to avoid false matches
    # (e.g., "merge" shouldn't match "emergency")
    patterns = ASK_GIT if is_git else ASK_GH
    for cmd, risk in patterns:
        # Match as exact token sequence at start of subcommand
        cmd_tokens = cmd.split()
        sub_tokens = subcommand.split()
        if len(sub_tokens) >= len(cmd_tokens) and sub_tokens[:len(cmd_tokens)] == cmd_tokens:
            ask(command, risk)

    # Allow by default (exit 0, no output)
    sys.exit(0)


if __name__ == "__main__":
    main()
