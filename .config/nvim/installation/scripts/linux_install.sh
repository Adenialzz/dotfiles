
set -e -u

# install the newest neovim
if [ -z `which nvim` ]; then
    sudo apt install software-properties-common -y
    sudo add-apt-repository ppa:neovim-ppa/stable  
    sudo apt update
    # sudo apt-cache madison neovim		# 这个命令可以查看某个包可安装的版本
    sudo apt install neovim -y
fi

INSTALL_SCRIPT_DIR=$(cd $(dirname $0);pwd)
PLUG_DIR=${XDG_DATA_HOME:-$HOME}/.local/share/nvim/site/autoload/

if [ ! -f ${PLUG_DIR}/plug.vim ]; then
    mkdir -p ${PLUG_DIR}
    mv ${INSTALL_SCRIPT_DIR}/plug.vim ${PLUG_DIR}
fi

