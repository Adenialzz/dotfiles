#!/usr/bin/python3
import json
import re
import shutil
import sys
from pathlib import Path


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0

    tool_input = payload.get("tool_input", {})
    command = tool_input.get("command", "")

    if not command:
        return 0

    # 可选：只在 uv 项目里启用，避免全局误伤
    if not Path("pyproject.toml").exists() or shutil.which("uv") is None:
        return 0

    # 已经使用 uv 的命令直接放行
    if re.search(r"(^|[;&|]\s*)uv\s+(run|pip|add|sync|lock|tree|python)\b", command):
        return 0

    blocked_patterns = [
        r"(^|[;&|]\s*)python(\d+(\.\d+)?)?\b",
        r"(^|[;&|]\s*)pytest\b",
        r"(^|[;&|]\s*)pip(\d+(\.\d+)?)?\b",
    ]

    if not any(re.search(pattern, command) for pattern in blocked_patterns):
        return 0

    print(
        """Blocked: do not run Python tooling directly in this project.

Use uv instead:
- `uv run python ...` instead of `python ...`
- `uv run pytest ...` instead of `pytest ...`
- `uv add ...` or `uv pip ...` instead of bare `pip ...`

Please revise the command and try again.
""",
        file=sys.stderr,
    )

    # exit code 2 blocks the tool call and shows stderr to Claude Code
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
