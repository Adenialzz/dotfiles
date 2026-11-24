#!/usr/bin/env python3
"""Block bare python/pytest/pip commands in uv-managed projects."""

import json
import re
import shutil
import sys
from pathlib import Path


def allow() -> int:
    print(json.dumps({"decision": "allow"}))
    return 0


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return allow()

    tool_call = payload.get("toolCall", {})
    args = tool_call.get("args", {})
    command = args.get("CommandLine", "")
    cwd = payload.get("cwd") or "."

    if not command:
        return allow()

    if not (Path(cwd) / "pyproject.toml").exists() or shutil.which("uv") is None:
        return allow()

    if re.search(r"(^|[;&|]\s*)uv\s+(run|pip|add|sync|lock|tree|python)\b", command):
        return allow()

    blocked_patterns = [
        r"(^|[;&|]\s*)python(\d+(\.\d+)?)?\b",
        r"(^|[;&|]\s*)pytest\b",
        r"(^|[;&|]\s*)pip(\d+(\.\d+)?)?\b",
    ]

    if not any(re.search(pattern, command) for pattern in blocked_patterns):
        return allow()

    reason = (
        "Blocked: do not run Python tooling directly in this project.\n\n"
        "Use uv instead:\n"
        "- `uv run python ...` instead of `python ...`\n"
        "- `uv run pytest ...` instead of `pytest ...`\n"
        "- `uv add ...` or `uv pip ...` instead of bare `pip ...`"
    )
    print(json.dumps({"decision": "deny", "reason": reason}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
