# Claude Code Plugins Quick Reference

Reference guide for AI assistants working with this repository.

## Repository Purpose

This is a **Claude Code plugins repository** containing production-ready hooks for development workflows.

## Available Plugins

| Plugin | Type | Tools | Purpose |
|--------|------|-------|---------|
| **webfetch-guard** | PreToolUse | WebFetch, WebSearch | Blocks outdated year references in web queries |
| **markdown-validator** | PostToolUse | Write, Edit | Validates markdown with markdownlint and cspell |
| **token-validator** | PreToolUse | Write, Edit | Enforces configurable file token limits |
| **issue-limiter** | PreToolUse | Bash (gh) | Prevents GitHub issue backlog overflow |

## Plugin Development

### Structure Requirements

All plugins must follow this structure:

```
plugin-name/
├── .claude-plugin/plugin.json  # Metadata (required)
├── hooks/hooks.json            # Hook config (required)
├── scripts/                    # Implementation (required)
└── README.md                   # Documentation (required)
```

### plugin.json Schema

```json
{
  "name": "plugin-name",
  "version": "1.0.0",
  "description": "Brief description",
  "author": {
    "name": "JacobPEvans",
    "email": "20714140+JacobPEvans@users.noreply.github.com"
  },
  "license": "MIT",
  "keywords": ["hooks", "category", "relevant-tags"]
}
```

### hooks.json Pattern

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "ToolName|Pattern",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/script.py",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

### Best Practices

- Use `${CLAUDE_PLUGIN_ROOT}` for all plugin-relative paths
- Exit code 0 = allow operation
- Exit code 2 = block operation (stderr shown to Claude)
- Fail open when external tools unavailable
- Provide actionable error messages
- Follow `noun-verb` naming pattern

## CI/CD

### Workflows

- **validate-plugin.yml**: Validates plugin structure on PR
- **auto-label-issues.yml**: Auto-applies priority/size labels

### Pre-commit Hooks

- Markdown linting via markdownlint-cli2
- Spell checking via cspell
- Conventional commit enforcement

## Labels

### Required per PR/Issue

- `type:*` - One required (bug, feature, breaking, docs, chore, ci, test, refactor, perf)
- `priority:*` - Exactly one (critical, high, medium, low)
- `size:*` - Exactly one (xs, s, m, l, xl)

### Workflow Labels

- `ai:created` - Created by AI (needs human review)
- `ai:ready` - AI-created content approved
- `ready-for-dev` - Ready to implement
- `good-first-issue` - Good for newcomers

## Marketplace

**Name**: `jacobpevans-cc-plugins`
**Registry**: `.claude-plugin/marketplace.json`

### Installation Command Pattern

```bash
claude plugins add jacobpevans-cc-plugins/<plugin-name>
```
