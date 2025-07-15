#!/usr/bin/env python3
import os
import sys
import tempfile
import subprocess
from ollama_query import ollama_query
from dotenv import load_dotenv
import time
import shutil

class LLM_PLX():
    def __init__(self, *args, **kwargs):
        self.model = kwargs.get("model", None)
        self.host = kwargs.get("host", None)
        self.prompt_file = tempfile.NamedTemporaryFile(delete=False)
        self.system_message_file = tempfile.NamedTemporaryFile(delete=False)
        with open(self.system_message_file.name, "w") as f:
            f.write("You are a helpful AI assistant.")
        self.context_file = tempfile.NamedTemporaryFile(delete=False)
        self.files_file = tempfile.NamedTemporaryFile(delete=False)
        self.output_file = tempfile.NamedTemporaryFile(delete=False)
        self.nvim_path = shutil.which("nvim")
        
        # Get path to the Lua script
        self.lua_script_path = os.path.join(os.path.dirname(__file__), "context_popup.lua")
    
    def run(self):
        try:
            while True:
                result = subprocess.run(
                    [
                        self.nvim_path,
                        "-c", "set nonumber norelativenumber wrap | resize 20",
                        "-c", f"split {self.prompt_file.name} | wincmd k",
                        "-c", f"vsplit {self.files_file.name} | FileSelector",
                        "-c", "command! Send wa | qall | cquit 0",
                        "-c", "command! Exit cquit 1",
                        "-c", f"let g:llm_plx_context_file = '{self.context_file.name}' | luafile {self.lua_script_path}",
                        self.system_message_file.name,
                    ],
                    stdin=sys.stdin,
                    stdout=sys.stdout,
                )
                if result.returncode != 0:
                    break
                
                # Read content from the files
                with open(self.prompt_file.name, "r") as f:
                    prompt = f.read().strip()
                with open(self.system_message_file.name, "r") as f:
                    system_message = f.read().strip()
                
                # Query the AI model
                print("Querying AI model...", end="", flush=True)
                try:
                    response, debug_string = ollama_query(self.model, prompt, system_message, self.host)
                except Exception as e:
                    print(f"Error querying model: {e}")
                    continue
                
                # Create temporary file for output
                with open(self.output_file.name, "w") as f:
                    f.write(response)
                
                # Display the response in neovim (also include context popup functionality)
                subprocess.run(
                    [
                        self.nvim_path,
                        "-c", f"set nonumber norelativenumber wrap | let g:llm_plx_context_file = '{self.context_file.name}' | luafile {self.lua_script_path}",
                        self.output_file.name,
                    ],
                    stdin=sys.stdin,
                    stdout=sys.stdout,
                )
        finally:
            # Clean up temporary files
            for file in [self.prompt_file.name, self.system_message_file.name, 
                        self.files_file.name, self.context_file.name, 
                        self.output_file.name]:
                try:
                    os.unlink(file)
                except (NameError, OSError):
                    pass

def main():
    env_init()
    model = os.getenv(
        "OLLAMA_MODEL", "hf.co/unsloth/Devstral-Small-2507-GGUF:UD-Q4_K_XL"
    )
    host = os.getenv("OLLAMA_HOST", "localhost")
    llm_plx = LLM_PLX(model=model, host=host)
    llm_plx.run()

def env_init():
    env_path = ".env"
    if not os.path.exists(env_path):
        host = input("Enter OLLAMA_HOST (e.g., http://localhost:11434): ").strip()
        if not host:
            host = "http://localhost:11434"
        with open(env_path, "w") as f:
            f.write(f"OLLAMA_HOST={{host}}\\n")
    load_dotenv()

if __name__ == "__main__":
    main()
