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
import re
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


def _is_year_reference(text_lower: str, year: int) -> bool:
    """
    Heuristically determine whether a numeric occurrence of `year` in the
    given lowercased text is likely to be a calendar year, rather than
    part of another identifier (for example "RFC 2024" or "ISO 2022").
    """
    year_str = str(year)

    # Ignore some known identifier-style prefixes where the number is not a date.
    # Example false positives the rule warns about:
    # - "RFC 2024" (RFC number)
    # - "ISO 2022" (standard identifier)
    if re.search(rf"\b(?:rfc|iso)\s+{year_str}\b", text_lower):
        return False

    # Fallback: treat a standalone numeric token as a year reference.
    # This is similar to the old \b{year}\b check but routed through this helper
    # so that we can centralize exclusions above.
    return re.search(rf"\b{year_str}\b", text_lower) is not None


def find_blocked_year(text: str, blocked_years: list[int]) -> int | None:
    """Find first blocked year in text, or None."""
    text_lower = text.lower()
    # Check for more recent years first (optimization)
    for year in sorted(blocked_years, reverse=True):
        if _is_year_reference(text_lower, year):
            return year
    return None


def main():
    # Define year block range constant (years to block: current - 2)
    YEAR_BLOCK_RANGE = 2

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
        blocked_years = list(range(current_year - YEAR_BLOCK_RANGE, current_year - 1))
    else:
        blocked_years = list(range(current_year - YEAR_BLOCK_RANGE, current_year))

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
            f"Your search included an outdated year. The current date is {formatted_date}.\n\n"
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
