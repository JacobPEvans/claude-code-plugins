#!/usr/bin/env python3
"""Tests for validate-token-limits.py hook.

Verifies that only Write/Edit tools are checked, binary files are skipped,
empty content passes through, and the hook fails open when 'atc' is unavailable.

Run with: python3 content-guards/scripts/test_validate_token_limits.py
"""

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).parent / "validate-token-limits.py"


def run(inp: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["python3", str(SCRIPT)],
        input=inp,
        capture_output=True,
        text=True,
    )


def check(label: str, inp: str, expected_code: int) -> bool:
    result = run(inp)
    ok = result.returncode == expected_code
    status = "PASS" if ok else "FAIL"
    print(f"{status} [{label}]: exit={result.returncode}")
    if not ok:
        print(f"  Expected exit: {expected_code}, Got: {result.returncode}")
    return ok


all_pass = True

# Invalid JSON - fail open (exit 0)
all_pass &= check("invalid JSON", "not valid json", 0)

# Empty JSON - fail open (exit 0)
all_pass &= check("empty JSON", "{}", 0)

# Non-Write/Edit tool is ignored (exit 0)
all_pass &= check(
    "Read tool ignored",
    json.dumps({"tool_name": "Read", "tool_input": {"file_path": "/tmp/test.txt"}}),
    0,
)

# Bash tool is ignored (exit 0)
all_pass &= check(
    "Bash tool ignored",
    json.dumps({"tool_name": "Bash", "tool_input": {"command": "echo hi"}}),
    0,
)

# Write tool with no file_path - fail open (exit 0)
all_pass &= check(
    "Write no file_path",
    json.dumps({"tool_name": "Write", "tool_input": {"content": "hello"}}),
    0,
)

# Write tool with no content - fail open (exit 0)
all_pass &= check(
    "Write no content",
    json.dumps({"tool_name": "Write", "tool_input": {"file_path": "/tmp/test.txt"}}),
    0,
)

# Binary file extension is skipped regardless of content (exit 0)
all_pass &= check(
    "Write PNG skipped",
    json.dumps(
        {
            "tool_name": "Write",
            "tool_input": {"file_path": "/tmp/image.png", "content": "data"},
        }
    ),
    0,
)

all_pass &= check(
    "Write PDF skipped",
    json.dumps(
        {
            "tool_name": "Write",
            "tool_input": {"file_path": "/tmp/report.pdf", "content": "data"},
        }
    ),
    0,
)

# Write tool with text content and no 'atc' available - fails open (exit 0)
# 'atc' is a token counter that may not be installed in all environments.
# The hook returns None from count_tokens() and allows the operation.
all_pass &= check(
    "Write text content (fail-open without atc)",
    json.dumps(
        {
            "tool_name": "Write",
            "tool_input": {
                "file_path": "/tmp/test.txt",
                "content": "hello world " * 100,
            },
        }
    ),
    0,
)

# Edit tool is treated the same as Write for routing purposes
all_pass &= check(
    "Edit tool routed same as Write",
    json.dumps(
        {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": "/tmp/test.txt",
                "content": "some edited content",
            },
        }
    ),
    0,
)

print()
print("ALL TESTS PASSED" if all_pass else "SOME TESTS FAILED")
sys.exit(0 if all_pass else 1)
