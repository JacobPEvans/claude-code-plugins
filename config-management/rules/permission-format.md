---
description: Permission format rules for AI tool settings — enforces Bash(command *) space-wildcard format
globs:
  - "agentsmd/permissions/**"
  - "**/settings.json"
  - "**/settings.local.json"
---

# Permission Format

## Generated Format

The correct format for Claude Code permission entries is `Bash(command *)` — **space-wildcard**, not colon-wildcard.

| Correct | Deprecated |
| --- | --- |
| `Bash(git *)` | `Bash(git:*)` |
| `Bash(docker exec *)` | `Bash(docker exec:*)` |
| `Bash(pytest *)` | `Bash(pytest:*)` |

The `:*` suffix format is deprecated per Claude Code documentation.

## Source Format

Source JSON files in `agentsmd/permissions/` store bare commands with no suffix:

```json
{
  "commands": [
    "git",
    "docker exec",
    "pytest"
  ]
}
```

The Nix formatter appends a space followed by `*` when generating `settings.json`. Never add `:*` or a trailing space-wildcard to source files.

## Hierarchy

Allow direct tool invocations from nix dev shells — not wrapper forms:

| Correct (nix-first) | Unnecessary wrapper |
| --- | --- |
| `pytest` | `.venv/bin/pytest` |
| `ansible-lint` | `uv run ansible-lint` |
| `playwright` | `npx playwright` |
| `bun test` | `bun run test` |

## Precedence

Permission resolution order: **deny > ask > allow**.

Adding a command to `allow` does NOT override an `ask` entry for the same command prefix.
To allow `python -m pytest` without prompting, ensure `python` is NOT in `ask/`.
