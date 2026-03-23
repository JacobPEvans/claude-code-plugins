---
description: Require ≥1,000 GitHub stars before adding a dependency to trusted auto-merge lists
globs:
  - "renovate-presets.json"
  - "renovate.json"
  - ".github/renovate.json"
  - ".github/renovate.json5"
---

# Trusted Dependency Policy

Only repositories with **≥1,000 GitHub stars** may be added to trusted auto-merge lists (Renovate presets, GitHub Actions trusted orgs, etc.).

Before proposing any addition to a trusted list, verify the star count: `gh api repos/OWNER/REPO --jq '.stargazers_count'`
