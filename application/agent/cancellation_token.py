# application/agent/cancellation_token.py

import asyncio


class CancellationToken:
    """
    Cooperative cancellation primitive for async execution.

    Runtime periodically checks this token to determine whether
    execution should stop gracefully.
    """

    def __init__(self):
        self._event = asyncio.Event()

    def cancel(self) -> None:
        """
        Signal cancellation.
        """
        self._event.set()

    def is_cancelled(self) -> bool:
        """
        Non-blocking check.
        """
        return self._event.is_set()

    async def wait(self) -> None:
        """
        Await cancellation signal.
        """
        await self._event.wait()