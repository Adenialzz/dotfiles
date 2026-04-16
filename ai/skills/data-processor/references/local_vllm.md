# Local vLLM

用户要写单机、本地、离线的 vLLM 批处理脚本时读这份 reference。重点是图片多模态批量推理，不引入 Ray。

## 默认做法

- 用普通 Python 脚本 + `vllm.LLM`，不要默认上 Ray。
- 用 `argparse` 做 CLI。
- 用 `pandas` 读 `csv/parquet`。
- 用普通批处理循环调用 `LLM.generate(...)`。
- 用分片落盘，不要把全部结果攒在内存里。

## 图片多模态

优先：

- `AutoProcessor.apply_chat_template(...)` 生成 prompt
- 图片读成 `PIL.Image`
- `LLM.generate(...)`
- `multi_modal_data={"image": image}`

不优先：

- base64
- OpenAI 风格 `image_url`
- `LLM.chat()`

原因：直接传 `PIL.Image` 通常更省 CPU 和内存。

## 吞吐优化

本地离线 vLLM 的常见瓶颈是图片准备，不是模型本身。容易低效的写法是：

- 先下载一个 batch
- 再推理一个 batch

这样 GPU 会空闲。

优先做轻量流水线：

- batch 内用 `ThreadPoolExecutor` 并发准备图片
- batch 间用后台线程预取后续 batch
- 主线程专门做 GPU 推理

先不要默认上 `AsyncLLMEngine`；对单机离线脚本，线程池 + 预取通常已经够用。

## 落盘

优先边跑边落盘。

不要：

- 每个推理 batch 一个文件
- 全部结果最后一次性写出

优先：

- 推理按小 batch 跑
- 落盘按更大的 shard 聚合多个 batch

常用默认值：

- `batch_size = 16`
- `write_shard_batches = 32`

## 续跑

优先做 shard 粒度续跑：

- 输出为 `part-000000.parquet` 这类连续分片
- 启动时扫描已有 shard
- 从下一个 shard 对应的位置继续

前提：

- `batch_size` 不变
- `write_shard_batches` 不变

## 单文件脚本

如果用户明确要单文件：

- 用 PEP 723 metadata 声明依赖
- 把少量工具函数直接内联
- 只保留必要依赖

对这类脚本，`argparse` 通常比 `fire` 更稳。

## Data Parallel

离线 DP 不要理解成“只加一个参数”。

在线 `vllm serve` 场景里，`--data-parallel-size` 很直接；但离线 `LLM` 脚本通常还要补：

- 多进程
- 每个 rank 的环境变量
- 手动切分输入数据
- 每个 rank 独立写结果

所以如果用户问离线脚本能不能加 DP，先提醒这通常不是一行参数改动。

## 什么时候换方案

如果需求变成：

- 多机
- 超大规模数据
- 强依赖调度、容错、弹性

这时再考虑 Ray 或其他更重的编排方案。
