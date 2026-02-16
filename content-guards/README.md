# content-guards

Content validation and guard hooks via PostToolUse.

## Features

- **markdown-validator**: Validates markdown with markdownlint and cspell
- **token-validator**: Enforces configurable file token limits
- **webfetch-guard**: Blocks outdated year references in web queries
- **issue-limiter**: Prevents GitHub issue backlog overflow

## Installation

```bash
claude plugins add jacobpevans-cc-plugins/content-guards
```

## Dependencies

- `jq` - JSON processing
- `atc` - Token counting tool
- `markdownlint-cli2` - Markdown linting
- `cspell` - Spell checking
- `gh` - GitHub CLI

## Testing

The markdown-validator has automated tests using [bats-core](https://github.com/bats-core/bats-core):

```bash
# Install bats-core (if not already installed)
brew install bats-core

# Run the test suite from repo root
bats tests/content-guards/markdown-validator/validate-markdown.bats
```

Test coverage includes:
- File type filtering (non-markdown, missing, dotfiles)
- Config resolution (project vs fallback)
- Cross-repo editing scenarios
- Unbound variable regression prevention (PR #39, #40)

## License

Apache-2.0
