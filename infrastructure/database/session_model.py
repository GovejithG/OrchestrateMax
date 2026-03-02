from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from infrastructure.database.session import Base
from datetime import datetime


class SessionModel(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    tasks = relationship(
        "TaskModel",
        back_populates="session",
        cascade="all, delete-orphan",
    )