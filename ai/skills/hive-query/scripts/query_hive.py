#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10,<3.11"
# dependencies = [
#   "thrift",
#   "zhihu-pyhive==0.6.2",
#   "python-dotenv"
# ]
# ///

import argparse
import json
import os
import re
import sys
from pathlib import Path
from dotenv import load_dotenv

from pyhive import hive


READONLY_SQL_PREFIXES = ("SELECT", "SHOW", "DESCRIBE", "WITH", "EXPLAIN")
WRITE_SQL_KEYWORDS = (
    "ALTER",
    "CREATE",
    "DELETE",
    "DROP",
    "INSERT",
    "LOAD",
    "MERGE",
    "MSCK",
    "REPLACE",
    "TRUNCATE",
    "UPDATE",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a single read-only Hive query.")
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--sql", help="Inline SQL to execute.")
    source_group.add_argument("--file", help="Path to a file that contains the SQL.")
    parser.add_argument(
        "--format",
        choices=("json", "tsv"),
        default="json",
        help="Output format. Defaults to json.",
    )
    parser.add_argument("--output", help="Optional output file path.")
    return parser.parse_args()


def load_sql(args: argparse.Namespace) -> str:
    if args.sql is not None:
        return args.sql
    return Path(args.file).read_text()


class HiveClient:
    def __init__(self) -> None:
        self._connect_args = {
            "host": os.environ.get("HIVE_HOST", "hive-adhoc"),
            "port": int(os.environ.get("HIVE_PORT", "10000")),
            "auth": os.environ.get("HIVE_AUTH", "NOSASL"),
            "username": os.environ["HADOOP_USER_NAME"],
            "password": os.environ["HADOOP_USER_PASSWORD"],
            "configuration": {
                "mapreduce.job.queuename": os.environ["HADOOP_QUEUE"],
            },
        }

    def run_sql(self, sql_str: str) -> list[dict]:
        sql_str = self._validate_sql(sql_str)
        connection = hive.connect(**self._connect_args)
        cursor = connection.cursor()
        try:
            cursor.execute(sql_str)
            if cursor.description is None:
                return []
            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def _validate_sql(sql_str: str) -> str:
        sql_str = sql_str.strip()
        if not sql_str:
            raise ValueError("SQL 不能为空")
        if ";" in sql_str:
            raise ValueError("只允许单条 SQL，且不要带分号")

        normalized_sql = re.sub(r"\s+", " ", sql_str).upper()
        if not normalized_sql.startswith(READONLY_SQL_PREFIXES):
            raise ValueError("只允许查询类 SQL")

        for keyword in WRITE_SQL_KEYWORDS:
            if re.search(rf"\b{keyword}\b", normalized_sql):
                raise ValueError(f"禁止执行写操作: {keyword}")

        return sql_str


def format_rows(rows: list[dict], output_format: str) -> str:
    if output_format == "json":
        return json.dumps(rows, ensure_ascii=False, indent=2, default=str) + "\n"

    if not rows:
        return ""

    columns = list(rows[0].keys())
    lines = ["\t".join(columns)]
    for row in rows:
        lines.append("\t".join("" if row[column] is None else str(row[column]) for column in columns))
    return "\n".join(lines) + "\n"


def write_output(content: str, output_path: str | None) -> None:
    if output_path is None:
        sys.stdout.write(content)
        return

    Path(output_path).write_text(content)
    print(output_path, file=sys.stderr)


def main() -> None:
    os.environ.pop("http_proxy")
    os.environ.pop("https_proxy")

    dotenv_path = Path(__file__).resolve().with_name(".env")
    if not load_dotenv(dotenv_path, override=True):
        raise EnvironmentError(f"读取 .env 文件失败: {dotenv_path}")
    print(f"Loaded .env from {dotenv_path}")

    args = parse_args()
    sql_str = load_sql(args)
    client = HiveClient()
    try:
        rows = client.run_sql(sql_str)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from None
    content = format_rows(rows, args.format)
    write_output(content, args.output)


if __name__ == "__main__":
    main()
