import httpx
from typing import List, Dict, Any
from application.llm.base_llm import BaseLLM
from config import settings


class OllamaClient(BaseLLM):

    def __init__(
        self,
        model: str = settings.OLLAMA_MODEL,
        base_url: str = settings.OLLAMA_BASE_URL,
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
                timeout=float(settings.OLLAMA_TIMEOUT),
            )

        response.raise_for_status()
        return response.json()