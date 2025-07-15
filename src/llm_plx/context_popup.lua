-- context_popup.lua
-- This script creates a popup window to display context file contents

local M = {}

function M.show_context_popup(context_file_path)
	-- Read the context file
	local file = io.open(context_file_path, "r")
	if not file then
		vim.notify("Context file not found or empty", vim.log.levels.WARN)
		return
	end

	local content = file:read("*all")
	file:close()

	if content == "" or content == nil then
		vim.notify("Context file is empty", vim.log.levels.INFO)
		return
	end

	-- Split content into lines
	local lines = {}
	for line in content:gmatch("[^\r\n]+") do
		table.insert(lines, line)
	end

	-- Add empty line if no lines found
	if #lines == 0 then
		lines = { "" }
	end

	-- Calculate popup dimensions (80% of screen)
	local width = math.floor(vim.o.columns * 0.8)
	local height = math.floor(vim.o.lines * 0.8)

	-- Calculate position to center the popup
	local row = math.floor((vim.o.lines - height) / 2)
	local col = math.floor((vim.o.columns - width) / 2)

	-- Create a buffer for the popup
	local buf = vim.api.nvim_create_buf(false, true)
	vim.api.nvim_buf_set_lines(buf, 0, -1, false, lines)

	-- Set buffer options
	vim.api.nvim_buf_set_option(buf, "bufhidden", "wipe")
	vim.api.nvim_buf_set_option(buf, "filetype", "text")
	vim.api.nvim_buf_set_option(buf, "modifiable", false)

	-- Window options
	local opts = {
		relative = "editor",
		width = width,
		height = height,
		row = row,
		col = col,
		style = "minimal",
		border = "rounded",
		title = " Context ",
		title_pos = "center",
	}

	-- Create the popup window
	local win = vim.api.nvim_open_win(buf, true, opts)

	-- Set window-specific options
	vim.api.nvim_win_set_option(win, "wrap", true)
	vim.api.nvim_win_set_option(win, "number", false)
	vim.api.nvim_win_set_option(win, "relativenumber", false)
	vim.api.nvim_win_set_option(win, "cursorline", true)

	-- Set up key mappings to close the popup
	local keymaps = {
		{ "n", "q", "<cmd>close<cr>", { noremap = true, silent = true } },
		{ "n", "<Esc>", "<cmd>close<cr>", { noremap = true, silent = true } },
		{ "n", "<CR>", "<cmd>close<cr>", { noremap = true, silent = true } },
	}

	for _, keymap in ipairs(keymaps) do
		vim.api.nvim_buf_set_keymap(buf, keymap[1], keymap[2], keymap[3], keymap[4])
	end

	-- Auto-close when leaving the buffer
	vim.api.nvim_create_autocmd("BufLeave", {
		buffer = buf,
		callback = function()
			if vim.api.nvim_win_is_valid(win) then
				vim.api.nvim_win_close(win, true)
			end
		end,
		once = true,
	})
end

-- Create the command
vim.api.nvim_create_user_command("Context", function()
	-- Get the context file path from a global variable set by Python
	local context_file = vim.g.llm_plx_context_file
	if context_file then
		M.show_context_popup(context_file)
	else
		vim.notify("Context file path not set", vim.log.levels.ERROR)
	end
end, {})

return M
