# webfetch-guard

A Claude Code plugin that intercepts WebFetch and WebSearch calls to enforce date awareness.

## Behavior

| Condition | Action |
|-----------|--------|
| URL/query contains "2024" | **BLOCK** - Denies the request with current date info |
| URL/query contains "2025" | **WARN** - Allows but reminds Claude to check the date |
| No year reference | **PASS** - Silent allow |

## Installation

### Option 1: Add the marketplace (recommended)

```bash
/plugin marketplace add ~/git/claude-plugins
```

Then install the plugin:

```bash
/plugin install webfetch-guard@jacobpevans-plugins
```

### Option 2: Test locally during development

```bash
claude --plugin-dir ~/git/claude-plugins/webfetch-guard
```

## Testing

```bash
python3 ~/git/claude-plugins/webfetch-guard/scripts/test_hook.py
```

## Structure

```
webfetch-guard/
├── .claude-plugin/
│   └── plugin.json          # Plugin manifest
├── hooks/
│   └── hooks.json           # Hook configuration
├── scripts/
│   ├── webfetch-guard.py    # Hook implementation
│   └── test_hook.py         # Tests
└── README.md
```

## How It Works

The hook intercepts `PreToolUse` events for `WebFetch` and `WebSearch` tools:

1. Reads the tool input (URL, prompt, or query)
2. Checks for year references ("2024" or "2025")
3. Returns a hook decision:
   - `deny` with reason for 2024 references
   - `allow` with warning for 2025 references
   - Silent exit (code 0) for no year references

## Customization

Edit `scripts/webfetch-guard.py` to:

- Add more blocked years
- Change warning messages
- Add domain-based rules
- Modify the check logic
