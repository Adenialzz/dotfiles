
# My .config files

## config

make sure no `.config` file in your home directory
```shell
cd $HOME
git clone git@github.com:Adenialzz/.config.git
```

and 

```shell
cd .config
bash run_config.sh
```

or manually add the following lines to your ~/.zshrc

```shell
source ~/.config/misc/aliases.sh
source ~/.config/misc/settings.sh
if [ `basename $SHELL` = zsh ]; then
	source ~/.config/zsh/vi.zsh
fi
```
