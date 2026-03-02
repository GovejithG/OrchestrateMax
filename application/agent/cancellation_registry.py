# application/agent/cancellation_registry.py

from typing import Dict
from application.agent.cancellation_token import CancellationToken


class CancellationRegistry:
    """
    In-memory registry mapping task_id -> CancellationToken.
    """

    def __init__(self):
        self._tokens: Dict[str, CancellationToken] = {}

    def register(self, task_id: str, token: CancellationToken) -> None:
        self._tokens[task_id] = token

    def unregister(self, task_id: str) -> None:
        self._tokens.pop(task_id, None)

    def cancel(self, task_id: str) -> bool:
        token = self._tokens.get(task_id)
        if not token:
            return False

        token.cancel()
        return True