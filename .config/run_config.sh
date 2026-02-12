RCFILE=$HOME/.`basename ${SHELL}`rc
cat << EOF > $RCFILE
source ~/.config/misc/settings.sh
source ~/.config/misc/aliases.sh
if [ `basename $SHELL` = zsh ]; then
	source ~/.config/zsh/vi.zsh
fi
EOF
