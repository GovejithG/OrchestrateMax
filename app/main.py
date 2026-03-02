from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from application.services.task_service import TaskService
from application.services.session_service import SessionService
from application.llm.ollama_client import OllamaClient
from application.agent.agent_controller import AgentController
from application.agent.task_executor import TaskExecutor

from container import get_task_service, get_session_service
from infrastructure.database.session import engine, Base, AsyncSessionLocal
from infrastructure.repositories.sqlalchemy_task_repository import (
    SQLAlchemyTaskRepository,
)
from infrastructure.repositories.sqlalchemy_execution_event_repository import (
    SQLAlchemyExecutionEventRepository,
)
from infrastructure.repositories.execution_repository import ExecutionRepository

from domain.entities.execution_event import ExecutionEventType

from fastapi.middleware.cors import CORSMiddleware

from domain.entities.execution import Execution


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

llm = OllamaClient()

# ---------------------------------
# Global Task Executor (Worker Pool)
# ---------------------------------
task_executor = TaskExecutor(timeout_seconds=30, max_workers=1)


# -----------------------------
# Database Initialization
# -----------------------------
@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# -----------------------------
# Request Schemas
# -----------------------------
class CreateSessionRequest(BaseModel):
    name: Optional[str] = None


class CreateTaskRequest(BaseModel):
    title: str
    description: Optional[str] = None


class AgentRunRequest(BaseModel):
    user_input: str


# -----------------------------
# Session Endpoints
# -----------------------------
@app.post("/sessions")
async def create_session(
    request: CreateSessionRequest,
    service: SessionService = Depends(get_session_service),
):
    session = await service.create_session(name=request.name)

    return {
        "id": session.id,
        "name": session.name,
        "created_at": session.created_at,
    }


# -----------------------------
# Task Endpoints
# -----------------------------
@app.post("/sessions/{session_id}/tasks")
async def create_task(
    session_id: str,
    request: CreateTaskRequest,
    task_service: TaskService = Depends(get_task_service),
    session_service: SessionService = Depends(get_session_service),
):
    session = await session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    task = await task_service.create_task(
        session_id=session_id,
        title=request.title,
        description=request.description,
    )

    return {
        "id": task.id,
        "session_id": task.session_id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "created_at": task.created_at,
    }


# -----------------------------
# Get Task Endpoint
# -----------------------------
@app.get("/tasks/{task_id}")
async def get_task(
    task_id: str,
    service: TaskService = Depends(get_task_service),
):
    task = await service.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return {
        "id": task.id,
        "session_id": task.session_id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "final_output": task.final_output,
        "error_message": task.error_message,
        "execution_started_at": task.execution_started_at,
        "execution_finished_at": task.execution_finished_at,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
    }


# -----------------------------
# Agent Execution Endpoint (Execution-Owned)
# -----------------------------
@app.post("/agent-run/{session_id}/{task_id}")
async def run_agent(
    session_id: str,
    task_id: str,
    request: AgentRunRequest,
):

    async with AsyncSessionLocal() as db:

        # 1️⃣ Create execution FIRST
        execution_repo = ExecutionRepository(db)

        execution = Execution.create(
            task_id=task_id,
            attempt_number=1,
        )

        await execution_repo.save(execution)

        execution_id = execution.id

        # 2️⃣ Create controller
        task_repo = SQLAlchemyTaskRepository(db)
        controller = AgentController(llm, task_repo)

        # 3️⃣ Enqueue execution
        try:
            task_executor.enqueue_execution(
                controller,
                session_id,
                execution_id,
                request.user_input,
            )
        except RuntimeError as e:
            raise HTTPException(status_code=400, detail=str(e))

    return {
        "message": "Execution started.",
        "execution_id": execution_id,
    }


# -----------------------------
# Get Execution Events
# -----------------------------
@app.get("/executions/{execution_id}/events")
async def get_execution_events(execution_id: str):

    async with AsyncSessionLocal() as db:
        repo = SQLAlchemyExecutionEventRepository(db)
        events = await repo.get_by_execution_id(execution_id)

    return [
        {
            "id": e.id,
            "execution_id": e.execution_id,
            "event_type": e.event_type,
            "payload": e.payload,
            "created_at": e.created_at,
        }
        for e in events
    ]


