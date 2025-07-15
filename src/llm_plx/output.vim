set filetype=markdown
set nonumber norelativenumber wrap
execute "let g:llm_plx_context_file = '" . g:context_file . "' | luafile " . g:lua_script_path
