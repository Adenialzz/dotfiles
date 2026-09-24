#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11,<3.12"
# dependencies = [
#   "thrift",
#   "zhihu-pyhive==0.6.2",
#   "python-dotenv"
# ]
# ///

import argparse
import csv
import json
import os
import re
import sys
import time
from datetime import date
from pathlib import Path
from typing import TextIO

from dotenv import load_dotenv
from pyhive import hive
from TCLIService.ttypes import TOperationState

DATE_PARAMETER_PATTERN = re.compile(
    r"^--\s*biz_date:\s*(?P<biz_date>[0-9]{4}-[0-9]{2}-[0-9]{2})\s*$",
    re.MULTILINE,
)
DATE_PLACEHOLDER = "{{ biz_date }}"
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
        choices=("json", "jsonl", "tsv"),
        default="json",
        help="Output format. Defaults to json.",
    )
    parser.add_argument("--output", help="Optional output file path.")
    parser.add_argument(
        "--fetch-size",
        type=positive_int,
        default=100,
        help="每批从 Hive 读取的行数，默认 100。",
    )
    return parser.parse_args()


def positive_int(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("--fetch-size 必须大于 0")
    return number


def load_sql(args: argparse.Namespace) -> str:
    if args.sql is not None:
        return args.sql
    return Path(args.file).read_text()


def render_sql(sql_str: str) -> str:
    if DATE_PLACEHOLDER not in sql_str:
        return sql_str

    matches = list(DATE_PARAMETER_PATTERN.finditer(sql_str))
    if len(matches) != 1:
        raise ValueError("包含 biz_date 占位符的 SQL 必须声明唯一的日期参数")
    date_value = date.fromisoformat(matches[0].group("biz_date")).isoformat()
    return sql_str.replace(DATE_PLACEHOLDER, date_value)


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

    def run_sql(
        self,
        sql_str: str,
        output: TextIO,
        output_format: str,
        fetch_size: int,
    ) -> None:
        sql_str = self._validate_sql(sql_str)
        connection = hive.connect(**self._connect_args)
        cursor = connection.cursor()
        try:
            try:
                cursor.execute(sql_str, async_=True)
                self._wait_for_operation(cursor)
                if cursor.description is None:
                    return
                columns = [column[0] for column in cursor.description]
                write_rows(cursor, columns, output, output_format, fetch_size)
            except Exception:
                self._print_operation_logs(cursor)
                raise
        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def _wait_for_operation(cursor) -> None:
        pending_states = {
            TOperationState.INITIALIZED_STATE,
            TOperationState.RUNNING_STATE,
            TOperationState.PENDING_STATE,
        }
        while True:
            status = cursor.poll()
            if status.operationState == TOperationState.FINISHED_STATE:
                return
            if status.operationState not in pending_states:
                state_name = TOperationState._VALUES_TO_NAMES.get(
                    status.operationState, str(status.operationState)
                )
                raise RuntimeError(
                    f"Hive operation {state_name}: {status.errorMessage or '无错误详情'}"
                )
            time.sleep(1)

    @staticmethod
    def _print_operation_logs(cursor) -> None:
        if getattr(cursor, "_operationHandle", None) is None:
            return
        try:
            logs = cursor.fetch_logs()
        except Exception as error:
            print(f"读取 Hive operation log 失败: {error}", file=sys.stderr)
            return
        if not logs:
            return

        keywords = (
            "application_",
            "container_",
            "diagnostic",
            "exception",
            "failed",
            "killed",
            "error",
        )
        important_logs = [
            line
            for line in logs
            if any(keyword in line.lower() for keyword in keywords)
        ]
        selected_logs = list(dict.fromkeys([*important_logs, *logs[-200:]]))
        print("Hive operation log:", file=sys.stderr)
        for line in selected_logs:
            print(line, file=sys.stderr)

    @staticmethod
    def _validate_sql(sql_str: str) -> str:
        sql_str = sql_str.strip()
        if not sql_str:
            raise ValueError("SQL 不能为空")
        if ";" in sql_str:
            raise ValueError("只允许单条 SQL，且不要带分号")

        sql_without_leading_comments = sql_str
        while True:
            sql_without_leading_comments = sql_without_leading_comments.lstrip()
            if sql_without_leading_comments.startswith("--"):
                _, separator, sql_without_leading_comments = (
                    sql_without_leading_comments.partition("\n")
                )
                if not separator:
                    sql_without_leading_comments = ""
                    break
                continue
            if sql_without_leading_comments.startswith("/*"):
                comment_end = sql_without_leading_comments.find("*/", 2)
                if comment_end == -1:
                    sql_without_leading_comments = ""
                    break
                sql_without_leading_comments = sql_without_leading_comments[
                    comment_end + 2 :
                ]
                continue
            break

        normalized_sql = re.sub(r"\s+", " ", sql_str).upper()
        normalized_prefix = re.sub(r"\s+", " ", sql_without_leading_comments).upper()
        if not normalized_prefix.startswith(READONLY_SQL_PREFIXES):
            raise ValueError("只允许查询类 SQL")

        for keyword in WRITE_SQL_KEYWORDS:
            if re.search(rf"\b{keyword}\b", normalized_sql):
                raise ValueError(f"禁止执行写操作: {keyword}")

        return sql_without_leading_comments


def write_rows(
    cursor, columns: list[str], output: TextIO, output_format: str, fetch_size: int
) -> None:
    if output_format == "json":
        output.write("[\n")
    writer = csv.writer(output, delimiter="\t", lineterminator="\n")
    first = True
    while rows := cursor.fetchmany(fetch_size):
        for values in rows:
            row = dict(zip(columns, values, strict=True))
            if output_format == "json":
                if not first:
                    output.write(",\n")
                output.write(
                    "  "
                    + json.dumps(
                        row, ensure_ascii=False, indent=2, default=str
                    ).replace("\n", "\n  ")
                )
            elif output_format == "jsonl":
                output.write(
                    json.dumps(
                        row, ensure_ascii=False, default=str, separators=(",", ":")
                    )
                    + "\n"
                )
            else:
                if first:
                    writer.writerow(columns)
                writer.writerow(["" if value is None else value for value in values])
            first = False
    if output_format == "json":
        output.write("\n]\n" if not first else "]\n")


def main() -> None:
    args = parse_args()
    os.environ["http_proxy"] = ""
    os.environ["https_proxy"] = ""

    dotenv_path = Path(__file__).resolve().with_name(".env")
    if not load_dotenv(dotenv_path, override=True):
        raise OSError(f"读取 .env 文件失败: {dotenv_path}")
    print(f"Loaded .env from {dotenv_path}", file=sys.stderr)

    try:
        sql_str = render_sql(load_sql(args))
        client = HiveClient()
        if args.output is None:
            client.run_sql(sql_str, sys.stdout, args.format, args.fetch_size)
        else:
            output_path = Path(args.output)
            temporary_path = output_path.with_name(f".{output_path.name}.tmp")
            try:
                with temporary_path.open("w", encoding="utf-8", newline="") as output:
                    client.run_sql(sql_str, output, args.format, args.fetch_size)
                temporary_path.replace(output_path)
            except Exception:
                temporary_path.unlink(missing_ok=True)
                raise
            print(output_path, file=sys.stderr)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from None


if __name__ == "__main__":
    main()
