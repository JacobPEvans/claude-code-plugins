---
name: delegate-to-ai
description: Route tasks to external AI models via Bifrost and PAL MCP multi-model tools
---

# Delegate to External AI

Routes tasks to specialized models based on task type using Bifrost (single-model) or PAL MCP (multi-model).

## When to Delegate

Delegate when Claude is not the best tool:

- **Large context** (1M+ tokens) -> Gemini 3 Pro via Bifrost
- **Math/reasoning** -> DeepSeek R1 via Bifrost
- **Private/offline** -> Local MLX via Bifrost (port 30080 routes to local MLX server)
- **Code review consensus** -> Multi-model via PAL `consensus`
- **Parallel multi-model research** -> PAL `clink` (when you need multiple model perspectives simultaneously)
- **Architecture planning** -> Claude Opus native subagent (Plan mode or `Plan` subagent type)

## Route Selection

| Task Type | Cloud Model | Local Model | Route |
| --- | --- | --- | --- |
| Research (single) | Gemini 3 Pro | mlx-community/Qwen3-235B-A22B-4bit | Bifrost |
| Research (multi) | Multiple | mlx-community/Qwen3-235B-A22B-4bit¹ | PAL clink |
| Complex Coding | Claude Opus | mlx-community/Qwen3.5-122B-A10B-4bit | native subagent |
| Fast Tasks | Claude Sonnet | mlx-community/Qwen3.5-27B-4bit | Bifrost |
| Code Review | Multi-model | mlx-community/Qwen3.5-27B-4bit | PAL consensus |
| Architecture | Claude Opus | mlx-community/Qwen3-235B-A22B-4bit | native subagent |

**Bifrost endpoint**: `http://localhost:30080/v1/chat/completions` (OpenAI-compatible)

¹ In local-only mode, `PAL clink` (multi-model) falls back to this single best local model.

## PAL MCP Tools (multi-model only)

- **`clink`** - Parallel queries across multiple models
- **`consensus`** - Multi-model agreement for critical decisions

All other PAL tools have native Claude Code equivalents — use Bifrost or native subagents instead.

## Workflow

1. **Identify task type** (research, coding, review, architecture)
2. **Select route**: Bifrost for single-model, PAL for multi-model, native subagent for implementation work
3. **Execute**: Bifrost via `curl`/Bash; PAL via MCP tool call; native subagent via Agent tool
4. **Synthesize results** if using multi-model tools

## Local-Only Mode

When `localOnlyMode` is enabled or `--local` flag is passed, route all tasks through
Bifrost to the local MLX inference server (overrides native subagent rows). No cloud API calls are made.

## Related Skills

- auto-maintain (ai-delegation)
