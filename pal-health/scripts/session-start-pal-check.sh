#!/usr/bin/env bash
# Fast, non-blocking check for recent PAL MCP failures (no network calls).
# Runs on SessionStart to warn the user before they discover missing tools.
set -euo pipefail

LOG="${XDG_STATE_HOME:-$HOME/.local/state}/doppler-mcp.log"

if [ -f "$LOG" ]; then
  last_line=$(tail -1 "$LOG" 2>/dev/null || true)
  if echo "$last_line" | grep -q "preflight failed"; then
    cat <<'WARN' >&2
WARNING: PAL MCP had a recent Doppler auth failure.
  Run: doppler login && check-pal-mcp
  Then restart Claude Code.
WARN
  fi
fi

exit 0
