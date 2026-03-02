from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class Session:
    id: str
    name: Optional[str]
    created_at: datetime

    @staticmethod
    def create(name: Optional[str] = None) -> "Session":
        return Session(
            id=str(uuid.uuid4()),
            name=name,
            created_at=datetime.utcnow(),
        )