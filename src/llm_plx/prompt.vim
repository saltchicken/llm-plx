set nonumber norelativenumber wrap
resize 20
execute "split " . g:prompt_file
wincmd k
execute "vsplit " . g:files_file
FileSelector
wincmd j
command! Send wa | qall | cquit 0
command! Exit cquit 1
execute "let g:llm_plx_context_file = '" . g:context_file . "' | luafile " . g:lua_script_path
