# agent/executor_engine.py — Multi-Worker Parallel Execution Engine for JARVIS MK37
from __future__ import annotations

import asyncio
import inspect
import logging
import time
from typing import Any, Callable, Dict, List, Optional
from agent.types import ExecutionReport, GoalGraph, StepStatus, TaskStepNode
from core.runtime import get_runtime
from events.bus import get_event_bus
from events.types import TaskEvent

logger = logging.getLogger("JARVIS.ExecutorEngine")


class ParallelExecutionEngine:
    """Multi-Worker Parallel Task Execution Engine with Human-in-the-Loop Safety Interlocks."""

    def __init__(self, max_workers: Optional[int] = None):
        self.runtime = get_runtime()
        self.event_bus = get_event_bus()
        self.max_workers = max_workers or self.runtime.config.system.max_workers
        self._cancelled = False

        # Register self in DI container
        self.runtime.container.register_instance(ParallelExecutionEngine, self)
        logger.info(f"⚡ ParallelExecutionEngine initialized with {self.max_workers} parallel workers")

    def cancel_all(self) -> None:
        """Emergency stop: Cancel all active and queued goal executions."""
        self._cancelled = True
        logger.warning("🛑 Emergency Stop Signal Issued: Cancelling ExecutionEngine")

    async def execute_step(
        self,
        step: TaskStepNode,
        tool_resolver_fn: Optional[Callable[[str, Dict[str, Any]], Any]] = None,
    ) -> TaskStepNode:
        """Execute a single DAG task step with safety interlock and verification."""
        if self._cancelled:
            step.status = StepStatus.CANCELLED
            return step

        # Human-in-the-Loop Safety Interlock
        if step.requires_approval and step.status != StepStatus.SUCCESS:
            step.status = StepStatus.WAITING_FOR_APPROVAL
            logger.warning(f"⚠️ Human Approval Interlock: Step #{step.step_id} [{step.description}] requires confirmation!")
            self.event_bus.publish(TaskEvent(
                topic="task.step.approval_required",
                task_id=str(step.step_id),
                goal=step.description,
                status="WAITING_FOR_APPROVAL",
                payload={"tool": step.tool, "risk_level": step.risk_level.value}
            ))
            return step

        step.status = StepStatus.IN_PROGRESS
        step.start_time = time.time()

        self.event_bus.publish(TaskEvent(
            topic="task.step.start",
            task_id=str(step.step_id),
            goal=step.description,
            status="IN_PROGRESS"
        ))

        try:
            logger.info(f"▶ Executing Step #{step.step_id}: {step.description} (Tool: {step.tool})")

            # Execute tool if resolver provided
            if tool_resolver_fn:
                if inspect.iscoroutinefunction(tool_resolver_fn):
                    res = await tool_resolver_fn(step.tool, step.parameters)
                else:
                    res = tool_resolver_fn(step.tool, step.parameters)
                step.result = res
            else:
                # Simulated verification execution
                await asyncio.sleep(0.05)
                step.result = {"status": "success", "executed_tool": step.tool}

            step.status = StepStatus.SUCCESS
            step.end_time = time.time()

            self.event_bus.publish(TaskEvent(
                topic="task.step.completed",
                task_id=str(step.step_id),
                goal=step.description,
                status="SUCCESS",
                payload={"result": str(step.result)}
            ))

        except Exception as e:
            step.status = StepStatus.FAILED
            step.error = str(e)
            step.end_time = time.time()
            logger.error(f"❌ Step #{step.step_id} Failed: {e}", exc_info=True)

            self.event_bus.publish(TaskEvent(
                topic="task.step.failed",
                task_id=str(step.step_id),
                goal=step.description,
                status="FAILED",
                payload={"error": str(e)}
            ))

        return step

    async def execute_graph(
        self,
        graph: GoalGraph,
        tool_resolver_fn: Optional[Callable[[str, Dict[str, Any]], Any]] = None,
    ) -> ExecutionReport:
        """Execute an entire GoalGraph DAG respecting step dependencies and parallelism."""
        self._cancelled = False
        start_t = time.time()
        completed_count = 0
        total_steps = len(graph.steps)

        logger.info(f"🚀 Executing GoalGraph [{graph.goal}] ({total_steps} steps)")

        # DAG resolution loop
        while completed_count < total_steps and not self._cancelled:
            ready_steps = [
                s for s in graph.steps
                if s.status == StepStatus.PENDING and
                all(graph.steps[dep - 1].status == StepStatus.SUCCESS for dep in s.depends_on)
            ]

            if not ready_steps:
                # Check for failed or blocked steps
                if any(s.status == StepStatus.FAILED for s in graph.steps):
                    break
                if any(s.status == StepStatus.WAITING_FOR_APPROVAL for s in graph.steps):
                    logger.info("⏸ Graph execution paused waiting for user approval.")
                    break
                # No progress possible
                break

            # Execute ready steps (parallel workers up to max_workers)
            batch = ready_steps[:self.max_workers]
            tasks = [self.execute_step(step, tool_resolver_fn) for step in batch]
            results = await asyncio.gather(*tasks)

            for step in results:
                if step.status == StepStatus.SUCCESS:
                    completed_count += 1
                elif step.status == StepStatus.FAILED and step.critical:
                    logger.error(f"Critical Step #{step.step_id} failed. Halting graph execution.")
                    break

        duration = time.time() - start_t
        overall_status = "SUCCESS" if completed_count == total_steps else "PARTIAL" if completed_count > 0 else "FAILED"

        return ExecutionReport(
            goal_id=graph.goal_id,
            status=overall_status,
            completed_steps=completed_count,
            total_steps=total_steps,
            duration_s=duration,
        )


_global_executor_engine: Optional[ParallelExecutionEngine] = None


def get_executor_engine() -> ParallelExecutionEngine:
    global _global_executor_engine
    if _global_executor_engine is None:
        _global_executor_engine = ParallelExecutionEngine()
    return _global_executor_engine
