# Content Guards

Combined validation and guard plugin that enforces content quality and safety rules in Claude Code.

## What This Plugin Does

This plugin merges four validation hooks into a single package:

1. **Token Validator** - Blocks file writes that exceed token limits
2. **Markdown Validator** - Validates markdown with markdownlint and cspell
3. **WebFetch Guard** - Prevents outdated year references in web queries
4. **Issue Limiter** - Prevents GitHub issue backlog overflow

## Token Validator

### How It Works

Intercepts `Write` and `Edit` tools and counts tokens using the `atc` CLI tool.
If the file would exceed the configured limit, the operation is blocked with detailed resolution guidance.

### Configuration

Create a `.token-limits.yaml` file at your repository root:

```yaml
defaults:
  max_tokens: 2000

limits:
  # Pattern-based overrides (glob matching)
  "*.md": 3000
  "docs/**/*.md": 4000
  "CLAUDE.md": 6000
```

The hook searches upward from the current directory (like git does with `.git/`) to find the config file.

### Resolving Token Limit Violations

When you hit the hard limit, you'll see this error with resolution steps:

```text
❌ Token limit violation: <file>
   Tokens: <count> (limit: <limit>, excess: +<over>)

HOW TO RESOLVE — follow these steps in order:

1. REFACTOR INTO MULTIPLE FILES (most common fix)
   - Split the file by logical concern (one responsibility per file)
   - Use imports/includes to compose the pieces back together
   - Example: large Nix module → split into options.nix, config.nix, services.nix

2. EXTRACT EMBEDDED CODE TO SEPARATE FILES
   - NEVER embed shell scripts inside Nix files — use a .sh file and reference it
   - NEVER embed Python scripts inside YAML (GitHub Actions, etc.) — use a .py file
   - NEVER inline large configs — put them in their own file with correct extension
   - Each file should contain ONE language/format only

3. REEVALUATE THE DIRECTORY STRUCTURE
   - If a file is large because it handles many concerns, rethink the structure
   - Create subdirectories to group related smaller files
   - Example: monolithic default.nix → directory with focused modules

4. REVIEW FOR DEAD/DUPLICATE CODE
   - Remove unused imports, dead code, and duplicated logic
   - But NEVER remove comments — comments are always valuable

IMPORTANT — DO NOT:
  ✗ Remove or reduce comments to save tokens (comments are ALWAYS worth keeping)
  ✗ Compress code onto fewer lines to fit the limit
  ✗ Increase the token limit in .token-limits.yaml to paper over the issue
  ✗ Remove documentation strings or docstrings

The goal is SMALLER, FOCUSED FILES — not less-documented code.
```

**Key principle**: Comments are always valuable. Never remove them to reduce file size. Refactor instead.

### Behavior

- **Success** (under limit): Silent pass (exit 0)
- **Failure** (exceeds limit): Block with detailed error (exit 2)
- **Unavailable** (`atc` not found): Fail open, allow operation (exit 0)

Binary files (`.png`, `.jpg`, `.pdf`, `.bin`, `.zip`) are automatically skipped.

## Markdown Validator

Validates markdown files using `markdownlint-cli2` and `cspell` on `Write` and `Edit` operations.

### Markdown Validator - How It Works

- Runs only on files that appear to be Markdown (typically `*.md`, `*.markdown`)
- Invokes `markdownlint-cli2` with the repository's markdownlint configuration (if present)
- Invokes `cspell` to spell‑check prose and code blocks using the repo's cspell configuration (if present)
- Both tools run against the *post‑edit* content so you see issues from the current change

The exact rule set and dictionaries are controlled by your local markdownlint/cspell config files;
the hook does not alter those rules, it only enforces them on every write/edit.

### Markdown Validator - Behavior

- **Success** (no lint/spell errors): Silent pass (exit 0)
- **Failure** (lint/spell errors found): Operation blocked, tool output shown (non‑zero exit)
- **Unavailable** (tools not found): Fail open, allow operation to proceed (exit 0)

Binary and non‑markdown files are automatically skipped by this validator.

## WebFetch Guard

Blocks `WebFetch` and `WebSearch` operations that contain outdated year references
(e.g., requesting "2024" data when the current year is 2026).

### WebFetch Guard - How It Works

- Intercepts `WebFetch` and `WebSearch` tools before the request is sent
- Scans the query text/URL for explicit Gregorian years (e.g., `2023`, `2024`, `2025`)
- Compares any detected years against the current calendar year
- If the query targets a year older than the current year, treats it as a stale‑data request
- A hard‑coded grace period around New Year allows queries for the just‑previous year
  (e.g., early in January) to reduce false positives

The exact grace‑period duration and comparison rules are currently hard‑coded in the hook
implementation and are not user‑configurable; refer to the hook source for precise values.

### WebFetch Guard - Behavior

- **Allowed**: Queries without explicit year literals, or that target the current year
- **Blocked**: Queries with only outdated years outside the grace period; guard explains
  why blocked and suggests updating or generalizing the query
- **Unavailable** (tooling/environment not available): Fails open, allows request (exit 0)

## Issue Limiter

Prevents creating GitHub issues when the backlog exceeds a hard‑coded threshold
(to avoid unbounded issue growth).

### Issue Limiter - How It Works

- Intercepts commands that create new GitHub issues (typically `gh issue create`)
- Uses the `gh` CLI to query the current backlog of open issues for the target repository
- Compares the number of open issues against a backlog limit
- The backlog limit is currently a fixed, hard‑coded value inside the hook
  (not configurable via settings file yet); consult the hook implementation for the exact threshold

Behavior is deterministic across runs: once the open‑issue count reaches or exceeds
the built‑in threshold, additional issue‑creation attempts through the guarded path
will be blocked until the backlog is reduced.

### Issue Limiter - Behavior

- **Below threshold**: New issues allowed to be created normally (exit 0)
- **At/above threshold**: Issue creation blocked with message indicating backlog limit reached
  and suggesting triage/cleanup before adding more issues (non‑zero exit)
- **Unavailable** (`gh` not found, or unable to query issues): Fails open, allows creation (exit 0)

## Installation

```bash
claude plugins add jacobpevans-cc-plugins/content-guards
```

## Dependencies

- `jq` - JSON processing (used by validation hooks)
- `atc` - Token counting tool (for token-validator)
- `markdownlint-cli2` - Markdown linting (for markdown-validator)
- `cspell` - Spell checking (for markdown-validator)
- `gh` - GitHub CLI (for issue-limiter)

Hooks rely on these external tools; if a dependency is unavailable, the affected hook
may be skipped or may surface an error, and behavior is not guaranteed to fail open.
