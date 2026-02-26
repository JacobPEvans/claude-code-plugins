#!/usr/bin/env python3
"""
Git Permission Guard - Blocks dangerous git/gh commands.

Exit 0 with JSON output for deny/allow decisions.
Most Bash commands are not git/gh - early exit is critical for performance.
"""

import json
import re
import sys

# Patterns checked against ALL commands (not git-specific)
DENY_ALWAYS = [
    (r"pre-commit\s+uninstall", "removes pre-commit hooks"),
    (r"rm\s+.*\.git/hooks", "deletes git hooks"),
    (r"chmod\s+.*-x\s+\.git/hooks", "disables git hooks"),
]

# Patterns checked ONLY when command starts with 'git ' to avoid false
# positives from matching substrings in gh api body text or other commands
DENY_GIT_ONLY = [
    (r"commit\s+.*(-n|--no-verify)", "bypasses pre-commit hooks"),
    (r"merge\s+.*--no-verify", "bypasses merge hooks"),
    (r"cherry-pick\s+.*--no-verify", "bypasses commit hooks"),
    (r"rebase\s+.*--no-verify", "bypasses commit hooks"),
    (r"config\s+.*core\.hooksPath", "changes hook directory"),
    (r"-c\s+core\.hooksPath", "bypasses configured hooks"),
]

# Commands requiring explicit user confirmation
# Ordered from most specific to least specific to avoid false matches
ASK_GIT = [
    ("commit --amend", "Rewrites the last commit"),
    ("push --force-with-lease", "Overwrites remote history"),
    ("push --force", "Overwrites remote history"),
    ("push -f", "Overwrites remote history"),
    ("worktree remove --force", "Removes worktree directory, discarding uncommitted changes"),
    ("worktree remove -f", "Removes worktree directory, discarding uncommitted changes"),
    ("cherry-pick", "Rewrites commit history"),
    ("merge", "Can create merge commits or conflicts"),
    ("reset", "Can lose uncommitted work permanently"),
    ("restore", "Can discard local changes"),
    ("rebase", "Rewrites commit history"),
    ("clean", "Removes untracked files permanently"),
    ("prune", "Removes unreferenced objects"),
    ("rm", "Removes files from working tree and index"),
    ("gc", "May remove unreferenced objects"),
]

ASK_GH = [
    ("repo delete", "PERMANENTLY deletes repository"),
    ("release delete", "Deletes releases permanently"),
    ("issue close", "Closes issues - could be accidental"),
    ("pr close", "Closes pull requests - could be accidental"),
    ("pr merge", "Merges PR - ONLY do when user EXPLICITLY requests"),
]

DENY_GH = [
    ("pr comment", (
        "gh pr comment creates top-level issue comments that cannot be resolved or tracked.\n"
        "\n"
        "For code review feedback, you MUST use review threads (line-specific, resolvable comments) instead.\n"
        "\n"
        "Use the documented thread workflows for creating review comments, replying, and resolving threads:\n"
        "  - github-workflows/skills/resolve-pr-threads/graphql-queries.md\n"
        "  - github-workflows/skills/resolve-pr-threads/rest-api-patterns.md\n"
        "\n"
        "These workflows create resolvable, line-specific review threads — the only acceptable way to post review\n"
        "feedback on PRs."
    )),
]

# Maps incorrect GraphQL mutation names to (correct_name, example_command).
# Based on log analysis: addPullRequestReviewComment (711 failures),
# resolvePullRequestReviewThread (162 failures).
WRONG_MUTATIONS = {
    "addPullRequestReviewComment": (
        "addPullRequestReviewThreadReply",
        (
            "gh api graphql --raw-field query='"
            "mutation { addPullRequestReviewThreadReply(input: {"
            "pullRequestReviewThreadId: \"THREAD_ID\", body: \"reply text\""
            "}) { comment { id } } }'"
        ),
    ),
    "resolvePullRequestReviewThread": (
        "resolveReviewThread",
        (
            "gh api graphql --raw-field query='"
            "mutation { resolveReviewThread(input: {"
            "threadId: \"THREAD_ID\""
            "}) { thread { id isResolved } } }'"
        ),
    ),
}


def deny(reason: str) -> None:
    """Output deny decision and exit."""
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"BLOCKED: {reason}",
        }
    }))
    sys.exit(0)


def ask(command: str, risk: str) -> None:
    """Output ask decision (requires user confirmation) and exit."""
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": f"CAUTION: {risk}\nCommand: {command}",
        }
    }))
    sys.exit(0)


def allow_with_guidance(reason: str) -> None:
    """Allow command but show guidance for self-correction."""
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionDecisionReason": reason,
        }
    }))
    sys.exit(0)


def _strip_jq_content(command: str) -> str:
    """Remove --jq '...' and --jq "..." content to avoid false positives."""
    command = re.sub(r"--jq\s+'[^']*'", "", command)
    command = re.sub(r'--jq\s+"[^"]*"', "", command)
    command = re.sub(r"--jq\s+\S+", "", command)
    return command


