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

### Global Markdownlint Configuration

This plugin uses a global markdownlint configuration file at `~/.markdownlint-cli2.yaml`. The configuration
defines the validation rules used by this plugin. If this file is missing, the validation hook will fail with
a clear error message prompting you to create it.

**Recommended configuration** (`~/.markdownlint-cli2.yaml`):

```yaml
config:
  default: true
  MD013:
    line_length: 160
    heading_line_length: 120
    code_block_line_length: 160
    tables: false
  MD060: false
fix: true
```

> **Note:** The YAML format shown above uses markdownlint-cli2's structure with a `config:` wrapper for rules
> and a top-level `fix:` option. If using JSON format (`.markdownlint.json`), use a flat structure without
> the `config` wrapper and omit the `fix` property, as shown in this repository's `.markdownlint.json`.

**Key settings:**

- **MD013**: Line length limits configured for readability
  - `line_length: 160`: Regular text lines (default 80 breaks sentences mid-sentence)
  - `heading_line_length: 120`: Heading lines
  - `code_block_line_length: 160`: Code block lines
  - `tables: false`: Disable table line length checks
- **MD060**: Disabled due to version mismatch between GitHub Actions and nixpkgs
- **fix: true**: Auto-fix issues where possible during validation

If you don't have this file, create it with the above configuration.

### Hook Configuration

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
