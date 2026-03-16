---
name: batch-dataprocess-script-programmer
description: 当用户要求编写单文件 python 数据处理脚本时使用此技能。
---

# Python Script Programmer

用户会将一些简单的 Python 单文件数据处理脚本编码任务交给你，以下是一些具体要求，请按照要求实现。如果你认为用户给定的任务与下列要求存在冲突或方案不合理之处，主动提出并于用户探讨合理方案。

## 批量数据处理

### 基础参数选项

一般来说，在编写批量数据处理脚本时，你的实现需要支持以下基础参数选项：

- 输入文件和输出文件，分别用 `--input-path`, `-i` 和 `--output-path`, `-o` 来指定；

- 如果有必要（比如涉及接口调用等），必须支持并发请求，并提供 `--concurrency`, `-con` 参数来控制并发度。简单的数据处理，不需要支持并发。

- 支持设置测试条数 `--limit`

- 支持进度条显示（比如用 tqdm），默认开启进度条显示，并提供禁用选项 `--disable-progress-bar`

除了以上基础批量数据处理参数选项之外，你应该根据具体任务，支持其他有必要的参数选项。比如需要调用 llm 时，需要支持 `--client` 。

### 少批量测试

在编写完批量数据处理脚本后，需要你自己先进行少批量测试。在测试时：

- 使用 `--limit` 参数限制测试条数，一般设置 10 条即可；

- 串行或低并发进行测试，`--concurrency <=2`；

- 如果少批量测试 5min 内仍未完成，考虑减少测试条数或直接返回给用户测试；

- **一定不要**自己跑全量或高并发，务必在写完脚本并少批量测试完成后要求用户检查。不要自己直接运行

### 注释

在编码并少批量测试完成后，在单文件的最上方添加多行注释，说明以下信息：

- 可配置参数
- 所实现功能以及用到的关键包
- 输入文件所需字段及其含义
- 输出文件字段及其含义


## 调用 LLM

如果需要调用 LLM，以下是一些要求。

- 模型提供商一般都会兼容 openai 接口协议，你应该使用 openai 接口协议来实现对 llm 的调用；

- 从 references/llm_client.json 中选择模型。注意其中的 extra_body 字段要在代码中一起透传；

- 不要自行进行高并发测试。

## 脚本工具

本 skill 配备了一些常用的工具，方便你进行数据分析和编码。

- `scripts/profile_dataframe.py`
  - 用于快速理解表格型数据文件（如 `.csv`、`.json`、`.excel`、`.parquet` 等）的结构；
  - 适合在写脚本前先看 schema、缺失情况、样例值和候选字段角色；
  - stdout 输出 JSON 摘要；详细字段说明看 `uv run scripts/profile_dataframe.py --help`。

- `scripts/ping_openai_client.py`
  - 用于快速验证某个 OpenAI 协议兼容的 LLM endpoint 是否可用；
  - 示例：`uv run --with openai scripts/ping_openai_client.py --client deepseek-chat`，其中可选 client 见 references/llm_client.json
  - stdout 输出 JSON，成功时返回响应摘要，失败时返回结构化错误，便于排障。

如果你在分析数据与编码过程中，认为某种工具或操作非常常用，可以主动向用户建议在本 skill 中抽象封装这类工具，方便你日后的开发。

## 参考文档

以下提供一些常用文档的获取方式，你可以按需读取。

- `references/llm_client.json`
  - 存放常用 LLM client 的预置配置；
  - 字段包括 `base_url`、`model`、`env_key`；
  - 需要快速验证某个 provider 是否可用时，优先读取这份配置并配合 `scripts/ping_openai_client.py --client <name>` 使用。

- `references/zhihu_service_docs/overview.md`
  - 存放知乎服务接口文档总览，默认服务地址是 `http://localhost:6199`；
  - 当任务需要根据知乎 URL、内容 ID、评论 ID、视频 ID 拉取元数据或下载链接时，优先从这里进入；
  - 文档按能力拆成 `base_api.md`、`content_api.md`、`comment_api.md`、`video_api.md`，分别覆盖健康检查、内容查询、评论树查询、视频信息与下载地址查询；
  - 如果只需要确认字段、请求参数、响应结构或接口是否存在，以 `references/zhihu_service_docs/openapi.json` 为最终事实来源，拆分后的 Markdown 仅用于快速阅读。
  - 注意代理问题：如果环境里存在 `http_proxy` / `https_proxy`，但没有配置 `no_proxy` / `NO_PROXY`，那么访问 `127.0.0.1:6199` 这类本地知乎服务时，命令行或 Python 请求可能会被错误地转发到代理服务器，表现为 squid `503`、`ERR_CONNECT_FAIL`、`Connection refused` 等，看起来像本地服务没启动，实际上是请求没有打到本机。 遇到这种情况时，优先检查环境变量；如果确认是本地服务请求，建议显式绕过代理，例如设置 `no_proxy=127.0.0.1,localhost`，或在 Python `requests` 中使用 `session.trust_env = False` 后再请求本地服务。
