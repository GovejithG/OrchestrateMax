import asyncio
from typing import Dict, List

class EventBus:
    def __init__(self):
        self._queues: Dict[str, List[asyncio.Queue]] = {}

    def subscribe(self, execution_id: str) -> asyncio.Queue:
        queue = asyncio.Queue()
        if execution_id not in self._queues:
            self._queues[execution_id] = []
        self._queues[execution_id].append(queue)
        return queue

    def unsubscribe(self, execution_id: str, queue: asyncio.Queue) -> None:
        if execution_id in self._queues:
            if hasattr(self._queues[execution_id], 'discard'):
                self._queues[execution_id].discard(queue)
            try:
                self._queues[execution_id].remove(queue)
            except ValueError:
                pass
            if not self._queues[execution_id]:
                del self._queues[execution_id]

    async def publish(self, execution_id: str, event_data: dict) -> None:
        if execution_id not in self._queues:
            return
        for queue in self._queues[execution_id]:
            await queue.put(event_data)

event_bus = EventBus()
