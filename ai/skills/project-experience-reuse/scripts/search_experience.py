#!/usr/bin/env python3
"""Search Markdown experience records with YAML front matter."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


LIST_FIELDS = {"tags", "tech_stack", "environment", "related"}
FILTER_FIELDS = {
    "project",
    "module",
    "type",
    "status",
    "severity",
    "root_cause_type",
}


def split_front_matter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    raw = text[4:end].strip()
    body = text[end + 4 :].lstrip()
    return parse_yaml(raw), body


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
        if value == "":
            data[key] = []
        else:
            data[key] = parse_scalar(value)
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


def as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).lower() for item in value]
    return [str(value).lower()]


def norm(value: Any) -> str:
    return str(value or "").lower()


def load_records(root: Path) -> list[dict[str, Any]]:
    records = []
    for path in sorted(root.rglob("*.md")):
        meta, body = split_front_matter(path.read_text(encoding="utf-8"))
        records.append({"path": str(path), "meta": meta, "body": body})
    return records


def matches_filters(record: dict[str, Any], args: argparse.Namespace) -> bool:
    meta = record["meta"]
    for field in FILTER_FIELDS:
        expected = getattr(args, field)
        if expected and norm(meta.get(field)) != expected.lower():
            return False
    for field, expected_items in (
        ("tags", args.tags),
        ("tech_stack", args.tech_stack),
    ):
        if expected_items:
            actual = set(as_list(meta.get(field)))
            if not set(item.lower() for item in expected_items).issubset(actual):
                return False
    return True


def score_record(record: dict[str, Any], args: argparse.Namespace) -> tuple[int, list[str]]:
    meta = record["meta"]
    body = record["body"]
    score = 0
    reasons: list[str] = []
    for field in FILTER_FIELDS:
        expected = getattr(args, field)
        if expected and norm(meta.get(field)) == expected.lower():
            score += 8
            reasons.append(f"{field} matched")
    for field, expected_items in (
        ("tags", args.tags),
        ("tech_stack", args.tech_stack),
    ):
        actual = set(as_list(meta.get(field)))
        for item in expected_items or []:
            if item.lower() in actual:
                score += 6
                reasons.append(f"{field}:{item} matched")
    for token in query_tokens(args.query):
        haystacks = [
            norm(meta.get("title")),
            " ".join(as_list(meta.get("tags"))),
            " ".join(as_list(meta.get("tech_stack"))),
            body.lower(),
        ]
        if any(token in haystack for haystack in haystacks):
            score += 2
            reasons.append(f"query token:{token}")
    return score, reasons


def query_tokens(query: str | None) -> list[str]:
    if not query:
        return []
    return [token for token in re.split(r"\W+", query.lower()) if len(token) >= 2]


def relevance(score: int) -> str:
    if score >= 24:
        return "highly_relevant"
    if score >= 12:
        return "possibly_relevant"
    if score >= 4:
        return "weakly_relevant"
    return "not_relevant"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("experiences_dir", type=Path)
    parser.add_argument("--project")
    parser.add_argument("--module")
    parser.add_argument("--type")
    parser.add_argument("--status")
    parser.add_argument("--severity")
    parser.add_argument("--root-cause-type", dest="root_cause_type")
    parser.add_argument("--tags", action="append", default=[])
    parser.add_argument("--tech-stack", action="append", default=[])
    parser.add_argument("--query")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    rows = []
    for record in load_records(args.experiences_dir):
        if not matches_filters(record, args):
            continue
        score, reasons = score_record(record, args)
        rows.append(
            {
                "path": record["path"],
                "title": record["meta"].get("title", ""),
                "project": record["meta"].get("project", ""),
                "module": record["meta"].get("module", ""),
                "type": record["meta"].get("type", ""),
                "status": record["meta"].get("status", ""),
                "severity": record["meta"].get("severity", ""),
                "root_cause_type": record["meta"].get("root_cause_type", ""),
                "score": score,
                "relevance": relevance(score),
                "reasons": reasons,
            }
        )
    rows.sort(key=lambda row: row["score"], reverse=True)
    rows = rows[: args.limit]

    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return

    for row in rows:
        print(f"[{row['relevance']}] score={row['score']} {row['path']}")
        print(f"  title: {row['title']}")
        print(
            "  meta: "
            f"project={row['project']} module={row['module']} "
            f"type={row['type']} status={row['status']} "
            f"severity={row['severity']} root_cause_type={row['root_cause_type']}"
        )
        if row["reasons"]:
            print(f"  reasons: {', '.join(row['reasons'][:8])}")


if __name__ == "__main__":
    main()
