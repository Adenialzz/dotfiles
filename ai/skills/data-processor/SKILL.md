---
name: data-processor
description: 当用户要求编写单文件 python 数据处理脚本时使用此 skill。如果你看到某个 python 脚本开头有 `Authored by {MODEL_NAME} with batch-processor skill` 说明那个文件是由本 skill 生成的，你也需要参考本 skill 的要求。
---

# Data Processor

用户会将一些简单的 Python 单文件数据处理脚本编码任务交给你，以下是一些具体要求，请按照要求实现。如果你认为用户给定的任务与下列要求存在冲突或方案不合理之处，主动提出并于用户探讨合理方案。

## 批量数据处理基础要求

### 基础参数选项

一般来说，在编写批量数据处理脚本时，你的实现需要支持以下基础参数选项：

- 输入文件和输出文件，分别用 `--input-path`, `-i` 和 `--output-path`, `-o` 来指定；

- 如果有必要（比如涉及接口调用等），必须支持并发请求，并提供 `--concurrency`, `-con` 参数来控制并发度。简单的数据处理，不需要支持并发。

- 支持设置测试条数 `--limit`

- 支持进度条显示（比如用 tqdm），默认开启进度条显示，并提供禁用选项 `--disable-progress-bar`

除了以上基础批量数据处理参数选项之外，你应该根据具体任务，支持其他有必要的参数选项。比如需要调用 llm 时，需要支持 `--client` 。

### 错误处理

你应该在所有可能出错的地方（如模型请求、内容 RPC 请求等）添加错误处理，确保主进程不会因为某一行的偶然失败而中断，并将错误信息输出到 `error` 字段。

### 少批量测试

在编写完批量数据处理脚本后，需要你自己先进行少批量测试。在测试时：

- 使用 `--limit` 参数限制测试条数，一般设置 10 条即可；

- 串行或低并发进行测试，`--concurrency <=2`；

- 如果少批量测试 5min 内仍未完成，考虑减少测试条数或直接返回给用户测试；

- **一定不要**自己跑全量或高并发，务必在写完脚本并少批量测试完成后要求用户检查。不要自己直接运行

### 依赖

使用 PEP 723 来通过元数据指定单文件 Python 脚本的依赖，如：

```python
# /// script
# dependencies = [
#   "openai",
#   "requests"
# ]
# ///
```

### 注释

在编码并少批量测试完成后，在单文件的第一行署名 `Authored by {YOUR_MODEL_NAME} with batch-processor skill`，其中 `{YOUR_MODEL_NAME}` 填上你真实的模型名。

然后在署名后，添加多行注释，说明以下信息：

- 可配置参数
- 所实现功能以及用到的关键包
- 输入文件所需字段及其含义
- 输出文件字段及其含义

## 参考

### 调用 LLM

如果需要调用 LLM，参考 `references/llm.md` 中的要求。

### 本地离线 vLLM

如果用户要写单机、本地、离线的 vLLM 批处理脚本，尤其是图片多模态批量推理，参考 `references/local_vllm.md`。

### 召回检索

如果涉及召回检索，参考 `references/recall.md` 中的要求。

### 相关工具

- 当需要先理解陌生的表格型数据文件（如 csv、tsv、txt、Excel、parquet、json/jsonl、feather、pickle等），使用 `profile-dataframe` skill。

- 当需要获取知乎文章内容、视频下载链接、评论信息等时，使用 `zhihu-service` skill。

### 脚本工具

本 skill 配备了一些常用的工具，方便你进行数据分析和编码。

- `scripts/ping_openai_client.py`
  - 用于快速验证某个 OpenAI 协议兼容的 LLM endpoint 是否可用；
  - 示例：`uv run --with openai scripts/ping_openai_client.py --client deepseek-chat`，其中可选 client 见 `references/llm_client.json`
  - stdout 输出 JSON，成功时返回响应摘要，失败时返回结构化错误，便于排障。

如果你在分析数据与编码过程中，认为某种工具或操作非常常用，可以主动向用户建议在本 skill 中抽象封装这类工具，方便你日后的开发。
