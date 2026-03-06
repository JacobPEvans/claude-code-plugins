#!/usr/bin/env python3
"""
Claude Code PreToolUse hook for GitHub issue and PR rate limiting.
Blocks `gh issue create` when issue limits are exceeded, and enforces
24-hour rate limits on issue and PR creation/updates.

Limits:
  - 50 total open issues: Hard block on issue creation
  - 25 AI-created issues: Hard block on issue creation
  - 15 issues created in 24 hours: Rate limit block (checked per resource type)
  - 15 PRs created in 24 hours: Rate limit block (checked per resource type)

Exit codes:
  0 = allow the command
  2 = block the command (shows stderr to Claude)

Input: JSON from stdin with tool_input.command containing the Bash command
"""

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone

# Hard limits for issue creation
TOTAL_ISSUE_LIMIT = 50
AI_ISSUE_LIMIT = 25

# 24-hour rate limit for issues and PRs
RATE_LIMIT_24H = 15

_GH_ERRORS = (
    subprocess.TimeoutExpired,
    subprocess.SubprocessError,
    json.JSONDecodeError,
    ValueError,
)


def get_issue_counts() -> tuple[int, int]:
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
    except _GH_ERRORS as e:
        print(
            f"Warning: Could not determine issue counts: {e}. "
            "Allowing command to proceed.",
            file=sys.stderr,
        )
        return 0, 0


def _count_recent(resource: str, extra_args: list[str] | None = None) -> int:
    """Count items of `resource` ('issue' or 'pr') created in the last 24 hours."""
    cmd = [
        "gh", resource, "list", "--state", "all",
        "--json", "createdAt", "--limit", "100",
    ]
    if extra_args:
        cmd.extend(extra_args)
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True, timeout=30
        )
        items = json.loads(result.stdout)
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        return sum(
            1 for item in items
            if item.get("createdAt")
            and datetime.fromisoformat(item["createdAt"].replace("Z", "+00:00")) >= cutoff
        )
    except _GH_ERRORS as e:
        print(
            f"Warning: Could not check recent {resource}s: {e}. "
            "Allowing command to proceed.",
            file=sys.stderr,
        )
        return 0


def block_rate_limit(kind: str, count: int) -> None:
    """Print rate limit block message and exit with code 2."""
    print(
        f"\n{'=' * 64}\n"
        f"BLOCKED: Rate limit exceeded\n"
        f"{'=' * 64}\n\n"
        f"  {RATE_LIMIT_24H}+ {kind} created in the past 24 hours "
        f"(count: {count}).\n\n"
        "Ask the user for explicit permission before creating or updating "
        "another issue or pull request.\n"
        f"{'=' * 64}\n",
        file=sys.stderr,
        flush=True,
    )
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
            reasons_str = "\n".join(f"  {r}" for r in reasons)
            print(
                f"\n{'=' * 64}\n"
                f"BLOCKED: Issue creation limit exceeded\n"
                f"{'=' * 64}\n\n"
                f"{reasons_str}\n\n"
                "Required actions:\n"
                "  1. Close or resolve duplicate and completed issues\n"
                "  2. Focus on creating PRs to close existing issues\n"
                "  3. Ask the user for explicit permission to create more issues\n\n"
                f"{'=' * 64}\n",
                file=sys.stderr,
                flush=True,
            )
            sys.exit(2)

        # Check 24h issue rate limit
        recent_issues = _count_recent("issue")
        if recent_issues >= RATE_LIMIT_24H:
            block_rate_limit("issues", recent_issues)

    # --- gh pr create / gh pr edit: check 24h PR rate limit ---
    if is_pr_create or is_pr_edit:
        recent_prs = _count_recent("pr", ["--author", "@me"])
        if recent_prs >= RATE_LIMIT_24H:
            block_rate_limit("PRs", recent_prs)


if __name__ == "__main__":
    main()
