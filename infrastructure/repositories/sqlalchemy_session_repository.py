from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from domain.entities.session import Session
from domain.repositories.session_repository import SessionRepository
from infrastructure.database.session_model import SessionModel


class SQLAlchemySessionRepository(SessionRepository):

    def __init__(self, db: AsyncSession):
        self.db = db

    async def add(self, session: Session) -> None:
        model = SessionModel(
            id=session.id,
            name=session.name,
            created_at=session.created_at,
        )
        self.db.add(model)
        await self.db.commit()

    async def get_by_id(self, session_id: str) -> Session | None:
        result = await self.db.execute(
            select(SessionModel).where(SessionModel.id == session_id)
        )
        model = result.scalar_one_or_none()

        if not model:
            return None

        return Session(
            id=model.id,
            name=model.name,  # ← THIS WAS MISSING
            created_at=model.created_at,
        )

    async def list_all(self) -> list[Session]:
        result = await self.db.execute(
            select(SessionModel).order_by(SessionModel.created_at.desc())
        )
        models = result.scalars().all()
        return [Session(id=m.id, name=m.name, created_at=m.created_at) for m in models]

    async def delete(self, session_id: str) -> None:
        result = await self.db.execute(
            select(SessionModel).where(SessionModel.id == session_id)
        )
        model = result.scalar_one_or_none()
        if model:
            await self.db.delete(model)
            await self.db.commit()