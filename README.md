# Claude Code Plugins

A collection of Claude Code plugins for enhanced development workflows with AI assistants.

## Available Plugins

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
- `jacobpevans-cc-plugins/webfetch-guard`
- `jacobpevans-cc-plugins/markdown-validator`
- `jacobpevans-cc-plugins/token-validator`
- `jacobpevans-cc-plugins/issue-limiter`

### Local Development

Clone this repository and link plugins:

```bash
git clone https://github.com/JacobPEvans/claude-code-plugins.git
cd claude-code-plugins
claude plugins link ./webfetch-guard
claude plugins link ./markdown-validator
claude plugins link ./token-validator
claude plugins link ./issue-limiter
```

## Plugin Structure

Each plugin follows Claude Code official best practices:

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json       # Plugin metadata
├── hooks/
│   └── hooks.json        # Hook configuration
├── scripts/
│   └── hook-script.py    # Implementation
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

## License

MIT License - See [LICENSE](LICENSE) for details.

## Author

**JacobPEvans**
- GitHub: [@JacobPEvans](https://github.com/JacobPEvans)
- Email: 20714140+JacobPEvans@users.noreply.github.com
