" Plugins
let g:plug_url_format = 'git@github.com:%s.git'
call plug#begin()
Plug 'neoclide/coc.nvim'
Plug 'scrooloose/nerdtree'
Plug 'jiangmiao/auto-pairs'
Plug 'tomtom/tcomment_vim'
Plug 'junegunn/vim-easy-align'
call plug#end()
unlet g:plug_url_format
" Plugins END

" General Settings

" set relativenumber " set rnu/nornu
set number " set nu/nonu
set autoindent
set tabstop=4
set softtabstop=4
set shiftwidth=4
set foldmethod=indent
set foldlevelstart=99
" set foldmethod="expr"
" set foldexpr="nvim_treesitter#foldexpr()"
" set foldenable=false
" noremap se :set splitbelow<CR>:split<CR>
noremap <LEADER>/ :set splitbelow<CR>:split<CR>:res +10<CR>:term<CR>

" remove highlights after search
noremap <LEADER><LEADER><CR> :noh<CR>  

" General Settings End

" vim-terminal 
" let g:terminal_key = "C-="
" vim-terminal END

" NERDTree Settings
nmap <leader>3 :NERDTreeToggle<CR>
" NERDTree Settings END

" COC Configure
let g:coc_global_extensions = [
		\ 'coc-json',
		\ 'coc-vimlsp',
		\ 'coc-pyright',
		\ 'coc-clangd',
		\ 'coc-metals']
set updatetime=300
set shortmess+=c

inoremap <silent><expr> <TAB>
      \ pumvisible() ? "\<C-n>" :
      \ CheckBackspace() ? "\<TAB>" :
      \ coc#refresh()
inoremap <expr><S-TAB> pumvisible() ? "\<C-p>" : "\<C-h>"

function! CheckBackspace() abort
  let col = col('.') - 1
  return !col || getline('.')[col - 1]  =~# '\s'
endfunction

" for easy align
" Start interactive EasyAlign in visual mode (e.g. vipga)
xmap ga <Plug>(EasyAlign)

" Start interactive EasyAlign for a motion/text object (e.g. gaip)
nmap ga <Plug>(EasyAlign)



" COC Configure END

" TreeSitter Configure
" TreeSitter Configure END

" keymap
nnoremap <C-q> 0
nnoremap <C-e> $
nnoremap <C-k> 5k
nnoremap <C-j> 5j

