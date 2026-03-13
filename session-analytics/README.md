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

Set these environment variables (recommended: Doppler):

- `SPLUNK_NETWORK` — JSON array with Splunk IP (e.g., `["192.168.0.200"]`)
- `SPLUNK_USERNAME` — Splunk admin username
- `SPLUNK_PASSWORD` — Splunk admin password

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
