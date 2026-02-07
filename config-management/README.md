# config-management

Claude Code plugin for syncing AI tool permissions across repositories and quickly adding always-allow permissions.

## Skills

- **`/sync-permissions`** - Scan, analyze, and merge local AI permission settings into repository-wide permissions
- **`/quick-add-permission`** - Quickly add always-allow permissions to all AI tool permission lists

## Installation

```bash
claude plugins add jacobpevans-cc-plugins/config-management
```

## Usage

```text
/sync-permissions
/quick-add-permission "docker ps"
/quick-add-permission "docker ps" "docker logs" "kubectl get"
```

## License

MIT
