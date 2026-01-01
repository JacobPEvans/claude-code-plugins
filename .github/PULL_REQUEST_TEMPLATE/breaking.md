# Breaking Change Pull Request

⚠️ **WARNING: This PR contains breaking changes** ⚠️

<!-- PR Title Format: feat!: brief description OR breaking(scope): description -->
<!-- Example: feat!: remove deprecated v1 API endpoints -->

## Breaking Changes Summary

<!-- What will break for existing users? Describe each breaking change clearly. -->

## Migration Path

<!-- How should users migrate their code to accommodate these changes? -->

### Example Migration

```diff
// Before
- oldFunction()

// After
+ newFunction()
```

## Rationale

<!-- Why is this breaking change necessary? -->

## Related Issues

<!-- CRITICAL: Link issues discussing this breaking change -->

- [ ] I have found and linked all related issues
  - Closes #
  - Related to #

## Changes Made

<!-- List the specific changes in this PR -->

-
-
-

## Deprecation Timeline

<!-- If there was a deprecation period before this breaking change -->

- [ ] Deprecation warnings added in previous version
- [ ] Migration guide provided
- [ ] Release notes prepared

## Testing

<!-- Describe the testing performed -->

- [ ] Tests updated for new behavior
- [ ] Migration path tested
- [ ] All tests passing
- [ ] Backward compatibility tests removed

## Documentation

<!-- Describe all documentation changes -->

- [ ] CHANGELOG updated with BREAKING CHANGE notice
- [ ] Migration guide written
- [ ] API documentation updated
- [ ] README updated
- [ ] Examples updated

## Version Impact

- **Semantic Version**: MAJOR version bump required
- **Minimum Affected Version**: Describe which versions are affected
- **Support Status**: Will old versions be supported? For how long?

## Labels

**Apply these labels before submitting:**

- [ ] **Type**: `type:breaking`
- [ ] **Priority**: `priority:___` (critical, high, medium, low)
- [ ] **Size**: `size:___` (xs, s, m, l, xl)

See [LABELS.md](../docs/LABELS.md) for label definitions.

## Checklist

<!-- Please confirm the following before submitting your pull request -->

- [ ] PR title follows conventional commits format: `feat!: description` or `breaking(scope): description`
- [ ] Commit body includes "BREAKING CHANGE:" section (if using feat! format)
- [ ] All commits are GPG signed
- [ ] No merge commits (rebased if needed)
- [ ] Migration path is clear and documented
- [ ] All tests passing
- [ ] Self-review completed
- [ ] Labels applied (type:breaking, priority:*, size:*)
- [ ] Release notes drafted

## Additional Context

<!-- Alternative approaches considered, discussion threads, upgrade impact analysis, etc. -->
