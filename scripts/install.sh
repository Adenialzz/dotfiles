#!/bin/bash

set -eu

install_macos() {
  if ! command -v brew >/dev/null 2>&1; then
    echo "Homebrew 未安装，请先安装 Homebrew"
    exit 1
  fi

  brew update
  brew install jq neovim tmux node
  npm install -g @openai/codex @anthropic-ai/claude-code
}

install_ubuntu() {
  if [ ! -f /etc/os-release ]; then
    echo "无法识别当前 Linux 发行版"
    exit 1
  fi

  . /etc/os-release
  if [ "${ID:-}" != "ubuntu" ]; then
    echo "当前仅支持 Ubuntu"
    exit 1
  fi

  sudo apt-get update
  sudo apt-get install -y jq neovim tmux nodejs npm
  sudo npm install -g @openai/codex @anthropic-ai/claude-code
}

case "$(uname -s)" in
  Darwin)
    install_macos
    ;;
  Linux)
    install_ubuntu
    ;;
  *)
    echo "当前系统不支持: $(uname -s)"
    exit 1
    ;;
esac
