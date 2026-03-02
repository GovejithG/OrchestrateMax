from typing import Optional

from domain.entities.session import Session
from domain.repositories.session_repository import SessionRepository


class SessionService:

    def __init__(self, repository: SessionRepository):
        self.repository = repository

    async def create_session(self, name: Optional[str] = None) -> Session:
        session = Session.create(name=name)
        await self.repository.add(session)
        return session

    async def get_session(self, session_id: str) -> Session | None:
        return await self.repository.get_by_id(session_id)