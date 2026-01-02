# token-validator

Claude Code plugin that enforces file token limits on Write and Edit operations.

## Features

- Validates token counts before file writes
- Configurable per-file limits via `.token-limits.yaml`
- Glob pattern matching for file-specific limits
- Fails open if token counting unavailable

## Behavior

| Condition | Action |
|-----------|--------|
| File exceeds token limit | Block with detailed error |
| Binary file detected | Skip validation |
| Token counter unavailable | Allow (fail open) |
| No config file found | Use defaults |

## Installation

### From Marketplace

```bash
claude plugins add jacobpevans-cc-plugins/token-validator
```

### Local Development

```bash
claude plugins link ./token-validator
```

## Configuration

Create `.token-limits.yaml` in your project root:

```yaml
defaults:
  max_tokens: 2000

limits:
  "**/*.md": 1500
  "**/*.py": 3000
  "agentsmd/commands/*.md": 1000
```

## Dependencies

- Python 3.10+
- `atc` CLI (Anthropic Token Counter)
- `pyyaml` Python package

## How It Works

1. Intercepts Write/Edit tool calls via PreToolUse hook
2. Searches upward for `.token-limits.yaml`
3. Counts tokens using `atc -m sonnet`
4. Blocks if file exceeds configured limit
5. Returns detailed error with current vs. allowed tokens
