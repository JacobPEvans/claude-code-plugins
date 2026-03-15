# Claude Code Plugins Quick Reference

Reference guide for AI assistants working with this repository.

## Repository Purpose

This is a **Claude Code plugins repository** containing production-ready hooks for development workflows.

## Available Plugins

| Plugin | Type | Tools/Commands | Purpose |
|--------|------|--------|------|
| **ai-delegation** | Skill | `/delegate-to-ai`, `/auto-maintain` | Route tasks to external AI models (Gemini, Ollama, etc.) via PAL MCP |
| **codeql-resolver** | Command/Skill/Agent | `/resolve-codeql` | Resolve CodeQL security alerts in GitHub Actions workflows |
| **config-management** | Skill | `/sync-permissions`, `/quick-add-permission` | Manage Claude and Gemini permission configs across repositories |
| **content-guards** | Pre/PostToolUse | Bash, Write, Edit | Token limits, markdown/README validation, webfetch guard, issue/PR rate limiting, branch limits |
| **git-guards** | PreToolUse | Bash, Edit, Write, NotebookEdit | Blocks dangerous git/gh commands and file edits on main branch |
| **git-workflows** | Command/Skill | `/rebase-pr`, `/sync-main`, `/refresh-repo`, `/troubleshoot-rebase`, `/troubleshoot-precommit`, `/troubleshoot-worktree` | Git sync, refresh, and PR merge workflows |
| **github-workflows** | Command/Skill | `/finalize-pr`, `/squash-merge-pr`, `/resolve-pr-threads`, `/shape-issues`, `/trigger-ai-reviews` | GitHub PR/issue management workflows |
| **infra-orchestration** | Skill | `/orchestrate-infra`, `/sync-inventory`, `/test-e2e` | Cross-repo infrastructure orchestration for Terraform and Ansible |
| **pr-lifecycle** | PostToolUse | Bash | Automatically triggers `/finalize-pr` after `gh pr create` succeeds |
| **process-cleanup** | PostToolUse | — | Cleanup orphaned MCP server processes on session exit |
| **session-analytics** | Skill | `/token-breakdown` | Session token analytics via Splunk OTEL telemetry |

## Multi-Model Delegation

<!-- cspell:words Ollama -->

Use `/delegate-to-ai` to route tasks to external AI models (Gemini, local Ollama, etc.) via PAL MCP.
Useful for research, code review consensus, and multi-model validation. See the `ai-delegation` plugin.
