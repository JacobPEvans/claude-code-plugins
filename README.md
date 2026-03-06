# Claude Code Plugins

A collection of Claude Code plugins for enhanced development workflows with AI assistants.

## Available Plugins

### git-guards

Git security and workflow protection via PreToolUse hooks.

- **Type**: PreToolUse hook
- **Features**: git-permission-guard (blocks dangerous git/gh commands), main-branch-guard (prevents edits on main)
- **Purpose**: Enforce safe git practices and worktree workflow

### content-guards

Combined content validation and guard hooks.

- **Type**: PostToolUse hook
- **Tools**: Write, Edit, Bash (gh CLI)
- **Features**: markdown-validator, token-validator, webfetch-guard, issue-limiter
- **Purpose**: Markdown quality, file size governance, date-aware web queries, backlog control

### git-workflows

Git worktree initialization, main branch synchronization, and PR merging skills.

- **Type**: Command/Skill-based plugin
- **Skills**: `/init-worktree`, `/sync-main`, `/rebase-pr`, `/refresh-repo`, and troubleshooting skills
- **Purpose**: Structured worktree and PR merge workflows

### github-workflows

GitHub PR and issue management skills.

- **Type**: Command/Skill-based plugin
- **Skills**: `/finalize-pr`, `/squash-merge-pr`, `/resolve-pr-threads`, `/shape-issues`, `/trigger-ai-reviews`
- **Purpose**: PR lifecycle and issue shaping workflows

### ai-delegation

Delegate tasks to external AI models and run autonomous maintenance loops.

- **Type**: Skill-based plugin
- **Skills**: `auto-maintain`, `delegate-to-ai`
- **Purpose**: AI-assisted automation and delegation

### config-management

Sync AI tool permissions across repositories.

- **Type**: Skill-based plugin
- **Skills**: `sync-permissions`, `quick-add-permission`
- **Purpose**: Consistent always-allow permission management

### codeql-resolver

Systematic CodeQL alert analysis and resolution for GitHub Actions workflows.

- **Type**: Command/Skill/Agent-based plugin
- **Purpose**: Diagnose and fix CodeQL security alerts

### infra-orchestration

Cross-repo infrastructure orchestration for Terraform and Ansible workflows.

- **Type**: Skill-based plugin
- **Purpose**: Orchestrate infrastructure changes across multiple repositories

### process-cleanup

Cleanup orphaned MCP server processes on session exit.

- **Type**: PostToolUse hook
- **Purpose**: Workaround for upstream MCP process leak bug

## Installation

### From Marketplace

```bash
claude plugins add jacobpevans-cc-plugins/<plugin-name>
```

**Available plugins**:

- `jacobpevans-cc-plugins/git-guards`
- `jacobpevans-cc-plugins/content-guards`
- `jacobpevans-cc-plugins/git-workflows`
- `jacobpevans-cc-plugins/github-workflows`
- `jacobpevans-cc-plugins/ai-delegation`
- `jacobpevans-cc-plugins/config-management`
- `jacobpevans-cc-plugins/codeql-resolver`
- `jacobpevans-cc-plugins/infra-orchestration`
- `jacobpevans-cc-plugins/process-cleanup`

### Local Development

Clone this repository and link plugins:

```bash
git clone https://github.com/JacobPEvans/claude-code-plugins.git
cd claude-code-plugins
claude plugins link ./git-guards
claude plugins link ./content-guards
claude plugins link ./git-workflows
claude plugins link ./github-workflows
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
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Follow conventional commits: `feat(plugin): description`
4. Sign your commits (GPG required)
5. Submit a pull request

## Development

### Requirements

- Claude Code CLI
- Python 3.10+ (for hook scripts)
- bats-core (for running tests)
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

### Running Tests

Run the shared test runner to execute all plugin tests:

```bash
# Run all tests
./scripts/run-tests.sh

# Run tests for a specific plugin
./scripts/run-tests.sh content-guards

# Alternative: run bats directly on a specific test file
bats tests/content-guards/markdown-validator/validate-markdown.bats
```

### Git Hooks

Enable optional pre-push hooks that run tests before pushing:

```bash
# Enable git hooks
git config core.hooksPath .githooks

# Disable git hooks
git config --unset core.hooksPath
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

**Secret Name**: `GH_PAT_WORKFLOW_DISPATCH`

**Required Scopes**:

- `repo` - Full control of private repositories
- `workflow` - Update GitHub Action workflows

**Setup Instructions**:

1. Generate PAT: GitHub.com → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Select required scopes: `repo` and `workflow`
3. Set expiration to 1 year
4. Copy the token
5. Add as organization secret: Organization Settings → Secrets and variables → Actions → New organization secret
6. Name: `GH_PAT_WORKFLOW_DISPATCH`
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

Apache License 2.0 - See [LICENSE](LICENSE) for details.

## Author

JacobPEvans

- GitHub: [@JacobPEvans](https://github.com/JacobPEvans)
- Email: <20714140+JacobPEvans@users.noreply.github.com>
