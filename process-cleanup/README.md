# process-cleanup

Cleans up orphaned MCP server processes when a Claude Code session exits.

## Purpose

Workaround for upstream Claude Code bug [#1935](https://github.com/anthropics/claude-code/issues/1935),
where MCP server child processes are not reliably terminated when a Claude session ends.

This plugin fires on the `Stop` event (triggered by `/exit` or Ctrl+C) and sweeps
system-wide for orphaned processes with `ppid=1` — meaning they were reparented to
launchd because their parent terminal died without cleanup.

## Safety Guarantees

- **Only kills ppid=1 processes** — cannot affect processes with a living parent
- **Cannot affect other Claude sessions** — active sessions have a living parent terminal
- **SIGTERM first, SIGKILL only for survivors** — 2-second grace period
- **Targets node processes by substring match** — matches orphaned `node` processes whose command
  line contains `mcp` or `context7`; unrelated node processes with those substrings could be affected

## Targets

| Process | Description |
|---------|-------------|
| `terraform-mcp-server` | Terraform/OpenTofu MCP server |
| `context7-mcp` | Context7 documentation MCP server |
| `node` (with MCP args) | Node-based MCP servers with mcp/context7 in arguments |

## Logs

Cleanup activity is logged to:

```text
~/Library/Logs/claude-process-cleanup/cleanup-YYYY-MM-DD.log
```

## Hook Architecture

This is a **defense-in-depth** second layer. The primary cleanup runs via `zshexit()`
in the parent zsh shell (Layer 1), which catches tab close via SIGHUP. This layer
catches explicit Claude exits (`/exit`, Ctrl+C) when zshexit may not fire.

Both layers are complementary and safe to run together.
