#!/usr/bin/env python3
"""
Claude Code PreToolUse hook for GitHub issue and PR rate limiting.

Blocks `gh issue create` and `gh pr create` when limits are exceeded.
Uses `--author @me` for identity-based filtering (unforgeable).

Hard limits (per-repo):
  - 100 total open issues
  - 15 total open PRs
  - 25 AI-created open issues/PRs (labeled "ai-created")

Rate limits (24h rolling window):
  - 25 issues created by @me
  - 25 PRs created by @me

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

# Hard limits: (total_open, ai_created_open) per resource type
HARD_LIMITS = {"issue": (100, 25), "pr": (15, 15)}

# 24h rolling rate limit per resource type
RATE_LIMIT_24H = 25

_CMD_RE = re.compile(r"(?:^|\s)gh\s+(issue|pr)\s+(create|edit)(?:\s|$)")

_GH_ERRORS = (
    OSError,
    subprocess.TimeoutExpired,
    subprocess.SubprocessError,
    json.JSONDecodeError,
    ValueError,
)


def _extract_repo_dir(command: str) -> str | None:
    """Extract target repo directory from cd prefix in bash commands."""
    m = re.match(r'^\s*cd\s+("(?:[^"]+)"|\'(?:[^\']+)\'|[^\s;&]+)', command)
    if m:
        path = m.group(1).strip("'\"")
        path = os.path.abspath(os.path.expanduser(path))
        if not os.path.isdir(path):
            return None
        return path
    return None


def _gh_json(args: list[str], cwd: str | None = None) -> list[dict]:
    """Run a gh command that returns JSON, fail-open on any error."""
    try:
        result = subprocess.run(
            ["gh", *args],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
            cwd=cwd,
        )
        return json.loads(result.stdout)
    except _GH_ERRORS as e:
        print(
            f"Warning: gh command failed: {e}. Allowing command to proceed.",
            file=sys.stderr,
        )
        return []


def _get_counts(resource: str, cwd: str | None = None) -> tuple[int, int]:
    """Count total and AI-created open items for a resource type."""
    items = _gh_json([
        resource, "list", "--state", "open",
        "--json", "number,labels", "--limit", "100",
    ], cwd=cwd)
    total = len(items)
    ai_created = sum(
        1 for item in items
        if any(label["name"] == "ai-created" for label in item.get("labels", []))
    )
    return total, ai_created


def _count_recent(resource: str, cwd: str | None = None) -> int:
    """Count items created by @me in the last 24 hours."""
    items = _gh_json([
        resource, "list", "--state", "all",
        "--author", "@me",
        "--json", "createdAt", "--limit", "100",
    ], cwd=cwd)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    return sum(
        1 for item in items
        if item.get("createdAt")
        and datetime.fromisoformat(item["createdAt"].replace("Z", "+00:00")) >= cutoff
    )


def _normalize_title(title: str) -> list[str]:
    """Strip conventional-commit prefix and return first 4 lowercase words."""
    cleaned = re.sub(r"^[a-z]+(\([^)]*\))?:\s*", "", title.strip().lower())
    return cleaned.split()[:4]


def _check_duplicate(resource: str, label: str, command: str, cwd: str | None = None) -> None:
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

    proposed = _normalize_title(title)
    if len(proposed) < 2:
        return

    items = _gh_json([
        resource, "list", "--state", "open",
        "--json", "title,number", "--limit", "100",
    ], cwd=cwd)
    for item in items:
        existing_title = item.get("title", "")
        existing_words = _normalize_title(existing_title)
        if len(existing_words) >= 2 and proposed == existing_words:
            _block(
                f"Duplicate {label} detected",
                f"Your title matches existing #{item['number']}: {existing_title!r}\n\n"
                f"Ask the user before creating a duplicate {label}.",
            )


def _block(reason: str, details: str) -> None:
    """Print block message and exit with code 2."""
    indented = "\n".join(f"  {line}" if line else "" for line in details.splitlines())
    print(
        f"\n{'=' * 64}\n"
        f"BLOCKED: {reason}\n"
        f"{'=' * 64}\n\n"
        f"{indented}\n\n"
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

    # Edits modify existing items — never rate-limit them
    if action == "edit":
        sys.exit(0)

    label = resource.upper() if resource == "pr" else resource.capitalize()

    # Extract target repo directory from cd prefix (fixes CWD bug)
    repo_dir = _extract_repo_dir(command)

    # Create-only checks: duplicate detection and hard limits
    if action == "create":
        _check_duplicate(resource, label, command, cwd=repo_dir)

        total_limit, ai_limit = HARD_LIMITS[resource]
        total, ai_created = _get_counts(resource, cwd=repo_dir)

        reasons = []
        if total >= total_limit:
            reasons.append(f"Total {label}s: {total}/{total_limit} (limit reached)")
        if ai_created >= ai_limit:
            reasons.append(f"AI-created {label}s: {ai_created}/{ai_limit} (limit reached)")
        if reasons:
            reasons_str = "\n  ".join(reasons)
            _block(
                f"{label} creation limit exceeded",
                f"{reasons_str}\n\n"
                f"Required actions:\n"
                f"  1. Close or resolve duplicate and completed {label}s\n"
                f"  2. Ask the user for explicit permission to create more {label}s",
            )

    # 24h rate limit (create only — edits are always allowed)
    if action == "create":
        recent = _count_recent(resource, cwd=repo_dir)
        if recent >= RATE_LIMIT_24H:
            _block(
                "Rate limit exceeded",
                f"{recent} {label}s created in the past 24 hours (limit: {RATE_LIMIT_24H}).\n\n"
                "The user can re-run the blocked command directly in their\n"
                "terminal to bypass this rate limit.",
            )


if __name__ == "__main__":
    main()
