from sqlalchemy import Column, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from infrastructure.database.session import Base


class ExecutionEventModel(Base):
    __tablename__ = "execution_events"

    id = Column(String, primary_key=True, index=True)

    execution_id = Column(
        String,
        ForeignKey("executions.id"),
        nullable=False,
        index=True
    )

    event_type = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    execution = relationship(
        "ExecutionModel",
        back_populates="events"
    )