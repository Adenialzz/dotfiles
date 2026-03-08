---
name: consolidate
description: "触发条件：当用户要求你将当前对话上下文中的知识点沉淀下来。"
license: MIT
---

## 说明

将当前对话上下文中的知识点沉淀到一个 Markdown 文件中。

1. 首先搜索目标目录下已有的 Markdown 文件，看有没有与当前要整理的知识点相近的，
    - 如果有，直接修改、追加到那个 Markdown 文件；
    - 如果没有，抽取当前知识点名，作为 Markdown 文件名，新建 Markdown 文件
2. 将知识点内容，包括背景、解释、用例等，写入到 Markdown 文件中

## 保存位置

除非用户特别说明，否则保存到 `~/.adenialzz/consolidate/`
