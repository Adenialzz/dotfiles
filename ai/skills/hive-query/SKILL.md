---
name: hive-query
description: 基于 references/ 中的表文档编写并执行只读 Hive SQL。用于内部数仓查数、确认表结构、解释字段关系、生成安全查询、或把指标问题落到具体 Hive 表和 SQL 时。
---

# Hive Query

## Overview

使用 `references/` 作为表信息和指标口径的唯一来源。调用 `scripts/query_hive.py` 执行单条只读 Hive SQL，并把结果输出为 JSON 或 TSV。

## Workflow

1. 先在 `references/` 中定位相关表和指标说明。优先用 `rg --files references` 或 `rg "关键词" references`。
2. 明确粒度、分区字段、时间范围、主键和可用 join key。
3. 先写单条只读 SQL。探索性查询默认加 `limit`，且优先显式写出分区过滤。
4. 需要实际查数时，运行 `uv run scripts/query_hive.py --sql "..."` 或 `uv run scripts/query_hive.py --file path/to/query.sql`。
5. 结果返回后，先核对行数、时间范围和空值，再给结论。

## Query Rules

- 只写单条 SQL，不要带分号。
- 只允许 `SELECT`、`SHOW`、`DESCRIBE`、`WITH`、`EXPLAIN`。
- 未确认字段含义前，不要猜；回到 `references/` 查文档。
- 探索字段时优先选明确列名，不要默认 `select *`，除非用户明确要求。
- 查大表时先缩小日期分区和样本范围。
- 需要跨表时，先确认两侧粒度和 join key 再动手。

## Add a new table

- 用户要求你新增一张表时，会给你提供你一些原始表结构信息，你需要对其进行整理并保存在 `references/` 目录下；
- 新表可以直接从 `references/tables_template.md` 复制模板补充。
- 每张表至少记录：全名、粒度、主键或唯一键、分区字段、常用过滤条件、常见 join key、口径 caveat、示例 SQL。
- 如果用户提供的信息不完整，你可以主动询问相关信息

## Scripts

`query_hive.py` hive sql 查询

常用命令：

```bash
uv run scripts/query_hive.py --sql "SELECT 1 AS value"
uv run scripts/query_hive.py --file /path/to/query.sql
uv run scripts/query_hive.py --file /path/to/query.sql --format tsv --output /tmp/result.tsv
```

## References

- 表信息存放在 `references/`
