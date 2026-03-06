# github-workflows

Claude Code plugin for PR management and issue shaping with Shape Up methodology.

## Skills

- **`/finalize-pr`** - Finalize PRs for merge: single PR, all repo PRs (`all`), or all org PRs (`org`). Includes bot-authored PRs in all modes.
- **`/squash-merge-pr`** - Validate PR readiness and squash merge into main (errors if not ready)
- **`/resolve-pr-threads`** - Orchestrate resolution of PR review threads (requires superpowers plugin)
- **`/shape-issues`** - Shape raw ideas into actionable GitHub Issues using Shape Up methodology
- **`/trigger-ai-reviews`** - Trigger Claude, Gemini, and Copilot reviews on a PR

## Installation

```bash
claude plugins add jacobpevans-cc-plugins/github-workflows
```

## Usage

```text
/finalize-pr              # Finalize PR on current branch
/finalize-pr 42           # Finalize specific PR by number
/finalize-pr all          # Finalize all open PRs in repo (including bots)
/finalize-pr org          # Finalize all open PRs across org (including bots)
/squash-merge-pr          # Validate and squash merge
/resolve-pr-threads       # Batch resolve review threads
/shape-issues             # Shape ideas into GitHub issues
/trigger-ai-reviews       # Trigger Claude, Gemini, Copilot reviews
```

## Dependencies

| Skill | Requires | Why |
|-------|----------|-----|
| `/resolve-pr-threads` | `superpowers` plugin | Sub-agents invoke `superpowers:receiving-code-review` for review feedback handling |
| `/squash-merge-pr` | `git-workflows` plugin | Reads `/rebase-pr` Step 1 for PR validation query (single source of truth) |

Install superpowers: `claude plugins add superpowers-marketplace/superpowers`

## License

MIT
