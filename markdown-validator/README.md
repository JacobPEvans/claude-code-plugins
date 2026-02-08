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

## Skip Behavior

The validator automatically skips:

- All files in home directory dotfiles/dotdirs (`~/.config/`, `~/.local/`, `~/.claude/`, etc.)
- All files within any `.claude` directory at any level
- Non-markdown files (files not ending in `.md`)
- Missing/deleted files

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

### Markdownlint Config Resolution

The plugin resolves markdownlint configuration in this order:

1. **Project config** — if a markdownlint config file exists in the edited file's directory tree
   (e.g., `.markdownlint.json`, `.markdownlint-cli2.yaml`), markdownlint-cli2 discovers it naturally
2. **User override** — `~/.markdownlint-cli2.yaml`, if it exists
3. **Plugin default** — `config/.markdownlint-cli2.yaml` bundled with this plugin
4. **Guaranteed fallback** — Temporary inline config with MD013=160 (ensures 160-character line limit is always enforced)

This means the plugin always has a working config. Project configs take precedence, user home overrides
are respected but not required, and plugin upgrades update the default without touching user overrides. The guaranteed
fallback ensures that even if the plugin config cannot be loaded, the 160-character line limit is still enforced.

### Customizing Rules

To override the plugin default globally, create `~/.markdownlint-cli2.yaml`:

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

To override per-project, add a markdownlint config file to your project root (e.g., `.markdownlint.json`).

> **Note:** The YAML format uses markdownlint-cli2's structure with a `config:` wrapper for rules
> and a top-level `fix:` option. If using JSON format (`.markdownlint.json`), use a flat structure without
> the `config` wrapper and omit the `fix` property.

**Default rule settings:**

- **MD013**: Line length limits configured for readability
  - `line_length: 160`: Regular text lines (default 80 breaks sentences mid-sentence)
  - `heading_line_length: 120`: Heading lines
  - `code_block_line_length: 160`: Code block lines
  - `tables: false`: Disable table line length checks
- **MD060**: Disabled due to version mismatch between GitHub Actions and nixpkgs
- **fix: true**: Auto-fix issues where possible during validation

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
