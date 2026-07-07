#!/usr/bin/env python3
"""Validate and normalize Markdown experience records."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = {
    "title",
    "date",
    "project",
    "module",
    "type",
    "status",
    "severity",
    "tags",
    "tech_stack",
    "environment",
    "root_cause_type",
    "reusable",
    "verified",
    "source",
}
LIST_FIELDS = {"tags", "tech_stack", "environment", "related"}
BOOL_FIELDS = {"reusable", "verified"}
ENUMS = {
    "type": {
        "pitfall",
        "incident_review",
        "bug_debugging",
        "technical_decision",
        "performance_optimization",
        "deployment_issue",
        "outage",
        "other",
    },
    "status": {"draft", "verified", "deprecated"},
    "severity": {"low", "medium", "high", "critical"},
    "root_cause_type": {
        "config",
        "code",
        "dependency",
        "data",
        "infra",
        "network",
        "resource",
        "process",
        "unknown",
        "other",
    },
}
REQUIRED_SECTIONS = [
    "摘要",
    "背景",
    "问题现象",
    "影响范围",
    "根因",
    "排查过程",
    "解决方案",
    "验证方式",
    "复用条件",
    "不适用情况",
    "预防措施",
    "待补充信息",
]


def split_front_matter(text: str) -> tuple[dict[str, Any], str, str]:
    if not text.startswith("---\n"):
        return {}, "", text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, "", text
    raw = text[4:end].strip()
    body = text[end + 4 :].lstrip()
    return parse_yaml(raw), raw, body


def parse_yaml(raw: str) -> dict[str, Any]:
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(raw) or {}
        return data if isinstance(data, dict) else {}
    except ImportError:
        return parse_simple_yaml(raw)


def parse_simple_yaml(raw: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current_key: str | None = None
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("  - ") and current_key:
            data.setdefault(current_key, []).append(parse_scalar(line[4:].strip()))
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        current_key = key
        data[key] = [] if value == "" else parse_scalar(value)
    return data


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value in {"true", "True"}:
        return True
    if value in {"false", "False"}:
        return False
    if value in {"null", "None", "~"}:
        return None
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [parse_scalar(item.strip()) for item in inner.split(",")]
    return value


def section_text(body: str, section: str) -> str:
    pattern = rf"^##\s+{re.escape(section)}\s*$"
    match = re.search(pattern, body, flags=re.MULTILINE)
    if not match:
        return ""
    rest = body[match.end() :]
    next_match = re.search(r"^##\s+", rest, flags=re.MULTILINE)
    return rest[: next_match.start()].strip() if next_match else rest.strip()


def validate(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    meta, _raw, body = split_front_matter(text)
    errors: list[str] = []
    missing = sorted(REQUIRED_FIELDS - set(meta))
    if missing:
        errors.append(f"missing required fields: {', '.join(missing)}")
    if "date" in meta and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(meta["date"])):
        errors.append("date must use YYYY-MM-DD")
    for field, allowed in ENUMS.items():
        if field in meta and meta[field] not in allowed:
            errors.append(f"{field} must be one of: {', '.join(sorted(allowed))}")
    for field in LIST_FIELDS:
        if field in meta and not isinstance(meta[field], list):
            errors.append(f"{field} must be a list")
    for field in BOOL_FIELDS:
        if field in meta and not isinstance(meta[field], bool):
            errors.append(f"{field} must be boolean")
    for section in REQUIRED_SECTIONS:
        if not re.search(rf"^##\s+{re.escape(section)}\s*$", body, flags=re.MULTILINE):
            errors.append(f"missing section: ## {section}")
    if meta.get("reusable") is True:
        for section in ("复用条件", "不适用情况"):
            if not section_text(body, section):
                errors.append(f"reusable=true requires non-empty section: ## {section}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()

    failed = False
    for input_path in args.paths:
        paths = sorted(input_path.rglob("*.md")) if input_path.is_dir() else [input_path]
        for path in paths:
            errors = validate(path)
            if errors:
                failed = True
                print(f"FAIL {path}")
                for error in errors:
                    print(f"  - {error}")
            else:
                print(f"OK {path}")
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
