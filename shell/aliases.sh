alias c="clear"
alias nv="watch -n -0.5 nvidia-smi"
alias lt="ls -lrth"
alias py="python"
alias sc="scala"
alias vi="nvim"
alias pips-thu="pip install -i https://pypi.tuna.tsinghua.edu.cn/simple"
alias hss="history | grep"

set_proxy="http_proxy=$PROXY_URL https_proxy=$PROXY_URL"
alias pxy="$set_proxy"

# ai coding
alias cc="$set_proxy claude"

alias cx="$set_proxy codex"
alias cxr="$set_proxy codex resume"
alias cxc="$set_proxy codex resume --last"

# git
alias gs="git status"
alias gd="git diff"

RCFILE=$HOME/.`basename ${SHELL}`rc
alias ss="source $RCFILE"

if [ `uname -s` = Darwin ]; then
	alias pss="ps -ax | grep -v "grep" | grep -v "pss" | grep --color=auto"
	alias make="make -j`sysctl -n machdep.cpu.core_count`"
elif [ `uname -s` = Linux ]; then
	alias pss="ps -aux | grep -v "grep" | grep -v "pss" | grep --color=auto"
	alias make="make -j`nproc`"
fi
