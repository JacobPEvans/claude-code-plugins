# skill-guards

Ensures fresh execution of skills on every invocation via a UserPromptSubmit hook.

## Problem

When a skill like `/ship` is called a second time in a session, Claude may shortcut
by assuming previous results are still valid instead of re-running all commands against
live state.

## Solution

A UserPromptSubmit hook detects `/skill-name` patterns in user prompts and injects a
systemMessage reminding Claude to execute every step from scratch using current live state.

## Installation

```bash
claude plugins add jacobpevans-cc-plugins/skill-guards
```

## Usage

No manual invocation required. The hook activates automatically on every user prompt.

## Hook Behavior

- **Fires on**: Every user prompt submission
- **Detects**: `/lowercase-with-hyphens` skill invocation patterns
- **Excludes**: Common filesystem paths (`/usr`, `/tmp`, `/etc`, `/nix`, etc.)
- **Output**: `{"systemMessage": "FRESH EXECUTION: /skill — ..."}` or `{}`
- **Exit code**: Always 0 (never blocks prompts)

## Part of a Three-Layer System

1. **Global rule** (`skill-execution-integrity`) — establishes the mental model
2. **This hook** — tactical trigger at moment of invocation
3. **Skill preambles** — skill-specific state warnings in SKILL.md files
