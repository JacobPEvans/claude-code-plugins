#!/usr/bin/env python3
"""
WebFetch Guard Hook

Blocks outdated year references in WebFetch/WebSearch tool calls.
Grace period (Jan-Mar): allows previous year, blocks 2+ years ago.
After grace period (Apr-Dec): blocks previous year and older.
Warns (but allows) current year searches.
"""

import json
import re
import sys
from datetime import datetime


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)

    tool_name = input_data.get("tool_name", "")
    if tool_name not in ("WebFetch", "WebSearch"):
        sys.exit(0)

    tool_input = input_data.get("tool_input", {})
    text = (
        f"{tool_input.get('url', '')} {tool_input.get('prompt', '')}"
        if tool_name == "WebFetch"
        else tool_input.get("query", "")
    )
    text_lower = text.lower()

    now = datetime.now()
    current_year = now.year
    current_month = now.month

    # Grace period (Jan-Mar): allow previous year, block 2+ years ago
    # After (Apr-Dec): block previous year and older
    if current_month <= 3:
        blocked_years = [current_year - 2]
    else:
        blocked_years = [current_year - 1, current_year - 2]

    # Find blocked year in text using word boundaries
    blocked_year = None
    for year in blocked_years:
        if re.search(rf"\b{year}\b", text_lower):
            blocked_year = year
            break

    if blocked_year:
        date_str = now.strftime("%B %d, %Y")
        reason = (
            f"BLOCKED: Your search contains '{blocked_year}' (outdated).\n\n"
            f"Current date: {date_str}\n"
            f"Current year: {current_year}\n\n"
            f"Please search using the current year or remove the year reference."
        )
        print(
            json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            })
        )
        return

    # Warn if current year is referenced (using word boundaries)
    if re.search(rf"\b{current_year}\b", text_lower):
        date_str = now.strftime("%B %d, %Y")
        reason = (
            f"WARNING: You're searching with the current year ({current_year}).\n\n"
            f"Current date: {date_str}\n\n"
            f"Always verify the current date before running date-specific searches."
        )
        print(
            json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "allow",
                    "permissionDecisionReason": reason,
                }
            })
        )


if __name__ == "__main__":
    main()
