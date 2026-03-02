from datetime import datetime
from uuid import uuid4


class Task:

    def __init__(
        self,
        id: str,
        session_id: str,
        title: str,
        description: str | None,
        status: str,
        created_at: datetime,
        updated_at: datetime,
        final_output: str | None = None,
        error_message: str | None = None,
        execution_started_at: datetime | None = None,
        execution_finished_at: datetime | None = None,
    ):
        self.id = id
        self.session_id = session_id
        self.title = title
        self.description = description
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at

        self.final_output = final_output
        self.error_message = error_message
        self.execution_started_at = execution_started_at
        self.execution_finished_at = execution_finished_at

    @classmethod
    def create(
        cls,
        session_id: str,
        title: str,
        description: str | None = None,
    ) -> "Task":

        now = datetime.utcnow()

        return cls(
            id=str(uuid4()),
            session_id=session_id,
            title=title,
            description=description,
            status="created",
            created_at=now,
            updated_at=now,
        )

    # -------------------------
    # Lifecycle Methods
    # -------------------------

    def mark_running(self) -> None:
        self.status = "running"
        self.execution_started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def mark_completed(self, output: str) -> None:
        self.status = "completed"
        self.final_output = output
        self.error_message = None
        self.execution_finished_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def mark_failed(self, error: str) -> None:
        self.status = "failed"
        self.error_message = error
        self.execution_finished_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def mark_cancelled(self) -> None:
        self.status = "cancelled"
        self.execution_finished_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def mark_timed_out(self) -> None:
        """
        System-triggered timeout (not user cancellation).
        """
        self.status = "failed"
        self.error_message = "Execution timed out."
        self.execution_finished_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()