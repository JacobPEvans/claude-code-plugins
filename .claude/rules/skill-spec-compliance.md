# Agent Skill Spec Compliance

All skills MUST pass `agentskills validate` ([agentskills.io spec](https://agentskills.io/specification)).

- Run `agentskills validate {skill-dir}` before committing any SKILL.md change
- Every skill needs a `.github/skills/{name}` symlink
- Every skill needs a `## Related Skills` section (by name, never path)
- Custom frontmatter fields go in `metadata:`, not top-level
