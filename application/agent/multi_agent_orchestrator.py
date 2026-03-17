from application.agent.runtime import AgentRuntime
from domain.entities.execution_event import (
    ExecutionEvent,
    ExecutionEventType,
)
from domain.repositories.execution_event_repository import (
    ExecutionEventRepository,
)
import os
import shutil
import logging
from application.constants import WORKSPACE_DIR

PLANNER_PROMPT = """You are a senior software architect and technical planner. Your sole job is to read the user's coding request and produce a precise, structured implementation plan.

Your output MUST follow this exact format:
TASK SUMMARY: <one sentence describing what will be built>
LANGUAGE & STACK: <language, frameworks, libraries>
FILE STRUCTURE:
- <filename>: <purpose>
IMPLEMENTATION STEPS:
1. <specific step>
2. <specific step>
...
EDGE CASES TO HANDLE:
- <edge case>
EXPECTED OUTPUT: <what the final result should look like>

Do NOT write any code. Only output the plan in the format above. Be specific about function names, class names, and data structures."""

EXECUTOR_PROMPT = """You are a senior software engineer. You will receive an implementation plan. Your job is to write the complete, working code exactly as specified in the plan.

Rules:
- Write complete, runnable code — no placeholders, no TODOs, no "..." shortcuts
- Use write_file tool to save each file as you create it
- Use read_file tool if you need to check a file you already wrote
- Use run_python tool to test your code after writing it
- If run_python returns an error, fix the code and run it again
- Only stop when the code runs without errors

Output only the final working code summary after all files are written."""

REVIEWER_PROMPT = """You are a strict code reviewer. You will receive code that has been written by an AI executor agent. Review it thoroughly.

Your output MUST follow this exact format:
SCORE: <number>/10
VERDICT: <PASS if score >= 7, FAIL if score < 7>
ISSUES:
- [CRITICAL] <issue> (blocks functionality)
- [WARNING] <issue> (degrades quality)
- [INFO] <issue> (minor suggestion)
STRENGTHS:
- <what was done well>
SUMMARY: <2-3 sentence overall assessment>

Review criteria: correctness, error handling, edge cases, code clarity, security, performance."""


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

        # Clear workspace at start of each pipeline run
        # Clear workspace at start of each pipeline run
        if os.path.exists(WORKSPACE_DIR):
            shutil.rmtree(WORKSPACE_DIR)
        os.makedirs(WORKSPACE_DIR, exist_ok=True)

        # -------------------------
        # 1️⃣ PLANNER
        # -------------------------
        await self._emit_role_event(execution_id, "PLANNER", "started")

        planner_result = await self.planner_runtime.execute(
            execution_id=execution_id,
            system_prompt=PLANNER_PROMPT,
            user_input=user_input,
        )

        if planner_result.get("status") != "completed":
            return planner_result

        await self._emit_role_event(execution_id, "PLANNER", "completed")

        plan_output = planner_result.get("final_output", "")

        # Emit plan immediately so frontend shows it now
        await self._emit_section(execution_id, "PLAN", plan_output)

        # -------------------------
        # 2️⃣ EXECUTOR
        # -------------------------
        await self._emit_role_event(execution_id, "EXECUTOR", "started")

        executor_result = await self.executor_runtime.execute(
            execution_id=execution_id,
            system_prompt=EXECUTOR_PROMPT,
            user_input=plan_output,
        )

        if executor_result.get("status") != "completed":
            return executor_result

        await self._emit_role_event(execution_id, "EXECUTOR", "completed")

        # Always read workspace files first
        logger = logging.getLogger("orchestratemax")

        # Always read workspace files for code output
        code_parts = []
        logger.info(f"Reading workspace from: {WORKSPACE_DIR}")
        logger.info(f"Workspace exists: {os.path.exists(WORKSPACE_DIR)}")

        if os.path.exists(WORKSPACE_DIR):
            all_files = os.listdir(WORKSPACE_DIR)
            logger.info(f"Files in workspace: {all_files}")
            for filename in sorted(all_files):
                filepath = os.path.join(WORKSPACE_DIR, filename)
                if os.path.isfile(filepath):
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                    ext = filename.rsplit(".", 1)[-1] if "." in filename else "python"
                    code_parts.append(f"```{ext}\n{content}\n```")
                    logger.info(f"Read file: {filename} ({len(content)} chars)")

        if code_parts:
            execution_output = "\n\n".join(code_parts)
            # Also build a clean version for the reviewer (no markdown fences)
            reviewer_input = "\n\n".join([
                f"# {filename}\n" + open(
                    os.path.join(WORKSPACE_DIR, filename), "r", encoding="utf-8"
                ).read()
                for filename in sorted(os.listdir(WORKSPACE_DIR))
                if os.path.isfile(os.path.join(WORKSPACE_DIR, filename))
            ])
            logger.info(f"Using workspace files for code output")
        else:
            # Fallback to executor text output only if no files were written
            execution_output = executor_result.get("final_output", "")
            reviewer_input = execution_output
            logger.warning(f"No workspace files found, falling back to executor output")

        # Pass the actual code to the reviewer
        await self._emit_section(execution_id, "CODE", execution_output)

        # -------------------------
        # 3️⃣ REVIEWER
        # -------------------------
        await self._emit_role_event(execution_id, "REVIEWER", "started")

        reviewer_result = await self.reviewer_runtime.execute(
            execution_id=execution_id,
            system_prompt=REVIEWER_PROMPT,
            user_input=reviewer_input,
        )

        if reviewer_result.get("status") != "completed":
            return reviewer_result

        await self._emit_role_event(execution_id, "REVIEWER", "completed")

        review_output = reviewer_result.get("final_output", "")

        # Emit review immediately
        await self._emit_section(execution_id, "REVIEW", review_output)

        # Build combined output for storage
        combined_output = (
            "## Plan\n\n"
            + plan_output
            + "\n\n---\n\n"
            + "## Code\n\n"
            + execution_output
            + "\n\n---\n\n"
            + "## Review\n\n"
            + review_output
        )

        # Emit the single terminal FINAL_OUTPUT
        from domain.entities.execution_event import ExecutionEvent, ExecutionEventType
        await self.event_repo.add(
            ExecutionEvent.create(
                execution_id=execution_id,
                event_type=ExecutionEventType.FINAL_OUTPUT,
                payload={
                    "final_output": combined_output,
                },
            )
        )

        reviewer_result["final_output"] = combined_output
        return reviewer_result

    async def _emit_section(self, execution_id: str, section: str, content: str):
        from domain.entities.execution_event import ExecutionEvent, ExecutionEventType
        await self.event_repo.add(
            ExecutionEvent.create(
                execution_id=execution_id,
                event_type=ExecutionEventType.AGENT_SECTION_READY,
                payload={
                    "section": section,
                    "content": content,
                },
            )
        )

    async def _emit_role_event(self, execution_id: str, role: str, status: str):
        event_type = (
            ExecutionEventType.AGENT_ROLE_STARTED 
            if status == "started" 
            else ExecutionEventType.AGENT_ROLE_COMPLETED
        )
        await self.event_repo.add(
            ExecutionEvent.create(
                execution_id=execution_id,
                event_type=event_type,
                payload={
                    "agent_role": role,
                    "status": status
                },
            )
        )