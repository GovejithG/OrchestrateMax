# infrastructure/repositories/execution_repository.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, List

from domain.entities.execution import Execution, ExecutionStatus
from infrastructure.database.models.execution_model import ExecutionModel

class ExecutionRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, execution: Execution):
        model = ExecutionModel(
            id=execution.id,
            task_id=execution.task_id,
            status=execution.status.value,
            started_at=execution.started_at,
            finished_at=execution.finished_at,
            final_output=execution.final_output,
            error_message=execution.error_message,
            attempt_number=execution.attempt_number,
        )
        self.session.add(model)
        await self.session.commit()

    async def update(self, execution: Execution):
        result = await self.session.execute(
            select(ExecutionModel).where(ExecutionModel.id == execution.id)
        )
        model = result.scalar_one()

        model.status = execution.status.value
        model.started_at = execution.started_at
        model.finished_at = execution.finished_at
        model.final_output = execution.final_output
        model.error_message = execution.error_message
        model.attempt_number = execution.attempt_number

        await self.session.commit()

    async def get_by_id(self, execution_id: str) -> Optional[Execution]:
        result = await self.session.execute(
            select(ExecutionModel).where(ExecutionModel.id == execution_id)
        )
        model = result.scalar_one_or_none()

        if not model:
            return None

        return Execution(
            id=model.id,
            task_id=model.task_id,
            status=ExecutionStatus(model.status),
            started_at=model.started_at,
            finished_at=model.finished_at,
            final_output=model.final_output,
            error_message=model.error_message,
            attempt_number=model.attempt_number,
        )

    async def get_by_task(self, task_id: str) -> List[Execution]:
        result = await self.session.execute(
            select(ExecutionModel).where(ExecutionModel.task_id == task_id)
        )
        models = result.scalars().all()

        return [
            Execution(
                id=m.id,
                task_id=m.task_id,
                status=ExecutionStatus(m.status),
                started_at=m.started_at,
                finished_at=m.finished_at,
                final_output=m.final_output,
                error_message=m.error_message,
                attempt_number=m.attempt_number,
            )
            for m in models
        ]