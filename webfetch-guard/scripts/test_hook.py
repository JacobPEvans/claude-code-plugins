#!/usr/bin/env python3
"""Tests for webfetch-guard hook."""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HOOK = Path(__file__).parent / "webfetch-guard.py"
now = datetime.now()
Y0 = now.year
M = now.month
Y1 = Y0 - 1
Y2 = Y0 - 2
GRACE = M <= 3

TESTS = [
    ("Block 2+ years ago", "WebFetch", {"url": f"https://example.com/{Y2}/api"}, "deny"),
    (
        f"{'Allow' if GRACE else 'Block'} previous year",
        "WebSearch",
        {"query": f"Python docs {Y1}"},
        None if GRACE else "deny",
    ),
    ("Warn current year", "WebSearch", {"query": f"Python {Y0}"}, "allow"),
    ("Pass silent", "WebFetch", {"url": "https://example.com/latest"}, None),
    ("Ignore other tools", "Read", {"file_path": f"/file/{Y2}.txt"}, None),
]


def run_hook(tool_name: str, tool_input: dict) -> dict | None:
    """Run hook and return parsed output, or None if no output."""
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps({"tool_name": tool_name, "tool_input": tool_input}),
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout) if result.stdout.strip() else None


def main():
    for name, tool, input_data, expected in TESTS:
        output = run_hook(tool, input_data)
        actual = output["hookSpecificOutput"]["permissionDecision"] if output else None
        status = "✅" if actual == expected else "❌"
        print(f"{status} {name}: {actual}")


if __name__ == "__main__":
    main()
