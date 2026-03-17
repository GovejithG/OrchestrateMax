from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from domain.entities.task import Task
from domain.repositories.task_repository import TaskRepository
from infrastructure.database.task_model import TaskModel


class SQLAlchemyTaskRepository(TaskRepository):

    def __init__(self, db: AsyncSession):
        self.db = db

    async def add(self, task: Task) -> None:
        """
        Save behavior:
        - INSERT if new
        - UPDATE if exists
        """

        result = await self.db.execute(
            select(TaskModel).where(TaskModel.id == task.id)
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Core fields
            existing.session_id = task.session_id
            existing.title = task.title
            existing.description = task.description
            existing.status = task.status

            # Timestamps
            existing.created_at = task.created_at
            existing.updated_at = task.updated_at

        else:
            model = TaskModel(
                id=task.id,
                session_id=task.session_id,
                title=task.title,
                description=task.description,
                status=task.status,

                created_at=task.created_at,
                updated_at=task.updated_at,
            )
            self.db.add(model)

        await self.db.commit()

    async def get_by_id(self, task_id: str) -> Task | None:
        result = await self.db.execute(
            select(TaskModel).where(TaskModel.id == task_id)
        )
        model = result.scalar_one_or_none()

        if not model:
            return None

        return Task(
            id=model.id,
            session_id=model.session_id,
            title=model.title,
            description=model.description,
            status=model.status,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def get_by_session_id(self, session_id: str) -> list[Task]:
        result = await self.db.execute(
            select(TaskModel).where(TaskModel.session_id == session_id)
        )
        models = result.scalars().all()

        tasks: list[Task] = []

        for model in models:
            tasks.append(
                Task(
                    id=model.id,
                    session_id=model.session_id,
                    title=model.title,
                    description=model.description,
                    status=model.status,
                    created_at=model.created_at,
                    updated_at=model.updated_at,
                )
            )

        return tasks