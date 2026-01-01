# Performance Improvement Pull Request

<!-- PR Title Format: perf(scope): brief description -->
<!-- Example: perf(queries): add database indexes for user lookup -->

## Performance Issue

<!-- What performance problem does this PR address? -->

## Solution

<!-- How does this PR improve performance? What's the approach? -->

## Benchmarks

### Before

```text
<!-- Benchmark results before optimization -->
```

### After

```text
<!-- Benchmark results after optimization -->
```

### Improvement

- **Metric**: ___% improvement
- **Impact**: [ ] User-facing / [ ] Backend only

## Related Issues

<!-- Link related issues if any -->

- [ ] I have found and linked all related issues (if any)
  - Closes #
  - Related to #

## Changes Made

<!-- List the specific changes in this PR -->

-
-
-

## Testing

<!-- Describe the testing performed -->

- [ ] Performance tests added/updated
- [ ] Benchmarks documented
- [ ] All tests passing
- [ ] No regression in other areas

## Trade-offs

<!-- Any trade-offs made? Memory vs speed, readability vs performance, complexity vs efficiency, etc. -->

## Documentation

<!-- Describe any documentation changes -->

- [ ] Performance characteristics documented
- [ ] Code comments explain optimizations
- [ ] CHANGELOG updated

## Labels

**Apply these labels before submitting:**

- [ ] **Type**: `type:perf`
- [ ] **Priority**: `priority:___` (critical, high, medium, low)
- [ ] **Size**: `size:___` (xs, s, m, l, xl)

See [LABELS.md](../docs/LABELS.md) for label definitions.

## Checklist

<!-- Please confirm the following before submitting your pull request -->

- [ ] PR title follows conventional commits format: `perf(scope): description`
- [ ] Commits follow conventional commits specification
- [ ] All commits are GPG signed
- [ ] No merge commits (rebased if needed)
- [ ] Benchmarks prove improvement
- [ ] All tests passing
- [ ] Self-review completed
- [ ] Labels applied (type:perf, priority:*, size:*)

## Additional Context

<!-- Profiling results, flame graphs, alternative approaches considered, scalability analysis, etc. -->
