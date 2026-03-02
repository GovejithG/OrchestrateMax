import asyncio
from typing import Dict, Any, Callable


class ToolRegistry:

    def __init__(self):
        self._tools: Dict[str, Callable] = {
            "echo_tool": self.echo_tool
        }

    def get_tool_definitions(self) -> list[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "echo_tool",
                    "description": "Echoes the provided text.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "Text to echo back"
                            }
                        },
                        "required": ["text"],
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

    async def echo_tool(self, text: str) -> str:
        await asyncio.sleep(10)  # artificial delay for cancellation test
        return f"ECHO: {text}"