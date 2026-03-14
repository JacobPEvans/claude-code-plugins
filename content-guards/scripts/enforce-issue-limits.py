#!/usr/bin/env python3
"""
Claude Code PreToolUse hook for GitHub issue and PR rate limiting.

Blocks `gh issue create` and `gh pr create/edit` when limits are exceeded.
Uses `--author @me` for identity-based filtering (unforgeable).

Hard limits (per-repo):
  - 50 total open issues/PRs
  - 25 AI-created open issues/PRs (labeled "ai-created")

Rate limits (24h rolling window):
  - 10 issues created by @me
  - 10 PRs created by @me

Exit codes:
  0 = allow the command
  2 = block the command (shows stderr to Claude)

Input: JSON from stdin with tool_input.command containing the Bash command
"""

import json
import re
import shlex
import subprocess
import sys
from datetime import datetime, timedelta, timezone

# Hard limits: (total_open, ai_created_open) per resource type
HARD_LIMITS = {"issue": (50, 25), "pr": (50, 25)}

# 24h rolling rate limit per resource type
RATE_LIMIT_24H = 10

_CMD_RE = re.compile(r"(?:^|\s)gh\s+(issue|pr)\s+(create|edit)(?:\s|$)")

_GH_ERRORS = (
    subprocess.TimeoutExpired,
    subprocess.SubprocessError,
    json.JSONDecodeError,
    ValueError,
)


def _gh_json(args: list[str]) -> list[dict]:
    """Run a gh command that returns JSON, fail-open on any error."""
    try:
        result = subprocess.run(
            ["gh", *args],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
        return json.loads(result.stdout)
    except _GH_ERRORS as e:
        print(
            f"Warning: gh command failed: {e}. Allowing command to proceed.",
            file=sys.stderr,
        )
        return []


def _get_counts(resource: str) -> tuple[int, int]:
    """Count total and AI-created open items for a resource type."""
    items = _gh_json([
        resource, "list", "--state", "open",
        "--json", "number,labels", "--limit", "100",
    ])
    total = len(items)
    ai_created = sum(
        1 for item in items
        if any(label["name"] == "ai-created" for label in item.get("labels", []))
    )
    return total, ai_created


def _count_recent(resource: str) -> int:
    """Count items created by @me in the last 24 hours."""
    items = _gh_json([
        resource, "list", "--state", "all",
        "--author", "@me",
        "--json", "createdAt", "--limit", "100",
    ])
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    return sum(
        1 for item in items
        if item.get("createdAt")
        and datetime.fromisoformat(item["createdAt"].replace("Z", "+00:00")) >= cutoff
    )


def _check_duplicate(resource: str, label: str, command: str) -> None:
    """Block if an open item has a similar title to the one being created."""
    try:
        tokens = shlex.split(command)
    except ValueError:
        return
    # Extract --title value
    title = None
    for i, token in enumerate(tokens):
        if token == "--title" and i + 1 < len(tokens):
            title = tokens[i + 1]
            break
        if token.startswith("--title="):
            title = token[len("--title="):]
            break
    if not title:
        return

    # Normalize: strip type prefix (e.g. "fix:") and take first 4 words
    cleaned = re.sub(r"^[a-z]+(\([^)]*\))?:\s*", "", title.strip().lower())
    proposed = cleaned.split()[:4]
    if len(proposed) < 2:
        return

    items = _gh_json([
        resource, "list", "--state", "open",
        "--json", "title,number", "--limit", "100",
    ])
    for item in items:
        existing_title = item.get("title", "")
        existing_cleaned = re.sub(r"^[a-z]+(\([^)]*\))?:\s*", "", existing_title.strip().lower())
        existing_words = existing_cleaned.split()[:4]
        if len(existing_words) >= 2 and proposed == existing_words:
            _block(
                f"Duplicate {label} detected",
                f"Your title matches existing #{item['number']}: {existing_title!r}\n\n"
                f"Ask the user before creating a duplicate {label.lower()}.",
            )


def _block(reason: str, details: str) -> None:
    """Print block message and exit with code 2."""
    print(
        f"\n{'=' * 64}\n"
        f"BLOCKED: {reason}\n"
        f"{'=' * 64}\n\n"
        f"  {details}\n\n"
        f"{'=' * 64}\n",
        file=sys.stderr,
        flush=True,
    )
    sys.exit(2)


def main() -> None:
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    command = hook_input.get("tool_input", {}).get("command", "")
    match = _CMD_RE.search(command)
    if not match:
        sys.exit(0)

    resource = match.group(1)  # "issue" or "pr"
    action = match.group(2)    # "create" or "edit"
    label = resource.upper() if resource == "pr" else resource.capitalize()

    # Duplicate detection (create only)
    if action == "create":
        _check_duplicate(resource, label, command)

    # Hard limits (create only)
    if action == "create":
        total_limit, ai_limit = HARD_LIMITS[resource]
        total, ai_created = _get_counts(resource)

        reasons = []
        if total >= total_limit:
            reasons.append(f"Total {resource}s: {total}/{total_limit} (limit reached)")
        if ai_created >= ai_limit:
            reasons.append(f"AI-created {resource}s: {ai_created}/{ai_limit} (limit reached)")
        if reasons:
            reasons_str = "\n  ".join(reasons)
            _block(
                f"{label} creation limit exceeded",
                f"{reasons_str}\n\n"
                f"Required actions:\n"
                f"  1. Close or resolve duplicate and completed {label.lower()}s\n"
                f"  2. Ask the user for explicit permission to create more {label.lower()}s",
            )

    # 24h rate limit (create and edit for PRs, create only for issues)
    if action == "create" or (resource == "pr" and action == "edit"):
        recent = _count_recent(resource)
        if recent >= RATE_LIMIT_24H:
            _block(
                "Rate limit exceeded",
                f"{recent} {resource}s created in the past 24 hours (limit: {RATE_LIMIT_24H}).\n\n"
                "The user can re-run the blocked command directly in their\n"
                "terminal to bypass this rate limit.",
            )


if __name__ == "__main__":
    main()
