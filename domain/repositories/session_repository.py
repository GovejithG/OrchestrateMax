from abc import ABC, abstractmethod
from typing import Optional
from domain.entities.session import Session


class SessionRepository(ABC):

    @abstractmethod
    async def add(self, session: Session) -> None:
        pass

    @abstractmethod
    async def get_by_id(self, session_id: str) -> Optional[Session]:
        pass