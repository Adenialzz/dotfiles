set -e -u

function version_lt() { test "$(printf '%s\n' "$@" | sort -V | head -n 1)" = "$1"; }

COC_HOME=${HOME}/.local/share/nvim/plugged/coc.nvim 

if [ -z `which node` ] || version_lt `node -v` "v14.14.0"; then  # node 版本小于14.14.0，需更新
	if [ -z `which nvm` ]; then
		curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.2/install.sh | bash
		source $HOME/.`basename ${SHELL}`rc
	fi
	nvm install 16
	nvm use 16
fi

yarn --cwd ${COC_HOME} install 
yarn --cwd ${COC_HOME} build
