from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from application.services.task_service import TaskService
from application.services.session_service import SessionService
import os
import shutil
import asyncio

from application.events.event_bus import event_bus
from sse_starlette.sse import EventSourceResponse
from application.llm.ollama_client import OllamaClient
from application.agent.agent_controller import AgentController
from application.agent.task_executor import TaskExecutor
from application.constants import WORKSPACE_DIR
from config import settings

from container import get_task_service, get_session_service
from infrastructure.database.session import engine, Base, AsyncSessionLocal
from infrastructure.repositories.sqlalchemy_execution_event_repository import (
    SQLAlchemyExecutionEventRepository,
)
from infrastructure.repositories.execution_repository import ExecutionRepository
from infrastructure.repositories.sqlalchemy_artifact_repository import (
    SQLAlchemyArtifactRepository,
)

from domain.entities.execution_event import ExecutionEventType

from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse
import traceback
import logging
import json

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("orchestratemax")

app = FastAPI()

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(
        f"Unhandled exception on {request.method} {request.url}: {exc}",
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Check server logs."},
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

llm = OllamaClient()

# ---------------------------------
# Global Task Executor (Worker Pool)
# ---------------------------------
task_executor = TaskExecutor(
    llm,
    timeout_seconds=settings.TIMEOUT_SECONDS,
    max_workers=settings.MAX_WORKERS,
    max_retries=settings.MAX_RETRIES,
)


# -----------------------------
# Database Initialization & Health
# -----------------------------
@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/health")
async def health_check():
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Database unavailable")

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

@app.get("/sessions")
async def list_sessions(
    service: SessionService = Depends(get_session_service),
):
    sessions = await service.list_sessions()
    return [
        {"id": s.id, "name": s.name, "created_at": s.created_at}
        for s in sessions
    ]

@app.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    service: SessionService = Depends(get_session_service),
):
    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    await service.delete_session(session_id)
    return {"message": "Session deleted."}

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

@app.get("/sessions/{session_id}/tasks")
async def list_session_tasks(
    session_id: str,
    task_service: TaskService = Depends(get_task_service),
    session_service: SessionService = Depends(get_session_service),
):
    session = await session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    tasks = await task_service.get_tasks_by_session(session_id)
    return [
        {
            "id": t.id,
            "session_id": t.session_id,
            "title": t.title,
            "description": t.description,
            "status": t.status,
            "created_at": t.created_at,
            "updated_at": t.updated_at,
        }
        for t in tasks
    ]

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

    async with AsyncSessionLocal() as db:
        execution_repo = ExecutionRepository(db)
        latest_execution = await execution_repo.get_latest_by_task_id(task_id)

    return {
        "id": task.id,
        "session_id": task.session_id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "final_output": latest_execution.final_output if latest_execution else None,
        "error_message": latest_execution.error_message if latest_execution else None,
        "execution_started_at": latest_execution.started_at if latest_execution else None,
        "execution_finished_at": latest_execution.finished_at if latest_execution else None,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
    }

@app.get("/tasks/{task_id}/executions")
async def list_task_executions(task_id: str):
    async with AsyncSessionLocal() as db:
        repo = ExecutionRepository(db)
        executions = await repo.get_by_task(task_id)
    return [
        {
            "id": e.id,
            "task_id": e.task_id,
            "status": e.status,
            "attempt_number": e.attempt_number,
            "started_at": e.started_at,
            "finished_at": e.finished_at,
            "final_output": e.final_output,
            "error_message": e.error_message,
        }
        for e in executions
    ]

@app.get("/executions/{execution_id}/artifacts")
async def get_execution_artifacts(execution_id: str):
    async with AsyncSessionLocal() as db:
        repo = SQLAlchemyArtifactRepository(db)
        artifacts = await repo.get_by_execution_id(execution_id)
    return [
        {
            "id": a.id,
            "execution_id": a.execution_id,
            "name": a.name,
            "artifact_type": a.artifact_type,
            "content": a.content,
            "created_at": a.created_at,
        }
        for a in artifacts
    ]

# -----------------------------
# Workspace Management
# -----------------------------

