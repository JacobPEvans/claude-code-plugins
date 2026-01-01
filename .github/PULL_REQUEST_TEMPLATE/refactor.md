# Refactoring Pull Request

<!-- PR Title Format: refactor(scope): brief description -->
<!-- Example: refactor(auth): extract validation logic to separate module -->

## Refactoring Goals

<!-- What is being refactored and why? -->

## Motivation

<!-- Why is this refactoring necessary? What problem does it solve? -->

## Changes Made

### Before

<!-- Describe the old structure/approach -->

### After

<!-- Describe the new structure/approach -->

## Impact Assessment

- **Functionality**: [ ] No behavior changes / [ ] Behavior changes (explain below)
- **Performance**: [ ] No impact / [ ] Improved / [ ] Degraded (explain)
- **API**: [ ] No API changes / [ ] API changes (document below)

### Detailed Impact (if any)

<!-- Describe any changes above in detail -->

## Related Issues

<!-- Link related issues if any -->

- [ ] I have found and linked all related issues (if any)
  - Closes #
  - Related to #

## Testing

<!-- Describe the testing performed -->

- [ ] All existing tests still pass
- [ ] No new tests needed (pure refactor)
- [ ] Tests updated to match new structure (if needed)
- [ ] Manual testing completed

## Code Quality Metrics

<!-- If applicable: cyclomatic complexity, code duplication, test coverage changes -->

## Documentation

<!-- Describe any documentation changes -->

- [ ] Code comments updated for complex logic
- [ ] CHANGELOG updated (if user-facing)

## Labels

**Apply these labels before submitting:**

- [ ] **Type**: `type:refactor`
- [ ] **Priority**: `priority:___` (critical, high, medium, low)
- [ ] **Size**: `size:___` (xs, s, m, l, xl)

See [LABELS.md](../docs/LABELS.md) for label definitions.

## Checklist

<!-- Please confirm the following before submitting your pull request -->

- [ ] PR title follows conventional commits format: `refactor(scope): description`
- [ ] Commits follow conventional commits specification
- [ ] All commits are GPG signed
- [ ] No merge commits (rebased if needed)
- [ ] No functional changes (or clearly documented)
- [ ] All tests passing
- [ ] Self-review completed
- [ ] Labels applied (type:refactor, priority:*, size:*)

## Additional Context

<!-- Design patterns used, architectural decisions, alternative approaches considered, etc. -->
