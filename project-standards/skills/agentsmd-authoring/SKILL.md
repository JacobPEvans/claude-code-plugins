---
name: agentsmd-authoring
description: Use when editing agentsmd files, creating skills/agents/rules, or working in ai-assistant-instructions
---

# AgentsMD Authoring Standards

## File Structure

```text
agentsmd/                     # Single source of truth
├── AGENTS.md                 # Main entry point
├── rules/                    # Auto-load every session (via .claude/rules symlink)
├── skills/                   # On-demand (via .claude/skills symlink)
├── agents/                   # Task subagents (via .claude/agents symlink)
└── workflows/                # Development workflow docs

.copilot/, .claude/, .gemini/ # Vendor dirs — symlinks only, no duplicates
```

## Token Targets

- **Target**: 500 tokens per file
- **Maximum**: 1,000 tokens per file
- **CLAUDE.md additions**: bare minimum — link to rules/skills for details
- **Single-purpose**: each skill/agent/rule does one thing

## Two-Tier Architecture

| Tier | Location | Purpose |
| --- | --- | --- |
| Agents | `.claude/agents/` | Task execution — single-responsibility workers |
| Skills | `agentsmd/skills/` | Canonical patterns — reusable rules/decision trees |

**Agents** reference skills for patterns. **Skills** define the "right way"
to do something. Agents do NOT duplicate skill logic — they reference it.

## Naming Convention

- **Skills**: `noun-pattern` (e.g., `permission-patterns`)
- **Agents**: `noun-doer` (e.g., `permissions-analyzer`)

## Frontmatter Templates

**Skill**:

```yaml
---
name: skill-name
description: Pattern description
---
```

**Agent**:

```yaml
---
name: agent-name
description: Action-focused description
model: haiku  # or sonnet/opus
author: JacobPEvans
allowed-tools: [list of tools]
---
```

## Cross-Referencing

- **In CLAUDE.md**: Use `@path/to/file` to compose content inline.
  Use markdown links only for conditional "see X if relevant" references.
- **In agents/skills/rules**: Reference by name
  (e.g., "the code-standards rule"). Rules in `.claude/rules/` auto-load.

## Vendor Config Standard

Vendor directories contain symlinks only. All canonical content lives in
`agentsmd/`. DRY — never duplicate across vendors.

Rules in `agentsmd/rules/` auto-load every session via `.claude/rules`
symlink. Keep rules focused and under 1,000 tokens.

## Related Skills

- **skills-registry** (project-standards) — Use when looking up available tools, skills, commands, agents, or plugins
- **workspace-standards** (project-standards) — Use when setting up or managing multi-repo workspaces
