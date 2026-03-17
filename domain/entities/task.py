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
    ):
        self.id = id
        self.session_id = session_id
        self.title = title
        self.description = description
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at

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
        self.updated_at = datetime.utcnow()

    def mark_completed(self) -> None:
        self.status = "completed"
        self.updated_at = datetime.utcnow()

    def mark_failed(self) -> None:
        self.status = "failed"
        self.updated_at = datetime.utcnow()

    def mark_cancelled(self) -> None:
        self.status = "cancelled"
        self.updated_at = datetime.utcnow()

    def mark_timed_out(self) -> None:
        """
        System-triggered timeout (not user cancellation).
        """
        self.status = "failed"
        self.updated_at = datetime.utcnow()