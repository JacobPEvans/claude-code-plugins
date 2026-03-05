#!/usr/bin/env python3
"""
Claude Code PreToolUse hook for GitHub issue and PR rate limiting.
Blocks `gh issue create` when issue limits are exceeded, and enforces
24-hour rate limits on issue and PR creation/updates.

Limits:
  - 50 total open issues: Hard block on issue creation
  - 25 AI-created issues: Hard block on issue creation
  - 15 issues or PRs created/updated in 24 hours: Rate limit block

Exit codes:
  0 = allow the command
  2 = block the command (shows stderr to Claude)

Input: JSON from stdin with tool_input.command containing the Bash command
"""

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from typing import Tuple

# Hard limits for issue creation
TOTAL_ISSUE_LIMIT = 50
AI_ISSUE_LIMIT = 25

# 24-hour rate limit for issues and PRs
RATE_LIMIT_24H = 15


def get_issue_counts() -> Tuple[int, int]:
    """Count total and AI-created open issues in one pass."""
    cmd = ["gh", "issue", "list", "--state", "open", "--json", "number,labels"]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True, timeout=30
        )
        issues = json.loads(result.stdout)
        total_issues = len(issues)
        ai_created_issues = sum(
            1
            for issue in issues
            if any(label["name"] == "ai-created" for label in issue["labels"])
        )
        return total_issues, ai_created_issues
    except (
        subprocess.TimeoutExpired,
        subprocess.SubprocessError,
        subprocess.CalledProcessError,
        json.JSONDecodeError,
        ValueError,
    ) as e:
        # Fail open and allow command, but log warning
        print(
            f"Warning: Could not determine issue counts: {e}. "
            "Allowing command to proceed.",
            file=sys.stderr,
        )
        return 0, 0


def check_recent_issues() -> int:
    """Count issues created in the last 24 hours."""
    cmd = ["gh", "issue", "list", "--state", "all", "--json", "createdAt", "--limit", "100"]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True, timeout=30
        )
        issues = json.loads(result.stdout)
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        count = 0
        for issue in issues:
            created_at = issue.get("createdAt", "")
            if not created_at:
                continue
            created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            if created >= cutoff:
                count += 1
        return count
    except (
        subprocess.TimeoutExpired,
        subprocess.SubprocessError,
        subprocess.CalledProcessError,
        json.JSONDecodeError,
        ValueError,
    ) as e:
        print(
            f"Warning: Could not check recent issues: {e}. "
            "Allowing command to proceed.",
            file=sys.stderr,
        )
        return 0


def check_recent_prs() -> int:
    """Count PRs created or updated in the last 24 hours."""
    cmd = ["gh", "pr", "list", "--state", "all", "--json", "createdAt,updatedAt", "--limit", "100"]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True, timeout=30
        )
        prs = json.loads(result.stdout)
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        count = 0
        for pr in prs:
            created_at = pr.get("createdAt", "")
            updated_at = pr.get("updatedAt", "")
            in_window = False
            if created_at:
                created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                if created >= cutoff:
                    in_window = True
            if not in_window and updated_at:
                updated = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                if updated >= cutoff:
                    in_window = True
            if in_window:
                count += 1
        return count
    except (
        subprocess.TimeoutExpired,
        subprocess.SubprocessError,
        subprocess.CalledProcessError,
        json.JSONDecodeError,
        ValueError,
    ) as e:
        print(
            f"Warning: Could not check recent PRs: {e}. "
            "Allowing command to proceed.",
            file=sys.stderr,
        )
        return 0


def block_rate_limit(kind: str, count: int) -> None:
    """Print rate limit block message and exit with code 2."""
    print("\n" + "=" * 64, file=sys.stderr)
    print("BLOCKED: Rate limit exceeded", file=sys.stderr)
    print("=" * 64, file=sys.stderr)
    print("", file=sys.stderr)
    print(
        f"  {RATE_LIMIT_24H}+ {kind} created in the past 24 hours "
        f"(count: {count}).",
        file=sys.stderr,
    )
    print("", file=sys.stderr)
    print(
        "Ask the user for explicit permission before creating another.",
        file=sys.stderr,
    )
    print("=" * 64 + "\n", file=sys.stderr, flush=True)
    sys.exit(2)


def main() -> None:
    # Read hook input from stdin
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)  # Invalid input, allow

    # Get tool info and command
    tool_input = hook_input.get("tool_input", {})
    command = tool_input.get("command", "")
    stripped = command.strip()
    padded = f" {command} "

    is_issue_create = (
        stripped.startswith("gh issue create") or " gh issue create " in padded
    )
    is_pr_create = (
        stripped.startswith("gh pr create") or " gh pr create " in padded
    )
    is_pr_edit = (
        stripped.startswith("gh pr edit") or " gh pr edit " in padded
    )

    # Only act on commands we care about
    if not (is_issue_create or is_pr_create or is_pr_edit):
        sys.exit(0)

    # --- gh issue create: check existing limits AND 24h rate limit ---
    if is_issue_create:
        # Check hard limits (50 total / 25 ai:created)
        total, ai_created = get_issue_counts()

        blocked = False
        reasons = []

        if total >= TOTAL_ISSUE_LIMIT:
            blocked = True
            reasons.append(f"Total issues: {total}/{TOTAL_ISSUE_LIMIT} (limit reached)")

        if ai_created >= AI_ISSUE_LIMIT:
            blocked = True
            reasons.append(
                f"AI-created issues: {ai_created}/{AI_ISSUE_LIMIT} (limit reached)"
            )

        if blocked:
            print("\n" + "=" * 64, file=sys.stderr)
            print("BLOCKED: Issue creation limit exceeded", file=sys.stderr)
            print("=" * 64, file=sys.stderr)
            print("", file=sys.stderr)
            for reason in reasons:
                print(f"  {reason}", file=sys.stderr)
            print("", file=sys.stderr)
            print("Required actions:", file=sys.stderr)
            print("  1. Use the consolidate-issues skill to reduce issue count", file=sys.stderr)
            print("  2. Close duplicates and resolved issues", file=sys.stderr)
            print("  3. Focus on creating PRs to close existing issues", file=sys.stderr)
            print("", file=sys.stderr)
            print("See: agentsmd/skills/consolidate-issues/SKILL.md", file=sys.stderr)
            print("=" * 64 + "\n", file=sys.stderr, flush=True)
            sys.exit(2)

        # Check 24h issue rate limit
        recent_issues = check_recent_issues()
        if recent_issues >= RATE_LIMIT_24H:
            block_rate_limit("issues", recent_issues)

    # --- gh pr create / gh pr edit: check 24h PR rate limit ---
    if is_pr_create or is_pr_edit:
        recent_prs = check_recent_prs()
        if recent_prs >= RATE_LIMIT_24H:
            block_rate_limit("PRs", recent_prs)


if __name__ == "__main__":
    main()
