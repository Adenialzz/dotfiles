
# My Dotfiles

个人系统配置文件仓库，包含 AI 工具、Shell 和编辑器相关配置。

## 目录结构

```text
dotfiles/
├── ai/                         # AI 工具相关配置
│   ├── claude/                 # Claude Code 配置
│   │   ├── README.md           # Claude 配置说明
│   │   └── settings.json       # Claude settings
│   ├── codex/                  # Codex 配置
│   │   ├── README.md           # Codex 配置说明
│   │   ├── config.toml         # Codex 主配置
│   │   └── rules/              # Codex rules
│   ├── prompts/                # 共享 prompts
│   │   └── coding_system.md    # Claude / Codex 共享 system prompt
│   ├── skills/                 # 可复用 skills
│   │   ├── blog-reviewer/      # 博文审阅 skill
│   │   ├── consolidate/        # 内容整合 skill
│   │   ├── data-processor/     # 数据处理 skill
│   │   ├── paper-reader/       # 论文阅读 skill
│   │   ├── plot/               # 绘图 skill
│   │   ├── prompt-refiner/     # Prompt 优化 skill
│   │   ├── rebuild-docs/       # 文档重建 skill
│   │   └── rfc-reviewer/       # RFC 审阅 skill
│   └── mcp_config.json         # MCP 配置
├── config/                     # 用户配置文件
│   └── nvim/                   # Neovim 配置
├── shell/                      # Shell 配置
│   ├── alias/                  # 命令别名
│   │   ├── shell-base.sh       # 基础别名
│   │   ├── git.sh              # Git 别名
│   │   ├── tmux.sh             # tmux 别名
│   │   └── coding-agents.sh    # Claude / Codex 别名
│   ├── funcs.sh                # shell 函数
│   ├── settings.sh             # shell 设置
│   └── vi.zsh                  # zsh vi mode 配置
├── tmux/                       # tmux 配置
│   └── .tmux.conf              # tmux 基础配置
├── .example.env                # 环境变量示例
├── run_config.sh               # 安装和软链接脚本
└── README.md                   # 仓库说明
```

## 快速开始

### 0. 安装依赖

```bash
bash scripts/install.sh
```

脚本会按系统安装 `jq`、`codex`、`claude code`、`neovim`、`tmux`。

### 1. 配置环境变量

先复制 `.example.env` 为 `.env` 并填写变量值：

```bash
cp .example.env .env
# 编辑 .env
```

`run_config.sh` 会检查 `.env` 中的每个变量是否为空；如果存在空值，会直接退出。

### 2. 运行配置脚本

```bash
bash run_config.sh
```

脚本会自动：
- 检查并加载 `.env` 文件
- 链接 Claude Code / Codex 相关配置到用户目录
- 链接 tmux 配置到 `~/.tmux.conf`
- 追加 shell 初始化配置到当前 shell 的 rc 文件
- 处理仓库中的配置文件软链接

### 3. 应用 shell 配置

```bash
source ~/.zshrc  # 或 ~/.bashrc
```

## .env 文件说明

`.env` 文件用于存放敏感信息和个性化配置，不会被提交到 git。必须包含所有在 `.example.env` 中定义的变量，且不能留空。

`run_config.sh` 会在执行前检查 `.env` 文件：
- 如果文件不存在 → 报错退出
- 如果存在空变量 → 报错退出并显示哪些变量为空
- 所有变量都有值 → 加载并继续执行

## 说明文档

- `ai/claude/README.md`：Claude Code 配置说明
- `ai/codex/README.md`：Codex 配置说明

## Key Files

| 文件 | 用途 |
|------|------|
| `run_config.sh` | 安装脚本，负责检查 `.env`、创建软链接并追加 shell 配置 |
| `shell/alias/` | 按主题拆分的 shell 别名配置 |
| `shell/funcs.sh` | shell 函数 |
| `shell/settings.sh` | shell 环境设置 |
| `tmux/.tmux.conf` | tmux 基础配置 |
| `config/nvim/init.vim` | Neovim 配置 |
| `ai/prompts/coding_system.md` | Claude / Codex 共享系统提示词 |
| `.example.env` | 环境变量模板 |
