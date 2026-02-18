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

### Hook Implementation Language Selection

Choose the implementation language based on complexity:

**Use Shell (bash/zsh) for**:

- Simple git command checks (10-30 lines)
- File existence/path validation
- Basic string matching and JSON field extraction
- Exit code based logic
- Repository-aware file checks

**Use Python for**:

- Complex JSON manipulation beyond simple field extraction
- Multi-step conditional logic (>50 lines)
- Cross-platform compatibility requirements
- Integration with Python-specific tools

**Dependencies**:

- Shell scripts may use: `jq`, `git`, standard Unix tools
- Prefer fewer dependencies when possible
- Always fail-open when dependencies unavailable

**Examples**:

- ✅ Shell: main-branch-guard (~60 lines, extracts JSON field, runs git commands from file's directory)
- ✅ Python: git-permission-guard (command pattern matching and blocking)
- ✅ Python: Complex AST parsing or multi-stage file transformation
- ❌ Python: Simple branch checks (overkill, harder to maintain)

**Key principle**: Simplicity beats sophistication. Use the simplest tool that solves the problem correctly.

## File Linking & Memory Organization

### `@` File Imports

When linking to other files in CLAUDE.md or any rules file, **always use `@path/to/file` syntax** — never markdown links `[text](path)`. The `@` syntax is the official Claude Code import: it actually loads the file's content into context. Markdown links are inert text.

```md
# ✅ Correct — imports the file's content
See @docs/setup.md for environment setup.

# ❌ Wrong — just a text reference, nothing is loaded
See [Setup](docs/setup.md) for environment setup.
```

### `.claude/rules/` for Always-Active Rules

Place rules that should always be loaded into `.claude/rules/` — Claude Code auto-loads all `.md` files there with the same priority as CLAUDE.md. No `@` import needed.

Rules files support YAML frontmatter to scope them to specific file patterns:

```md
---
paths:
  - "hooks/**/*.py"
---
# Hook Script Rules
- All hooks must exit 0 (allow) or 2 (block)
```

Rules without `paths` frontmatter apply unconditionally. Use `.claude/rules/` over `@` imports when rules should always be active, not just when a specific file is referenced. Symlinks in `.claude/rules/` are supported — use them to share rules across repos.

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
