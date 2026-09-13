
case ":$PATH:" in
  *":$HOME/.config/.mbin:"*) ;;
  *) export PATH="$PATH:$HOME/.config/.mbin" ;;
esac

set -o vi
