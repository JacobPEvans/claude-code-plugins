#!/usr/bin/env python3
"""Tests for webfetch-guard hook."""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HOOK = Path(__file__).parent / "webfetch-guard.py"
CURRENT_YEAR = datetime.now().year
OUTDATED_YEAR = CURRENT_YEAR - 1

TESTS = [
    ("BLOCK outdated year", "WebFetch", {"url": f"https://example.com/{OUTDATED_YEAR}/api"}, "deny"),
    ("WARN current year", "WebSearch", {"query": f"Python best practices {CURRENT_YEAR}"}, "allow"),
    ("PASS silent", "WebFetch", {"url": "https://example.com/latest"}, None),
    ("IGNORE other", "Read", {"file_path": f"/file/{OUTDATED_YEAR}.txt"}, None),
]


def run_hook(tool_name: str, tool_input: dict) -> dict | None:
    """Run hook and return parsed output, or None if no output."""
    payload = {"tool_name": tool_name, "tool_input": tool_input}
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
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
