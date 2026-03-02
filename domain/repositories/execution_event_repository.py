from abc import ABC, abstractmethod
from typing import List
from domain.entities.execution_event import ExecutionEvent


class ExecutionEventRepository(ABC):

    @abstractmethod
    async def add(self, event: ExecutionEvent) -> None:
        pass

    @abstractmethod
    async def get_by_execution_id(self, execution_id: str) -> List[ExecutionEvent]:
        pass