---
name: token-breakdown
description: Analyze current Claude Code session token usage via Splunk. Shows per-model, per-tool, and subagent token breakdown with cache efficiency metrics.
metadata:
  version: "1.0.0"
  author: JacobPEvans
---

# Token Breakdown

Query Splunk for detailed token usage analytics of the current Claude Code session.

## Prerequisites

The Splunk MCP server must be configured in Claude Code. This is managed by nix-darwin:

- `splunk` MCP server defined in `programs.claude.mcpServers`
- Credentials injected via Doppler (`SPLUNK_MCP_ENDPOINT`, `SPLUNK_MCP_TOKEN`)
- Self-signed TLS handled by `NODE_TLS_REJECT_UNAUTHORIZED=0` in the MCP server env

Verify: `mcp__splunk__splunk_get_info` should return the Splunk version.

## Invocation

```text
/token-breakdown [session-id]
```

- No arguments: analyzes the current active session
- With session-id: analyzes a specific session UUID

## Workflow

### Phase 1: Session Identification

Determine the current session ID and validate it has a useful name.

**Step 1a — Find session ID:**

If no session-id argument was provided, find the current session:

```bash
# Compute encoded project path (slashes become hyphens)
encoded_path=$(echo "$PWD" | sed 's|^/|-|; s|/|-|g')

# Find the most recently modified JSONL session file
session_file=$(ls -t "$HOME/.claude/projects/${encoded_path}/"*.jsonl 2>/dev/null | head -1)

# Validate a session file was found
if [ -z "$session_file" ]; then
  echo "No active session found for current project directory: $PWD"
  exit 1
fi

# Extract session ID from filename
session_id=$(basename "$session_file" .jsonl)
```

**Step 1b — Read session metadata:**

Read line 1 of the session file to extract the slug and version:

```bash
head -1 "$session_file"
```

Extract `slug`, `version`, and `sessionId` from the JSON.

**Step 1c — Check session name quality:**

If the `slug` matches the auto-generated pattern (three hyphenated words like `glistening-gliding-cook`):

- Tell the user: "This session has an auto-generated name: `{slug}`."
- Suggest: "For better Splunk searchability, run `/rename` to give it a descriptive name."
- **Do NOT block** — continue with the analysis regardless
- Note the suggestion in the output header

### Phase 2: Execute Splunk Queries

Run **all four queries in parallel** using the Splunk MCP server tools.

**MCP tool call pattern:**

Each query uses `mcp__splunk__splunk_run_query` with the SPL query text and time range:

```text
mcp__splunk__splunk_run_query({
  "search_query": "<SPL query>",
  "earliest_time": "-7d",
  "latest_time": "now"
})
```

The MCP server handles authentication, TLS, and connection management.
Results are returned as structured JSON — no manual parsing of newline-delimited export format needed.

#### Query 2a: Session Overview by Model

```spl
search index=claude sourcetype="claude:code:session" sessionId="{session_id}" type="assistant"
| spath path=message.usage.input_tokens output=input_tokens
| spath path=message.usage.output_tokens output=output_tokens
| spath path=message.usage.cache_read_input_tokens output=cache_read
| spath path=message.usage.cache_creation_input_tokens output=cache_creation
| spath path=message.model output=model
| stats
    sum(input_tokens) as input,
    sum(output_tokens) as output,
    sum(cache_read) as cache_read,
    sum(cache_creation) as cache_write,
    count as api_calls
    by model
| eval total=input+output+cache_read+cache_write
| eval cache_pct=if((cache_read+input)>0, round(cache_read/(cache_read+input)*100, 1), 0.0)
| sort -total
| addcoltotals labelfield=model label="TOTAL"
```

#### Query 2b: Token Usage by Tool

```spl
search index=claude sourcetype="claude:code:session" sessionId="{session_id}" type="assistant"
| spath path=message.content{} output=content_items
| spath path=message.usage.output_tokens output=output_tokens
| eval tool_count=mvcount(mvfilter(match(content_items, "\"type\":\s*\"tool_use\"")))
| eval output_per_call=if(tool_count>0, output_tokens/tool_count, 0)
| mvexpand content_items
| spath input=content_items path=type output=content_type
| spath input=content_items path=name output=tool_name
| where content_type="tool_use"
| stats count as calls, sum(output_per_call) as output_tokens by tool_name
| sort -calls
```

