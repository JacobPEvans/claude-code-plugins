#!/usr/bin/env python3
"""Tests for webfetch-guard hook."""

import json
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).parent / "webfetch-guard.py"

TESTS = [
    ("BLOCK 2024", "WebFetch", {"url": "https://example.com/2024/api"}, "deny"),
    ("WARN 2025", "WebSearch", {"query": "Python best practices 2025"}, "allow"),
    ("PASS silent", "WebFetch", {"url": "https://example.com/latest"}, None),
    ("IGNORE other", "Read", {"file_path": "/file/2024.txt"}, None),
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
