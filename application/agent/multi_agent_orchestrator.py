from application.agent.runtime import AgentRuntime
from domain.entities.execution_event import (
    ExecutionEvent,
    ExecutionEventType,
)
from domain.repositories.execution_event_repository import (
    ExecutionEventRepository,
)


class MultiAgentOrchestrator:
    """
    3-Stage Linear Multi-Agent Pipeline:

    1. Planner   → creates plan
    2. Executor  → executes plan
    3. Reviewer  → validates/improves output
    """

    def __init__(
        self,
        planner_runtime: AgentRuntime,
        executor_runtime: AgentRuntime,
        reviewer_runtime: AgentRuntime,
        execution_event_repository: ExecutionEventRepository,
    ):
        self.planner_runtime = planner_runtime
        self.executor_runtime = executor_runtime
        self.reviewer_runtime = reviewer_runtime
        self.event_repo = execution_event_repository

    async def execute(
        self,
        execution_id: str,
        system_prompt: str,
        user_input: str,
    ) -> dict:

        # -------------------------
        # 1️⃣ PLANNER
        # -------------------------
        await self._emit_role_event(execution_id, "PLANNER")

        planner_result = await self.planner_runtime.execute(
            execution_id=execution_id,
            system_prompt=system_prompt,
            user_input=user_input,
        )

        if planner_result.get("status") != "completed":
            return planner_result

        plan_output = planner_result.get("final_output", "")

        # -------------------------
        # 2️⃣ EXECUTOR
        # -------------------------
        await self._emit_role_event(execution_id, "EXECUTOR")

        executor_result = await self.executor_runtime.execute(
            execution_id=execution_id,
            system_prompt="Execute the following plan carefully.",
            user_input=plan_output,
        )

        if executor_result.get("status") != "completed":
            return executor_result

        execution_output = executor_result.get("final_output", "")

        # -------------------------
        # 3️⃣ REVIEWER
        # -------------------------
        await self._emit_role_event(execution_id, "REVIEWER")

        reviewer_result = await self.reviewer_runtime.execute(
            execution_id=execution_id,
            system_prompt="Review and improve the following result.",
            user_input=execution_output,
        )

        return reviewer_result

    async def _emit_role_event(self, execution_id: str, role: str):
        await self.event_repo.add(
            ExecutionEvent.create(
                execution_id=execution_id,
                event_type=ExecutionEventType.LLM_REQUEST,
                payload={
                    "agent_role_started": role
                },
            )
        )