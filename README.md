# Claude Code Plugins

A collection of Claude Code plugins for enhanced development workflows with AI assistants.

## Available Plugins

### git-rebase-workflow

Local rebase-merge workflow for maintaining linear git history with signed commits.

- **Type**: Command/Skill-based plugin
- **Command**: `/rebase-pr`
- **Purpose**: Merge PRs using a local rebase workflow that preserves commit signatures

### webfetch-guard

Intercepts WebFetch and WebSearch tool calls to enforce date awareness and block outdated year references.

- **Type**: PreToolUse hook
- **Tools**: WebFetch, WebSearch
- **Purpose**: Prevents Claude from using outdated search queries by blocking old year references

### markdown-validator

Validates markdown files after Write/Edit operations using industry-standard linting tools.

- **Type**: PostToolUse hook
- **Tools**: Write, Edit
- **Linters**: markdownlint-cli2, cspell
- **Purpose**: Ensures markdown quality and consistency

### token-validator

Enforces configurable token limits on files to prevent bloat and maintain focused modules.

- **Type**: PreToolUse hook
- **Tools**: Write, Edit
- **Configuration**: `.token-limits.yaml`
- **Purpose**: File size governance via token counting

### issue-limiter

Prevents GitHub issue backlog overflow by enforcing creation limits.

- **Type**: PreToolUse hook
- **Tools**: Bash (gh CLI)
- **Limits**: 50 total issues, 25 AI-created issues
- **Purpose**: Backlog management and quality control

## Installation

### From Marketplace

```bash
claude plugins add jacobpevans-cc-plugins/<plugin-name>
```

**Available plugins**:

- `jacobpevans-cc-plugins/git-rebase-workflow`
- `jacobpevans-cc-plugins/issue-limiter`
- `jacobpevans-cc-plugins/markdown-validator`
- `jacobpevans-cc-plugins/token-validator`
- `jacobpevans-cc-plugins/webfetch-guard`

### Local Development

Clone this repository and link plugins:

```bash
git clone https://github.com/JacobPEvans/claude-code-plugins.git
cd claude-code-plugins
claude plugins link ./git-rebase-workflow
claude plugins link ./issue-limiter
claude plugins link ./markdown-validator
claude plugins link ./token-validator
claude plugins link ./webfetch-guard
```

## Plugin Structure

Each plugin follows Claude Code official best practices. Most plugins use hook-based structure:

```text
plugin-name/
├── .claude-plugin/
│   └── plugin.json       # Plugin metadata
├── hooks/
│   └── hooks.json        # Hook configuration
├── scripts/
│   └── hook-script.py    # Implementation
└── README.md             # Plugin documentation
```

Command/skill-based plugins use a different structure:

```text
plugin-name/
├── .claude-plugin/
│   └── plugin.json       # Plugin metadata
├── commands/
│   └── command.md        # Command definition
├── skills/
│   └── skill-name/
│       └── SKILL.md      # Skill documentation
└── README.md             # Plugin documentation
```

## Contributing

See individual plugin READMEs for specific details. General contribution guidelines:

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Follow conventional commits: `feat(plugin): description`
4. Sign your commits (GPG required)
5. Submit a pull request

## Development

### Requirements

- Claude Code CLI
- Python 3.10+ (for hook scripts)
- Tool-specific dependencies (see individual plugin READMEs)

### Testing Plugins Locally

```bash
# Link a plugin for testing
claude plugins link ./plugin-name

# Verify it loaded
claude plugins list

# Test functionality
# (trigger the hook conditions for the specific plugin)
```

## Repository Integration

### Nix Flake Auto-Update

This repository automatically triggers Nix flake updates when changes are merged to main.
This ensures downstream repositories (like [nix-config](https://github.com/JacobPEvans/nix))
immediately pull in plugin updates instead of waiting for scheduled updates.

#### How It Works

1. Changes merged to `main` branch trigger `.github/workflows/trigger-nix-update.yml`
2. Workflow sends a `repository_dispatch` event to the nix repository
3. Nix repository's `deps-update-flake.yml` workflow updates the `claude-code-plugins` flake input
4. Automated PR created with the updated `flake.lock`

#### Organization Secret Required

The trigger workflow requires a GitHub Personal Access Token (PAT) stored as an organization secret:

**Secret Name**: `WORKFLOW_DISPATCH_PAT`

**Required Scopes**:

- `repo` - Full control of private repositories
- `workflow` - Update GitHub Action workflows

**Setup Instructions**:

1. Generate PAT: GitHub.com → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Select required scopes: `repo` and `workflow`
3. Set expiration to 1 year
4. Copy the token
5. Add as organization secret: Organization Settings → Secrets and variables → Actions → New organization secret
6. Name: `WORKFLOW_DISPATCH_PAT`
7. Paste token value
8. Select repository access (all repositories or specific repos)

**Security Notes**:

- Token has minimal scopes (no admin, no packages)
- Rotate token annually before expiration
- Never expose token in logs or workflow outputs
- Organization-level secret is accessible to all repos

#### Reusable Pattern

This pattern can be replicated to any JacobPEvans repository that's a flake input. Simply:

1. Copy `.github/workflows/trigger-nix-update.yml` to the target repository
2. Update the `flake_input_name` field to match the flake input name in `nix/flake.nix`
3. No changes needed to the nix repository workflow (uses generic event type)

## License

MIT License - See [LICENSE](LICENSE) for details.

## Author

JacobPEvans

- GitHub: [@JacobPEvans](https://github.com/JacobPEvans)
- Email: <20714140+JacobPEvans@users.noreply.github.com>
