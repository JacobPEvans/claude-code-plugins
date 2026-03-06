# Claude Code Plugins Quick Reference

Reference guide for AI assistants working with this repository.

## Repository Purpose

This is a **Claude Code plugins repository** containing production-ready hooks for development workflows.

## Available Plugins

| Plugin | Type | Tools/Commands | Purpose |
|--------|------|--------|------|
| **git-guards** | PreToolUse | Bash, Edit, Write, NotebookEdit | Blocks dangerous git/gh commands and file edits on main branch |
| **git-workflows** | Command/Skill | `/rebase-pr`, `/sync-main`, `/refresh-repo`, `/troubleshoot-rebase`, `/troubleshoot-precommit`, `/troubleshoot-worktree` | Git sync, refresh, and PR merge workflows |
| **github-workflows** | Command/Skill | `/finalize-pr`, `/squash-merge-pr`, `/resolve-pr-threads`, `/shape-issues`, `/trigger-ai-reviews` | GitHub PR/issue management workflows |
| **content-guards** | Pre/PostToolUse | Bash, Write, Edit | Token limits, markdown/README validation, webfetch guard, issue/PR rate limiting |

## Multi-Model Delegation

<!-- cspell:words Ollama -->

Use `/delegate-to-ai` to route tasks to external AI models (Gemini, local Ollama, etc.) via PAL MCP.
Useful for research, code review consensus, and multi-model validation. See the `ai-delegation` plugin.
