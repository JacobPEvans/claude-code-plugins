---
name: delegate-to-ai
description: Route tasks to external AI models via PAL MCP tools
---

# Delegate to External AI

Routes tasks to specialized models based on task type and constraints using PAL MCP tools.

## When to Delegate

Delegate when Claude is not the best tool:

- **Large context** (1M+ tokens) -> Gemini 3 Pro via PAL `chat` tool
- **Math/reasoning** -> DeepSeek R1 via PAL `chat` tool
- **Private/offline** -> Local Ollama via PAL `chat` tool
- **Code review consensus** -> Multi-model via PAL `consensus` tool
- **Architecture planning** -> Claude Opus or Gemini via PAL `planner` tool

## PAL MCP Tools

- **`chat`** - Single model for straightforward tasks
- **`clink`** - Parallel queries across multiple models
- **`consensus`** - Multi-model agreement for critical decisions
- **`codereview`** - Structured code review with multiple perspectives
- **`planner`** - Architecture and design planning
- **`precommit`** - Quick validation before committing

## Workflow

1. **Identify task type** (research, coding, review, architecture, planning)
2. **Select PAL MCP tool** based on type and constraints
3. **Execute via Task tool** with appropriate agent subtype
4. **Synthesize results** if using multi-model tools

## Model Routing

| Task Type | Cloud Model | Local Model | PAL Tool |
| --- | --- | --- | --- |
| Research | Gemini 3 Pro | qwen3-next:80b | `chat`, `clink` |
| Complex Coding | Claude Opus | qwen3-coder:30b | `codereview` |
| Fast Tasks | Claude Sonnet | qwen3-next:latest | `chat` |
| Code Review | Multi-model | deepseek-r1:70b | `consensus` |
| Architecture | Claude Opus | qwen3-next:80b | `planner` |

## Local-Only Mode

When `localOnlyMode` is enabled or `--local` flag is passed, all tasks route to Ollama models.
No cloud API calls are made.
