# infrastructure/repositories/sqlalchemy_execution_event_repository.py

import json
from typing import List

from application.events.event_bus import event_bus
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from domain.entities.execution_event import ExecutionEvent
from domain.repositories.execution_event_repository import ExecutionEventRepository
from infrastructure.database.execution_event_model import ExecutionEventModel


class SQLAlchemyExecutionEventRepository(ExecutionEventRepository):

    def __init__(self, db: AsyncSession):
        self.db = db

    async def add(self, event: ExecutionEvent) -> None:
        model = ExecutionEventModel(
            id=event.id,
            execution_id=event.execution_id,  # 🔥 CHANGED
            event_type=event.event_type,
            payload=json.dumps(event.payload),
            created_at=event.created_at,
        )

        self.db.add(model)
        await self.db.commit()

        await event_bus.publish(event.execution_id, {
            "id": event.id,
            "execution_id": event.execution_id,
            "event_type": event.event_type.value if hasattr(event.event_type, "value") else event.event_type,
            "payload": event.payload,
            "created_at": event.created_at.isoformat(),
        })

    async def get_by_execution_id(self, execution_id: str) -> List[ExecutionEvent]:
        result = await self.db.execute(
            select(ExecutionEventModel)
            .where(ExecutionEventModel.execution_id == execution_id)
            .order_by(ExecutionEventModel.created_at)
        )

        models = result.scalars().all()

        return [
            ExecutionEvent(
                id=m.id,
                execution_id=m.execution_id,
                event_type=m.event_type,
                payload=json.loads(m.payload),
                created_at=m.created_at,
            )
            for m in models
        ]