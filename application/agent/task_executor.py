import asyncio
import logging
from typing import Dict, Tuple

logger = logging.getLogger("orchestratemax.executor")

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
from infrastructure.repositories.sqlalchemy_task_repository import (
    SQLAlchemyTaskRepository,
)

from infrastructure.database.session import AsyncSessionLocal


class TaskExecutor:
    """
    Queue-based worker pool executor (Execution-based).
    Now includes retry boundary.
    """

    def __init__(
        self,
        llm,
        timeout_seconds: int = 60,
        max_workers: int = 3,
        max_retries: int = 2,
    ):
        self._llm = llm
        self._running_executions: Dict[str, asyncio.Task] = {}
        self._timeout_seconds = timeout_seconds
        self._max_workers = max_workers
        self._max_retries = max_retries

        self._queue: asyncio.Queue[
            Tuple[str, str, str, str]
        ] = asyncio.Queue()

        for _ in range(self._max_workers):
            asyncio.create_task(self._worker_loop())

    # -------------------------
    # Enqueue Execution
    # -------------------------
    def enqueue_execution(
        self,
        session_id: str,
        task_id: str,
        execution_id: str,
        user_input: str,
    ) -> None:

        if execution_id in self._running_executions:
            raise RuntimeError("Execution is already running.")

        self._queue.put_nowait(
            (session_id, task_id, execution_id, user_input)
        )

    # -------------------------
    # Worker Loop
    # -------------------------
    async def _worker_loop(self):

        while True:
            session_id, task_id, execution_id, user_input = await self._queue.get()

            task = asyncio.create_task(
                self._execute(session_id, task_id, execution_id, user_input)
            )

            self._running_executions[execution_id] = task

            try:
                await task
            except Exception as e:
                # Prevent background task crashes
                logger.error(f"Worker loop error for execution {execution_id}: {e}", exc_info=True)
            finally:
                self._running_executions.pop(execution_id, None)
                self._queue.task_done()

    # -------------------------
    # Core Execution Logic
    # -------------------------
    async def _execute(
        self,
        session_id: str,
        task_id: str,
        execution_id: str,
        user_input: str,
    ) -> None:

        async with AsyncSessionLocal() as db:

            # 1) Create and save execution record
            execution_repo = ExecutionRepository(db)

            execution = Execution.create(
                task_id=task_id,
                attempt_number=1,
            )
            # Override the auto-generated id with the one provided by the endpoint
            execution.id = execution_id

            await execution_repo.save(execution)

            # 2) Mark running and persist
            execution.mark_running()
            await execution_repo.update(execution)

            logger.info(f"Execution {execution_id} started (attempt {execution.attempt_number})")

            # 3) Construct repos and controller inside this session
            task_repo = SQLAlchemyTaskRepository(db)
            controller = AgentController(self._llm, task_repo)

            # 4) Run with timeout — session stays alive for the entire duration
            try:
                await asyncio.wait_for(
                    controller.run(
                        session_id=session_id,
                        execution_id=execution_id,
                        user_input=user_input,
                    ),
                    timeout=self._timeout_seconds,
                )
                logger.info(f"Execution {execution_id} completed successfully")

            except asyncio.TimeoutError:
                logger.error(f"Execution {execution_id} failed: timeout of {self._timeout_seconds}s exceeded")
                cancellation_registry.cancel(execution_id)

                event_repo = SQLAlchemyExecutionEventRepository(db)

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

                # Re-fetch execution to get latest state
                execution = await execution_repo.get_by_id(execution_id)

                if execution and execution.status == "running":
                    execution.mark_failed("Timeout exceeded")
                    await execution_repo.update(execution)

                    await self._maybe_retry(
                        session_id,
                        task_id,
                        execution,
                        user_input,
                        execution_repo,
                        event_repo,
                    )

            except Exception as e:
                logger.error(f"Execution {execution_id} failed: {e}", exc_info=True)

    # -------------------------
    # Retry Logic
    # -------------------------
    async def _maybe_retry(
        self,
        session_id: str,
        task_id: str,
        execution,
        user_input: str,
        execution_repo: ExecutionRepository,
        event_repo: SQLAlchemyExecutionEventRepository,
    ) -> None:

        if execution.attempt_number >= self._max_retries:
            return

        new_execution = Execution.create(
            task_id=task_id,
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

        # Requeue new execution (controller will be reconstructed in _execute)
        self._queue.put_nowait(
            (session_id, task_id, new_execution.id, user_input)
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