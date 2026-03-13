# session-analytics

Claude Code session token analytics via Splunk OTEL telemetry.

## Skills

- **`/token-breakdown`** — Analyze token usage for the current session
  - Per-model breakdown (input, output, cache read, cache write)
  - Per-tool call frequency and output token cost
  - Subagent token usage
  - Token burn rate timeline (5-min buckets)
  - Cache efficiency analysis

## Prerequisites

Splunk MCP server configured in Claude Code (managed by nix-darwin):

- `splunk` entry in `programs.claude.mcpServers`
- Doppler secrets: `SPLUNK_MCP_ENDPOINT`, `SPLUNK_MCP_TOKEN`

## Data Pipeline

```text
Claude Code → OTEL Collector → Cribl Stream → Splunk HEC → index=claude
```

All aggregation happens server-side in Splunk via SPL queries.
Claude only receives summary rows.

## Installation

```bash
claude plugins add jacobpevans-cc-plugins/session-analytics
```

## License

Apache-2.0
