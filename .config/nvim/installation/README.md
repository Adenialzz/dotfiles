# neovim及coc.nvim自动补全初探

> 分享一下笔者自己的 `init.vim`：https://github.com/Adenialzz/nvim （很简单，后面会慢慢更新）
>
> 和大佬的：https://github.com/theniceboy/nvim

## 安装

mac 的话直接 brew 安装：

```shell
# 安装
brew install neovim
# 查看neovim安装路径
brew list nvim

# ubuntu
apt install neovim
```

这里 ubuntu 18.04 直接装的话装到 v0.2.2 ，版本过低，可根据[这篇博客](https://www.jianshu.com/p/83a8d5e52e19)介绍安装新版

```shell
# 如果已经安装老版，先卸载
sudo apt remove neovim -y
sudo apt remove neovim-runtime -y

sudo apt-get install software-properties-common

sudo add-apt-repository ppa:neovim-ppa/stable  
sudo apt-get update
sudo apt-cache madison neovim		# 这个命令可以查看某个包可安装的版本
sudo apt-get install neovim -y

# 需要用到的Python模块
sudo apt-get install python-dev python-pip python3-dev python3-pip
```

习惯了打开 vi/vim 的方式，可以用个 alias 在 `~/.zshrc` 中设置一下：

```shell
alias vi="nvim"
```

## 插件

### vim-plug

*vim-plug* 是一个非常好用的插件管理器，我们先安装它，然后再通过他来安装其他好用的插件。

Unix/Linux 根据 [github 主页](https://github.com/junegunn/vim-plug) 给出的命令安装即可（可能需要走代理）：

```shell
sh -c 'curl -fLo "${XDG_DATA_HOME:-$HOME/.local/share}"/nvim/site/autoload/plug.vim --create-dirs \
       https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim'
```

我们知道 vim 的配置文件是 `vimrc` ，而在 nvim 中，配置文件是 `init.vim` 。

使用 *vim-plug* 安装插件的过程是这样的：

1. 将所需的插件写到 `init.vim` 的如下位置：

   ```vimscript
   call plug#begin()
   " ...
   " 要安装的插件列表
   " ...
   call plug#end()
   ```

   想要安装的 vim 插件可以到 https://vimawesome.com/ 网站去寻找。

2. 打开 neovim，执行：`:PlugInstall` 。其他相关的命令还有 `:PlugStatus `，`:PlugClean`，`:PlugUpdate`。

### coc

*[coc](https://github.com/neoclide/coc.nvim)* 是一个知名的自动补全插件。

在安装完 *vim-plug* 之后，*coc* 的安装就很简单了，就按照我们上面介绍的步骤安装即可，首先去 https://vimawesome.com/ 网站中将 *vim-plug* 安装方式的一行复制到 `init.vim` 上面指定的插件列表处：

```vimscript
call plug#begin()
Plug 'neoclide/coc.nvim', {'branch': 'release'}
call plug#end()
```

然后打开 neovim，执行 `:PluginInstall` 即可。

安装完成后可以用 `:checkhealth` 命令检查各插件（现在我们还只有一个）安装是否正常。

#### 几个可能的报错

1. 提示 node 未安装，安装即可：

   ```shell
   sudo apt update
   sudo apt install nodejs npm
   ```

2. 需要手动安装

   这时可能会报错：

   ```
   neovim [coc.nvim] build/inderx.js not found, please install dependencies and compile coc.nvim : yarn install
   ```

   这时需要到安装目录 `coc.nvim` 中再去手动安装一下：

   ```shell
   cd ~/.vim/bundle/coc.nvim	# for vim
   cd ~/.local/share/nvim/plugged/coc.nvim 	# for neovim
   # 注意不要用 `apt install yarn` 安装，会装到 0.32 的老版本
   npm install yarn@latest -g
   yarn install
   yarn build
   ```

3. `yarn install` 时 报错 node 版本不匹配

   参考[升级node到指定版本](https://www.jianshu.com/p/e6d3f7110a60)

   安装 *n* ，*n* 是 node 版本管理工具

   ```shell
   npm install -g n
   n stable 
   # 会输出：
   #  installing : node-v16.15.1
   #       mkdir : /usr/local/n/versions/node/16.15.1
   #       fetch : https://nodejs.org/dist/v16.15.1/node-v16.15.1-linux-x64.tar.xz
   #     copying : node/16.15.1
   #   installed : v16.15.1 to /usr/local/bin/node
   #      active : v15.12.0 at /usr/local/nvm/versions/node/v15.12.0/bin/node
   node -v
   which node
   
   # 输出：v15.12.0，/usr/local/nvm/versions/node/v15.12.0/bin/node
   # 这时看到已经安装新版本，但是 -v 输出还是老版本，是因为尚未激活，在PATH中将新版本的所处路径放到老版本前面即可
   export PATH=/usr/local/bin:$PATH
   node -v 
   # 输出: v16.15.1
   ```

#### 安装coc拓展

在 *coc* 安装完成之后还不能直接使用，还需要安装对应语言的扩展，如 Python 的 coc.pyright，具体有哪些扩展，可安装 markerplace 查看。

coc 常用命令：

```
CocList extensions	" 列出当前扩展
CocInstall xxx	" 安装某个扩展
...
```

也可以将 coc 的扩展写到 `init.vim` 中，再次打开 neovim 时会自动安装：

```vimscript
let g:coc_global_extensions = [
                \ 'coc-json',
                \ 'coc-vimlsp',
                \ 'coc-pyright'
                \ 'coc-clangd']
```

除此之外，还需要按照作者的推荐（在其 github 首页）修改一下 `init.vim` 文件，来添加一些常用的快捷键（如 Tab 键补全等），建议大家搞懂作者提过的 vimscript 的内容，然后按需选择，添加到自己的 `init.vim` 文件中，这里推荐一个大神的[解读视频](https://www.bilibili.com/video/BV1Ka4y1E7AM) ，供大家参考。

```
CocInstall coc-explorer
```

### auto-pairs

自动补全括号插件，必装：

```vimscript
call plug#begin()
Plug 'jiangmiao/auto-pairs'
call plug#end()
```

### tcomment_vim

[注释插件](https://vimawesome.com/plugin/tcomment)

```
Plug 'tomtom/tcomment_vim'
```

这里介绍最常用的几个键，详情见 https://vimawesome.com/plugin/tcomment

```shell
gcc #注释/反注释一行
gc[motion]	# 注释/反注释motion指定的位置，如gc3j，注释当前行和下两行
V选中+g>	# 注释V可视模型选中的代码段
```

### NERDTree

注意 NERDTree 本身没有设置快捷键，我们自己按照喜好来设置即可。

如：

```shell
nmap <leader>3 :NERDTreeToggle<CR> # 设置 `\3` 为打开/关闭NERDTree
```

常用命令及解释：

|           功能           |    快捷键     |                             解释                             |
| :----------------------: | :-----------: | :----------------------------------------------------------: |
|         新建文件         |      ma       | 在要创建文件的目录中按命令 ma然后键入你要创建的文件名称即可。 |
|         删除文件         |      md       |         在要删除的文件上按命令md然后输入y回车即可。          |
|   移动文件/修改文件名    |      mm       |  在要修改的文件上按命令mm然后输入对应的目录和名称回车即可。  |
| 设置当前目录为项目根目录 |       C       | 在要设置为根目录的目录上按命令C【大写】即可。（刚学vim的时候总是不小心按到u命令把不必要的目录设置成了我的项目根目录，当时一直没找到比较好的解决方案很尴尬只能重启vim解决现在只要按C命令改回来即可） |
|   查看当前文件所在目录   | :NERDTreeFind | 执行命令 :NERDTreeFind 或则在.vimrc中添加 map \<leader\>v :NERDTreeFind\<CR\> 全局使用 \<leader\>v命令(我的是,v)直接显示当前文件所在目录。 |





