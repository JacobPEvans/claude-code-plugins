# markdown-validator

A Claude Code plugin that automatically validates markdown files after Write or Edit operations.

## Features

- **markdownlint-cli2**: Validates markdown formatting and structure
- **cspell**: Checks spelling and terminology

## Behavior

| Condition | Action |
|-----------|--------|
| `.md` file written/edited | Runs validation automatically |
| Validation passes | Silent success (exit 0) |
| Validation fails | Blocks Claude with error details (exit 2) |
| Non-markdown file | Skips validation silently |

## Installation

```bash
# Add marketplace
/plugin marketplace add <path-to-claude-code-plugins-repo>

# Install the plugin
/plugin install markdown-validator@jacobpevans-plugins
```

## Dependencies

This plugin requires these tools to be installed:

```bash
# Install markdownlint-cli2
npm install -g markdownlint-cli2

# Install cspell
npm install -g cspell
```

## Configuration

The hook is configured in `hooks/hooks.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/validate-markdown.sh",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

## How It Works

1. Hook intercepts `PostToolUse` events for `Write` and `Edit` tools
2. Checks if the file path ends with `.md`
3. Runs `markdownlint-cli2` and `cspell` validation
4. Returns exit code:
   - `0`: Validation passed (or not a markdown file)
   - `2`: Validation failed (blocks Claude, shows errors)

## Customization

Edit `scripts/validate-markdown.sh` to:
- Add more validation tools
- Change validation rules
- Skip certain file patterns
- Modify error messages

## Related

Extracted from [ai-assistant-instructions#351](https://github.com/JacobPEvans/ai-assistant-instructions/pull/351)
