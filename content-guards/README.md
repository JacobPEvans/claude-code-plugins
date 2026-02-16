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

Run tests using the shared test runner:

```bash
# From repository root
./scripts/run-tests.sh content-guards

# Alternative: run bats directly
bats content-guards/tests/*.bats
```

## License

Apache-2.0
