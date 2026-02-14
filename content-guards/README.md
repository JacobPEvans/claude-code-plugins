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

## WebFetch Guard

Blocks `WebFetch` and `WebSearch` operations that contain outdated year references (e.g., "2024" when current year is 2026).

## Issue Limiter

Prevents creating GitHub issues when the backlog exceeds the configured threshold (blocks issue overflow).

## Installation

```bash
claude plugins add jacobpevans-cc-plugins/content-guards
```

## Dependencies

- `atc` - Token counting tool (for token-validator)
- `markdownlint-cli2` - Markdown linting (for markdown-validator)
- `cspell` - Spell checking (for markdown-validator)
- `gh` - GitHub CLI (for issue-limiter)

All hooks fail open when their dependencies are unavailable, allowing the operation to proceed.
