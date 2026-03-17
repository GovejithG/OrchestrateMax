from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from infrastructure.database.session import Base
from datetime import datetime


class TaskModel(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)

    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, nullable=False)

    # -------------------------
    # Execution Persistence (Legacy - migrated)
    # -------------------------

    # -------------------------
    # Timestamps
    # -------------------------
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # -------------------------
    # Relationships
    # -------------------------
    session = relationship("SessionModel", back_populates="tasks")

    executions = relationship(
        "ExecutionModel",
        back_populates="task",
        cascade="all, delete-orphan",
        lazy="selectin"
    )