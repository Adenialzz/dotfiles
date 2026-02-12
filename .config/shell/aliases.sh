alias c="clear"
alias nv="watch -n -0.5 nvidia-smi"
alias lt="ls -lrt"
alias JJ="conda activate JJ_env"
alias py="python"
alias sc="scala"
alias vi="nvim"
alias act="conda activate"
alias pips-thu="pip install -i https://pypi.tuna.tsinghua.edu.cn/simple"
alias hss="history | grep"
alias spo="source $HOME/.config/.mbin/set-proxy"

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
