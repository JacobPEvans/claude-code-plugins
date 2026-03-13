#!/usr/bin/env bash
# Stop hook: kill orphaned MCP server processes (ppid=1 = reparented to launchd)
#
# SAFETY: Only kills processes with ppid=1. Cannot affect active Claude sessions.

set -euo pipefail

LOG_DIR="$HOME/Library/Logs/claude-process-cleanup"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/cleanup-$(date +%Y-%m-%d).log"

log() { printf '%s [%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1" "${*:2}" >> "$LOG_FILE"; }

# Single pass: find all orphaned MCP processes (single ps call = no duplicates possible)
all_pids=()
while IFS= read -r pid; do
  [[ -n "$pid" ]] && all_pids+=("$pid")
done < <(
  ps -Aeo pid,ppid,command \
    | awk '$2 == 1 && ($3 ~ /terraform-mcp|context7-mcp/ || ($3 ~ /node/ && $0 ~ /mcp|context7/)) {print $1}'
)

[[ ${#all_pids[@]} -eq 0 ]] && exit 0

for pid in "${all_pids[@]}"; do
  log INFO "Sending SIGTERM to orphaned MCP process (pid=${pid})"
  kill -TERM "$pid" 2>/dev/null || true
done

sleep 2

# SIGKILL survivors — re-validate PID identity before escalating (guards against PID reuse)
for pid in "${all_pids[@]}"; do
  if kill -0 "$pid" 2>/dev/null; then
    pid_cmd=$(ps -p "$pid" -o command= 2>/dev/null || true)
    if [[ "$pid_cmd" =~ terraform-mcp|context7-mcp|node ]]; then
      log WARN "SIGKILL to surviving process (pid=${pid}, cmd=${pid_cmd})"
      kill -KILL "$pid" 2>/dev/null || true
    fi
  fi
done

log INFO "Cleanup complete"
exit 0
