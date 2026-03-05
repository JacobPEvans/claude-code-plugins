#!/usr/bin/env python3
"""
Claude Code PostToolUse hook for README validation.
Validates README files after Write/Edit operations for required sections,
badge health, and installation code blocks.

Configuration: .readme-validator.yaml (searches upward from file's directory)

Exit codes:
  0 = allow (pass or non-critical warnings only)
  2 = block (missing required sections)

Input: JSON from stdin with tool_input.file_path containing the edited file
"""

import json
import re
import sys
from pathlib import Path
from typing import Optional
from urllib.error import URLError
from urllib.request import Request, urlopen


def find_config_file(start_path: Path) -> Optional[Path]:
    """
    Search upward from file's directory for .readme-validator.yaml.

    Walks up to 10 directory levels, similar to how git finds .git/.
    """
    current = start_path if start_path.is_dir() else start_path.parent
    for _ in range(10):
        config = current / ".readme-validator.yaml"
        if config.exists():
            return config
        if current.parent == current:  # Reached filesystem root
            break
        current = current.parent
    return None


def parse_simple_yaml(text: str) -> dict:
    """Parse a simple YAML config with top-level keys and list values.

    Handles the subset of YAML used by .readme-validator.yaml:
    - key: value (scalars: strings, booleans, integers)
    - key:\\n  - item1\\n  - item2 (lists)

    Does NOT handle nested dicts, multi-line strings, or anchors.
    """
    result: dict = {}
    current_key = None
    current_list: list[str] | None = None

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # List item under current key
        if stripped.startswith("- ") and current_key is not None:
            if current_list is None:
                current_list = []
            current_list.append(stripped[2:].strip())
            continue

        # Flush previous list
        if current_key is not None and current_list is not None:
            result[current_key] = current_list
            current_list = None
            current_key = None

        # Key: value pair
        if ":" in stripped:
            key, _, value = stripped.partition(":")
            key = key.strip()
            value = value.strip()
            if value:
                # Scalar value — parse booleans and integers
                if value.lower() in ("true", "yes"):
                    result[key] = True
                elif value.lower() in ("false", "no"):
                    result[key] = False
                elif value.isdigit():
                    result[key] = int(value)
                else:
                    result[key] = value
            else:
                # Value on next lines (list)
                current_key = key

    # Flush final list
    if current_key is not None and current_list is not None:
        result[current_key] = current_list

    return result


def load_config(file_path: Path) -> dict:
    """Load README validation config from .readme-validator.yaml."""
    defaults = {
        "required_sections": ["Installation", "Usage"],
        "optional_sections": ["Contributing", "License", "API"],
        "check_badges": True,
        "badge_timeout": 5,
    }

    config_path = find_config_file(file_path)
    if not config_path:
        return defaults

    try:
        text = config_path.read_text(encoding="utf-8")
        config = parse_simple_yaml(text)
        return {
            "required_sections": config.get(
                "required_sections", defaults["required_sections"]
            ),
            "optional_sections": config.get(
                "optional_sections", defaults["optional_sections"]
            ),
            "check_badges": config.get("check_badges", defaults["check_badges"]),
            "badge_timeout": config.get("badge_timeout", defaults["badge_timeout"]),
        }
    except Exception:
        # Config parse error, fail open with defaults
        return defaults


def parse_headings(content: str) -> list[str]:
    """Extract all ## level headings from markdown content."""
    headings = []
    for line in content.splitlines():
        match = re.match(r"^##\s+(.+)$", line)
        if match:
            headings.append(match.group(1).strip())
    return headings


def get_section_content(content: str, section_name: str) -> Optional[str]:
    """Extract the content under a specific ## heading until the next ## heading."""
    pattern = re.compile(
        rf"^##\s+{re.escape(section_name)}\s*$",
        re.IGNORECASE | re.MULTILINE,
    )
    match = pattern.search(content)
    if not match:
        return None

    start = match.end()
    # Find the next ## heading or end of content
    next_heading = re.search(r"^##\s+", content[start:], re.MULTILINE)
    if next_heading:
        return content[start : start + next_heading.start()]
    return content[start:]


def check_required_sections(
    content: str, required: list[str]
) -> list[str]:
    """Check that all required sections exist. Returns list of missing section names."""
    headings_lower = [h.lower() for h in parse_headings(content)]
    missing = []
    for section in required:
        if section.lower() not in headings_lower:
            missing.append(section)
    return missing


def check_badges(content: str, timeout: int) -> list[str]:
    """
    Find markdown badge images and verify URLs return HTTP 200.
    Returns list of warning strings for broken badges.
    """
    warnings = []

    # Match [![alt](badge_url)](link_url) and ![alt](badge_url) patterns
    badge_pattern = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
    for match in badge_pattern.finditer(content):
        alt_text = match.group(1)
        badge_url = match.group(2)

        # Skip local/relative URLs and data URIs
        if not badge_url.startswith(("http://", "https://")):
            continue

        try:
            req = Request(badge_url, method="HEAD")
            req.add_header("User-Agent", "readme-validator/1.0")
            response = urlopen(req, timeout=timeout)  # noqa: S310
            if response.status != 200:
                warnings.append(
                    f"Badge '{alt_text}' returned HTTP {response.status}: {badge_url}"
                )
        except (URLError, OSError, TimeoutError, ValueError):
            warnings.append(f"Badge '{alt_text}' unreachable: {badge_url}")

    return warnings


def check_install_code_blocks(content: str) -> bool:
    """Check that the Installation section contains at least one code block."""
    section = get_section_content(content, "Installation")
    if section is None:
        # No Installation section found; the required-sections check handles this
        return True
    return "```" in section


def main() -> None:
    # Read hook input from stdin
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)  # Invalid input, fail open

    tool_input = hook_input.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if not file_path:
        sys.exit(0)

    # Only act on README files
    file_name = Path(file_path).name
    if not re.match(r"README.*\.md$", file_name, re.IGNORECASE):
        sys.exit(0)

    # Skip if file doesn't exist
    path = Path(file_path)
    if not path.exists():
        sys.exit(0)

    # Load config
    config = load_config(path)

    # Read file content
    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        sys.exit(0)  # Can't read file, fail open

    # Collect blocking errors and non-blocking warnings
    errors = []
    warnings = []

    # Check required sections
    missing = check_required_sections(content, config["required_sections"])
    if missing:
        errors.append(f"Missing required sections: {', '.join(missing)}")

    # Check for code blocks in Installation section
    if not check_install_code_blocks(content):
        warnings.append(
            "Installation section has no code blocks "
            "(expected at least one ``` code block with install steps)"
        )

    # Check badge validity
    if config["check_badges"]:
        badge_warnings = check_badges(content, config["badge_timeout"])
        warnings.extend(badge_warnings)

    # Check optional sections (warnings only)
    headings_lower = [h.lower() for h in parse_headings(content)]
    missing_optional = [
        s
        for s in config["optional_sections"]
        if s.lower() not in headings_lower
    ]
    if missing_optional:
        warnings.append(
            f"Missing optional sections: {', '.join(missing_optional)}"
        )

    # Print warnings to stderr (shown to Claude)
    if warnings:
        print(f"README validation warnings for: {file_path}", file=sys.stderr)
        for warning in warnings:
            print(f"  - {warning}", file=sys.stderr)

    # Block only for missing required sections
    if errors:
        print("", file=sys.stderr)
        print(f"README validation FAILED for: {file_path}", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        print("", file=sys.stderr)
        print(
            "Add the missing required sections to the README "
            "or update .readme-validator.yaml to change requirements.",
            file=sys.stderr,
        )
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
