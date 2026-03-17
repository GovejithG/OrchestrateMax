import pytest
from datetime import datetime
from domain.entities.execution import Execution, ExecutionStatus
from domain.entities.task import Task
from domain.entities.session import Session
from domain.entities.execution_event import ExecutionEvent, ExecutionEventType


def test_execution_lifecycle():
    execution = Execution.create(task_id="task-1", attempt_number=1)
    assert execution.status == ExecutionStatus.QUEUED

    execution.mark_running()
    assert execution.status == ExecutionStatus.RUNNING
    assert execution.started_at is not None

    execution.mark_completed("output text")
    assert execution.status == ExecutionStatus.COMPLETED
    assert execution.final_output == "output text"
    assert execution.finished_at is not None


def test_execution_cannot_complete_from_queued():
    execution = Execution.create(task_id="task-1", attempt_number=1)
    with pytest.raises(ValueError):
        execution.mark_completed("output")


def test_execution_cannot_fail_from_queued():
    execution = Execution.create(task_id="task-1", attempt_number=1)
    with pytest.raises(ValueError):
        execution.mark_failed("error")


def test_execution_cancel_from_queued():
    execution = Execution.create(task_id="task-1", attempt_number=1)
    execution.mark_cancelled()
    assert execution.status == ExecutionStatus.CANCELLED


def test_execution_cancel_from_running():
    execution = Execution.create(task_id="task-1", attempt_number=1)
    execution.mark_running()
    execution.mark_cancelled()
    assert execution.status == ExecutionStatus.CANCELLED


def test_task_create():
    task = Task.create(session_id="session-1", title="Test task")
    assert task.status == "created"
    assert task.title == "Test task"
    assert task.id is not None


def test_session_create():
    session = Session.create(name="My session")
    assert session.name == "My session"
    assert session.id is not None
    assert session.created_at is not None


def test_execution_event_create():
    event = ExecutionEvent.create(
        execution_id="exec-1",
        event_type=ExecutionEventType.AGENT_ROLE_STARTED,
        payload={"agent_role": "PLANNER", "status": "started"},
    )
    assert event.execution_id == "exec-1"
    assert event.event_type == ExecutionEventType.AGENT_ROLE_STARTED
    assert event.payload["agent_role"] == "PLANNER"
