---
name: codeql-permission-classification
description: Permission requirements for GitHub Actions
version: "1.0.0"
author: JacobPEvans
---

# CodeQL Permission Classification

Single source of truth for GitHub Actions permission requirements.

## Permission Types

GitHub Actions provides these permission scopes:

```
contents            # Read/write repository content (checkout, tags, releases)
pull-requests       # Read/write PR comments, reviews, assignments
issues              # Read/write issue comments, labels, projects
deployments         # Read/write deployment status
packages            # Read/write packages
actions             # Read/write GitHub Actions (runners, artifacts, caches)
checks              # Read/write check runs and annotations
statuses            # Read/write commit statuses
security-events     # Read/write code scanning and secret scanning results
```

## Common Actions → Permissions Matrix

| Action | Required Permissions | Use Case |
|--------|----------------------|----------|
| `actions/checkout@v6` | `contents: read` | Clone repository |
| `actions/upload-artifact@v6` | None (usually) | Store build artifacts |
| `actions/download-artifact@v6` | None (usually) | Retrieve artifacts |
| `actions/setup-node@v6` | None | Install Node.js |
| `actions/github-script@v6` | Depends on script | Usually `contents: read` minimum |
| `actions/create-release@v1` | `contents: write` | Create GitHub release |
| `github/codeql-action/upload-sarif@v2` | `security-events: write` | Upload CodeQL results |

## Decision Tree

**Q1: Does your job use `actions/checkout`?**
- YES → Add `contents: read`
- NO  → Continue to Q2

**Q2: Does your job modify repository (create PR, tag, release)?**
- YES → Add `contents: write`
- NO  → Continue to Q3

**Q3: Does your job post comments to PR or issues?**
- YES → Add `pull-requests: write` (PR) or `issues: write` (issues)
- NO  → Continue to Q4

**Q4: Does your job modify deployments?**
- YES → Add `deployments: write`
- NO  → Continue to Q5

**Q5: Does your job use `github.rest` API?**
- YES → Add permission for the API endpoint you're calling
- NO  → Continue to Q6

**Q6: Does your job call a reusable workflow?**
- YES → Add union of ALL permissions needed by that workflow's jobs
- NO  → Continue to Q7

**Q7: Is your job just aggregating results with no API access?**
- YES → Add `permissions: {}` (empty - no token needed)
- NO  → You probably missed something. Review again.

## Examples

### Example 1: Simple Checkout & Test

```yaml
test:
  runs-on: ubuntu-latest
  permissions:
    contents: read  # For checkout
  steps:
    - uses: actions/checkout@v6
    - run: npm test
```

### Example 2: Create Release

```yaml
release:
  runs-on: ubuntu-latest
  permissions:
    contents: write  # For creating release
  steps:
    - uses: actions/checkout@v6
    - uses: actions/create-release@v1
      with:
        tag_name: v1.0.0
```

### Example 3: Post PR Comment

```yaml
comment:
  runs-on: ubuntu-latest
  permissions:
    contents: read       # For checkout
    pull-requests: write # For creating comment
  steps:
    - uses: actions/checkout@v6
    - run: npm run lint | tee lint-result.txt
    - uses: actions/github-script@v6
      with:
        script: |
          github.rest.pulls.createReview({
            pull_number: context.issue.number,
            body: 'Lint check passed'
          })
```

### Example 4: Reusable Workflow Call

If `.github/workflows/_validate.yml` contains:
```yaml
jobs:
  validate:
    permissions:
      contents: read
      pull-requests: write  # This job posts comments
    steps: ...
```

Then the caller must declare:
```yaml
validate:
  permissions:
    contents: read
    pull-requests: write  # Union of nested job permissions
  uses: ./.github/workflows/_validate.yml
```

### Example 5: No Permissions Needed

```yaml
gate:
  runs-on: ubuntu-latest
  permissions: {}  # Explicitly no permissions needed
  steps:
    - uses: re-actors/alls-green@release/v1
      with:
        allowed-skips: job1, job2
        jobs: ${{ toJSON(needs) }}
```

## Reusable Workflow Caller Contract

**Important**: When a job calls a reusable workflow via `uses:`, the caller job must declare permissions for all jobs within the reusable workflow.

**Why**: The reusable workflow's nested jobs inherit the permissions from the caller's `GITHUB_TOKEN`, so the caller must declare everything the callee needs.

**Example mismatch** (WRONG):
```yaml
# ci-gate.yml
validate:
  # Missing permissions!
  uses: ./.github/workflows/_validate.yml

# _validate.yml
jobs:
  check:
    permissions:
      contents: read
      pull-requests: write
    steps: ...
```

**Correct**:
```yaml
# ci-gate.yml
validate:
  permissions:
    contents: read
    pull-requests: write  # Declare what _validate.yml needs
  uses: ./.github/workflows/_validate.yml
```

## GitHub Token Default Behavior

**Without explicit permissions:**
- **Public repos**: Defaults to `GITHUB_TOKEN: read-all` (dangerous!)
- **Private repos**: Defaults to `GITHUB_TOKEN: read-write` (very dangerous!)

**With explicit permissions**:
- Uses minimum required scope (safe, follows least-privilege)
- Auditable - others can see exactly what tokens can access
- CodeQL approves (no "missing permissions" alert)

## Common Mistakes

❌ **Mistake 1**: Forgetting PR/issues permissions
```yaml
# WRONG - Creates comment but no permission
comment:
  steps:
    - uses: actions/github-script@v6
      with:
        script: github.rest.issues.createComment({...})
```

✅ **Correct**:
```yaml
comment:
  permissions:
    issues: write  # ← Add this
  steps:
    - uses: actions/github-script@v6
      with:
        script: github.rest.issues.createComment({...})
```

❌ **Mistake 2**: Not declaring union of reusable workflow permissions
```yaml
# WRONG - Reusable workflow's jobs need more permissions
my-job:
  permissions:
    contents: read  # But reusable also needs pull-requests: write
  uses: ./.github/workflows/_validate.yml
```

✅ **Correct**:
```yaml
my-job:
  permissions:
    contents: read
    pull-requests: write  # Include all permissions from reusable
  uses: ./.github/workflows/_validate.yml
```

❌ **Mistake 3**: Over-permissioning
```yaml
# WRONG - Too much permission
build:
  permissions:
    contents: write  # Unnecessary - only reads files
  steps:
    - uses: actions/checkout@v6
    - run: npm build
```

✅ **Correct** (least-privilege):
```yaml
build:
  permissions:
    contents: read  # Minimum needed for checkout
  steps:
    - uses: actions/checkout@v6
    - run: npm build
```

## Testing Your Permissions

Run CodeQL scan locally:
```bash
codeql database create my_db --language=actions --source-root=.
codeql database analyze my_db actions/security-and-quality.qls --format=sarif-latest --output=results.sarif
```

Or wait for GitHub to scan and check:
```bash
gh pr checks  # See if CodeQL permission alerts appear
```

## References

- [GitHub Actions: Permissions](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions#permissions)
- [GitHub Actions: Default GITHUB_TOKEN Permissions](https://docs.github.com/en/actions/security-guides/automatic-token-authentication#permissions-for-the-github_token)
- [GitHub Actions: Calling Reusable Workflows](https://docs.github.com/en/actions/using-workflows/reusing-workflows)
