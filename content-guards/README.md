# content-guards

Content validation and guard hooks via PostToolUse.

See [ARCHITECTURE.md](ARCHITECTURE.md) for integration diagrams.

## Features

- **markdown-validator**: Validates markdown with markdownlint and cspell
- **token-validator**: Enforces configurable file token limits
- **webfetch-guard**: Blocks outdated year references in web queries
- **readme-validator**: Checks README files for required sections and badge health
- **issue-limiter**: Prevents GitHub issue backlog overflow with 24h rate limiting

## Usage

No manual invocation required. All hooks activate automatically:

- **token-validator** — blocks files exceeding token limits (PreToolUse: Write, Edit)
- **webfetch-guard** — blocks outdated year references in web queries (PreToolUse: WebFetch, WebSearch)
- **issue-limiter** — rate limits `gh issue create` and `gh pr create` (PreToolUse: Bash)
- **branch-limiter** — limits concurrent open branches (PreToolUse: Bash)
- **markdown-validator** — runs markdownlint + cspell after writes (PostToolUse: Write, Edit)
- **readme-validator** — checks README required sections after writes (PostToolUse: Write, Edit)

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
bats tests/content-guards/**/*.bats
```

Test coverage includes:

- File type filtering (non-markdown, missing, dotfiles)
- Config resolution (project vs fallback)
- Cross-repo editing scenarios
- Unbound variable regression prevention (PR #39, #40)
- Issue/PR rate limiting and hard-limit blocking
- README required section and installation code block validation

## License

Apache-2.0
