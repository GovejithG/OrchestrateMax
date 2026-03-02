from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseLLM(ABC):

    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]] | None = None,
    ) -> Dict[str, Any]:
        """
        Returns raw model response.
        Must support tool-calling structure later.
        """
        pass