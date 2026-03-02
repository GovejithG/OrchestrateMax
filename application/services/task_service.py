from domain.entities.task import Task
from domain.repositories.task_repository import TaskRepository


class TaskService:

    def __init__(self, repository: TaskRepository):
        self.repository = repository

    async def create_task(
        self,
        session_id: str,
        title: str,
        description: str | None = None,
    ) -> Task:

        task = Task.create(
            session_id=session_id,
            title=title,
            description=description,
        )

        await self.repository.add(task)
        return task

    async def get_task(self, task_id: str) -> Task | None:
        return await self.repository.get_by_id(task_id)
        