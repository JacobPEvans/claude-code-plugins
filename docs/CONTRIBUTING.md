# Contributing

First off, thanks for considering contributing to this project. It's just me here, so any help is genuinely appreciated.

## The Short Version

1. Fork it
2. Create your feature branch (`git checkout -b feat/cool-thing`)
3. Commit your changes (`git commit -m 'Add some cool thing'`)
4. Push to the branch (`git push origin feat/cool-thing`)
5. Open a Pull Request

That's it. I'm not picky.

## Signing Your Commits

**Commit signing is required** for all contributions. This verifies that commits actually come from you.

### Getting Started with Commit Signing

If you've never signed commits before, don't worry—it only takes a few minutes to set up:

1. **Generate a GPG key** (if you don't have one): Follow [GitHub's guide on generating a GPG key](https://docs.github.com/en/authentication/managing-commit-signature-verification/generating-a-new-gpg-key)

2. **Configure Git to sign your commits**: After setting up your GPG key, tell Git to use it:

   ```bash
   # The following commands apply only to this repository.
   # To sign commits for all your projects, add the `--global` flag.
   git config user.signingkey <YOUR_GPG_KEY_ID>
   git config commit.gpgsign true
   ```

   (Replace `<YOUR_GPG_KEY_ID>` with your actual key ID from step 1)

3. **Add your public key to GitHub**: [Add your GPG key to your GitHub account](https://docs.github.com/en/authentication/managing-commit-signature-verification/adding-a-gpg-key-to-your-github-account)

Once set up, Git will automatically sign all your commits. Your PRs will show a "Verified" badge next to your commits.

**Need more help?** See GitHub's [complete guide to commit signature verification](https://docs.github.com/en/authentication/managing-commit-signature-verification).

## Reporting Issues

Found a bug? Something unclear? Open an issue. Describe what you expected, what happened instead, and any relevant context. Screenshots are nice but not required.

## Pull Requests

### Selecting a Template

This repository provides multiple PR templates for different types of changes. Select the template that best matches your PR:

- **Bug fixes**: Append `?template=bug.md` to the PR creation URL
- **New features**: Append `?template=feature.md` to the PR creation URL
- **Breaking changes**: Append `?template=breaking.md` to the PR creation URL
- **Documentation**: Append `?template=docs.md` to the PR creation URL
- **Refactoring**: Append `?template=refactor.md` to the PR creation URL
- **Performance**: Append `?template=performance.md` to the PR creation URL
- **Other changes** (chores, CI, tests): Default template loads automatically

### PR Title Format

All PRs must use **conventional commit format** in the title:

**Format**: `type(scope): brief description`

**Types** (must match `type:*` labels):

- `feat` - New features (type:feature)
- `fix` - Bug fixes (type:bug)
- `docs` - Documentation (type:docs)
- `chore` - Maintenance (type:chore)
- `ci` - CI/CD changes (type:ci)
- `test` - Test updates (type:test)
- `refactor` - Code refactoring (type:refactor)
- `perf` - Performance (type:perf)
- `feat!` or `breaking(scope):` - Breaking changes (type:breaking)

**Examples**:

- `feat(api): add user authentication endpoint`
- `fix(ui): resolve button alignment issue`
- `docs(readme): update installation instructions`
- `chore(deps): update dependencies`
- `feat!: remove deprecated v1 API endpoints`

See [Conventional Commits](https://www.conventionalcommits.org/) for full specification.

### Required Labels

Every PR must have these labels applied:

- **Type**: One `type:*` label (feat, fix, breaking, docs, chore, ci, test, refactor, perf)
- **Priority**: One `priority:*` label (critical, high, medium, low)
- **Size**: One `size:*` label (xs, s, m, l, xl)

See [LABELS.md](LABELS.md) for complete label definitions.

### Issue Linking

**Always link all related issues** in your PR description:

- Use `Closes #123` for issues this PR fully resolves
- Use `Related to #123` for connected issues
- Use `Partially addresses #123` when incomplete (create child issues/tasks for remaining work)

### Before You Start

- Check if there's already an issue or PR for what you're planning
- For big changes, maybe open an issue first to discuss (or don't, I'm not your boss)

### Code Style

This repo has markdown linting via `markdownlint-cli2`. The pre-commit hooks will catch most issues, but if you want to check locally:

```bash
markdownlint-cli2 "**/*.md"
```

Follow the existing patterns in `agentsmd/`. If you're not sure about something, just make your best guess. I can always tweak it during review.

### Commit Messages

**Conventional commits are required**. Format your commit messages as:

- `feat(scope): description` for new features
- `fix(scope): description` for bug fixes
- `docs(scope): description` for documentation changes
- `refactor(scope): description` for code changes that don't add features or fix bugs
- Other types: `chore`, `ci`, `test`, `perf`, etc.

Your PR title must also follow this format (see "PR Title Format" section above).

See [Conventional Commits](https://www.conventionalcommits.org/) for full specification.

### Pre-Submission Checklist

Before submitting your PR:

- [ ] PR title follows conventional commits format: `type(scope): description`
- [ ] Related issues are linked in the description
- [ ] Type, priority, and size labels are applied
- [ ] Commits follow conventional commits specification
- [ ] All commits are GPG signed
- [ ] No merge commits (rebase if needed)
- [ ] Markdown linting passes
- [ ] PR is focused on a single concern
- [ ] Self-review completed

## What Gets Accepted

Pretty much anything that:

- Improves the documentation
- Adds useful AI assistant workflows
- Fixes bugs or typos
- Makes the codebase more maintainable

I'll probably accept most reasonable PRs. This is a documentation repo, not a nuclear reactor.

## What Might Not Get Accepted

- Breaking changes without discussion
- Vendor-specific instructions that don't fit the multi-AI philosophy
- Changes that make the repo significantly more complex without clear benefit

## Development Setup

1. Clone the repo
2. Install pre-commit: `pip install pre-commit && pre-commit install`
3. Make changes
4. Commit and push

That's the whole setup. No build system, no dependencies to install, no configuration files to create.

## Questions?

Open an issue. I'll respond when I can.

---

*Thanks for reading this far. Most people don't.*
