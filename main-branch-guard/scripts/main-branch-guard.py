#!/usr/bin/env python3
"""
main-branch-guard.py - PreToolUse hook to prevent Edit/Write/NotebookEdit on main branch

Blocks file editing operations when:
1. The file path contains '/main/' as a directory segment (worktree check)
2. The current branch is 'main' (fallback branch check)

Follows fail-open philosophy: any errors allow the operation to proceed.
Exit codes: 0=allow or error, 2=deny (unused, we exit 0 with JSON)
"""

import json
import sys
import subprocess
from pathlib import Path


def main():
    try:
        # Parse input from stdin
        input_data = json.loads(sys.stdin.read())
        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})

        # Early exit: only care about Edit, Write, NotebookEdit
        if tool_name not in ["Edit", "Write", "NotebookEdit"]:
            sys.exit(0)

        # Extract file_path based on tool type
        if tool_name == "NotebookEdit":
            file_path = tool_input.get("notebook_path")
        else:
            file_path = tool_input.get("file_path")

        if not file_path:
            # No file path provided, allow (fail-open)
            sys.exit(0)

        # Path check: resolve to absolute path
        try:
            abs_path = Path(file_path).resolve()
            path_parts = abs_path.parts

            # Check if '/main/' appears as a directory segment
            if "main" in path_parts:
                # Find the index to ensure it's a directory, not filename
                main_index = path_parts.index("main")
                # Ensure it's not the last component (the file itself)
                if main_index < len(path_parts) - 1:
                    deny_operation(
                        f"File '{file_path}' is in the main worktree. "
                        "Editing files on the main branch is not allowed."
                    )
        except Exception:
            # Path resolution failed, continue to branch check
            pass

        # Branch check (fallback): check current git branch
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )

            if result.returncode == 0:
                current_branch = result.stdout.strip()
                if current_branch == "main":
                    deny_operation(
                        f"Current branch is 'main'. "
                        "Editing files on the main branch is not allowed."
                    )
        except Exception:
            # Git command failed, fail-open
            pass

        # All checks passed or failed-open, allow operation
        sys.exit(0)

    except Exception:
        # Any unexpected error: fail-open (allow operation)
        sys.exit(0)


def deny_operation(message):
    """Output deny decision and exit"""
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"BLOCKED: {message}\n\nRun `/init-worktree` to create a feature branch.",
        }
    }
    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()
