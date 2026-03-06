---
name: validate-readme
description: >-
  Validate all README files in the repository for required sections and
  installation code blocks. Checks section presence using config from
  .readme-validator.yaml or sensible defaults. Badge URL reachability
  is checked on-demand via WebFetch.
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

Find all `README*.md` files in the repository, excluding `.git/` and `.claude/`
directories.

### 2. Validate each README

For each README found, check:

- Required sections present (from `.readme-validator.yaml` or defaults)
- Installation section contains at least one code block
- Optional sections present (warnings only)

Badge URL reachability may be checked on-demand using WebFetch for any badge
images found in the README.

### 3. Report results

Output a summary table:

| File | Status | Issues |
|------|--------|--------|
| ./README.md | PASS | -- |
| ./plugin/README.md | WARN | Missing: Contributing |

## Configuration

Place a `.readme-validator.yaml` file anywhere in the directory tree above the
README being validated. The hook searches upward up to 10 levels.

```yaml
required_sections:
  - Installation
  - Usage
optional_sections:
  - Contributing
  - License
  - API
```

**Defaults** (used when no config file is found):

- `required_sections`: `Installation`, `Usage`
- `optional_sections`: `Contributing`, `License`, `API`
