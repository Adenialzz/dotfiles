
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
│   │   ├── deepseek.config.toml # DeepSeek profile
│   │   ├── deepseek-models.json # DeepSeek 模型目录
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
│   ├── init.sh                 # Shell 统一加载入口
│   ├── bin/                    # 链接到 ~/.config/.mbin
│   ├── funcs.sh                # shell 函数
│   ├── settings.sh             # shell 设置
│   └── vi.zsh                  # zsh vi mode 配置
├── tmux/                       # tmux 配置
│   └── .tmux.conf              # tmux 基础配置
├── .example.env                # 环境变量示例
├── scripts/run.sh              # 安装和软链接脚本
└── README.md                   # 仓库说明
```

## 快速开始

### 0. 安装依赖

```bash
bash scripts/install.sh
```

脚本会按系统安装 `jq`、`codex`、`claude code`、`neovim`、`tmux`。

### 1. 配置环境变量（可选）

需要代理或 API Key 时，复制 `.example.env` 为 `.env` 并填写所需变量：

```bash
cp .example.env .env
# 编辑 .env
```

安装不依赖 `.env`，未使用的变量可以留空。

### 2. 运行配置脚本

```bash
bash scripts/run.sh
```

脚本会自动：
- 链接 Claude Code / Codex 相关配置到用户目录
- 将包含 `SKILL.md` 的每个 skill 目录链接到 `~/.claude/skills/` 和 `~/.agents/skills/`
- 链接 Zed 配置、`uv/uv.toml` 和 `shell/bin`
- 链接 tmux 配置到 `~/.tmux.conf`
- 在 Bash / Zsh 的 rc 文件中维护一行 `source "仓库路径/shell/init.sh"`

重复运行会跳过正确的链接和已有入口。迁移旧版生成的 Shell 初始化块前会备份 rc 文件；将旧 skill 目录改为软链接前也会备份原目录，其他工具安装的 skill 保留。skill 内部增删文件立即生效，新增整个 skill 时需重跑安装。

### 3. 应用 shell 配置

```bash
source ~/.zshrc  # 或 ~/.bashrc
```

## .env 文件说明

`.env` 文件用于存放敏感信息和个性化配置，不会被提交到 git。`shell/init.sh` 在文件存在时加载并导出其中的变量；文件缺失或变量为空不会阻止安装。所需变量由实际使用它的功能检查，例如 DeepSeek 启动时需要 `DEEPSEEK_API_KEY`。

`.env` 使用 Shell 赋值语法，例如 `DEEPSEEK_API_KEY='你的 API Key'`。修改后重新加载 Shell 配置即可。新增 alias 或函数的加载语句统一放在 `shell/init.sh`，无需修改 rc 文件。

## 说明文档

- `ai/claude/README.md`：Claude Code 配置说明
- `ai/codex/README.md`：Codex 配置说明

## Key Files

| 文件 | 用途 |
|------|------|
| `scripts/run.sh` | 安装脚本，负责创建软链接并维护 Shell 加载入口 |
| `shell/init.sh` | 加载可选 `.env`、Shell 设置、alias 和函数 |
| `shell/alias/` | 按主题拆分的 shell 别名配置 |
| `shell/funcs.sh` | shell 函数 |
| `shell/settings.sh` | shell 环境设置 |
| `tmux/.tmux.conf` | tmux 基础配置 |
| `config/nvim/init.vim` | Neovim 配置 |
| `ai/prompts/coding_system.md` | Claude / Codex 共享系统提示词 |
| `.example.env` | 环境变量模板 |
