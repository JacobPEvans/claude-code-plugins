#!/usr/bin/env python3
"""
Git Permission Guard - PreToolUse hook for git/gh command permission management.

This hook intercepts Bash tool calls and applies allow/ask/deny logic to git and gh
commands with detailed warning messages explaining why commands are blocked.

Exit codes:
    0 (no output) - ALLOW: Command executes normally
    2 (with message) - BLOCK: Command is denied or requires confirmation
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Optional


def load_config(config_name: str) -> dict:
    """Load a JSON config file from the config directory."""
    plugin_dir = os.environ.get("CLAUDE_PLUGIN_DIR", str(Path(__file__).parent.parent))
    config_path = Path(plugin_dir) / "config" / f"{config_name}.json"

    if not config_path.exists():
        return {}

    with open(config_path) as f:
        return json.load(f)


def extract_git_command(command: str) -> Optional[tuple[str, str]]:
    """
    Extract the git/gh tool and subcommand from a command string.

    Handles:
        - git status
        - git -C /path status
        - git -c key=value status
        - gh pr list

    Returns:
        Tuple of (tool, full_subcommand) or None if not a git/gh command.
        Example: ("git", "merge main") or ("gh", "pr merge 123")
    """
    command = command.strip()

    # Check if this is a git or gh command
    if not (command.startswith("git ") or command.startswith("gh ") or
            command == "git" or command == "gh"):
        return None

    # Determine the tool
    if command.startswith("git"):
        tool = "git"
        rest = command[3:].strip()
    else:
        tool = "gh"
        rest = command[2:].strip()

    if not rest:
        return (tool, "")

    # For git, handle -C <path> and -c <key=value> options
    if tool == "git":
        # Keep processing until we get to the actual subcommand
        while rest:
            # Handle -C <path>
            match = re.match(r'^-C\s+("[^"]+"|\'[^\']+\'|\S+)\s*(.*)', rest)
            if match:
                rest = match.group(2).strip()
                continue

            # Handle -c <key=value>
            match = re.match(r'^-c\s+("[^"]+"|\'[^\']+\'|\S+)\s*(.*)', rest)
            if match:
                rest = match.group(2).strip()
                continue

            # Handle --git-dir=<path>
            match = re.match(r'^--git-dir[=\s]+("[^"]+"|\'[^\']+\'|\S+)\s*(.*)', rest)
            if match:
                rest = match.group(2).strip()
                continue

            # Handle --work-tree=<path>
            match = re.match(r'^--work-tree[=\s]+("[^"]+"|\'[^\']+\'|\S+)\s*(.*)', rest)
            if match:
                rest = match.group(2).strip()
                continue

            # No more options to strip, we have the subcommand
            break

    return (tool, rest)


def check_deny_patterns(command: str, deny_config: dict) -> Optional[dict]:
    """
    Check if command matches any deny patterns.

    Returns:
        Dict with 'reason' and 'alternative' if denied, None otherwise.
    """
    # Check regex patterns (for git commands with flags)
    for pattern in deny_config.get("patterns", []):
        if re.search(pattern["match"], command, re.IGNORECASE):
            return {
                "reason": pattern["reason"],
                "alternative": pattern.get("alternative", "")
            }

    # Check literal command patterns
    for cmd_pattern in deny_config.get("commands", []):
        if re.search(cmd_pattern["match"], command, re.IGNORECASE):
            return {
                "reason": cmd_pattern["reason"],
                "alternative": cmd_pattern.get("alternative", "")
            }

    return None


def check_ask_patterns(tool: str, subcommand: str, ask_config: dict) -> Optional[dict]:
    """
    Check if command matches any ask patterns.

    Returns:
        Dict with 'risk', 'safer', and optionally 'note' if needs confirmation, None otherwise.
    """
    tool_config = ask_config.get(tool, [])

    for pattern in tool_config:
        cmd = pattern["cmd"]
        # Check if subcommand starts with or contains the pattern
        # Handle both "merge" matching "merge main" and "push --force" matching "push --force origin"
        if subcommand.startswith(cmd) or f" {cmd}" in f" {subcommand}":
            return {
                "cmd": cmd,
                "risk": pattern["risk"],
                "safer": pattern.get("safer", []),
                "note": pattern.get("note", "")
            }

    return None


def format_deny_message(command: str, deny_info: dict) -> str:
    """Format a detailed deny message."""
    lines = [
        "",
        "=" * 70,
        "BLOCKED: Prohibited Git Command",
        "=" * 70,
        "",
        f"Command: {command}",
        "",
        f"THIS COMMAND IS NEVER ALLOWED because it {deny_info['reason']}.",
        "",
        "WHY THIS IS BLOCKED:",
        "  - Pre-commit hooks catch security vulnerabilities",
        "  - Hooks enforce consistent code formatting",
        "  - Bypassing hooks violates development standards",
        "",
    ]

    if deny_info.get("alternative"):
        lines.extend([
            "WHAT TO DO INSTEAD:",
            f"  - {deny_info['alternative']}",
            "",
        ])

    lines.append("=" * 70)

    return "\n".join(lines)


def format_ask_message(command: str, tool: str, ask_info: dict) -> str:
    """Format a detailed ask/warning message."""
    lines = [
        "",
        "=" * 70,
        f"CAUTION: Potentially Dangerous {'Git' if tool == 'git' else 'GitHub CLI'} Command",
        "=" * 70,
        "",
        f"Command: {command}",
        "",
        f"RISK: {ask_info['risk']}",
        "",
    ]

    # Add note if present (e.g., for gh pr merge)
    if ask_info.get("note"):
        lines.extend([
            "IMPORTANT:",
            f"  {ask_info['note']}",
            "",
        ])

    lines.append("WHY THIS MATTERS:")

    # Add context-specific warnings
    if "reset" in ask_info.get("cmd", ""):
        lines.extend([
            "  - Uncommitted changes may be discarded forever",
            "  - Cannot be undone without reflog knowledge",
            "  - May cause confusion if you forget what was lost",
        ])
    elif "force" in ask_info.get("cmd", ""):
        lines.extend([
            "  - Remote history will be overwritten",
            "  - Other collaborators may lose their work",
            "  - Can cause major repository synchronization issues",
        ])
    elif "merge" in ask_info.get("cmd", "") and tool == "gh":
        lines.extend([
            "  - Merging should only be done when explicitly requested",
            "  - PR may not be ready (failing checks, pending reviews)",
            "  - Accidental merges can be difficult to revert",
        ])
    elif "delete" in ask_info.get("cmd", ""):
        lines.extend([
            "  - This action is permanent and cannot be undone",
            "  - Others may depend on this resource",
            "  - Ensure you have backups if needed",
        ])
    elif "close" in ask_info.get("cmd", ""):
        lines.extend([
            "  - Work may be lost or harder to find later",
            "  - Accidental closure can disrupt workflows",
            "  - Consider if this is the right action",
        ])
    else:
        lines.extend([
            "  - This operation may have unintended consequences",
            "  - Changes may be difficult or impossible to reverse",
            "  - Verify this is the intended action",
        ])

    lines.append("")

    if ask_info.get("safer"):
        lines.append("SAFER ALTERNATIVES:")
        for alt in ask_info["safer"]:
            lines.append(f"  - {alt}")
        lines.append("")

    lines.extend([
        "To proceed, you must explicitly confirm this operation.",
        "=" * 70,
    ])

    return "\n".join(lines)


def main():
    """Main hook entry point."""
    # Read JSON input from stdin
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        # Not valid JSON, pass through
        sys.exit(0)

    # Check if this is a Bash tool call
    tool_name = input_data.get("tool_name", "")
    if tool_name != "Bash":
        sys.exit(0)

    # Extract the command
    tool_input = input_data.get("tool_input", {})
    command = tool_input.get("command", "")

    if not command:
        sys.exit(0)

    # Parse the command to identify git/gh
    parsed = extract_git_command(command)

    if parsed is None:
        # Not a git/gh command, pass through
        sys.exit(0)

    tool, subcommand = parsed

    # Load configurations
    deny_config = load_config("deny")
    ask_config = load_config("ask")

    # Check DENY list first (highest priority)
    deny_info = check_deny_patterns(command, deny_config)
    if deny_info:
        message = format_deny_message(command, deny_info)
        print(message)
        sys.exit(2)

    # Check ASK list
    ask_info = check_ask_patterns(tool, subcommand, ask_config)
    if ask_info:
        message = format_ask_message(command, tool, ask_info)
        print(message)
        sys.exit(2)

    # Default: ALLOW (exit 0 with no output)
    sys.exit(0)


if __name__ == "__main__":
    main()
