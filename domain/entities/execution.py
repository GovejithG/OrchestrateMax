# domain/entities/execution.py

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class ExecutionStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Execution:
    id: str
    task_id: str
    status: ExecutionStatus
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    final_output: Optional[str] = None
    error_message: Optional[str] = None
    attempt_number: int = 1

    @staticmethod
    def create(task_id: str, attempt_number: int) -> "Execution":
        return Execution(
            id=str(uuid.uuid4()),
            task_id=task_id,
            status=ExecutionStatus.QUEUED,
            attempt_number=attempt_number,
        )

    def mark_running(self):
        if self.status != ExecutionStatus.QUEUED:
            raise ValueError("Execution must be queued to start.")
        self.status = ExecutionStatus.RUNNING
        self.started_at = datetime.utcnow()

    def mark_completed(self, output: str):
        if self.status != ExecutionStatus.RUNNING:
            raise ValueError("Execution must be running to complete.")
        self.status = ExecutionStatus.COMPLETED
        self.final_output = output
        self.finished_at = datetime.utcnow()

    def mark_failed(self, error: str):
        if self.status != ExecutionStatus.RUNNING:
            raise ValueError("Execution must be running to fail.")
        self.status = ExecutionStatus.FAILED
        self.error_message = error
        self.finished_at = datetime.utcnow()

    def mark_cancelled(self):
        if self.status not in [ExecutionStatus.RUNNING, ExecutionStatus.QUEUED]:
            raise ValueError("Only running or queued executions can be cancelled.")
        self.status = ExecutionStatus.CANCELLED
        self.finished_at = datetime.utcnow()