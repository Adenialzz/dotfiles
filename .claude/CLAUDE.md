# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

这是一个 dotfiles 仓库，包含用户的系统配置文件。

## Architecture

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
│   ├── pip/                    # pip 配置
│   └── run_config.sh          # 安装配置脚本
└── README.md
```

## Key Files

| 文件 | 用途 |
|------|------|
| `.config/run_config.sh` | 将配置链接到 shell rc 文件的安装脚本 |
| `.config/shell/aliases.sh` | 包含常用别名（git、conda、nvim 等） |
| `.config/nvim/init.vim` | Neovim 配置，使用 vim-plug 管理插件 |

## Common Tasks

**应用配置：**
```bash
cd ~/.config
bash run_config.sh
```

**注意：** `run_config.sh` 会覆盖当前的 shell rc 文件（`~/.zshrc` 或 `~/.bashrc`）。
