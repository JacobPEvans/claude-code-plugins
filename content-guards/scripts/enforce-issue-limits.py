#!/usr/bin/env python3
"""
Claude Code PreToolUse hook for GitHub issue and PR rate limiting.
Blocks `gh issue create` when issue limits are exceeded, and enforces
two-tier 24-hour rate limits on issue and PR creation/updates.

Rate limit tiers (configurable via rate-limit-config.json):
  - Trusted users (allowlisted by GitHub user ID): higher limits
  - Default (everyone else: bots, AI, unknown): stricter limits

Hard limits (per-repo):
  - 50 total open issues: Hard block on issue creation
  - 25 AI-created issues: Hard block on issue creation
  - 50 total open PRs: Hard block on PR creation
  - 25 AI-created PRs: Hard block on PR creation

Exit codes:
  0 = allow the command
  2 = block the command (shows stderr to Claude)

Input: JSON from stdin with tool_input.command containing the Bash command
"""

import json
import os
import re
import shlex
import subprocess
import sys
from datetime import datetime, timedelta, timezone

# Hard limits for issue creation
TOTAL_ISSUE_LIMIT = 50
AI_ISSUE_LIMIT = 25

# Hard limits for PR creation
TOTAL_PR_LIMIT = 50
AI_PR_LIMIT = 25

_GH_ERRORS = (
    subprocess.TimeoutExpired,
    subprocess.SubprocessError,
    json.JSONDecodeError,
    ValueError,
)


_DEFAULT_CONFIG = {
    "trusted_user_ids": [],
    "limits": {
        "trusted": {"issues_24h": 10, "prs_24h": 20},
        "default": {"issues_24h": 5, "prs_24h": 5},
    },
}


def _load_rate_config() -> dict:
    """Load rate limit config from .github repo or use defaults.

    Only loads from the canonical shared config location to prevent
    untrusted repos from overriding rate limits via a local file.
    """
    path = os.path.expanduser("~/git/.github/main/.github/rate-limit-config.json")
    try:
        with open(path) as f:
            config = json.load(f)
    except (OSError, json.JSONDecodeError):
        return _DEFAULT_CONFIG

    # Validate expected shape; fall back to defaults for missing keys
    if not isinstance(config, dict):
        return _DEFAULT_CONFIG
    trusted_ids = config.get("trusted_user_ids", [])
    # Coerce string IDs to int (JSON files may be hand-edited)
    coerced: list[int] = []
    for uid in trusted_ids:
        try:
            coerced.append(int(uid))
        except (ValueError, TypeError):
            continue
    limits_raw = config.get("limits", {})
    defaults = _DEFAULT_CONFIG["limits"]
    return {
        "trusted_user_ids": coerced,
        "limits": {
            "trusted": {
                "issues_24h": limits_raw.get("trusted", {}).get("issues_24h", defaults["trusted"]["issues_24h"]),
                "prs_24h": limits_raw.get("trusted", {}).get("prs_24h", defaults["trusted"]["prs_24h"]),
            },
            "default": {
                "issues_24h": limits_raw.get("default", {}).get("issues_24h", defaults["default"]["issues_24h"]),
                "prs_24h": limits_raw.get("default", {}).get("prs_24h", defaults["default"]["prs_24h"]),
            },
        },
    }


def _get_current_user_id() -> int | None:
    """Get the numeric GitHub user ID of the authenticated user."""
    try:
        result = subprocess.run(
            ["gh", "api", "user", "--jq", ".id"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        return int(result.stdout.strip())
    except (subprocess.SubprocessError, ValueError):
        return None  # fail-open: unknown user gets default limits


def get_issue_counts() -> tuple[int, int]:
    """Count total and AI-created open issues in one pass."""
    cmd = ["gh", "issue", "list", "--state", "open", "--json", "number,labels", "--limit", "100"]
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


def get_pr_counts() -> tuple[int, int]:
    """Count total and AI-created open PRs in one pass."""
    cmd = ["gh", "pr", "list", "--state", "open", "--json", "number,labels", "--limit", "100"]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True, timeout=30
        )
        prs = json.loads(result.stdout)
        total_prs = len(prs)
        ai_created_prs = sum(
            1
            for pr in prs
            if any(label["name"] == "ai-created" for label in pr.get("labels", []))
        )
        return total_prs, ai_created_prs
    except _GH_ERRORS as e:
        print(
            f"Warning: Could not determine PR counts: {e}. "
            "Allowing command to proceed.",
            file=sys.stderr,
        )
        return 0, 0


def _count_recent(resource: str) -> int:
    """Count items of `resource` ('issue' or 'pr') created by @me in the last 24 hours."""
    cmd = [
        "gh", resource, "list", "--state", "all",
        "--author", "@me",
        "--json", "createdAt", "--limit", "100",
    ]
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


def block_rate_limit(kind: str, count: int, limit: int) -> None:
    """Print rate limit block message and exit with code 2."""
    print(
        f"\n{'=' * 64}\n"
        f"BLOCKED: Rate limit exceeded\n"
        f"{'=' * 64}\n\n"
        f"  {count} {kind} created in the past 24 hours (limit: {limit}).\n\n"
        "The user can re-run the blocked command directly in their\n"
        "terminal to bypass this rate limit.\n\n"
        f"{'=' * 64}\n",
        file=sys.stderr,
        flush=True,
    )
    sys.exit(2)


def block_hard_limit(resource_kind: str, reasons: list[str]) -> None:
    """Print hard limit block message and exit with code 2."""
    reasons_str = "\n".join(f"  {r}" for r in reasons)
    print(
        f"\n{'=' * 64}\n"
        f"BLOCKED: {resource_kind} creation limit exceeded\n"
        f"{'=' * 64}\n\n"
        f"{reasons_str}\n\n"
        "Required actions:\n"
        f"  1. Close or resolve duplicate and completed {resource_kind.lower()}s\n"
        f"  2. Ask the user for explicit permission to create more {resource_kind.lower()}s\n\n"
        f"{'=' * 64}\n",
        file=sys.stderr,
        flush=True,
    )
    sys.exit(2)


def extract_flag_value(command: str, flag: str) -> str | None:
    """Extract the value of a CLI flag (e.g. --title) from a command string."""
    try:
        tokens = shlex.split(command)
    except ValueError:
        return None
    for i, token in enumerate(tokens):
        if token == flag and i + 1 < len(tokens):
            return tokens[i + 1]
        if token.startswith(f"{flag}="):
            return token[len(flag) + 1 :]
    return None


def normalize_title(title: str) -> list[str]:
    """Strip type prefix (e.g. 'fix:', 'docs:') and return first 4 lowercase words."""
    cleaned = re.sub(r"^[a-z]+(\([^)]*\))?:\s*", "", title.strip().lower())
    words = cleaned.split()
    return words[:4]


def _block_duplicate(kind: str, title: str, existing_number: int) -> None:
    """Print duplicate block message and exit with code 2."""
    print(
        f"\n{'=' * 64}\n"
        f"BLOCKED: Duplicate {kind} detected\n"
        f"{'=' * 64}\n\n"
        f"  Your title matches existing #{existing_number}: {title!r}\n\n"
        f"Ask the user before creating a duplicate {kind}.\n"
        f"{'=' * 64}\n",
        file=sys.stderr,
        flush=True,
    )
    sys.exit(2)


def check_duplicate_pr(command: str) -> None:
    """Block if an open PR has a similar title to the one being created."""
    title = extract_flag_value(command, "--title")
    if not title:
        return
    proposed = normalize_title(title)
    if len(proposed) < 2:
        return
    cmd = ["gh", "pr", "list", "--state", "open", "--json", "title,number", "--limit", "100"]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True, timeout=30
        )
        prs = json.loads(result.stdout)
    except _GH_ERRORS:
        return  # fail-open
    for pr in prs:
        existing = normalize_title(pr.get("title", ""))
        if len(existing) >= 2 and proposed == existing:
            _block_duplicate("PR", pr["title"], pr["number"])


