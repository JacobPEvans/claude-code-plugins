#!/usr/bin/env python3
"""
WebFetch Guard Hook

Intercepts WebFetch and WebSearch tool calls to:
1. BLOCK calls containing "2024" in URL or query
2. WARN (but allow) calls containing "2025" with a date reminder

This helps ensure Claude uses current, up-to-date information.
"""

import json
import sys
from datetime import datetime


def get_current_date_info() -> dict:
    """Get current date information for warnings."""
    now = datetime.now()
    return {
        "date": now.strftime("%Y-%m-%d"),
        "year": now.year,
        "formatted": now.strftime("%A, %B %d, %Y"),
    }


def check_for_year_references(text: str) -> dict:
    """
    Check text for year references.

    Returns:
        dict with 'has_2024' and 'has_2025' boolean flags
    """
    text_lower = text.lower()
    return {
        "has_2024": "2024" in text_lower,
        "has_2025": "2025" in text_lower,
    }


def build_deny_response(reason: str) -> dict:
    """Build a deny response for the hook."""
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def build_allow_response(reason: str) -> dict:
    """Build an allow response for the hook."""
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionDecisionReason": reason,
        }
    }


def main():
    # Read hook input from stdin
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Failed to parse input JSON: {e}", file=sys.stderr)
        sys.exit(1)

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # Only process WebFetch and WebSearch
    if tool_name not in ("WebFetch", "WebSearch"):
        sys.exit(0)

    # Extract the relevant text to check
    # WebFetch uses 'url' and 'prompt', WebSearch uses 'query'
    texts_to_check = []

    if tool_name == "WebFetch":
        url = tool_input.get("url", "")
        prompt = tool_input.get("prompt", "")
        texts_to_check = [url, prompt]
    elif tool_name == "WebSearch":
        query = tool_input.get("query", "")
        texts_to_check = [query]

    # Combine all texts for checking
    combined_text = " ".join(texts_to_check)
    year_refs = check_for_year_references(combined_text)
    date_info = get_current_date_info()

    # BLOCK: If 2024 is referenced
    if year_refs["has_2024"]:
        deny_reason = (
            f"BLOCKED: Your request contains '2024' which is an outdated year reference.\n\n"
            f"CURRENT DATE: {date_info['formatted']}\n"
            f"CURRENT YEAR: {date_info['year']}\n\n"
            f"Please reformulate your request using the current year ({date_info['year']}) "
            f"or remove the year reference entirely to get current information.\n\n"
            f"Tool: {tool_name}\n"
            f"Input: {combined_text[:200]}..."
        )
        output = build_deny_response(deny_reason)
        print(json.dumps(output))
        sys.exit(0)

    # WARN: If 2025 is referenced (allow but warn)
    if year_refs["has_2025"]:
        warn_reason = (
            f"WARNING: Date-specific search detected.\n\n"
            f"====================================\n"
            f"CURRENT DATE: {date_info['formatted']}\n"
            f"CURRENT YEAR: {date_info['year']}\n"
            f"====================================\n\n"
            f"IMPORTANT: Always verify the current date before running web searches. "
            f"Your request contains '2025' which is correct for today, but remember:\n"
            f"- Check the current date at the start of each session\n"
            f"- Do not assume the year from previous searches\n"
            f"- When searching for 'latest' or 'recent' content, include the current year\n\n"
            f"Proceeding with {tool_name}..."
        )
        output = build_allow_response(warn_reason)
        print(json.dumps(output))
        sys.exit(0)

    # No year references - allow without special handling
    sys.exit(0)


if __name__ == "__main__":
    main()
