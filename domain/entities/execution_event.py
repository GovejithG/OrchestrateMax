# domain/entities/execution_event.py

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import uuid
from typing import Dict, Any


class ExecutionEventType(str, Enum):
    LLM_REQUEST = "LLM_REQUEST"
    LLM_RESPONSE = "LLM_RESPONSE"
    TOOL_EXECUTION = "TOOL_EXECUTION"
    FINAL_OUTPUT = "FINAL_OUTPUT"
    TASK_TIMEOUT = "TASK_TIMEOUT"
    TASK_CANCELLED = "TASK_CANCELLED"
    MAX_ITERATIONS_REACHED = "MAX_ITERATIONS_REACHED"

    # 🔥 NEW
    RETRY_SCHEDULED = "RETRY_SCHEDULED"


@dataclass
class ExecutionEvent:
    id: str
    execution_id: str
    event_type: ExecutionEventType
    payload: Dict[str, Any]
    created_at: datetime

    @staticmethod
    def create(
        execution_id: str,
        event_type: ExecutionEventType,
        payload: Dict[str, Any],
    ) -> "ExecutionEvent":
        return ExecutionEvent(
            id=str(uuid.uuid4()),
            execution_id=execution_id,
            event_type=event_type,
            payload=payload,
            created_at=datetime.utcnow(),
        )