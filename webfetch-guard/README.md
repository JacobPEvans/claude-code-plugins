# webfetch-guard

A Claude Code plugin that intercepts WebFetch and WebSearch calls to enforce date awareness.

## Behavior

| Condition | Action |
|-----------|--------|
| URL/query contains previous year | **BLOCK** - Denies the request with current date info |
| URL/query contains current year | **WARN** - Allows but reminds Claude to check the date |
| No year reference | **PASS** - Silent allow |

**Dynamic Years**: The hook automatically determines outdated (previous year) and current years based on the system date.

## Installation

### Option 1: Add the marketplace (recommended)

```bash
/plugin marketplace add <path-to-claude-code-plugins-repo>
```

Then install the plugin:

```bash
/plugin install webfetch-guard@jacobpevans-plugins
```

### Option 2: Test locally during development

```bash
claude --plugin-dir <path-to-claude-code-plugins-repo>/webfetch-guard
```

## Testing

```bash
python3 <path-to-claude-code-plugins-repo>/webfetch-guard/scripts/test_hook.py
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
2. Dynamically determines current year and previous year
3. Checks for year references in the input
4. Returns a hook decision:
   - `deny` with reason for previous year references
   - `allow` with warning for current year references
   - Silent exit (code 0) for no year references

## Customization

Edit `scripts/webfetch-guard.py` to:

- Adjust which years to block/warn (currently previous/current)
- Change warning messages
- Add domain-based rules
- Modify the check logic
