#!/usr/bin/env python3
"""Tests for main-branch-guard hook."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK = Path(__file__).parent / "main-branch-guard.py"


def run_hook(tool_name: str, tool_input: dict) -> dict | None:
    """Run hook and return parsed output, or None if no output."""
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps({"tool_name": tool_name, "tool_input": tool_input}),
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout) if result.stdout.strip() else None


def setup_test_repo():
    """Create a temporary git repo with main worktree structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        main_worktree = repo_root / "main"
        main_worktree.mkdir()

        # Initialize git repo
        subprocess.run(
            ["git", "init"], cwd=main_worktree, capture_output=True, check=True
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=main_worktree,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=main_worktree,
            capture_output=True,
            check=True,
        )

        # Create initial commit
        test_file = main_worktree / "test.txt"
        test_file.write_text("test")
        subprocess.run(
            ["git", "add", "test.txt"], cwd=main_worktree, capture_output=True, check=True
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=main_worktree,
            capture_output=True,
            check=True,
        )

        yield main_worktree


def test_deny_in_main_worktree():
    """Test that editing files in main worktree is denied."""
    for main_worktree in setup_test_repo():
        test_file = main_worktree / "README.md"
        test_file.write_text("# Test")

        output = run_hook("Edit", {"file_path": str(test_file)})
        actual = output["hookSpecificOutput"]["permissionDecision"] if output else None

        if actual == "deny":
            print("✅ Deny in main worktree: deny")
        else:
            print(f"❌ Deny in main worktree: {actual}")


def test_deny_on_main_branch():
    """Test that editing files on main branch is denied."""
    for main_worktree in setup_test_repo():
        # Ensure we're on main branch
        subprocess.run(
            ["git", "checkout", "-b", "main"],
            cwd=main_worktree,
            capture_output=True,
            check=False,
        )

        test_file = main_worktree / "test.txt"
        output = run_hook("Write", {"file_path": str(test_file)})
        actual = output["hookSpecificOutput"]["permissionDecision"] if output else None

        if actual == "deny":
            print("✅ Deny when branch is main: deny")
        else:
            print(f"❌ Deny when branch is main: {actual}")


def test_allow_for_non_main():
    """Test that editing files in non-main worktree/branch is allowed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        feat_worktree = repo_root / "feat" / "test-feature"
        feat_worktree.mkdir(parents=True)

        # Initialize git repo on a feature branch
        subprocess.run(
            ["git", "init"], cwd=feat_worktree, capture_output=True, check=True
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=feat_worktree,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=feat_worktree,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "checkout", "-b", "feat/test-feature"],
            cwd=feat_worktree,
            capture_output=True,
            check=True,
        )

        # Create initial commit
        test_file = feat_worktree / "test.txt"
        test_file.write_text("test")
        subprocess.run(
            ["git", "add", "test.txt"], cwd=feat_worktree, capture_output=True, check=True
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=feat_worktree,
            capture_output=True,
            check=True,
        )

        output = run_hook("Edit", {"file_path": str(test_file)})
        actual = output["hookSpecificOutput"]["permissionDecision"] if output else None

        if actual is None:
            print("✅ Allow for non-main: None")
        else:
            print(f"❌ Allow for non-main: {actual}")


def test_allow_non_edit_tools():
    """Test that non-Edit/Write/NotebookEdit tools are allowed."""
    output = run_hook("Read", {"file_path": "/tmp/test.txt"})
    actual = output["hookSpecificOutput"]["permissionDecision"] if output else None

    if actual is None:
        print("✅ Ignore other tools: None")
    else:
        print(f"❌ Ignore other tools: {actual}")


def test_notebook_edit():
    """Test that NotebookEdit is also guarded."""
    for main_worktree in setup_test_repo():
        notebook = main_worktree / "test.ipynb"
        notebook.write_text('{"cells": []}')

        output = run_hook("NotebookEdit", {"notebook_path": str(notebook)})
        actual = output["hookSpecificOutput"]["permissionDecision"] if output else None

        if actual == "deny":
            print("✅ Deny NotebookEdit in main: deny")
        else:
            print(f"❌ Deny NotebookEdit in main: {actual}")


def main():
    """Run all tests."""
    test_deny_in_main_worktree()
    test_deny_on_main_branch()
    test_allow_for_non_main()
    test_allow_non_edit_tools()
    test_notebook_edit()


if __name__ == "__main__":
    main()
