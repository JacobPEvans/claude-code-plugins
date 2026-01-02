# issue-limiter

Claude Code plugin that enforces GitHub issue creation limits to prevent backlog overflow.

## Features

- Limits total open issues per repository
- Limits AI-created issues (with `ai-created` label)
- Provides actionable guidance when limits reached
- Fails open if GitHub CLI unavailable

## Behavior

| Condition | Action |
|-----------|--------|
| Total open issues >= 50 | Block issue creation |
| AI-created issues >= 25 | Block issue creation |
| `gh` CLI unavailable | Allow (fail open) |
| Non-issue-create command | Pass through |

## Installation

### From Marketplace

```bash
claude plugins add jacobpevans-cc-plugins/issue-limiter
```

### Local Development

```bash
claude plugins link ./issue-limiter
```

## Configuration

Default limits (hardcoded):

- **Total open issues**: 50
- **AI-created issues**: 25

## Dependencies

- Python 3.10+
- `gh` CLI (GitHub CLI, authenticated)

## How It Works

1. Intercepts Bash tool calls via PreToolUse hook
2. Checks if command contains `gh issue create`
3. Queries current issue counts via `gh issue list`
4. Blocks if limits exceeded with detailed guidance
5. Suggests alternatives: close issues, remove labels, etc.