#### Query 2c: Subagent Token Usage

```spl
search index=claude sourcetype="claude:code:subagent" sessionId="{session_id}" type="assistant"
| spath path=message.usage.input_tokens output=input_tokens
| spath path=message.usage.output_tokens output=output_tokens
| spath path=message.model output=model
| spath path=slug output=agent_slug
| stats
    sum(input_tokens) as input,
    sum(output_tokens) as output,
    count as api_calls
    by model, agent_slug
| eval total=input+output
| sort -total
```

#### Query 2d: Token Burn Rate (Timeline)

```spl
search index=claude sourcetype="claude:code:session" sessionId="{session_id}" type="assistant"
| spath path=message.usage.input_tokens output=input_tokens
| spath path=message.usage.output_tokens output=output_tokens
| spath path=message.model output=model
| eval total=input_tokens+output_tokens
| bin _time span=5m
| stats sum(total) as tokens by _time, model
| sort _time
```

### Phase 3: Parse and Display Results

The MCP tool returns results as structured JSON directly — no newline-delimited parsing needed.
Extract the result rows from each query response and display as formatted markdown tables:

#### Output Format

```markdown
## Session Token Breakdown

**Session:** {slug} (`{session_id}`)
**Period:** {first_timestamp} → {last_timestamp}
**Claude Code:** v{version}

### Model Usage

| Model | Input | Output | Cache Read | Cache Write | Total | Cache % | API Calls |
|-------|------:|-------:|-----------:|------------:|------:|--------:|----------:|
| {model} | {n} | {n} | {n} | {n} | {n} | {pct}% | {n} |
| **TOTAL** | ... | ... | ... | ... | ... | ... | ... |

### Tool Usage (by call frequency)

| Tool | Calls | Output Tokens |
|------|------:|--------------:|
| {tool} | {n} | {n} |

### Subagent Usage

| Agent | Model | Input | Output | Total | API Calls |
|-------|-------|------:|-------:|------:|----------:|
| {slug} | {model} | {n} | {n} | {n} | {n} |

### Token Burn Rate (5-min buckets)

| Time | Model | Tokens |
|------|-------|-------:|
| {time} | {model} | {n} |
```

Format all token counts with thousand separators for readability (e.g., `37,064`).

### Phase 4: Efficiency Analysis

After displaying raw data, provide a brief analysis:

- **Cache efficiency:** If cache_pct < 50%, flag as "Low cache hit rate — context may be churning"
- **Heavy tools:** If any single tool accounts for >40% of output tokens, flag it
- **Subagent cost:** If subagent tokens exceed 30% of main session tokens, flag it
- **Burn rate spikes:** Note any 5-min buckets with >2x the average

Keep analysis to 3-5 bullet points max. Data speaks for itself.

## Error Handling

| Error | Resolution |
|-------|------------|
| MCP tool not available | "Splunk MCP server not configured. Check nix-darwin mcpServers." |
| Auth failure | "Splunk MCP auth failed. Check SPLUNK_MCP_TOKEN in Doppler." |
| Connection refused | "Cannot reach Splunk. Check VPN/network." |
| No results | "No telemetry for session {id}. Data may not have been ingested yet." |
| Subagent query empty | Skip subagent section — not all sessions use subagents |

## Notes

- All aggregation happens server-side in Splunk — Claude only receives summary rows
- Session data lands in Splunk via: Claude Code → OTEL Collector → Cribl Stream → Splunk HEC
- There may be a ~60s ingestion delay between Claude Code activity and Splunk availability
- Token counts come from the Anthropic API response `usage` object — they are exact, not estimates
- The Splunk MCP Server App has a 1-minute query timeout and 1000-event max per query
- Our queries use `stats` aggregation so results are small summary rows — well within limits

## Related Skills

This is a standalone analytics skill. It is useful alongside any development workflow skill that involves active Claude Code sessions.
