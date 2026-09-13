if [ -n "${ZSH_VERSION:-}" ]; then
  DOTFILES_DIR="$(cd "$(dirname "${(%):-%N}")/.." && pwd)"
else
  DOTFILES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fi

if [ -f "$DOTFILES_DIR/.env" ]; then
  case "$-" in
    *a*) source "$DOTFILES_DIR/.env" ;;
    *) set -a; source "$DOTFILES_DIR/.env"; set +a ;;
  esac
fi

source "$DOTFILES_DIR/shell/settings.sh"
source "$DOTFILES_DIR/shell/alias/shell-base.sh"
source "$DOTFILES_DIR/shell/alias/git.sh"
source "$DOTFILES_DIR/shell/alias/tmux.sh"
source "$DOTFILES_DIR/shell/funcs.sh"
source "$DOTFILES_DIR/shell/alias/coding-agents.sh"
if [ -n "${ZSH_VERSION:-}" ]; then
  source "$DOTFILES_DIR/shell/vi.zsh"
fi
unset DOTFILES_DIR
