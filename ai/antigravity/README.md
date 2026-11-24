# Antigravity 配置

运行仓库根目录的 `bash scripts/run.sh`，会自动完成以下配置软链接：

- `ai/prompts/coding_system.md` -> `~/.gemini/config/GEMINI.md`（全局规则）
- `ai/mcp_config.json` -> `~/.gemini/config/mcp_config.json`（全局 MCP 服务）
- `ai/antigravity/hooks.json` -> `~/.gemini/config/hooks.json`（生命周期 Hooks）
- `ai/antigravity/hooks/` -> `~/.gemini/config/hooks/`（Hook 脚本）
- `ai/skills/` -> `~/.agents/skills/`（已由共享 skills 流程自动链接）

## Hooks 说明

### 1. `enforce-uv-python` (`PreToolUse`)

在包含 `pyproject.toml` 且系统已安装 `uv` 的项目中，拦截直接调用 `python`、`pytest`、`pip` 的 `run_command` 操作，提示改用 `uv run` / `uv add` / `uv pip`。

### 2. `long-task-reminder` (`PreInvocation` / `Stop`)

当单轮任务耗时达到阈值（默认 600 秒），且完成后在空闲阈值（默认 300 秒）内没有新指令时，通过飞书机器人发送提醒。

- 环境变量复用顺序：当前进程环境变量 > `~/.codex/codex.env`。
- 支持的变量：`FEISHU_WEBHOOK`、`AGY_REMINDER_TASK_SECONDS`（回退 `CODEX_REMINDER_TASK_SECONDS`）、`AGY_REMINDER_IDLE_SECONDS`（回退 `CODEX_REMINDER_IDLE_SECONDS`）。
- 运行状态与日志保存在 `~/.gemini/config/reminder-state/` 和 `~/.gemini/config/reminder.log`。

## 关于 `settings.json`

`~/.gemini/antigravity-cli/settings.json` 包含本机登录状态与 UI/运行偏好，默认不纳入 dotfiles 软链接管理；如需在特定项目或会话临时覆盖，可使用 `agy --settings`。
