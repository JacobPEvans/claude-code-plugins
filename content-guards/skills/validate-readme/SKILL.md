---
name: validate-readme
description: >-
  Validate all README files in the repository for required sections and badge health.
  Checks section presence, installation code blocks, and badge URL reachability
  using config from .readme-validator.yaml or sensible defaults.
---

<!-- cspell:words validator -->

# Validate README

Run a comprehensive audit of all README.md files in the current repository.

## Usage

```text
/validate-readme
```

## Steps

### 1. Find all README files

```bash
find . -name "README*.md" -not -path "./.git/*" -not -path "./.claude/*"
```

### 2. Validate each README

For each README found, check:

- Required sections present (from `.readme-validator.yaml` or defaults)
- Badge URLs return HTTP 200
- Installation section contains code blocks

### 3. Report results

Output a summary table:

| File | Status | Issues |
|------|--------|--------|
| ./README.md | PASS | -- |
| ./plugin/README.md | WARN | Missing: Contributing |