def check_graphql_guidance(command: str) -> None:
    """Detect known gh api graphql failure patterns and emit corrective guidance.

    Allows the command to proceed (it will fail naturally) while showing the
    correct pattern inline so Claude can self-correct immediately.
    """
    warnings = []

    # Detection 1 - Shell $variable expansion (excluding --jq content)
    command_no_jq = _strip_jq_content(command)
    if re.search(r"\$[a-zA-Z]", command_no_jq):
        warnings.append(
            "SHELL VARIABLE EXPANSION: $variable in GraphQL queries is expanded by the shell before\n"
            "gh receives it, causing syntax errors. Use --raw-field with inline values instead:\n"
            "\n"
            "  WRONG:  gh api graphql -f query='mutation { ... threadId: $threadId }'\n"
            "  CORRECT: gh api graphql --raw-field query='mutation { ... threadId: \"ACTUAL_ID\" }'"
        )

    # Detection 2 - Wrong mutation names
    for wrong_name, (correct_name, example) in WRONG_MUTATIONS.items():
        if wrong_name in command:
            warnings.append(
                f"WRONG MUTATION NAME: '{wrong_name}' does not exist in the GitHub GraphQL API.\n"
                f"Use '{correct_name}' instead.\n"
                f"\n"
                f"  Example: {example}"
            )

    # Detection 3 - -f query= or -F query= flags (Go template processing)
    if re.search(r"\s-[fF]\s+query=", command):
        warnings.append(
            "WRONG FLAG: -f/-F applies Go template processing which causes variable expansion.\n"
            "Use --raw-field for GraphQL queries:\n"
            "\n"
            "  WRONG:  gh api graphql -f query='...'\n"
            "  CORRECT: gh api graphql --raw-field query='...'"
        )

    # Detection 4 - Multi-line indicators (trailing backslash or literal \n,
    # excluding false positives like \node, \name, \null, \number)
    if command.endswith("\\") or re.search(r"\\n(?![aouei])", command):
        warnings.append(
            "MULTI-LINE QUERY: GraphQL queries must be on a single line.\n"
            "Trailing backslashes and \\n sequences break gh api graphql.\n"
            "\n"
            "  WRONG:  gh api graphql --raw-field query=' \\\n"
            "            mutation { ... }'\n"
            "  CORRECT: gh api graphql --raw-field query='mutation { ... }'"
        )

    if warnings:
        header = "GRAPHQL GUIDANCE: This command has known failure patterns. Correct before retrying:\n\n"
        body = "\n\n".join(f"[{i + 1}] {w}" for i, w in enumerate(warnings))
        allow_with_guidance(header + body)


def main():
    # Parse input
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    # Only process Bash tool
    if data.get("tool_name") != "Bash":
        sys.exit(0)

    command = data.get("tool_input", {}).get("command", "").strip()
    if not command:
        sys.exit(0)

    # Check universal DENY patterns (non-git-specific)
    for pattern, reason in DENY_ALWAYS:
        if re.search(pattern, command, re.IGNORECASE):
            deny(f"This command {reason}. Fix the underlying issue instead.")

    # EARLY EXIT: Most commands are not git/gh
    is_git = command.startswith("git ") or command == "git"
    is_gh = command.startswith("gh ") or command == "gh"
    if not is_git and not is_gh:
        sys.exit(0)

    # Check git-specific DENY patterns (after early exit to avoid false
    # positives from matching substrings in non-git commands like gh api)
    if is_git:
        for pattern, reason in DENY_GIT_ONLY:
            if re.search(pattern, command, re.IGNORECASE):
                deny(f"This command {reason}. Fix the underlying issue instead.")

    # Extract subcommand for git (handle -C <path>, -c <key=value>)
    if is_git:
        rest = command[4:] if command.startswith("git ") else ""
        # Strip git options to find actual subcommand
        while rest:
            # -C <path>
            m = re.match(r'^-C\s+("[^"]+"|\'[^\']+\'|\S+)\s*(.*)', rest)
            if m:
                rest = m.group(2).strip()
                continue
            # -c <key=value>
            m = re.match(r'^-c\s+("[^"]+"|\'[^\']+\'|\S+)\s*(.*)', rest)
            if m:
                rest = m.group(2).strip()
                continue
            break
        subcommand = rest
    else:
        subcommand = command[3:] if command.startswith("gh ") else ""

    sub_tokens = subcommand.split()

    # Check DENY_GH patterns (token prefix match on gh subcommand)
    if is_gh:
        for pattern, reason in DENY_GH:
            tokens = pattern.split()
            if tokens and sub_tokens[:len(tokens)] == tokens:
                deny(reason)

    # Check GraphQL guidance (allow with corrective warnings)
    if is_gh and sub_tokens[:2] == ["api", "graphql"]:
        check_graphql_guidance(command)

    # Check ASK patterns - use word boundaries to avoid false matches
    # (e.g., "merge" shouldn't match "emergency")
    patterns = ASK_GIT if is_git else ASK_GH
    for cmd, risk in patterns:
        # Match as exact token sequence at start of subcommand
        cmd_tokens = cmd.split()
        if len(sub_tokens) >= len(cmd_tokens) and sub_tokens[:len(cmd_tokens)] == cmd_tokens:
            ask(command, risk)

    # Allow by default (exit 0, no output)
    sys.exit(0)


if __name__ == "__main__":
    main()
