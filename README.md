
# My Dotfiles

个人系统配置文件仓库。

## 目录结构

```
dotfiles/
├── .config/                    # 主要配置目录
│   ├── shell/                  # shell 配置
│   │   ├── aliases.sh         # 命令别名
│   │   ├── funcs.sh           # shell 函数
│   │   └── settings.sh        # shell 设置
│   ├── zsh/                    # zsh 特定配置
│   ├── nvim/                   # Neovim 配置
│   ├── conda/                  # Conda 配置
│   └── pip/                    # pip 配置
├── .env                        # 环境变量（需要自行创建）
├── .example.env                # 环境变量示例
├── run_config.sh               # 安装配置脚本
└── README.md
```

## 快速开始

### 1. 配置环境变量

首先复制 `.example.env` 为 `.env` 并填写所有变量：

```bash
cp .example.env .env
# 编辑 .env 文件，填写所有空变量
```

**重要**：`.env` 文件中所有 `export` 的变量都必须填写值，否则 `run_config.sh` 会报错退出。

### 2. 运行配置脚本

```bash
bash run_config.sh
```

脚本会自动：
- 检查并加载 `.env` 文件（确保无空变量）
- 链接配置文件到相应位置
- 配置 shell rc 文件

### 3. 应用 shell 配置

```bash
source ~/.zshrc  # 或 ~/.bashrc
```

## .env 文件说明

`.env` 文件用于存放敏感信息和个性化配置，不会被提交到 git。必须包含所有在 `.example.env` 中定义的变量，且不能留空。

`run_config.sh` 会在执行前检查 `.env` 文件：
- 如果文件不存在 → 报错退出
- 如果存在空变量 → 报错退出并显示哪些变量为空
- 所有变量都有值 → source 加载并继续执行

## Key Files

| 文件 | 用途 |
|------|------|
| `run_config.sh` | 将配置链接到 shell rc 文件的安装脚本 |
| `.config/shell/aliases.sh` | 包含常用别名（git、conda、nvim 等） |
| `.config/nvim/init.vim` | Neovim 配置，使用 vim-plug 管理插件 |
| `.example.env` | 环境变量模板 |