@app.delete("/workspace")
async def clear_workspace():
    if os.path.exists(WORKSPACE_DIR):
        shutil.rmtree(WORKSPACE_DIR)
    os.makedirs(WORKSPACE_DIR, exist_ok=True)
    return {"message": "Workspace cleared."}

@app.get("/workspace/files")
async def list_workspace_files():
    files = []
    for root, dirs, filenames in os.walk(WORKSPACE_DIR):
        for filename in filenames:
            full = os.path.join(root, filename)
            rel = os.path.relpath(full, WORKSPACE_DIR)
            files.append(rel.replace("\\", "/"))
    return {"files": files}

@app.get("/workspace/files/{file_path:path}")
async def get_workspace_file(file_path: str):
    safe_path = os.path.normpath(os.path.join(WORKSPACE_DIR, file_path))
    if not safe_path.startswith(os.path.normpath(WORKSPACE_DIR)):
        raise HTTPException(status_code=400, detail="Invalid path")
    if not os.path.exists(safe_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(safe_path)


# -----------------------------
# Agent Execution Endpoint (Execution-Owned)
# -----------------------------
@app.post("/agent-run/{session_id}/{task_id}")
async def run_agent(
    session_id: str,
    task_id: str,
    request: AgentRunRequest,
):
    import uuid

    execution_id = str(uuid.uuid4())

    try:
        task_executor.enqueue_execution(
            session_id,
            task_id,
            execution_id,
            request.user_input,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"execution_id": execution_id}


# -----------------------------
# Event Streaming & History
# -----------------------------

TERMINAL_EVENT_TYPES = {
    "FINAL_OUTPUT",
    "TASK_CANCELLED",
    "TASK_TIMEOUT",
    "MAX_ITERATIONS_REACHED",
}

@app.get("/executions/{execution_id}/stream")
async def stream_execution_events(execution_id: str):
    async def generator():
        queue = event_bus.subscribe(execution_id)
        try:
            while True:
                try:
                    event_data = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield {"data": json.dumps(event_data)}
                    if event_data.get("event_type") in TERMINAL_EVENT_TYPES:
                        break
                except asyncio.TimeoutError:
                    yield {"data": json.dumps({"event_type": "HEARTBEAT"})}
        finally:
            event_bus.unsubscribe(execution_id, queue)
    return EventSourceResponse(generator())

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

        llm_calls: int = 0
        tool_calls: int = 0
        retries: int = 0

        model_token_usage: dict = {}
        total_llm_duration_ms: int = 0

        for e in events_sorted:

            if e.event_type == ExecutionEventType.LLM_REQUEST:
                if e.payload and "iteration" in e.payload:
                    llm_calls = llm_calls + 1

            if e.event_type == ExecutionEventType.TOOL_EXECUTION:
                tool_calls = tool_calls + 1

            if e.event_type == ExecutionEventType.RETRY_SCHEDULED:
                retries = retries + 1

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

                model_token_usage[model]["prompt_tokens"] += int(prompt_tokens)
                model_token_usage[model]["completion_tokens"] += int(completion_tokens)

                total_duration_ns = int(response.get("total_duration", 0))
                total_llm_duration_ms = total_llm_duration_ms + (total_duration_ns // 1_000_000)

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
                float(usage["prompt_tokens"]) / 1000.0
            ) * float(pricing["prompt_per_1k"])

            completion_cost = (
                float(usage["completion_tokens"]) / 1000.0
            ) * float(pricing["completion_per_1k"])

            model_cost = float(prompt_cost) + float(completion_cost)
            estimated_cost += model_cost

            cost_breakdown[model] = {
                "prompt_tokens": usage["prompt_tokens"],
                "completion_tokens": usage["completion_tokens"],
                "estimated_cost_usd": round(float(model_cost), 6),
            }

        start_time = events_sorted[0].created_at
        end_time = events_sorted[-1].created_at

        total_duration_ms = int(
            (end_time - start_time).total_seconds() * 1000
        )

        avg_llm_latency_ms = (
            (total_llm_duration_ms // llm_calls)
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
            "estimated_cost_usd": round(float(estimated_cost), 6),
            "cost_breakdown": cost_breakdown,
        }