# -----------------------------
# Cancel Execution
# -----------------------------
@app.post("/executions/{execution_id}/cancel")
async def cancel_execution(execution_id: str):

    if not task_executor.is_running(execution_id):
        return {"message": "Execution not running or already finished."}

    cancelled = task_executor.cancel_execution(execution_id)

    if not cancelled:
        return {"message": "Cancellation token not found."}

    return {"message": "Cancellation requested."}


# -----------------------------
# Executor Status
# -----------------------------
@app.get("/executor/status")
async def executor_status():
    return task_executor.get_status()


from datetime import datetime
from infrastructure.repositories.sqlalchemy_execution_event_repository import (
    SQLAlchemyExecutionEventRepository,
)
from infrastructure.repositories.execution_repository import ExecutionRepository


MODEL_PRICING = {
    "gpt-4o-mini": {
        "prompt_per_1k": 0.00015,
        "completion_per_1k": 0.0006,
    },
    "gpt-4o": {
        "prompt_per_1k": 0.005,
        "completion_per_1k": 0.015,
    },
    "qwen2.5:7b-instruct": {
        "prompt_per_1k": 0.0,
        "completion_per_1k": 0.0,
    },
}


@app.get("/executions/{execution_id}/summary")
async def get_execution_summary(execution_id: str):

    async with AsyncSessionLocal() as db:

        execution_repo = ExecutionRepository(db)
        event_repo = SQLAlchemyExecutionEventRepository(db)

        execution = await execution_repo.get_by_id(execution_id)
        if not execution:
            return {"error": "Execution not found"}

        events = await event_repo.get_by_execution_id(execution_id)
        if not events:
            return {"error": "No events found"}

        events_sorted = sorted(events, key=lambda e: e.created_at)

        total_events = len(events_sorted)

        llm_calls = 0
        tool_calls = 0
        retries = 0

        model_token_usage = {}
        total_llm_duration_ms = 0

        for e in events_sorted:

            if e.event_type == ExecutionEventType.LLM_REQUEST:
                if e.payload and "iteration" in e.payload:
                    llm_calls += 1

            if e.event_type == ExecutionEventType.TOOL_EXECUTION:
                tool_calls += 1

            if e.event_type == ExecutionEventType.RETRY_SCHEDULED:
                retries += 1

            if e.event_type == ExecutionEventType.LLM_RESPONSE:
                response = e.payload.get("response", {})
                model = response.get("model")

                prompt_tokens = response.get("prompt_eval_count", 0)
                completion_tokens = response.get("eval_count", 0)

                if model not in model_token_usage:
                    model_token_usage[model] = {
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                    }

                model_token_usage[model]["prompt_tokens"] += prompt_tokens
                model_token_usage[model]["completion_tokens"] += completion_tokens

                total_duration_ns = response.get("total_duration", 0)
                total_llm_duration_ms += int(total_duration_ns / 1_000_000)

        # -------------------------
        # Cost Calculation
        # -------------------------
        estimated_cost = 0.0
        cost_breakdown = {}

        for model, usage in model_token_usage.items():

            pricing = MODEL_PRICING.get(model, {
                "prompt_per_1k": 0.0,
                "completion_per_1k": 0.0,
            })

            prompt_cost = (
                usage["prompt_tokens"] / 1000
            ) * pricing["prompt_per_1k"]

            completion_cost = (
                usage["completion_tokens"] / 1000
            ) * pricing["completion_per_1k"]

            model_cost = prompt_cost + completion_cost
            estimated_cost += model_cost

            cost_breakdown[model] = {
                "prompt_tokens": usage["prompt_tokens"],
                "completion_tokens": usage["completion_tokens"],
                "estimated_cost_usd": round(model_cost, 6),
            }

        start_time = events_sorted[0].created_at
        end_time = events_sorted[-1].created_at

        total_duration_ms = int(
            (end_time - start_time).total_seconds() * 1000
        )

        avg_llm_latency_ms = (
            int(total_llm_duration_ms / llm_calls)
            if llm_calls > 0
            else 0
        )

        return {
            "execution_id": execution_id,
            "status": execution.status,
            "attempt_number": execution.attempt_number,
            "total_events": total_events,
            "llm_calls": llm_calls,
            "tool_calls": tool_calls,
            "retries": retries,
            "total_duration_ms": total_duration_ms,
            "total_llm_duration_ms": total_llm_duration_ms,
            "avg_llm_latency_ms": avg_llm_latency_ms,
            "estimated_cost_usd": round(estimated_cost, 6),
            "cost_breakdown": cost_breakdown,
        }