def check_duplicate_issue(command: str) -> None:
    """Block if an open issue has a similar title to the one being created."""
    title = extract_flag_value(command, "--title")
    if not title:
        return
    proposed = normalize_title(title)
    if len(proposed) < 2:
        return
    cmd = ["gh", "issue", "list", "--state", "open", "--json", "title,number", "--limit", "100"]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True, timeout=30
        )
        issues = json.loads(result.stdout)
    except _GH_ERRORS:
        return  # fail-open
    for issue in issues:
        existing = normalize_title(issue.get("title", ""))
        if len(existing) >= 2 and proposed == existing:
            _block_duplicate("issue", issue["title"], issue["number"])


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

    # --- Load two-tier rate config ---
    config = _load_rate_config()
    user_id = _get_current_user_id()
    is_trusted = user_id in config.get("trusted_user_ids", [])
    tier = "trusted" if is_trusted else "default"
    limits = config.get("limits", {}).get(tier, _DEFAULT_CONFIG["limits"][tier])

    # --- Duplicate detection (before rate limits) ---
    if is_pr_create:
        check_duplicate_pr(command)
    if is_issue_create:
        check_duplicate_issue(command)

    # --- gh issue create: check existing limits AND 24h rate limit ---
    if is_issue_create:
        # Check hard limits (50 total / 25 ai-created)
        total, ai_created = get_issue_counts()

        reasons = []
        if total >= TOTAL_ISSUE_LIMIT:
            reasons.append(f"Total issues: {total}/{TOTAL_ISSUE_LIMIT} (limit reached)")
        if ai_created >= AI_ISSUE_LIMIT:
            reasons.append(
                f"AI-created issues: {ai_created}/{AI_ISSUE_LIMIT} (limit reached)"
            )
        if reasons:
            block_hard_limit("Issue", reasons)

        # Check 24h issue rate limit
        recent_issues = _count_recent("issue")
        if recent_issues >= limits["issues_24h"]:
            block_rate_limit("issues", recent_issues, limits["issues_24h"])

    # --- gh pr create: check hard limits AND 24h PR rate limit ---
    if is_pr_create:
        # Check hard limits (50 total / 25 ai-created)
        total, ai_created = get_pr_counts()

        reasons = []
        if total >= TOTAL_PR_LIMIT:
            reasons.append(f"Total PRs: {total}/{TOTAL_PR_LIMIT} (limit reached)")
        if ai_created >= AI_PR_LIMIT:
            reasons.append(
                f"AI-created PRs: {ai_created}/{AI_PR_LIMIT} (limit reached)"
            )
        if reasons:
            block_hard_limit("PR", reasons)

    # --- gh pr create / gh pr edit: check 24h PR rate limit ---
    # Note: `_count_recent` counts by `createdAt`, so `gh pr edit` on a PR
    # that was created more than 24 hours ago does not accumulate against this
    # limit.  Tracking edit frequency would require a separate local state
    # file with timestamps, which is out of scope for this hook.  The rate
    # limit therefore applies to PR *creation* only; the `gh pr edit` guard
    # exists to catch same-session churn on newly created PRs.
    if is_pr_create or is_pr_edit:
        recent_prs = _count_recent("pr")
        if recent_prs >= limits["prs_24h"]:
            block_rate_limit("PRs", recent_prs, limits["prs_24h"])


if __name__ == "__main__":
    main()
