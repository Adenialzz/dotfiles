---
title: "Codex 后台服务未继承新终端的环境变量"
date: "2026-09-28"
project: "dotfiles"
module: "codex-hooks"
type: "bug_debugging"
status: "draft"
severity: "low"
tags: ["codex", "hooks", "daemon", "environment"]
tech_stack: ["python", "bash", "codex"]
environment: ["linux", "local", "pid-daemon"]
root_cause_type: "process"
reusable: true
verified: false
source: "本次会话中的进程、环境变量、Unix socket 和 reminder 日志检查"
related: ["../../ai/codex/README.md"]
---

# Codex 后台服务与环境变量

## 摘要

终端中 `export` 的变量进入了新启动的 Codex CLI，但没有进入早已运行的后台 `app-server`。因此，重新打开 CLI 并不等于刷新执行 hook 的后台环境。当前通过 hook 主动读取 `~/.codex/codex.env` 解决配置来源问题。

## 背景

排查时 CLI 版本为 `0.157.1`，后台服务版本为 `0.158.0`，daemon 使用 `pid` 后端。提醒脚本读取 `FEISHU_WEBHOOK`、`CODEX_REMINDER_TASK_SECONDS` 和 `CODEX_REMINDER_IDLE_SECONDS`。

## 问题现象

终端设置变量后重新进入 Codex，提醒 hook 仍使用默认阈值，早期日志中 `feishu_configured=False`。增加配置文件读取后，日志可以显示文件中的阈值及 `feishu_configured=True`。

## 影响范围

本次涉及长任务提醒 hook。其他由共享后台服务创建的进程也可能遇到相同问题，但需要单独验证其环境传递方式。

## 根因

已确认 CLI 与后台服务的环境不同，且 CLI 通过 Unix socket 复用了旧服务：

| 当时的进程 | 启动时间（UTC） | 三个提醒变量 |
|---|---|---|
| CLI，PID `745547` | 2026-09-28 09:44 | 均存在且非空 |
| app-server，PID `712692` | 2026-09-28 05:57 | 均不存在 |
| daemon 管理进程，PID `668319` | 2026-09-27 02:50 | 均不存在 |

环境变量在创建子进程时传递；通过 socket 连接已有服务不会自动更新服务的环境。当前证据支持这一原因，但没有直接采集 hook 在加载配置文件之前的原始环境，因此保守保留 `draft` 状态。

## 排查过程

1. 检查进程关系及 `/proc/<pid>/environ`，仅输出变量是否存在，不输出 Webhook。
2. 用 `lsof -nP +E -a -U -p 712692,745547` 确认 CLI 与旧 app-server 的 socket 连接；当前会话命令也由该 app-server 创建。
3. 检查 `shell_environment_policy`：`inherit = "all"`，显式排除项未匹配这三个变量。
4. 对照提醒启动日志，确认配置文件加载后阈值和 `feishu_configured` 发生变化。

此前将现象称为“继承不稳定”不够准确；已观察到的具体差异是新 CLI 与旧后台服务持有不同环境。

## 解决方案

当前方案：源文件放在 `ai/codex/codex.env`，软链接到 `~/.codex/codex.env`。hook 启动时主动读取，并用 `os.environ.setdefault()` 加载，优先级为：**hook 进程已有环境变量 > 配置文件 > 脚本默认值**。

文件修改在下一次 hook 启动时读取；已经启动的后台等待进程保留原配置。文件已被 Git 忽略。目前只有 reminder hook 显式加载它，Codex 主进程不会因文件存在而自动加载。

如果需要按终端环境启动，可在退出当前 CLI 后使用 `codex --no-daemon resume --last`。本机帮助已确认支持 `--no-daemon`，官方[更新说明](https://learn.chatgpt.com/docs/changelog)也说明其用途是绕过共享后台服务；本次未实际切换会话验证。

## 验证方式

隔离测试已验证配置文件读取、环境变量优先级和新软链接路径。实际运行可查看 `~/.codex/reminder.log` 的 `task_threshold`、`idle_threshold` 和 `feishu_configured`，避免打印 Webhook 本身。

## 复用条件

适用于 CLI 复用常驻后台服务、配置依赖启动环境且新变量未传给后台进程的情况。先核对实际进程关系及变量是否存在，再复用结论。

## 不适用情况

不直接适用于独立运行的 CLI、显式转发环境变量的客户端，或由其他服务管理器启动的场景。变量已经存在但值错误、空值或配置解析错误，也需要另行排查。

## 预防措施

区分 CLI 环境、后台服务环境和 hook 环境；配置加载日志只记录阈值及敏感值是否存在。不要把“重开 CLI”视为“重启后台服务”。

## 待补充信息

尚未直接采集 hook 加载文件前的环境，也未验证 `--no-daemon` 或 daemon 重启后的端到端环境传递。本次没有重启共享后台服务。
