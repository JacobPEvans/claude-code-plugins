# AI Review Trigger Reference

Detailed reference for each AI's trigger mechanism.

## Claude

| Property | Value |
|----------|-------|
| Trigger | PR comment containing `@claude` |
| Example | `@claude review this PR` |
| Re-review | Yes — post another comment |
| Requirement | Claude Code GitHub App installed on repo |

Claude responds to any `@claude` mention in PR comments. Re-reviews are fully supported by posting a new comment.

## Gemini

| Property | Value |
|----------|-------|
| Trigger | PR comment `/gemini review` |
| Example | `/gemini review` |
| Re-review | Yes — post the command again |
| Requirement | Gemini Code Assist GitHub App installed on repo |

Gemini uses a slash-command style trigger. Additional flags are available (e.g., `/gemini review --focused`) but `/gemini review` covers the standard case.

## Copilot

| Property | Value |
|----------|-------|
| Trigger | `POST /repos/{owner}/{repo}/pulls/{number}/requested_reviewers` |
| Reviewer slug | `copilot-pull-request-reviewer[bot]` |
| Re-review | **Not supported via API** |
| Requirement | GitHub Copilot code review enabled for the repo/org |

### Copilot Limitation

The GitHub API only supports requesting Copilot as a reviewer when it hasn't yet been requested on
that PR. Once Copilot has submitted a review, there is no API to trigger a re-review.
The UI allows dismissing a review and re-requesting, but no programmatic equivalent exists.

**Expected API response when already reviewed:**

```json
HTTP 422 Unprocessable Entity
{
  "message": "Review cannot be requested at this time."
}
```

This is not an error in the skill — treat it as a warning.

### Checking Copilot Installation

To verify Copilot is available on a repo:

```bash
gh api /repos/{owner}/{repo}/collaborators \
  --jq '.[] | select(.login == "copilot-pull-request-reviewer[bot]")'
```

If empty, Copilot code review is not enabled for the repo.

## Troubleshooting

### No bot responds after triggering

1. Verify the GitHub App is installed: **Repo Settings → Integrations → GitHub Apps**
2. Check the App has `pull_requests: write` permission
3. Confirm the PR is open (drafts may be excluded)

### `gh` authentication errors

```bash
gh auth status        # check current auth
gh auth login         # re-authenticate
```

### Copilot reviewer slug format

The slug `copilot-pull-request-reviewer[bot]` must be passed as a reviewer, not a team. Use the `-f` flag with `gh api`:

```bash
gh api --method POST /repos/OWNER/REPO/pulls/NUMBER/requested_reviewers \
  -f "reviewers[]=copilot-pull-request-reviewer[bot]"
```
