import httpx
from typing import List, Dict, Any
from application.llm.base_llm import BaseLLM


class OllamaClient(BaseLLM):

    def __init__(
        self,
        model: str = "qwen2.5:7b-instruct",
        base_url: str = "http://localhost:11434",
    ):
        self.model = model
        self.base_url = base_url

    async def generate(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]] | None = None,
    ) -> Dict[str, Any]:

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }

        # Tools will be used in Phase 4
        if tools:
            payload["tools"] = tools

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=60.0,
            )

        response.raise_for_status()
        return response.json()