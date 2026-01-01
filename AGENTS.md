# AGENTS.md

Central config repo. Provides defaults for all JacobPEvans repos.

## Auto-Inherited Files

- `ISSUE_TEMPLATE/*.yml` → Issue forms
- `PULL_REQUEST_TEMPLATE/*.md` → PR forms
- `labels.yml` → Label definitions

## PR Templates

- Default (`pull_request_template.md`) → General/chore/ci/test
- `bug.md` → Bug fixes
- `feature.md` → New features
- `breaking.md` → Breaking changes
- `docs.md` → Documentation
- `refactor.md` → Code refactoring
- `performance.md` → Performance improvements

**Select template**: Add `?template=bug.md` to PR creation URL (default loads automatically)

## PR Title Format

Must follow [Conventional Commits](https://www.conventionalcommits.org/):

**Format**: `type(scope): brief description`

**Examples**:

- `feat(api): add user authentication`
- `fix(ui): resolve button alignment`
- `docs(readme): update installation`
- `feat!: remove deprecated v1 API` (breaking change)

## Labels (Required per issue and PR)

- `type:*` - One+ required: bug|feature|breaking|docs|chore|ci|test|refactor|perf
- `priority:*` - Exactly one: critical|high|medium|low
- `size:*` - Exactly one: xs|s|m|l|xl

## Workflow Labels

- `ai:created` alone → Needs human review
- `ai:created` + `ai:ready` → Approved for work
- `ready-for-dev` → Requirements clarified, ready to implement
- `good-first-issue` → Good for newcomers

## Sync Labels to Repo

```bash
gh label clone JacobPEvans/.github -R JacobPEvans/TARGET --force
```
