# infrastructure/db/models/execution_model.py

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from infrastructure.database.session import Base

class ExecutionModel(Base):
    __tablename__ = "executions"

    id = Column(String, primary_key=True, index=True)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False, index=True)

    status = Column(String, nullable=False)

    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)

    final_output = Column(String, nullable=True)
    error_message = Column(String, nullable=True)

    attempt_number = Column(Integer, nullable=False)

    task = relationship("TaskModel", back_populates="executions")

    events = relationship(
    "ExecutionEventModel",
    back_populates="execution",
    cascade="all, delete-orphan",
    lazy="selectin"
    )