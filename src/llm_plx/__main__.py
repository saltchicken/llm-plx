#!/usr/bin/env python3
import os
import sys
import tempfile
import subprocess
from ollama_query import ollama_query
from dotenv import load_dotenv
import time


def main():
    # Load environment variables from .env
    load_dotenv()

    # Get model and host from environment or use defaults
    model = os.getenv(
        "OLLAMA_MODEL", "hf.co/unsloth/Devstral-Small-2507-GGUF:UD-Q4_K_XL"
    )
    host = os.getenv("OLLAMA_HOST", "localhost")

    # Create temporary files
    prompt_file = tempfile.NamedTemporaryFile(delete=False)
    system_message_file = tempfile.NamedTemporaryFile(delete=False)
    context_file = tempfile.NamedTemporaryFile(delete=False)
    with open(system_message_file.name, "w") as f:
        f.write("You are a helpful AI assistant.")

    try:
        while True:
            nvim_path = subprocess.check_output(["which", "nvim"], text=True).strip()
            # nvim_path = "/opt/nvim-linux-x86_64/bin/nvim"
            result = subprocess.run(
                [
                    nvim_path,
                    "-c",
                    "set nonumber norelativenumber wrap",
                    "-c",
                    "resize 20",
                    "-c",
                    f"split {prompt_file.name}",
                    "-c",
                    "wincmd k",
                    "-c",
                    f"vsplit {context_file.name}",
                    "-c",
                    "FileSelector",
                    "-c",
                    "wincmd j",
                    "-c",
                    "command! Send wa | qall | cquit 0",
                    "-c",
                    "command! Exit cquit 1",
                    system_message_file.name,
                ],
                stdin=sys.stdin,
                stdout=sys.stdout,
            )

            if result.returncode != 0:
                break

            # Read content from the files
            with open(prompt_file.name, "r") as f:
                prompt = f.read().strip()

            with open(system_message_file.name, "r") as f:
                system_message = f.read().strip()

            # Query the AI model
            print("Querying AI model...", end="", flush=True)
            response, debug_string = ollama_query(model, prompt, system_message, host)

            # Create temporary file for output
            output_file = tempfile.NamedTemporaryFile(delete=False)
            with open(output_file.name, "w") as f:
                f.write(response)

            # Display the response in neovim
            subprocess.run(
                [
                    nvim_path,
                    "-c",
                    "set nonumber norelativenumber wrap",
                    output_file.name,
                ],
                stdin=sys.stdin,
                stdout=sys.stdout,
            )

    finally:
        # Clean up temporary files
        for file in [prompt_file.name, system_message_file.name, output_file.name]:
            try:
                os.unlink(file)
            except (NameError, OSError):
                pass


if __name__ == "__main__":
    main()
