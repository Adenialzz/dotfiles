# Codex 配置

运行仓库根目录的 `bash scripts/run.sh`，将本目录的 `config.toml`、`deepseek.config.toml`、`deepseek-models.json`、`hooks.json` 和 `hooks/` 下的脚本软链接到 `~/.codex/` 对应位置。仓库保存源文件，已有本地文件会先备份再替换为软链接。

## 长任务提醒

`hooks.json` 在 `UserPromptSubmit` 和 `Stop` 时调用 `hooks/long_task_reminder.py`。默认任务耗时达到 10 分钟，且完成后 5 分钟内同一会话没有新指令时，通过飞书机器人发送提醒；新指令会取消该会话尚未发送的提醒。

启动 Codex 前，在本机私有 Shell 配置或仓库未纳入版本控制的 `.env` 中导出 `FEISHU_WEBHOOK`。提醒包含工作目录与最后回复的前 1000 个字符。可通过 `CODEX_REMINDER_TASK_SECONDS` 和 `CODEX_REMINDER_IDLE_SECONDS` 调整任务耗时阈值和等待时间，单位为秒，默认分别为 `600` 和 `300`。

Hook 命令使用系统 `python3`，脚本仅依赖标准库。运行状态保存在 `~/.codex/reminder-state/`，日志保存在 `~/.codex/reminder.log`，均不迁入仓库。

## 选择模型后端

```sh
codex                              # 默认官方配置，使用已有登录
codex -p deepseek                  # DeepSeek V4 Pro，high 推理
codex -p deepseek -m deepseek-flash # DeepSeek Flash，支持图片输入
codex -p deepseek resume           # 使用 DeepSeek 配置恢复会话
```

当前版本的 `-p deepseek` 加载 `~/.codex/deepseek.config.toml`，覆盖基础配置中的同名字段，只影响本次启动。需要支持 `<name>.config.toml` profile 文件的 Codex 版本，可通过 `codex --help` 核对 `--profile` 说明。

DeepSeek 配置通过 `env_key` 读取启动终端中的环境变量：

```sh
export DEEPSEEK_API_KEY='你的 API Key'
codex -p deepseek
```

如需持久化，请将变量导出放入本机私有 shell 配置，不要将真实 Key 提交到仓库。此 profile 关闭内置网页搜索，保留基础配置中的其他设置，不会切换已打开的桌面端会话。

Profile 只覆盖本次配置，不隔离登录凭据。DeepSeek 通过 provider 的 `env_key` 认证，无需设置 `forced_login_method = "api"`；该设置会在已有 ChatGPT 登录时触发登出，因此不要在此 profile 或基础配置中添加它。

如果旧版配置已导致登出，先更新此 profile，再运行不带 profile 的 `codex login` 恢复官方登录。

`deepseek-models.json` 来自 DeepSeek 接入文档，保留其模型元数据及 agent 提示词；更新时从该文档同步。

- [Codex 官方文档](https://developers.openai.com/codex/)
- [Codex 配置参考](https://learn.chatgpt.com/docs/config-file/config-reference)
- [DeepSeek 接入文档](https://api-docs.deepseek.com/quick_start/agent_integrations/codex/)
