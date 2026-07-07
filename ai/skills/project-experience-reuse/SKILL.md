---
name: project-experience-reuse
description: 沉淀、检索和复用项目经验。Use when Codex needs to document project pitfalls, incident reviews, bug investigations, technical decisions, performance optimizations, deployment issues, or troubleshoot a new issue by searching Markdown experience records with YAML front matter and cautiously reusing historical solutions.
---

# Project Experience Reuse

## 核心原则

- 默认用中文输出，除非用户指定其他语言。
- 先理解当前问题，再检索历史经验；不要用历史方案替代现场证据。
- 明确区分事实、推测和已验证结论。任何未验证判断都标为“推测”。
- 复用历史方案前，必须比较相似点、差异点、复用条件、不适用情况和风险。
- 经验库默认是当前项目或用户指定目录下的 `experiences/`，每条经验是带 YAML front matter 的 Markdown。

## 经验文档格式

创建或整理经验时，使用一个 Markdown 文件，文件名建议为：

```text
YYYY-MM-DD-project-module-short-title.md
```

Front matter 必须包含：

```yaml
---
title: "简短标题"
date: "2026-07-07"
project: "项目名"
module: "模块或组件"
type: "bug_debugging"
status: "verified"
severity: "high"
tags: ["timeout", "training", "network"]
tech_stack: ["python", "pytorch", "uv"]
environment: ["local", "cuda"]
root_cause_type: "config"
reusable: true
verified: true
source: "log / issue / commit / user-report"
related: []
---
```

枚举值：

- `type`: `pitfall`, `incident_review`, `bug_debugging`, `technical_decision`, `performance_optimization`, `deployment_issue`, `outage`, `other`
- `status`: `draft`, `verified`, `deprecated`
- `severity`: `low`, `medium`, `high`, `critical`
- `root_cause_type`: `config`, `code`, `dependency`, `data`, `infra`, `network`, `resource`, `process`, `unknown`, `other`

列表字段：`tags`, `tech_stack`, `environment`, `related`。

正文必须包含这些二级标题：

```markdown
## 摘要
## 背景
## 问题现象
## 影响范围
## 根因
## 排查过程
## 解决方案
## 验证方式
## 复用条件
## 不适用情况
## 预防措施
## 待补充信息
```

当 `reusable: true` 时，`## 复用条件` 和 `## 不适用情况` 不能为空。若根因尚未确认，在 `## 根因` 中写“未确认”，并把相关判断放入“推测”小段。

## 沉淀经验流程

1. 提取事件事实：项目、模块、环境、技术栈、最近变更、触发方式、报错、症状、影响范围、时间线、已尝试操作和验证结果。
2. 判断经验类型和严重程度，填写 front matter。宁可保守标为 `draft`，不要把未验证结论写成 `verified`。
3. 正文按固定章节组织。排查过程保留关键证据、命令、日志片段和否定性发现。
4. 写出复用边界：哪些条件满足时可以复用，哪些条件不同就不能直接套用。
5. 保存到 `experiences/`，然后运行 `scripts/normalize_experience.py` 校验。

## 编辑已有经验

允许编辑已有经验，但必须保护历史事实和排查线索：

- 补充证据：追加日志、命令、配置、环境、排查过程、验证方式和影响范围。
- 修正结论：只有在有新证据时，才把“推测”改为“已验证结论”，并说明修正依据。
- 更新状态：常见流转是 `draft` -> `verified`；方案失效或上下文过时时改为 `deprecated`，不要直接删除。
- 补充复用边界：优先完善 `## 复用条件`、`## 不适用情况` 和风险，而不是只追加解决方案。
- 合并重复经验：保留信息更完整的一篇，把被合并文档标为 `deprecated`，并在 `related` 中互相引用。

编辑前先读取原文；如果在 git 仓库中，先查看工作区状态和相关 diff，避免覆盖他人或用户的未提交修改。不要静默改写时间线、原始症状、原始日志和当时的错误判断；需要修正时，在正文中增加“后续修正”或等价说明，区分原始结论和新结论。

## 遇到新问题时

先提取关键信号：

- 报错：异常类型、错误码、关键日志、堆栈顶部和底部。
- 模块：文件、函数、服务、训练阶段、部署阶段或数据链路位置。
- 环境：本地/CI/生产/训练平台、OS、GPU/CPU、容器、依赖版本、配置。
- 技术栈：语言、框架、数据库、中间件、模型、训练/部署工具。
- 最近变更：代码、配置、依赖、数据、资源、平台、权限、网络。
- 症状：可复现性、频率、性能变化、失败边界、影响用户或任务。

然后检索 `experiences/`：

```bash
uv run <skill-dir>/scripts/search_experience.py experiences --project myproj --module trainer --tech-stack pytorch --tags timeout --query "CUDA OOM after batch size change"
```

相关性分级：

- `highly_relevant`: 项目/模块或技术栈高度重合，症状和根因信号相同，复用条件基本满足。
- `possibly_relevant`: 有多个关键信号重合，但环境、版本、根因或触发条件仍需验证。
- `weakly_relevant`: 只有泛化模式相似，可作为排查灵感，不能直接复用方案。
- `not_relevant`: 关键上下文冲突，或只存在表面词汇重合。

输出必须包含：

```markdown
## 问题理解
- 事实：
- 推测：
- 待验证：

## 相关经验
- highly_relevant:
- possibly_relevant:
- weakly_relevant:
- not_relevant:

## 相似点
## 差异点
## 排查步骤
## 可复用方案
## 风险提示
```

## 脚本

- `scripts/search_experience.py`: 解析 `experiences/` 下 Markdown front matter，按 `project`, `module`, `tags`, `tech_stack`, `type`, `status`, `severity`, `root_cause_type` 过滤，并结合 `--query` 对元数据和正文打分。
- `scripts/normalize_experience.py`: 校验并规范化经验文档，检查必填字段、枚举值、列表字段、日期格式、必需章节，以及 `reusable: true` 时复用条件和不适用情况是否非空。

脚本只做轻量 Markdown + YAML 处理。不要引入向量数据库；若需要更强召回，先扩展元数据、标签和正文关键词。
