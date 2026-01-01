# .github

Default community health files, issue templates, and shared configurations for all JacobPEvans repositories.

## About This Repository

This is GitHub's special **`.github` repository**, which provides organization-wide default files for all public repositories.
Files stored here are automatically inherited by any repository that doesn't have its own version.

### How Inheritance Works

**Automatic Inheritance**: When someone views a community health file in a repository that doesn't have one, GitHub displays the version from this `.github` repository.
This happens in real-time.
No syncing is required.

**Search Order**: GitHub looks for files in this order within both the target repository and this `.github` repository:

1. The `.github/` folder
2. The repository root
3. The `docs/` folder

**One-Way Flow**: Files in this repository serve as fallbacks. Changes here don't overwrite or sync to repositories that already have their own versions.

**Override Behavior**: Any repository can override these defaults by creating its own version of a file.
For issue templates specifically, if a repository has ANY files in its own `.github/ISSUE_TEMPLATE/` folder, NONE of the defaults from this repository will be used.

**Public Requirement**: This repository **must be public** for inheritance to work organization-wide.
Private `.github` repositories only work for private repositories in the same organization.

**Learn More**:
[Creating a default community health file - GitHub Docs](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/creating-a-default-community-health-file)

### Supported Inheritable Files

According to [GitHub's documentation][supported-files], the following files can be inherited:

[supported-files]: https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/creating-a-default-community-health-file#supported-file-types

- `CODE_OF_CONDUCT.md`
- `CONTRIBUTING.md`
- Discussion category forms
- `FUNDING.yml`
- `GOVERNANCE.md`
- Issue and pull request templates
- `SECURITY.md`
- `SUPPORT.md`

**Note**: `LICENSE` files **cannot** be inherited and must be added to each repository individually.

## Repository Structure

### Root Files

| File         | Purpose                         | Inherited? | Documentation |
| ------------ | ------------------------------- | ---------- | ------------- |
| `README.md`  | This file                       | No         | -             |
| `LICENSE`    | MIT License for this repository | No         | -             |
| `AGENTS.md`  | Quick reference for AI agents   | No         | -             |

### `docs/`

Documentation files (inheritable by other repositories):

| File                   | Purpose                     | Inherited? | Documentation                      |
| ---------------------- | --------------------------- | ---------- | ---------------------------------- |
| `docs/CONTRIBUTING.md` | Contribution guidelines     | Yes        | [About CONTRIBUTING][contrib-docs] |
| `docs/LABELS.md`       | Label system documentation  | No         | -                                  |

[contrib-docs]: https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/setting-guidelines-for-repository-contributors

### `.github/`

| File                 | Purpose                     | Inherited? | Documentation                  |
| -------------------- | --------------------------- | ---------- | ------------------------------ |
| `.github/labels.yml` | Canonical label definitions | No         | [Managing labels][labels-docs] |

[labels-docs]: https://docs.github.com/en/issues/using-labels-and-milestones-to-track-work/managing-labels

#### `.github/ISSUE_TEMPLATE/`

Standardized [issue forms][issue-forms-docs] that enforce the label taxonomy and collect structured information:

| Template              | Description                               | Auto-Label     | File                  |
| --------------------- | ----------------------------------------- | -------------- | --------------------- |
| **Bug Report**        | Bug reports with reproduction steps       | `type:bug`     | `bug_report.yml`      |
| **Feature Request**   | Feature requests and enhancements         | `type:feature` | `feature_request.yml` |
| **Documentation**     | Documentation improvements                | `type:docs`    | `documentation.yml`   |
| **Chore/Maintenance** | Maintenance and tooling tasks             | `type:chore`   | `chore.yml`           |
| **Template Config**   | Disables blank issues, configures chooser | -              | `config.yml`          |

**All templates require**:

- Priority selection (`priority:critical/high/medium/low`)
- Size estimation (`size:xs/s/m/l/xl`)

**Learn More**:

- [About issue and pull request templates][issue-forms-docs]
- [Syntax for issue forms][issue-forms-syntax]

[issue-forms-docs]: https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/about-issue-and-pull-request-templates
[issue-forms-syntax]: https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms

#### `.github/PULL_REQUEST_TEMPLATE/`

Standardized [pull request templates][pr-templates-docs] that enforce conventional commits and collect structured information:

| Template              | Use Case                          | Type Label      | File                         |
| --------------------- | --------------------------------- | --------------- | ---------------------------- |
| **Default/General**   | Chores, CI, tests, other changes  | Multiple        | `pull_request_template.md`   |
| **Bug Fix**           | Bug fixes with root cause         | `type:bug`      | `bug.md`                     |
| **Feature**           | New features with design docs     | `type:feature`  | `feature.md`                 |
| **Breaking Change**   | Breaking changes with migration   | `type:breaking` | `breaking.md`                |
| **Documentation**     | Docs improvements                 | `type:docs`     | `docs.md`                    |
| **Refactoring**       | Code refactoring with impact      | `type:refactor` | `refactor.md`                |
| **Performance**       | Performance improvements          | `type:perf`     | `performance.md`             |

**All templates require**:

- Conventional commit format in PR title (`type(scope): description`)
- Related issue linking
- Type, priority, and size labels
- GPG-signed commits

**Selecting a template**:

- Default template loads automatically
- Use query parameter for specific template: `?template=bug.md`
- Templates align with [Conventional Commits][conventional-commits] specification

**Learn More**:

- [Creating a pull request template for your repository][pr-templates-docs]
- [Conventional Commits specification][conventional-commits]

[pr-templates-docs]: https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/creating-a-pull-request-template-for-your-repository
[conventional-commits]: https://www.conventionalcommits.org/

#### `.github/workflows/`

[GitHub Actions workflows][workflows-docs] that automate label management:

| Workflow                | Purpose                                                                  | Trigger        | Documentation                     |
| ----------------------- | ------------------------------------------------------------------------ | -------------- | --------------------------------- |
| `auto-label-issues.yml` | Automatically applies priority and size labels from issue form dropdowns | Issue creation | [Using workflows][workflows-docs] |

**How it works**: When an issue is created from a template, the workflow extracts the user's dropdown selections (priority and size).
It then applies the corresponding labels automatically.

[workflows-docs]: https://docs.github.com/en/actions/using-workflows/about-workflows

## Label System

All repositories use a consistent labeling taxonomy for issue classification and workflow management.

**See [LABELS.md](docs/LABELS.md) for complete documentation.**

### Quick Reference

- **Type labels** (`type:*`): bug, feature, breaking, docs, chore, ci, test, refactor, perf
- **Priority labels** (`priority:*`): critical, high, medium, low
- **Size labels** (`size:*`): xs, s, m, l, xl
- **AI workflow labels** (`ai:*`): created, ready
- **Triage labels**: duplicate, invalid, wontfix, question

**Learn More**: [Managing labels - GitHub Docs](https://docs.github.com/en/issues/using-labels-and-milestones-to-track-work/managing-labels)

## Using These Files in Your Repositories

### Option 1: Inherit (Recommended)

Simply don't create your own versions of community health files. GitHub will automatically display files from this `.github` repository as fallbacks.

**How to check**: Visit `https://github.com/JacobPEvans/YOUR_REPO/community` to see which files are inherited vs. defined in your repository.

**Pros**: Zero maintenance. Updates to this repository automatically apply to all repos without their own files.

**Cons**: Can't customize per-repository without losing inheritance completely.

### Option 2: Override

Create your own version of a file in your repository to override the default.

**Examples**:

- Add `CONTRIBUTING.md` to your repo root or `docs/` folder to replace the inherited version
- Add any file to `.github/ISSUE_TEMPLATE/` to disable ALL template inheritance

**Pros**: Full customization for specific repository needs.

**Cons**: Loses automatic updates from this `.github` repository.

### Option 3: Sync Labels

Labels are **not inherited** automatically. Use the [GitHub CLI](https://cli.github.com/) to sync them from `.github/labels.yml`:

```bash
# One-time sync from this repo to another
gh label clone JacobPEvans/.github -R JacobPEvans/YOUR_REPO --force
```

**Why `--force`?** Updates existing labels and creates new ones. Without it, the command fails if labels already exist.

**Learn More**: [GitHub CLI manual](https://cli.github.com/manual/)

## Contributing

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines on contributing to this repository.

---

**Related Documentation**:

- [About community profiles for public repositories](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/about-community-profiles-for-public-repositories)
- [Creating a default community health file](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/creating-a-default-community-health-file)
- [GitHub CLI documentation](https://cli.github.com/manual/)

**Maintained by**: Jacob P Evans
