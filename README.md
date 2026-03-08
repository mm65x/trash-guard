# trash-guard

A Claude Code `PreToolUse` hook that blocks destructive file deletion commands (`rm`, `shred`, `unlink`, `find -delete`) and suggests using [`trash`](https://hasseg.org/trash/) instead.

Written in Python. No dependencies beyond the standard library.

Inspired by [zcaceres/claude-rm-rf](https://github.com/zcaceres/claude-rm-rf) (MIT License, TypeScript/Bun implementation).

## What it blocks

| Pattern | Example |
|---|---|
| Basic `rm` | `rm file.txt`, `rm -rf dir/` |
| Path variants | `/bin/rm`, `/usr/bin/rm`, `./rm` |
| Privilege escalation | `sudo rm`, `xargs rm` |
| Alias bypass | `command rm`, `env rm`, `\rm` |
| Subshells | `bash -c "rm ..."`, `sh -c "rm ..."` |
| `find` with delete | `find . -delete`, `find . -exec rm {} \;` |
| `shred`, `unlink` | `shred secret.txt`, `unlink file` |

## What it allows

| Pattern | Why |
|---|---|
| `git rm` | Tracked by git, recoverable |
| Quoted strings | `echo 'rm test'`, `grep 'rm' Makefile` |
| Allowlisted paths | `/tmp/*`, `__pycache__`, `node_modules`, etc. |

### Allowlisted paths (rm -rf permitted)

- `/tmp/*`, `/var/tmp/*`, `/private/tmp/*`
- `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`
- `node_modules`, `*.egg-info`, `.tox`, `.nox`

Edit `ALLOWED_PATHS` and `ALLOWED_NAMES` in `trash_guard.py` to customize.

## Installation

### 1. Install `trash`

```bash
brew install trash
```

If trash is keg-only, add to PATH:
```bash
echo 'export PATH="/opt/homebrew/opt/trash/bin:$PATH"' >> ~/.zshrc
```

### 2. Clone this repo

```bash
git clone git@github.com:mm65x/trash-guard.git ~/code/trash-guard
```

### 3. Add the hook to Claude Code

Add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 /path/to/trash-guard/trash_guard.py"
          }
        ]
      }
    ]
  }
}
```

### 4. Add CLAUDE.md rule (recommended)

Add to your global `~/.claude/CLAUDE.md`:

```markdown
## File Deletion Policy

Never use `rm`, `rm -rf`, `shred`, or `unlink` to delete files. Use `trash` instead:
- `trash file.txt` instead of `rm file.txt`
- `trash directory/` instead of `rm -rf directory/`

A PreToolUse hook will block `rm` commands. The `trash` CLI moves files to the system trash where they can be recovered.
```

## Tests

```bash
python3 -m pytest test_trash_guard.py -v
```

52 test cases covering blocked commands, allowed commands, allowlisted paths, and quote stripping.
