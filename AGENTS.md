# Claude Code Plugins Quick Reference

Reference guide for AI assistants working with this repository.

## Repository Purpose

This is a **Claude Code plugins repository** containing production-ready hooks for development workflows.

## Available Plugins

| Plugin | Type | Tools/Commands | Purpose |
|--------|------|--------|---------|
| **git-permission-guard** | PreToolUse | Bash | Blocks dangerous git/gh commands |
| **git-workflows** | Command/Skill | `/rebase-pr`, `/sync-main`, `/refresh-repo` | Git sync, refresh, and PR merge workflows |
| **github-workflows** | Command/Skill | `/finalize-pr`, `/squash-merge-pr`, `/resolve-pr-threads`, `/shape-issues` | GitHub PR/issue management workflows |
| **content-guards** | Pre/PostToolUse | Bash, Write, Edit | Token limits, markdown/README validation, webfetch guard, issue/PR rate limiting |
| **main-branch-guard** | PreToolUse | Edit, Write, NotebookEdit | Blocks file edits on main branch |
| **pr-review-toolkit** | Skill | `/resolve-pr-threads` | Resolve PR review threads via GraphQL (read, reply, resolve) |

## Multi-Model Delegation

<!-- cspell:words Ollama -->

Use `/delegate-to-ai` to route tasks to external AI models (Gemini, local Ollama, etc.) via PAL MCP.
Useful for research, code review consensus, and multi-model validation. See the `ai-delegation` plugin.
