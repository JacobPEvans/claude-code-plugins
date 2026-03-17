# Worktree Conventions

When creating git worktrees, follow these project-specific conventions instead of
default `.worktrees/` placement.

## Path Convention

```text
~/git/{repo-name}/{branch-name}/
```

Examples:

- `~/git/claude-code-plugins/feat/add-readme-validation/`
- `~/git/terraform-proxmox/fix/firewall-rules/`

## Branch Naming

- Format: `{type}/{description}` (e.g., `feat/add-dark-mode`, `fix/login-bug`)
- Types: `feat`, `fix`, `chore`, `refactor`, `docs`, `ci`, `test`, `perf`
- Rules: lowercase, hyphens between words, alphanumeric + hyphens only

## Before Creating

1. Switch to main and sync: `cd ~/git/{repo-name}/main && git switch main && git pull`
2. Clean stale worktrees (merged PRs or `[gone]` remote branches):
   - `gh pr list --state merged --head <branch>` to confirm PR was merged
   - `git branch -vv | grep '\[gone\]'` to find deleted remote branches
   - `git worktree remove {path}` (never `--force`) + `git branch -d {branch}`
   - `git worktree prune` to clean up

## After Creating

- If `.docs/` exists at repo root, symlink it into the worktree
- Run `direnv allow` if the repo uses direnv

## Reference

Use `superpowers:using-git-worktrees` for worktree creation, guided by these conventions.
