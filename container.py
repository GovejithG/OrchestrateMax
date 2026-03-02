from infrastructure.database.session import AsyncSessionLocal
from infrastructure.repositories.sqlalchemy_task_repository import SQLAlchemyTaskRepository
from application.services.task_service import TaskService
from infrastructure.repositories.sqlalchemy_session_repository import SQLAlchemySessionRepository
from application.services.session_service import SessionService


async def get_task_service():
    async with AsyncSessionLocal() as db:
        repo = SQLAlchemyTaskRepository(db)
        service = TaskService(repo)
        yield service

async def get_session_service():
    async with AsyncSessionLocal() as db:
        repo = SQLAlchemySessionRepository(db)
        service = SessionService(repo)
        yield service