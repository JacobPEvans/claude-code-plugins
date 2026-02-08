# PR Review Toolkit

Systematic GitHub PR review thread management via GraphQL API.

## Overview

This plugin provides tools for resolving PR review feedback at scale. It automates
the read-implement-reply-resolve workflow so every review comment gets addressed
and no threads block your merge.

## What It Does

- Fetches all unresolved review threads via GitHub GraphQL API
- Classifies comments by priority (blocking, bugs, suggestions, questions, nitpicks)
- Implements requested code changes or drafts explanations
- Replies within review threads (not as top-level comments)
- Marks threads resolved after replying
- Verifies zero unresolved threads before completion

## Usage

```bash
/resolve-pr-threads              # Current branch PR
/resolve-pr-threads 142          # Specific PR number
/resolve-pr-threads all          # All open PRs (parallel processing)
```

## Key Features

### Thread-Aware Replies

Uses `addPullRequestReviewComment` GraphQL mutation to reply within threads,
not `gh pr comment` which creates top-level comments.

### Parameterized GraphQL

All queries use `-f` parameter syntax to avoid shell injection vulnerabilities
from string interpolation with `--raw-field`.

### Pagination Awareness

Documents the 100-thread query limit and warns when PRs exceed this threshold.

### Atomic Reply-Resolve

Every thread gets exactly one of: technical fix + reply + resolve, or
explanation + reply + resolve. Never resolves without replying first.

## Structure

```text
pr-review-toolkit/
├── .claude-plugin/
│   └── plugin.json              # Plugin metadata
├── skills/
│   └── resolve-pr-threads/
│       ├── SKILL.md             # Workflow implementation
│       └── graphql-queries.md   # Reusable GraphQL patterns
└── README.md                    # This file
```

## Requirements

- `gh` CLI authenticated with repo write access
- `jq` for JSON parsing
- GraphQL API access (comes with GitHub authentication)

## Security

- Uses parameterized GraphQL queries to prevent injection attacks
- Never exposes tokens or credentials in command examples
- Validates thread IDs before mutation operations

## Limitations

- Fetches only last 100 threads per query (document limitation, not pagination)
- Requires manual re-runs for PRs with more than 100 threads
- Cannot resolve threads the authenticated user did not create comments on

## License

MIT - See repository root LICENSE file
