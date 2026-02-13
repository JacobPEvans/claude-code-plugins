# Claude Code Plugins Quick Reference

Reference guide for AI assistants working with this repository.

## Repository Purpose

This is a **Claude Code plugins repository** containing production-ready hooks for development workflows.

## Available Plugins

| Plugin | Type | Tools/Commands | Purpose |
|--------|------|--------|---------|
| **git-permission-guard** | PreToolUse | Bash | Blocks dangerous git/gh commands |
| **git-rebase-workflow** | Command/Skill | `/rebase-pr` | Local rebase-merge workflow for linear git history |
| **issue-limiter** | PreToolUse | Bash (gh) | Prevents GitHub issue backlog overflow |
| **main-branch-guard** | PreToolUse | Edit, Write, NotebookEdit | Blocks file edits on main branch |
| **markdown-validator** | PostToolUse | Write, Edit | Validates markdown with markdownlint and cspell |
| **pr-review-toolkit** | Skill | `/resolve-pr-threads` | Resolve PR review threads via GraphQL (read, reply, resolve) |
| **token-validator** | PreToolUse | Write, Edit | Enforces configurable file token limits |
| **webfetch-guard** | PreToolUse | WebFetch, WebSearch | Blocks outdated year references in web queries |

## Plugin Development

### Structure Requirements

Most hook-based plugins follow this structure:

```text
plugin-name/
├── .claude-plugin/plugin.json  # Metadata (required)
├── hooks/hooks.json            # Hook config (required)
├── scripts/                    # Implementation (required)
└── README.md                   # Documentation (required)
```

Command/skill-based plugins use this structure:

```text
plugin-name/
├── .claude-plugin/plugin.json  # Metadata (required)
├── commands/                   # Command definitions
├── skills/                     # Skill definitions
└── README.md                   # Documentation (required)
```

### plugin.json Schema (Strict)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | YES | Must match directory name |
| `version` | string | YES | Semver (e.g., "1.0.0") |
| `description` | string | YES | Brief description |
| `author` | object | YES | `{"name": "JacobPEvans"}` — MUST be object, NOT string |
| `license` | string | no | SPDX identifier |
| `repository` | string | no | GitHub URL |
| `homepage` | string | no | Documentation URL |
| `keywords` | string[] | no | Tags for discoverability |
| `skills` | string[] | no | Paths: `["./skills/skill-name"]` — NOT objects |
| `commands` | string[] | no | Paths: `["./commands/cmd.md"]` — NOT objects |
| `agents` | string[] | no | Paths: `["./agents/agent.md"]` — NOT objects |

**Forbidden fields**: `bugs` (unrecognized by Claude Code runtime)

**Common mistakes**:
- `author` as string instead of object
- `skills`/`commands`/`agents` as arrays of objects with name/description instead of string paths

**Example**:
```json
{
  "name": "plugin-name",
  "version": "1.0.0",
  "description": "Brief description",
  "author": {
    "name": "JacobPEvans"
  },
  "license": "Apache-2.0",
  "repository": "https://github.com/JacobPEvans/claude-code-plugins",
  "keywords": ["hooks", "category", "relevant-tags"],
  "skills": [
    "./skills/skill-one",
    "./skills/skill-two"
  ]
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
