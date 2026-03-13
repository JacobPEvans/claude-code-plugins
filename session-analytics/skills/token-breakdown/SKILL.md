---
name: token-breakdown
description: Analyze current Claude Code session token usage via Splunk. Shows per-model, per-tool, and subagent token breakdown with cache efficiency metrics.
version: "1.0.0"
author: JacobPEvans
---

# Token Breakdown

Query Splunk for detailed token usage analytics of the current Claude Code session.

## Prerequisites

Three environment variables must be set (recommended: Doppler):

- `SPLUNK_NETWORK` — JSON array containing the Splunk IP (e.g., `["192.168.0.200"]`)
- `SPLUNK_USERNAME` — Splunk admin username
- `SPLUNK_PASSWORD` — Splunk admin password

The Splunk REST API URL is derived as `https://{first_ip_from_SPLUNK_NETWORK}:8089`.

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

### Phase 2: Validate Environment and Derive Splunk URL

Check that all three env vars are set and derive the REST API URL:

```bash
echo "${SPLUNK_NETWORK:?SPLUNK_NETWORK not set}" > /dev/null
echo "${SPLUNK_USERNAME:?SPLUNK_USERNAME not set}" > /dev/null
echo "${SPLUNK_PASSWORD:?SPLUNK_PASSWORD not set}" > /dev/null

# Extract first IP from JSON array and validate
SPLUNK_IP=$(echo "$SPLUNK_NETWORK" | jq -r '.[0]')
if [ -z "$SPLUNK_IP" ] || [ "$SPLUNK_IP" = "null" ]; then
  echo "SPLUNK_NETWORK does not contain a valid IP. Expected JSON array, e.g. [\"192.168.0.200\"]"
  exit 1
fi
SPLUNK_URL="https://${SPLUNK_IP}:8089"
```

If any env var is missing, stop with:
"Set SPLUNK_NETWORK, SPLUNK_USERNAME, and SPLUNK_PASSWORD (via Doppler or env vars)."

### Phase 3: Execute Splunk Queries

Run **all four queries in parallel** via the Bash tool. Each query uses the Splunk REST API one-shot export endpoint.

**Query template:**

```bash
# Pass credentials via stdin to avoid exposure in process list
curl -sk --fail-with-body --config - \
  "$SPLUNK_URL/services/search/jobs/export" \
  --data-urlencode 'search=<SPL_QUERY>' \
  -d output_mode=json \
  -d earliest_time='-7d' \
  -d latest_time='now' <<CURL_CFG
user = "$SPLUNK_USERNAME:$SPLUNK_PASSWORD"
CURL_CFG
```

- `-sk` — silent + insecure TLS for self-signed certs
- `--fail-with-body` — returns non-zero on HTTP errors (401, 500) while capturing the response body
- `--config -` — passes credentials via stdin to avoid exposure in the process list

#### Query 3a: Session Overview by Model

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

#### Query 3b: Token Usage by Tool

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

#### Query 3c: Subagent Token Usage

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

#### Query 3d: Token Burn Rate (Timeline)

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

### Phase 4: Parse and Display Results

Parse the JSON output from each query. Splunk export returns newline-delimited JSON objects with a `result` key.

**Important:**

- Parse each line as JSON
- Only process objects that contain a `"result"` key
- Discard objects where `"preview"` is `true` — those are intermediate results before search finalizes

Display the results as formatted markdown tables:

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

### Phase 5: Efficiency Analysis

After displaying raw data, provide a brief analysis:

- **Cache efficiency:** If cache_pct < 50%, flag as "Low cache hit rate — context may be churning"
- **Heavy tools:** If any single tool accounts for >40% of output tokens, flag it
- **Subagent cost:** If subagent tokens exceed 30% of main session tokens, flag it
- **Burn rate spikes:** Note any 5-min buckets with >2x the average

Keep analysis to 3-5 bullet points max. Data speaks for itself.

## Error Handling

| Error | Resolution |
|-------|------------|
| No session file found | "No active session found for current project directory" |
| Splunk connection refused | "Cannot reach Splunk at {SPLUNK_URL}. Check VPN/network and SPLUNK_NETWORK." |
| Auth failure (401) | "Splunk auth failed. Check SPLUNK_USERNAME and SPLUNK_PASSWORD." |
| No results returned | "No telemetry data found for session {id}. Data may not have been ingested yet (check OTEL collector)." |
| Subagent query empty | Skip subagent section — not all sessions use subagents |

## Notes

- All aggregation happens server-side in Splunk — Claude only receives summary rows
- Self-signed TLS is expected (`-k` flag); the Splunk instance uses internal certs
- Session data lands in Splunk via: Claude Code → OTEL Collector → Cribl Stream → Splunk HEC
- There may be a ~60s ingestion delay between Claude Code activity and Splunk availability
- Token counts come from the Anthropic API response `usage` object — they are exact, not estimates
