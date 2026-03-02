import asyncio
from typing import Dict, Tuple

from application.agent.agent_controller import (
    AgentController,
    cancellation_registry,
)

from domain.entities.execution_event import (
    ExecutionEvent,
    ExecutionEventType,
)
from domain.entities.execution import Execution

from infrastructure.repositories.sqlalchemy_execution_event_repository import (
    SQLAlchemyExecutionEventRepository,
)
from infrastructure.repositories.execution_repository import (
    ExecutionRepository,
)

from infrastructure.database.session import AsyncSessionLocal


class TaskExecutor:
    """
    Queue-based worker pool executor (Execution-based).
    Now includes retry boundary.
    """

    def __init__(
        self,
        timeout_seconds: int = 60,
        max_workers: int = 3,
        max_retries: int = 2,
    ):
        self._running_executions: Dict[str, asyncio.Task] = {}
        self._timeout_seconds = timeout_seconds
        self._max_workers = max_workers
        self._max_retries = max_retries

        self._queue: asyncio.Queue[
            Tuple[AgentController, str, str, str]
        ] = asyncio.Queue()

        for _ in range(self._max_workers):
            asyncio.create_task(self._worker_loop())

    # -------------------------
    # Enqueue Execution
    # -------------------------
    def enqueue_execution(
        self,
        controller: AgentController,
        session_id: str,
        execution_id: str,
        user_input: str,
    ) -> None:

        if execution_id in self._running_executions:
            raise RuntimeError("Execution is already running.")

        self._queue.put_nowait(
            (controller, session_id, execution_id, user_input)
        )

    # -------------------------
    # Worker Loop
    # -------------------------
    async def _worker_loop(self):

        while True:
            controller, session_id, execution_id, user_input = await self._queue.get()

            task = asyncio.create_task(
                self._execute(controller, session_id, execution_id, user_input)
            )

            self._running_executions[execution_id] = task

            try:
                await task
            except Exception as e:
                # Prevent background task crashes
                print(f"Worker loop error: {e}")
            finally:
                self._running_executions.pop(execution_id, None)
                self._queue.task_done()

    # -------------------------
    # Core Execution Logic
    # -------------------------
    async def _execute(
        self,
        controller: AgentController,
        session_id: str,
        execution_id: str,
        user_input: str,
    ) -> None:

        try:
            await asyncio.wait_for(
                controller.run(
                    session_id=session_id,
                    execution_id=execution_id,
                    user_input=user_input,
                ),
                timeout=self._timeout_seconds,
            )

        except asyncio.TimeoutError:
            cancellation_registry.cancel(execution_id)

            async with AsyncSessionLocal() as db:

                event_repo = SQLAlchemyExecutionEventRepository(db)
                execution_repo = ExecutionRepository(db)

                # Persist timeout event
                await event_repo.add(
                    ExecutionEvent.create(
                        execution_id=execution_id,
                        event_type=ExecutionEventType.TASK_TIMEOUT,
                        payload={
                            "timeout_seconds": self._timeout_seconds
                        },
                    )
                )

                execution = await execution_repo.get_by_id(execution_id)

                if execution and execution.status == "running":
                    execution.mark_failed("Timeout exceeded")
                    await execution_repo.update(execution)

                    await self._maybe_retry(
                        controller,
                        session_id,
                        execution,
                        user_input,
                        execution_repo,
                        event_repo,
                    )

        except Exception as e:
            print(f"Worker execution error: {e}")

    # -------------------------
    # Retry Logic
    # -------------------------
    async def _maybe_retry(
        self,
        controller: AgentController,
        session_id: str,
        execution,
        user_input: str,
        execution_repo: ExecutionRepository,
        event_repo: SQLAlchemyExecutionEventRepository,
    ) -> None:

        if execution.attempt_number >= self._max_retries:
            return

        new_execution = Execution.create(
            task_id=execution.task_id,
            attempt_number=execution.attempt_number + 1,
        )

        await execution_repo.save(new_execution)

        await event_repo.add(
            ExecutionEvent.create(
                execution_id=new_execution.id,
                event_type=ExecutionEventType.RETRY_SCHEDULED,
                payload={
                    "previous_execution_id": execution.id,
                    "attempt_number": new_execution.attempt_number,
                },
            )
        )

        # Requeue new execution
        self._queue.put_nowait(
            (controller, session_id, new_execution.id, user_input)
        )

    # -------------------------
    # Cancellation
    # -------------------------
    def cancel_execution(self, execution_id: str) -> bool:
        return cancellation_registry.cancel(execution_id)

    def is_running(self, execution_id: str) -> bool:
        return execution_id in self._running_executions

    # -------------------------
    # Introspection
    # -------------------------
    def get_status(self) -> dict:
        return {
            "running_executions": len(self._running_executions),
            "queued_executions": self._queue.qsize(),
            "max_workers": self._max_workers,
            "max_retries": self._max_retries,
        }