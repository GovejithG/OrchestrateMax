import json

from application.llm.base_llm import BaseLLM
from application.agent.tool_registry import ToolRegistry
from application.agent.agent_result import AgentResult
from application.agent.runtime import AgentRuntime
from application.agent.multi_agent_orchestrator import MultiAgentOrchestrator
from application.agent.cancellation_token import CancellationToken
from application.agent.cancellation_registry import CancellationRegistry
from config import settings

from domain.repositories.task_repository import TaskRepository
from domain.entities.artifact import Artifact, ArtifactType

from infrastructure.repositories.sqlalchemy_execution_event_repository import (
    SQLAlchemyExecutionEventRepository,
)
from infrastructure.repositories.execution_repository import ExecutionRepository
from infrastructure.repositories.sqlalchemy_artifact_repository import (
    SQLAlchemyArtifactRepository,
)


# --------------------------------------------------
# Single in-memory registry instance (app-level)
# --------------------------------------------------
cancellation_registry = CancellationRegistry()


class AgentController:

    def __init__(
        self,
        llm: BaseLLM,
        task_repository: TaskRepository,
    ):
        self.llm = llm
        self.task_repository = task_repository
        self.tool_registry = ToolRegistry()
        self.planner_max_iterations = settings.PLANNER_MAX_ITERATIONS
        self.executor_max_iterations = settings.EXECUTOR_MAX_ITERATIONS
        self.reviewer_max_iterations = settings.REVIEWER_MAX_ITERATIONS
        self._multi_agent_enabled = True

    async def run(
        self,
        session_id: str,
        execution_id: str,
        user_input: str,
    ) -> AgentResult:

        # -------------------------
        # LOAD EXECUTION
        # -------------------------
        execution_repository = ExecutionRepository(self.task_repository.db)
        execution = await execution_repository.get_by_id(execution_id)

        if not execution:
            raise ValueError("Execution not found")

        # -------------------------
        # LOAD & VALIDATE TASK
        # -------------------------
        task = await self.task_repository.get_by_id(execution.task_id)
        if not task:
            raise ValueError("Task not found")

        if task.session_id != session_id:
            raise ValueError("Task does not belong to this session")

        # -------------------------
        # SESSION MEMORY
        # -------------------------
        session_tasks = await self.task_repository.get_by_session_id(session_id)

        memory_summary = ""
        if session_tasks:
            memory_summary = "Previous tasks in this session:\n"
            for t in session_tasks:
                memory_summary += f"- {t.title} (status: {t.status})\n"

        base_system_prompt = (
            "You are an AI agent responsible for executing a task.\n\n"
            f"{memory_summary}\n"
            "Use tools when necessary. "
            "If you use a tool, wait for the tool result before continuing."
        )

        # -------------------------
        # CANCELLATION
        # -------------------------
        token = CancellationToken()
        cancellation_registry.register(execution.id, token)

        execution_event_repository = SQLAlchemyExecutionEventRepository(
            self.task_repository.db
        )

        artifact_repository = SQLAlchemyArtifactRepository(
            self.task_repository.db
        )

        # -------------------------
        # CREATE RUNTIMES
        # -------------------------
        planner_runtime = AgentRuntime(
            llm=self.llm,
            tool_registry=self.tool_registry,
            execution_event_repository=execution_event_repository,
            cancellation_token=token,
            max_iterations=self.planner_max_iterations,
        )

        executor_runtime = AgentRuntime(
            llm=self.llm,
            tool_registry=self.tool_registry,
            execution_event_repository=execution_event_repository,
            cancellation_token=token,
            max_iterations=self.executor_max_iterations,
        )

        reviewer_runtime = AgentRuntime(
            llm=self.llm,
            tool_registry=self.tool_registry,
            execution_event_repository=execution_event_repository,
            cancellation_token=token,
            max_iterations=self.reviewer_max_iterations,
        )

        # -------------------------
        # EXECUTE
        # -------------------------
        try:

            if self._multi_agent_enabled:

                orchestrator = MultiAgentOrchestrator(
                    planner_runtime=planner_runtime,
                    executor_runtime=executor_runtime,
                    reviewer_runtime=reviewer_runtime,
                    execution_event_repository=execution_event_repository,
                )

                result = await orchestrator.execute(
                    execution_id=execution.id,
                    system_prompt="You are a strategic planning AI.",
                    user_input=user_input,
                )

            else:

                result = await executor_runtime.execute(
                    execution_id=execution.id,
                    system_prompt=base_system_prompt,
                    user_input=user_input,
                )

        finally:
            cancellation_registry.unregister(execution.id)

        # -------------------------
        # UPDATE EXECUTION STATUS
        # -------------------------
        execution = await execution_repository.get_by_id(execution.id)

        if result["status"] == "completed":

            execution.mark_completed(result["final_output"])

            # -------------------------
            # SAVE ARTIFACT
            # -------------------------
            final_output = result["final_output"]

            artifact_type = ArtifactType.TEXT

            try:
                json.loads(final_output)
                artifact_type = ArtifactType.JSON
            except Exception:
                pass

            artifact = Artifact.create(
                execution_id=execution.id,
                name="final_output",
                artifact_type=artifact_type,
                content=final_output,
            )

            await artifact_repository.save(artifact)

        elif result["status"] == "cancelled":
            execution.mark_cancelled()

        else:
            execution.mark_failed(result["final_output"])

        await execution_repository.update(execution)

        # -------------------------
        # RETURN RESULT
        # -------------------------
        return AgentResult(
            final_output=result["final_output"],
            raw_response=result.get("raw_response", {}),
            tool_calls=result.get("tool_calls", []),
        )