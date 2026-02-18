# github-workflows

Claude Code plugin for PR management, multi-repo PR finalization, and issue shaping with Shape Up methodology.

## Skills

- **`/finalize-pr`** - Automatically finalize pull requests for merge (CodeQL checks, CI, review threads)
- **`/squash-merge-pr`** - Review PR metadata and recommend merge strategy with release-note-friendly commit message
- **`/ready-player-one`** - Orchestrate PR finalization across all repositories and report merge-readiness
- **`/resolve-pr-threads`** - Orchestrate resolution of PR review threads (requires superpowers plugin)
- **`/shape-issues`** - Shape raw ideas into actionable GitHub Issues using Shape Up methodology
- **`/trigger-ai-reviews`** - Trigger Claude, Gemini, and Copilot reviews on a PR

## Installation

```bash
claude plugins add jacobpevans-cc-plugins/github-workflows
```

## Usage

```text
/finalize-pr              # Automatic PR finalization workflow
/squash-merge-pr          # PR metadata review and merge recommendation
/ready-player-one         # Multi-repo PR finalization
/resolve-pr-threads       # Batch resolve review threads
/shape-issues             # Shape ideas into GitHub issues
/trigger-ai-reviews       # Trigger Claude, Gemini, Copilot reviews
```

## Dependencies

| Skill | Requires | Why |
|-------|----------|-----|
| `/resolve-pr-threads` | `superpowers` plugin | Sub-agents invoke `superpowers:receiving-code-review` for review feedback handling |

Install superpowers: `claude plugins add superpowers-marketplace/superpowers`

## License

MIT
