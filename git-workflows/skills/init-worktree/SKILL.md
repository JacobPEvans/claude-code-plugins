---
name: init-worktree
description: Initialize a clean worktree for new development work
---

# Init Worktree

**CRITICAL**: All development work MUST be done in a clean worktree. This skill ensures isolation between concurrent sessions
and prevents accidental changes on main.

Initialize a clean worktree in `~/git/<repo-name>/<branch-name>/` for new development work.

## Usage

```text
/init-worktree [description]
```

**Parameters:**

- `description` (optional): Brief description for branch/worktree naming (e.g., "fix login bug", "add dark mode")

If no description provided, will prompt for one.

## Steps

### 1. Validate

Verify git repo: `git rev-parse --is-inside-work-tree`. Get repo name: `basename $(git rev-parse --show-toplevel)`.

### 2. Remember State

Note current branch and directory for reporting.

### 3. Clean Stale Worktrees

Identify stale worktrees (merged/deleted/gone branches). Remove using `git worktree remove` + `git branch -d`. Run `git worktree prune`.

Detection criteria:

- **Branch merged**: `git branch --merged main | grep "^  $BRANCH$"`
- **Remote deleted**: `git branch -vv | grep "\[gone\]"`

### 4. Switch to Main and Sync

```bash
cd ~/git/<repo>/main && git switch main
git fetch --all --prune
git pull
```

### 5. Generate Branch and Worktree Names

Apply conventional branch naming:

- **Format**: `<type>/<description>` (e.g., `feat/add-dark-mode`, `fix/login-bug`)
- **Rules**: lowercase, hyphens separate words, alphanumeric + hyphens only

### 6. Create Worktree

```bash
git worktree add ~/git/<repo-name>/<branch-name> -b <branch-name> main
```

### 7. Symlink .docs/ (if exists)

If `.docs/` exists at repo root, symlink it into the worktree for project-specific documentation access.

### 8. Verify and Report

Switch to worktree, verify with `git status`. Report: previous branch, worktrees cleaned, new location, and whether `.docs/` was symlinked.
