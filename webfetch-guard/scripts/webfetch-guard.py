#!/usr/bin/env python3
"""
WebFetch Guard Hook

Intercepts WebFetch and WebSearch tool calls to:
1. BLOCK calls containing outdated year (previous year) in URL or query
2. WARN (but allow) calls containing current year with a date reminder

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


def check_for_year_references(text: str, outdated_year: str, warn_year: str) -> dict:
    """
    Check text for year references.

    Args:
        text: The text to search
        outdated_year: Year to block (typically previous year)
        warn_year: Year to warn about (typically current year)

    Returns:
        dict with 'has_outdated' and 'has_warn' boolean flags
    """
    text_lower = text.lower()
    return {
        "has_outdated": outdated_year in text_lower,
        "has_warn": warn_year in text_lower,
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

    # Get current date info and determine years dynamically
    date_info = get_current_date_info()
    current_year = date_info["year"]
    outdated_year = current_year - 1

    # Combine all texts for checking
    combined_text = " ".join(texts_to_check)
    year_refs = check_for_year_references(
        combined_text, str(outdated_year), str(current_year)
    )

    # BLOCK: If outdated year is referenced
    if year_refs["has_outdated"]:
        deny_reason = (
            f"BLOCKED: Your request contains '{outdated_year}' which is an outdated year reference.\n\n"
            f"CURRENT DATE: {date_info['formatted']}\n"
            f"CURRENT YEAR: {current_year}\n\n"
            f"Please reformulate your request using the current year ({current_year}) "
            f"or remove the year reference entirely to get current information.\n\n"
            f"Tool: {tool_name}\n"
            f"Input: {combined_text[:200]}..."
        )
        output = build_deny_response(deny_reason)
        print(json.dumps(output))
        sys.exit(0)

    # WARN: If current year is referenced (allow but warn)
    if year_refs["has_warn"]:
        warn_reason = (
            f"WARNING: Date-specific search detected.\n\n"
            f"====================================\n"
            f"CURRENT DATE: {date_info['formatted']}\n"
            f"CURRENT YEAR: {current_year}\n"
            f"====================================\n\n"
            f"IMPORTANT: Always verify the current date before running web searches. "
            f"Your request contains '{current_year}', but remember:\n"
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
