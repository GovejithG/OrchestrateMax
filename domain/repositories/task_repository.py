from abc import ABC, abstractmethod
from typing import List
from domain.entities.task import Task


class TaskRepository(ABC):

    @abstractmethod
    async def add(self, task: Task) -> None:
        pass

    @abstractmethod
    async def get_by_id(self, task_id: str) -> Task | None:
        pass

    @abstractmethod
    async def get_by_session_id(self, session_id: str) -> List[Task]:
        pass