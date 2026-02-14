# github-workflows

Claude Code plugin for PR management, multi-repo PR finalization, and issue shaping with Shape Up methodology.

## Skills

- **`/manage-pr`** - Create, monitor, fix, and prepare pull requests for merge (single PR scope)
- **`/ready-player-one`** - Orchestrate PR finalization across all repositories and report merge-readiness
- **`/resolve-pr-threads`** - Orchestrate resolution of PR review threads (requires superpowers plugin)
- **`/shape-issues`** - Shape raw ideas into actionable GitHub Issues using Shape Up methodology

## Installation

```bash
claude plugins add jacobpevans-cc-plugins/github-workflows
```

## Usage

```text
/manage-pr
/ready-player-one
/shape-issues
```

## Dependencies

| Skill | Requires | Why |
|-------|----------|-----|
| `/resolve-pr-threads` | `superpowers` plugin | Sub-agents invoke `superpowers:receiving-code-review` for review feedback handling |

Install superpowers: `claude plugins add superpowers-marketplace/superpowers`

## License

MIT
