---
description: Enforce standard formatting for all .claude/rules/ files
globs:
  - ".claude/rules/**"
---

# Rule Formatting Standard

All `.claude/rules/*.md` files must include YAML frontmatter with:

- **`description`** (required): One-line summary of what the rule enforces
- **`globs`** (required when file-scoped): Array of glob patterns restricting when the rule loads

Rules that apply only when specific files are edited must use `globs` to scope them.
Rules that apply universally (process guidance, conventions) omit `globs` but still require `description`.

```yaml
---
description: Brief description of the rule
globs:
  - "path/to/relevant/**"
---
```
