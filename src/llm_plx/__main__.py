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
        self.temp_dir = tempfile.TemporaryDirectory()
        self.prompt_file = os.path.join(self.temp_dir.name, "prompt")
        # with open(self.prompt_file, "w") as f:
        #     f.write("")
        self.system_message_file = os.path.join(self.temp_dir.name, "system_message")
        with open(self.system_message_file, "w") as f:
            f.write("You are a helpful AI assistant. You are given files designated by <files> to read and provide context. You are given <conversation_history> to provide what has already occured between you the AI and the User. Do not mention <conversation_history> or <files> in your response. To the best of your ability provide a response to the prompt designationed by <prompt>")
        self.context_file = os.path.join(self.temp_dir.name, "context")
        with open(self.context_file, "w") as f:
            f.write("Context: ")
        self.files_file = os.path.join(self.temp_dir.name, "files")
        # with open(self.files_file, "w") as f:
        #     f.write("")
        self.conversation_history_file = os.path.join(self.temp_dir.name, "conversation_history")
        with open(self.conversation_history_file, "w") as f:
            f.write("")
        self.output_file = os.path.join(self.temp_dir.name, "output")
        # with open(self.output_file, "w") as f:
        #     f.write("")
        self.nvim_path = shutil.which("nvim")
        
        # Get path to the Lua script
        self.lua_script_path = os.path.join(os.path.dirname(__file__), "context_popup.lua")
        self.prompt_script_path = os.path.join(os.path.dirname(__file__), "prompt.vim")
        self.output_script_path = os.path.join(os.path.dirname(__file__), "output.vim")
    
    def run(self):
        try:
            while True:
                result = subprocess.run(
                    [
                        self.nvim_path,
                        "-c", f"let g:prompt_file = '{self.prompt_file}'",
                        "-c", f"let g:files_file = '{self.files_file}'",
                        "-c", f"let g:context_file = '{self.context_file}'",
                        "-c", f"let g:lua_script_path = '{self.lua_script_path}'",
                        "-S", self.prompt_script_path,
                        self.system_message_file,
                    ],
                    stdin=sys.stdin,
                    stdout=sys.stdout,
                )
                if result.returncode != 0:
                    break
                
                # Read content from the files
                with open(self.prompt_file, "r") as f:
                    prompt = f.read().strip()
                with open(self.system_message_file, "r") as f:
                    system_message = f.read().strip()
                with open(self.conversation_history_file, "r") as f:
                    conversation_history = f.read().strip()
                with open(self.files_file, "r") as f:
                    files = f.read().strip()

                context = "<files>\n"
                for file in files.split("\n"):
                    if not os.path.exists(file):
                        print(f"File {file} does not exist. Skipping...", end="", flush=True)
                        continue
                    with open(file, "r") as f:
                        context += f"<filename>{file}</filename>\n"
                        context += f"<filecontent>\n{f.read()}\n</filecontent>\n"
                context += "</files>\n"
                context += f"<conversation_history>\n{conversation_history}\n</conversation_history>\n<prompt>\n{prompt}\n</prompt>"
                with open(self.context_file, "w") as f:
                    f.write(context)
                
                # Query the AI model
                print("Querying AI model...", end="", flush=True)
                try:
                    response, debug_string = ollama_query(self.model, context, system_message, self.host)
                except Exception as e:
                    print(f"Error querying model: {e}")
                    continue
                
                # Create temporary file for output
                with open(self.output_file, "w") as f:
                    f.write(response)
                
                # Display the response in neovim (also include context popup functionality)
                subprocess.run(
                    [
                        self.nvim_path,
                        "-c", f"let g:context_file = '{self.context_file}'",
                        "-c", f"let g:lua_script_path = '{self.lua_script_path}'",
                        "-S", self.output_script_path,
                        self.output_file,
                    ],
                    stdin=sys.stdin,
                    stdout=sys.stdout,
                )
                with open(self.conversation_history_file, "a") as f:
                    f.write(f"User: {prompt}\nAI: {response}\n")
                # NOTE: Temp
                # with open(self.conversation_history_file, "r") as conversation_history:
                #     with open(self.context_file, "w") as f:
                #         f.write(f"<conversation_history>\n{conversation_history.read()}</conversation_history>\n")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.temp_dir.cleanup()

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
