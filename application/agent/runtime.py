# application/agent/runtime.py

from typing import List, Dict, Any

from application.llm.base_llm import BaseLLM
from application.agent.tool_registry import ToolRegistry
from application.agent.cancellation_token import CancellationToken

from domain.repositories.execution_event_repository import ExecutionEventRepository
from domain.entities.execution_event import (
    ExecutionEvent,
    ExecutionEventType,
)


class AgentRuntime:

    def __init__(
        self,
        llm: BaseLLM,
        tool_registry: ToolRegistry,
        execution_event_repository: ExecutionEventRepository,
        cancellation_token: CancellationToken,
        max_iterations: int = 6,
    ):
        self.llm = llm
        self.tool_registry = tool_registry
        self.execution_event_repository = execution_event_repository
        self.cancellation_token = cancellation_token
        self.max_iterations = max_iterations

    async def execute(
        self,
        execution_id: str,
        system_prompt: str,
        user_input: str,
    ) -> dict:

        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ]

        tool_calls_accumulated: List[Dict[str, Any]] = []

        for iteration in range(self.max_iterations):

            if self.cancellation_token.is_cancelled():
                await self._emit_cancel_event(execution_id)
                return self._cancelled_result(tool_calls_accumulated)

            await self.execution_event_repository.add(
                ExecutionEvent.create(
                    execution_id=execution_id,
                    event_type=ExecutionEventType.LLM_REQUEST,
                    payload={
                        "iteration": iteration,
                        "messages": messages,
                    },
                )
            )

            response = await self.llm.generate(
                messages=messages,
                tools=self.tool_registry.get_tool_definitions(),
            )

            message = response.get("message", {})

            await self.execution_event_repository.add(
                ExecutionEvent.create(
                    execution_id=execution_id,
                    event_type=ExecutionEventType.LLM_RESPONSE,
                    payload={
                        "iteration": iteration,
                        "response": response,
                    },
                )
            )

            if not message:
                break

            messages.append(message)

            if "tool_calls" in message and message["tool_calls"]:

                for tool_call in message["tool_calls"]:

                    if self.cancellation_token.is_cancelled():
                        await self._emit_cancel_event(execution_id)
                        return self._cancelled_result(tool_calls_accumulated)

                    tool_name = tool_call["function"]["name"]
                    arguments = tool_call["function"]["arguments"]
                    tool_call_id = tool_call.get("id")

                    result = await self.tool_registry.execute(
                        tool_name,
                        arguments,
                    )

                    tool_calls_accumulated.append({
                        "tool": tool_name,
                        "arguments": arguments,
                        "result": result,
                    })

                    await self.execution_event_repository.add(
                        ExecutionEvent.create(
                            execution_id=execution_id,
                            event_type=ExecutionEventType.TOOL_EXECUTION,
                            payload={
                                "iteration": iteration,
                                "tool": tool_name,
                                "arguments": arguments,
                                "result": result,
                            },
                        )
                    )

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "content": str(result),
                    })

                continue

            final_output = message.get("content", "")

            await self.execution_event_repository.add(
                ExecutionEvent.create(
                    execution_id=execution_id,
                    event_type=ExecutionEventType.AGENT_OUTPUT,
                    payload={
                        "iteration": iteration,
                        "agent_output": final_output,
                    },
                )
            )

            return {
                "final_output": final_output,
                "tool_calls": tool_calls_accumulated,
                "raw_response": response,
                "status": "completed",
            }

        await self.execution_event_repository.add(
            ExecutionEvent.create(
                execution_id=execution_id,
                event_type=ExecutionEventType.MAX_ITERATIONS_REACHED,
                payload={
                    "max_iterations": self.max_iterations,
                },
            )
        )

        return {
            "final_output": "Max iterations reached.",
            "tool_calls": tool_calls_accumulated,
            "raw_response": {},
            "status": "failed",
        }

    async def _emit_cancel_event(self, execution_id: str) -> None:
        await self.execution_event_repository.add(
            ExecutionEvent.create(
                execution_id=execution_id,
                event_type=ExecutionEventType.TASK_CANCELLED,
                payload={
                    "reason": "Cancellation requested",
                },
            )
        )

    def _cancelled_result(self, tool_calls: List[Dict[str, Any]]) -> dict:
        return {
            "final_output": "Task cancelled.",
            "tool_calls": tool_calls,
            "raw_response": {},
            "status": "cancelled",
        }