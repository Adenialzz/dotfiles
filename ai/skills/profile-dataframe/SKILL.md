---
name: profile-dataframe
description: 当需要先理解陌生的表格型数据文件，再决定后续清洗、分析、建模或脚本实现方案时使用此 skill。适用于快速探查 csv、tsv、txt、Excel、parquet、json/jsonl、feather、pickle 等 dataframe-like 文件的 schema、样例行、空值、重复行、列类型、候选字段角色与基础统计，帮助你在真正写数据处理脚本前先建立可靠的数据认识。
---

# Profile Dataframe

在编写数据处理脚本、分析逻辑或字段映射前，先用附带脚本快速建立对输入文件的结构化认识。

## 使用方式

优先直接运行：

```bash
uv run ai/skills/profile-dataframe/scripts/profile_dataframe.py <path>
```

按需补充参数：

- `--sheet <name>`：读取指定 Excel sheet
- `--sample-rows <n>`：控制输出里的样例行数量，默认 `5`
- `--profile-rows <n>`：控制高成本列分析只扫描前多少行，默认 `50000`

常见示例：

```bash
uv run ai/skills/profile-dataframe/scripts/profile_dataframe.py data/orders.csv
uv run ai/skills/profile-dataframe/scripts/profile_dataframe.py data/users.xlsx --sheet Sheet2
uv run ai/skills/profile-dataframe/scripts/profile_dataframe.py data/events.jsonl --sample-rows 3 --profile-rows 10000
```

## 标准工作流

按下面顺序工作：

1. 先对用户给的主输入文件跑一次脚本，不要先凭文件名猜字段语义。
2. 先看顶层摘要：`shape`、`duplicate_row_count`、`sample_rows`、Excel 的 `available_sheets` / `selected_sheet`。
3. 再逐列看 `columns` 中的摘要，确认：
   - 哪些列像主键、外键、枚举、时间列、文本列、数值指标；
   - 哪些列空值很多、唯一值异常、值域异常；
   - 哪些列名误导性强，需要结合样例值重新理解。
4. 再基于 JSON 摘要决定后续方案：
   - 写清洗/转换脚本；
   - 选择 join key、分组字段、时间窗口字段；
   - 决定读取参数、类型转换、缺失值策略和校验逻辑。

如果用户给了多个表，优先分别 profile，再比较字段命名、主键候选和时间字段，最后再决定表间关系。

## 输出解读

脚本 stdout 永远输出单个 JSON 对象。

成功时：

- `ok=true`
- `path`：输入文件绝对路径
- `file_format`：识别到的文件类型
- `shape`：总行列数
- `sample_rows`：前几行样例，适合快速理解字段语义
- `duplicate_row_count`：整行重复数量
- `profiled_row_count`：用于高成本分析的扫描行数
- `columns`：逐列摘要

每个列摘要通常包含：

- `name`
- `dtype`
- `non_null_count` / `null_count` / `null_ratio`
- `unique_count`
- `sample_values`
- `inferred_roles`
- `numeric_summary` / `datetime_summary` / `text_summary` 中的部分字段

失败时：

- `ok=false`
- `error.type`
- `error.message`

依赖方应按这个结构做判断，不要依赖 stderr 文本。

## 角色推断约定

`inferred_roles` 是启发式提示，不是权威 schema。当前常见角色有：

- `identifier`
- `timestamp`
- `boolean`
- `measure`
- `categorical`
- `text`

使用这些角色时，务必结合列名、样例值、唯一值比例和业务上下文二次确认，尤其不要仅凭 `identifier` 或 `timestamp` 推断就直接写 join 或时间过滤逻辑。

## 适合用它解决的问题

- 在写批处理脚本前先理解输入表结构
- 判断某个文件是否真的是结构化表格数据
- 为清洗、聚合、映射、join、特征工程选择字段
- 快速排查“列类型不对”“空值太多”“Excel sheet 选错”“时间列格式混乱”等问题

## 不适合用它解决的问题

- 需要跨表业务推理或复杂口径定义时，它只能提供输入事实，不能代替业务判断
- 需要全量数据质量审计时，它只给快速摘要，不等于完整 profiling 报告
- 需要修改数据文件时，它只读输入并输出 JSON，不执行写回

## 后续动作建议

拿到摘要后，优先在你的回复或实现里显式记录这些关键信息：

- 输入文件格式与规模
- 每个关键字段的候选语义
- 计划使用的主键、时间列、类别列、指标列
- 已发现的风险，如高空值、重复行、疑似脏值、列类型不稳定

然后再开始写真正的数据处理脚本，避免一边猜 schema 一边编码。
