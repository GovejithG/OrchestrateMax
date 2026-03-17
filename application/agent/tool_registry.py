import os
import subprocess
import sys
from typing import Dict, Any, Callable

from application.constants import WORKSPACE_DIR


class ToolRegistry:

    def __init__(self):
        self._tools: Dict[str, Callable] = {
            "write_file": self.write_file,
            "read_file": self.read_file,
            "run_python": self.run_python,
            "list_files": self.list_files,
        }

    def get_tool_definitions(self) -> list[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "Writes content to a file in the workspace.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Relative path to the file in the workspace"
                            },
                            "content": {
                                "type": "string",
                                "description": "Content to write to the file"
                            }
                        },
                        "required": ["path", "content"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Reads content from a file in the workspace.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Relative path to the file in the workspace"
                            }
                        },
                        "required": ["path"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "run_python",
                    "description": "Runs a python script in the workspace and returns stdout/stderr.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filename": {
                                "type": "string",
                                "description": "Relative path to the python script in the workspace"
                            }
                        },
                        "required": ["filename"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "list_files",
                    "description": "Lists all files recursively in the workspace.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                    },
                },
            }
        ]

    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        tool = self._tools.get(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")

        return await tool(**arguments)

    # ----------------------------------------
    # Tool Implementations
    # ----------------------------------------

    async def write_file(self, path: str, content: str) -> str:
        safe_path = os.path.normpath(os.path.join(WORKSPACE_DIR, path))
        if not safe_path.startswith(os.path.normpath(WORKSPACE_DIR)):
            return "Error: path traversal attempt blocked"
        os.makedirs(os.path.dirname(safe_path), exist_ok=True)
        with open(safe_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"File written: {path}"

    async def read_file(self, path: str) -> str:
        safe_path = os.path.normpath(os.path.join(WORKSPACE_DIR, path))
        if not safe_path.startswith(os.path.normpath(WORKSPACE_DIR)):
            return "Error: path traversal attempt blocked"
        if not os.path.exists(safe_path):
            return f"Error: file not found: {path}"
        with open(safe_path, "r", encoding="utf-8") as f:
            return f.read()

    async def run_python(self, filename: str) -> str:
        safe_path = os.path.normpath(os.path.join(WORKSPACE_DIR, filename))
        if not safe_path.startswith(os.path.normpath(WORKSPACE_DIR)):
            return "Error: path traversal attempt blocked"
        if not os.path.exists(safe_path):
            return f"Error: file not found: {filename}"
        try:
            result = subprocess.run(
                [sys.executable, safe_path],
                capture_output=True,
                text=True,
                timeout=15,
                cwd=WORKSPACE_DIR,
            )
            output = ""
            if result.stdout:
                output += f"STDOUT:\n{result.stdout}"
            if result.stderr:
                output += f"STDERR:\n{result.stderr}"
            if not output:
                output = "Script ran successfully with no output."
            return output
        except subprocess.TimeoutExpired:
            return "Error: script timed out after 15 seconds"
        except Exception as e:
            return f"Error running script: {str(e)}"

    async def list_files(self) -> str:
        files = []
        for root, dirs, filenames in os.walk(WORKSPACE_DIR):
            for filename in filenames:
                full = os.path.join(root, filename)
                rel = os.path.relpath(full, WORKSPACE_DIR)
                files.append(rel)
        if not files:
            return "Workspace is empty."
        return "\n".join(files)