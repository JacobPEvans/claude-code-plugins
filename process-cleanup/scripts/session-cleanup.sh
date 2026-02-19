#!/usr/bin/env bash
# Claude Code Stop Hook: Cleanup orphaned MCP processes
#
# Fires when a Claude session exits via /exit or Ctrl+C.
# Sweeps for orphaned MCP server processes system-wide (ppid=1 means the
# process was reparented to launchd — its parent terminal died without cleanup).
#
# SAFETY: Only kills processes with ppid=1. Never touches processes that have
# a living parent. Cannot affect active Claude sessions in other terminals.
#
# Targets:
#   - terraform-mcp-server  (Terraform MCP server)
#   - context7-mcp          (Context7 MCP server, may run as node)
#   - node processes with MCP-related arguments (ppid=1)
#
# Logs to: ~/Library/Logs/claude-process-cleanup/

set -uo pipefail

LOG_DIR="$HOME/Library/Logs/claude-process-cleanup"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/cleanup-$(date +%Y-%m-%d).log"

log_info() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] $*" >> "$LOG_FILE"
}

log_warn() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') [WARN] $*" >> "$LOG_FILE"
}

# Find orphaned processes where ppid=1 and command path matches a pattern
find_orphans_by_pattern() {
  local pattern=$1
  ps -Aeo pid,ppid,command | awk -v pat="$pattern" '$2 == 1 && $3 ~ pat {print $1}'
}

# Find orphaned node processes running MCP servers (ppid=1, args reference mcp/context7)
find_orphan_node_mcp() {
  ps -Aeo pid,ppid,command | awk '$2 == 1 && $3 ~ /node/ && ($0 ~ /mcp|context7/) {print $1}'
}

declare -a mcp_patterns=(
  "terraform-mcp"
  "context7-mcp"
)

declare -a all_pids=()

# Collect orphans by process name pattern
for pattern in "${mcp_patterns[@]}"; do
  while IFS= read -r pid; do
    [[ -n "$pid" ]] || continue
    all_pids+=("$pid")
    log_info "Found orphaned ${pattern} (pid=${pid}, ppid=1)"
  done < <(find_orphans_by_pattern "$pattern")
done

# Collect orphaned node MCP processes
while IFS= read -r pid; do
  [[ -n "$pid" ]] || continue
  all_pids+=("$pid")
  log_info "Found orphaned node MCP process (pid=${pid}, ppid=1)"
done < <(find_orphan_node_mcp)

[[ ${#all_pids[@]} -eq 0 ]] && exit 0

total_killed=0

# SIGTERM (graceful shutdown)
for pid in "${all_pids[@]}"; do
  if kill -TERM "$pid" 2>/dev/null; then
    ((total_killed++))
  fi
done

sleep 2

# SIGKILL survivors
for pid in "${all_pids[@]}"; do
  if kill -0 "$pid" 2>/dev/null; then
    log_warn "SIGKILL to surviving process (pid=${pid})"
    kill -KILL "$pid" 2>/dev/null || true
  fi
done

log_info "Cleanup complete: sent SIGTERM to ${total_killed} orphaned MCP process(es)"

exit 0
