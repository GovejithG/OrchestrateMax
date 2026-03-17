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

    @abstractmethod
    async def list_all(self) -> list[Session]:
        pass

    @abstractmethod
    async def delete(self, session_id: str) -> None:
        pass