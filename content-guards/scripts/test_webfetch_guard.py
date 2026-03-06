#!/usr/bin/env python3
"""Tests for webfetch-guard.py hook.

Verifies that outdated year references are blocked/warned and
non-year queries are silently allowed.

Run with: python3 content-guards/scripts/test_webfetch_guard.py
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SCRIPT = Path(__file__).parent / "webfetch-guard.py"


def run(tool_name: str, **kwargs) -> tuple[int, dict]:
    inp = json.dumps({"tool_name": tool_name, "tool_input": kwargs})
    result = subprocess.run(
        ["python3", str(SCRIPT)],
        input=inp,
        capture_output=True,
        text=True,
    )
    output = json.loads(result.stdout.strip()) if result.stdout.strip() else {}
    return result.returncode, output


def get_decision(output: dict) -> str:
    if not output:
        return "silent_allow"
    return output["hookSpecificOutput"]["permissionDecision"]


def check(label: str, tool_name: str, expected: str, **kwargs) -> bool:
    _, output = run(tool_name, **kwargs)
    actual = get_decision(output)
    ok = actual == expected
    status = "PASS" if ok else "FAIL"
    print(f"{status} [{label}]: decision={actual}")
    if not ok:
        print(f"  Expected: {expected}, Got: {actual}")
    return ok


# Derive the always-blocked year the same way the script does
now = datetime.now()
current_year = now.year
blocked_year = current_year - 2  # blocked in both grace period and post-grace

all_pass = True

# Non-WebFetch/WebSearch tool is silently allowed
all_pass &= check("non-matching tool", "Bash", "silent_allow", command="ls")

# WebSearch with a definitively outdated year is denied
all_pass &= check(
    "WebSearch blocked year",
    "WebSearch",
    "deny",
    query=f"python tutorial {blocked_year}",
)

# WebFetch with outdated year in URL is denied
all_pass &= check(
    "WebFetch blocked year in URL",
    "WebFetch",
    "deny",
    url=f"https://docs.example.com/{blocked_year}/api",
    prompt="",
)

# WebFetch with outdated year in prompt is denied
all_pass &= check(
    "WebFetch blocked year in prompt",
    "WebFetch",
    "deny",
    url="https://example.com",
    prompt=f"show me news from {blocked_year}",
)

# WebSearch without any year is silently allowed
all_pass &= check(
    "WebSearch no year",
    "WebSearch",
    "silent_allow",
    query="python best practices",
)

# WebFetch without any year is silently allowed
all_pass &= check(
    "WebFetch no year",
    "WebFetch",
    "silent_allow",
    url="https://example.com/docs",
    prompt="How does this work?",
)

# WebSearch with the current year produces a warning (allow with reason)
all_pass &= check(
    "WebSearch current year warns",
    "WebSearch",
    "allow",
    query=f"python news {current_year}",
)

# WebFetch with current year in prompt produces a warning (allow with reason)
all_pass &= check(
    "WebFetch current year in prompt warns",
    "WebFetch",
    "allow",
    url="https://example.com",
    prompt=f"what happened in {current_year}",
)

print()
print("ALL TESTS PASSED" if all_pass else "SOME TESTS FAILED")
sys.exit(0 if all_pass else 1)
