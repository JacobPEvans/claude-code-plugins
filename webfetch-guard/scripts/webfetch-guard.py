#!/usr/bin/env python3
"""
WebFetch Guard Hook

Intercepts WebFetch and WebSearch tool calls to:
1. BLOCK calls containing outdated years in URL or query
2. WARN (but allow) calls containing current year with a date reminder

Grace period logic (Jan-Mar):
- Previous year is ALLOWED (still relevant at year start)
- 2+ years ago is BLOCKED

After grace period (Apr-Dec):
- Previous year and older are BLOCKED

This helps ensure Claude uses current, up-to-date information.
"""

import json
import sys
from datetime import datetime


def build_response(decision: str, reason: str) -> dict:
    """Build a hook response."""
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": reason,
        }
    }


def find_blocked_year(text: str, blocked_years: list[int]) -> int | None:
    """Find first blocked year in text, or None."""
    text_lower = text.lower()
    for year in blocked_years:
        if str(year) in text_lower:
            return year
    return None


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Failed to parse input JSON: {e}", file=sys.stderr)
        sys.exit(1)

    tool_name = input_data.get("tool_name", "")
    if tool_name not in ("WebFetch", "WebSearch"):
        sys.exit(0)

    tool_input = input_data.get("tool_input", {})

    # Extract text to check based on tool type
    if tool_name == "WebFetch":
        combined_text = f"{tool_input.get('url', '')} {tool_input.get('prompt', '')}"
    else:  # WebSearch
        combined_text = tool_input.get("query", "")

    # Get current date/time info
    now = datetime.now()
    current_year = now.year
    current_month = now.month
    formatted_date = now.strftime("%A, %B %d, %Y")

    # Grace period: Jan-Mar allows previous year, blocks 2+ years ago
    in_grace_period = current_month <= 3

    if in_grace_period:
        blocked_years = list(range(current_year - 10, current_year - 1))
    else:
        blocked_years = list(range(current_year - 10, current_year))

    # Check for year references
    blocked_year = find_blocked_year(combined_text, blocked_years)
    has_current_year = str(current_year) in combined_text.lower()

    # BLOCK if outdated year found
    if blocked_year is not None:
        print(
            f"\n⚠️  BLOCKED: You searched an old year ({blocked_year}).\n"
            f"   Current date: {formatted_date}\n"
            f"   Please search using the current year ({current_year}) instead.\n",
            file=sys.stderr,
        )
        reason = (
            f"BLOCKED: Your request contains '{blocked_year}' which is an outdated year reference.\n\n"
            f"Hey, you searched an old year. The current time and date are: "
            f"{now.strftime('%Y-%m-%d %H:%M:%S')}. Try again.\n\n"
            f"CURRENT DATE: {formatted_date}\n"
            f"CURRENT YEAR: {current_year}\n\n"
            f"Please reformulate your request using the current year ({current_year}) "
            f"or remove the year reference entirely to get current information.\n\n"
            f"Tool: {tool_name}\n"
            f"Input: {combined_text[:200]}..."
        )
        print(json.dumps(build_response("deny", reason)))
        sys.exit(0)

    # WARN if current year is referenced
    if has_current_year:
        reason = (
            f"WARNING: Date-specific search detected.\n\n"
            f"====================================\n"
            f"CURRENT DATE: {formatted_date}\n"
            f"CURRENT YEAR: {current_year}\n"
            f"====================================\n\n"
            f"IMPORTANT: Always verify the current date before running web searches. "
            f"Your request contains '{current_year}', but remember:\n"
            f"- Check the current date at the start of each session\n"
            f"- Do not assume the year from previous searches\n"
            f"- When searching for 'latest' or 'recent' content, include the current year\n\n"
            f"Proceeding with {tool_name}..."
        )
        print(json.dumps(build_response("allow", reason)))
        sys.exit(0)


if __name__ == "__main__":
    main()
