#!/usr/bin/env python3
"""
trash-guard: Block destructive file deletion commands in Claude Code.

A PreToolUse hook that intercepts Bash commands containing rm, shred, unlink,
or find -delete, and suggests using `trash` instead.

Inspired by zcaceres/claude-rm-rf (MIT License).
Rewritten in Python with configurable allowlist support.
"""

import json
import re
import sys

# Paths where rm -rf is allowed (exact prefix match).
# Keep this minimal — only paths that are always safe to delete.
ALLOWED_PATHS = [
    "/tmp/",
    "/var/tmp/",
    "/private/tmp/",
]

# Filename patterns where rm -rf is allowed (matched against the last path component).
ALLOWED_NAMES = [
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    ".egg-info",
    "*.egg-info",
    ".tox",
    ".nox",
]


def strip_quotes(command: str) -> str:
    """Remove quoted strings to avoid false positives."""
    # Remove double-quoted strings (handles escapes)
    stripped = re.sub(r'"(?:[^"\\]|\\.)*"', '""', command)
    # Remove single-quoted strings (no escapes in single quotes)
    stripped = re.sub(r"'[^']*'", "''", stripped)
    return stripped


def _extract_rm_subcommand(command: str) -> str | None:
    """Extract the rm sub-command from a potentially chained command."""
    # Split on shell operators to isolate the rm part
    parts = re.split(r"\s*(?:&&|\|\||;)\s*", command)
    for part in parts:
        part = part.strip()
        # Check if this sub-command starts with rm (possibly with sudo/env prefix)
        if re.match(r"(?:sudo\s+|env\s+|command\s+)?(?:\\)?rm\b", part):
            return part
        # Check for absolute path rm
        if re.match(r"(?:sudo\s+)?/.*?/rm\b", part):
            return part
    return None


def is_allowed_rm(command: str) -> bool:
    """Check if the rm command targets an allowed path or name."""
    rm_cmd = _extract_rm_subcommand(command)
    if rm_cmd is None:
        return False

    tokens = rm_cmd.split()
    rm_idx = None
    for i, tok in enumerate(tokens):
        if tok in ("rm", "\\rm") or tok.endswith("/rm"):
            rm_idx = i
            break
    if rm_idx is None:
        return False

    # Collect path arguments (skip flags starting with -)
    paths = [t for t in tokens[rm_idx + 1:] if not t.startswith("-")]

    if not paths:
        return False

    for path in paths:
        allowed = False
        # Check allowed path prefixes
        for prefix in ALLOWED_PATHS:
            if path.startswith(prefix):
                allowed = True
                break
        # Check allowed name patterns
        if not allowed:
            basename = path.rstrip("/").rsplit("/", 1)[-1] if "/" in path else path
            for pattern in ALLOWED_NAMES:
                if pattern.startswith("*"):
                    if basename.endswith(pattern[1:]):
                        allowed = True
                        break
                elif basename == pattern:
                    allowed = True
                    break
        if not allowed:
            return False

    return True


def contains_destructive_command(command: str) -> bool:
    """Check if command contains destructive deletion commands."""
    stripped = strip_quotes(command)

    # git rm is always safe (tracked by git, recoverable)
    if re.search(r"\bgit\s+rm\b", stripped):
        return False

    # Check for subshell patterns against the ORIGINAL command
    subshell_patterns = [
        r"\b(?:sh|bash|zsh|dash)\s+-c\s+.*\brm\b",
        r"\b(?:sh|bash|zsh|dash)\s+-c\s+.*\bshred\b",
        r"\b(?:sh|bash|zsh|dash)\s+-c\s+.*\bunlink\b",
        r"\b(?:sh|bash|zsh|dash)\s+-c\s+.*\bfind\b.*-delete\b",
    ]
    if any(re.search(p, command) for p in subshell_patterns):
        return True

    # Patterns for destructive commands
    # Matches: start of command, or after shell operators (&&, ||, ;, |, $()
    prefix = r"(?:^|&&|\|\||;|\||\$\(|`)\s*"

    destructive_patterns = [
        # rm at start or after operators
        prefix + r"rm\b",
        # shred, unlink
        prefix + r"shred\b",
        prefix + r"unlink\b",
        # Absolute/relative paths to rm
        prefix + r"/.*?/rm\b",
        prefix + r"\./rm\b",
        # Via sudo, xargs, command, env
        r"\bsudo\s+rm\b",
        r"\bsudo\s+/.*?/rm\b",
        r"\bxargs\s+rm\b",
        r"\bxargs\s+/.*?/rm\b",
        r"\bcommand\s+rm\b",
        r"\benv\s+rm\b",
        # Backslash escape to bypass aliases
        prefix + r"\\rm\b",
        # find with -delete or -exec rm
        r"\bfind\b.*\s-delete\b",
        r"\bfind\b.*-exec\s+rm\b",
        r"\bfind\b.*-exec\s+/.*?/rm\b",
    ]

    if not any(re.search(p, stripped) for p in destructive_patterns):
        return False

    # It matched a destructive pattern — check if it's on the allowlist
    if is_allowed_rm(command):
        return False

    return True


def main() -> None:
    try:
        data = json.loads(sys.stdin.read())
        command = data.get("tool_input", {}).get("command", "")

        if not command:
            sys.exit(0)

        if contains_destructive_command(command):
            print(
                "BLOCKED: Destructive file deletion detected. "
                "Use `trash` instead of `rm`:\n"
                "  trash file.txt\n"
                "  trash directory/\n\n"
                "Allowed exceptions (rm -rf only):\n"
                "  - /tmp/*, /var/tmp/*\n"
                "  - __pycache__, .pytest_cache, .mypy_cache, .ruff_cache\n"
                "  - node_modules, *.egg-info, .tox, .nox\n\n"
                "If trash is not installed: brew install trash",
                file=sys.stderr,
            )
            sys.exit(2)

        sys.exit(0)
    except Exception:
        # Parse errors allow through
        sys.exit(0)


if __name__ == "__main__":
    main()
