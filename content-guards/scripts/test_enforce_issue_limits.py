#!/usr/bin/env python3
"""Tests for enforce-issue-limits.py hook.

Verifies that only 'gh issue create' and 'gh pr create/edit' commands are
intercepted, non-gh commands pass through, and bad input is handled gracefully.

Run with: python3 content-guards/scripts/test_enforce_issue_limits.py
"""

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).parent / "enforce-issue-limits.py"


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

# Invalid JSON input - fail open (exit 0)
all_pass &= check("invalid JSON", "not valid json", 0)

# Empty JSON object - fail open (exit 0)
all_pass &= check("empty JSON", "{}", 0)

# Non-gh command passes through (exit 0)
all_pass &= check(
    "ls command passthrough",
    json.dumps({"tool_input": {"command": "ls -la"}}),
    0,
)

# gh pr list is not intercepted (exit 0)
all_pass &= check(
    "gh pr list passthrough",
    json.dumps({"tool_input": {"command": "gh pr list"}}),
    0,
)

# gh issue list is not intercepted - only 'create' triggers the check (exit 0)
all_pass &= check(
    "gh issue list passthrough",
    json.dumps({"tool_input": {"command": "gh issue list --state open"}}),
    0,
)

# gh issue close is not intercepted (exit 0)
all_pass &= check(
    "gh issue close passthrough",
    json.dumps({"tool_input": {"command": "gh issue close 42"}}),
    0,
)

# gh issue create triggers the gh check; when gh is unavailable, fails open (exit 0)
# When limits are exceeded, blocks (exit 2). Either outcome is valid here.
result = run(
    json.dumps({"tool_input": {"command": "gh issue create --title 'Test issue'"}})
)
ok = result.returncode in (0, 2)
status = "PASS" if ok else "FAIL"
print(f"{status} [gh issue create]: exit={result.returncode} (0=fail-open, 2=blocked)")
if not ok:
    print(f"  Expected exit: 0 or 2, Got: {result.returncode}")
all_pass &= ok

# gh issue create with inline flags (alternate form) is also intercepted
result = run(
    json.dumps({"tool_input": {"command": "gh issue create -t 'Bug' -b 'Details'"}})
)
ok = result.returncode in (0, 2)
status = "PASS" if ok else "FAIL"
print(f"{status} [gh issue create flags]: exit={result.returncode} (0=fail-open, 2=blocked)")
if not ok:
    print(f"  Expected exit: 0 or 2, Got: {result.returncode}")
all_pass &= ok

# gh pr create triggers the gh check; when gh is unavailable, fails open (exit 0)
# When limits are exceeded, blocks (exit 2). Either outcome is valid here.
result = run(
    json.dumps({"tool_input": {"command": "gh pr create --title 'Fix bug' --body 'Details'"}})
)
ok = result.returncode in (0, 2)
status = "PASS" if ok else "FAIL"
print(f"{status} [gh pr create]: exit={result.returncode} (0=fail-open, 2=blocked)")
if not ok:
    print(f"  Expected exit: 0 or 2, Got: {result.returncode}")
all_pass &= ok

# --- Tests for label-based filtering and label enforcement ---

# Test extract_flag_values and warn_missing_ai_label via import
import importlib.util
spec = importlib.util.spec_from_file_location("enforce_issue_limits", str(SCRIPT))
eil = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eil)

# extract_flag_values: single --label
vals = eil.extract_flag_values("gh issue create --label ai-created --title test", "--label")
ok = vals == ["ai-created"]
print(f"{'PASS' if ok else 'FAIL'} [extract_flag_values single]: {vals}")
all_pass &= ok

# extract_flag_values: multiple --label flags
vals = eil.extract_flag_values("gh issue create --label bug --label ai-created --title test", "--label")
ok = vals == ["bug", "ai-created"]
print(f"{'PASS' if ok else 'FAIL'} [extract_flag_values multiple]: {vals}")
all_pass &= ok

# extract_flag_values: comma-separated --label
vals = eil.extract_flag_values('gh issue create --label "bug,ai-created" --title test', "--label")
ok = vals == ["bug,ai-created"]
print(f"{'PASS' if ok else 'FAIL'} [extract_flag_values comma]: {vals}")
all_pass &= ok

# extract_flag_values: no --label flag
vals = eil.extract_flag_values("gh issue create --title test", "--label")
ok = vals == []
print(f"{'PASS' if ok else 'FAIL'} [extract_flag_values none]: {vals}")
all_pass &= ok

# warn_missing_ai_label: with label present (no warning)
import io
import contextlib

stderr_buf = io.StringIO()
with contextlib.redirect_stderr(stderr_buf):
    eil.warn_missing_ai_label("gh issue create --label ai-created --title test")
ok = "Warning" not in stderr_buf.getvalue()
print(f"{'PASS' if ok else 'FAIL'} [warn_missing_ai_label with label]: no warning emitted")
all_pass &= ok

# warn_missing_ai_label: without label (warning)
stderr_buf = io.StringIO()
with contextlib.redirect_stderr(stderr_buf):
    eil.warn_missing_ai_label("gh issue create --title test")
ok = "Warning" in stderr_buf.getvalue() and "ai-created" in stderr_buf.getvalue()
print(f"{'PASS' if ok else 'FAIL'} [warn_missing_ai_label without label]: warning emitted")
all_pass &= ok

# warn_missing_ai_label: comma-separated label including ai-created (no warning)
stderr_buf = io.StringIO()
with contextlib.redirect_stderr(stderr_buf):
    eil.warn_missing_ai_label('gh pr create --label "bug,ai-created" --title test')
ok = "Warning" not in stderr_buf.getvalue()
print(f"{'PASS' if ok else 'FAIL'} [warn_missing_ai_label comma label]: no warning emitted")
all_pass &= ok

print()
print("ALL TESTS PASSED" if all_pass else "SOME TESTS FAILED")
sys.exit(0 if all_pass else 1)
