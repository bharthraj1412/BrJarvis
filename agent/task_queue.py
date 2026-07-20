# agent/task_queue.py — JARVIS MK37 Parallel Task Queue
"""
High-performance task queue with parallel execution support.
- Concurrent goal execution (multiple tasks at once)
- Priority-based scheduling
- Real-time status tracking
- Cancellation support
"""
from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Any


class TaskStatus(Enum):
    PENDING   = "pending"
    RUNNING   = "running"
    COMPLETED = "completed"
    FAILED    = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    LOW    = 3
    NORMAL = 2
    HIGH   = 1


@dataclass(order=True)
class Task:
    priority:    int
    created_at:  float        = field(compare=False)
    task_id:     str          = field(compare=False)
    goal:        str          = field(compare=False)
    status:      TaskStatus   = field(compare=False, default=TaskStatus.PENDING)
    result:      Any          = field(compare=False, default=None)
    error:       str          = field(compare=False, default="")
    speak:       Any          = field(compare=False, default=None)
    on_complete: Any          = field(compare=False, default=None)
    cancel_flag: threading.Event = field(compare=False, default_factory=threading.Event)
    started_at:  float        = field(compare=False, default=0.0)
    finished_at: float        = field(compare=False, default=0.0)


class TaskQueue:
    """
    Multi-threaded task queue with parallel execution.
    Tasks can run simultaneously (configurable concurrency).
    """

    def __init__(self, max_concurrent: int = 3):
        self._queue:    list[Task]       = []
        self._lock:     threading.Lock   = threading.Lock()
        self._cond:     threading.Condition = threading.Condition(self._lock)
        self._tasks:    dict[str, Task]  = {}
        self._running:  bool             = False
        self._workers:  list[threading.Thread] = []
        self._active:   int              = 0
        self._max       = max_concurrent
        self._executor  = None

    def _get_executor(self):
        if self._executor is None:
            from agent.executor import AgentExecutor
            self._executor = AgentExecutor()
        return self._executor

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        # Start multiple worker threads for concurrency
        for i in range(self._max):
            t = threading.Thread(
                target=self._worker_loop,
                daemon=True,
                name=f"AgentWorker-{i+1}"
            )
            t.start()
            self._workers.append(t)
        print(f"[TaskQueue] ✅ Started with {self._max} workers")

    def stop(self) -> None:
        self._running = False
        with self._cond:
            self._cond.notify_all()

    def submit(
        self,
        goal:        str,
        priority:    TaskPriority = TaskPriority.NORMAL,
        speak:       Callable | None = None,
        on_complete: Callable | None = None,
    ) -> str:
        """Submit a goal for execution. Returns task ID immediately."""
        task_id = uuid.uuid4().hex[:8]
        task = Task(
            priority   = priority.value,
            created_at = time.time(),
            task_id    = task_id,
            goal       = goal,
            speak      = speak,
            on_complete = on_complete,
        )

        with self._cond:
            self._queue.append(task)
            self._queue.sort(key=lambda t: (t.priority, t.created_at))
            self._tasks[task_id] = task
            self._cond.notify()

        print(f"[TaskQueue] 📥 Queued [{task_id}]: {goal[:60]}")
        return task_id

    def submit_many(
        self,
        goals:       list[str],
        priority:    TaskPriority = TaskPriority.NORMAL,
        speak:       Callable | None = None,
    ) -> list[str]:
        """Submit multiple goals simultaneously. All run in parallel if capacity allows."""
        return [self.submit(goal, priority, speak) for goal in goals]

    def cancel(self, task_id: str) -> bool:
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return False
            if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
                return False
            task.cancel_flag.set()
            task.status = TaskStatus.CANCELLED
        return True

    def get_status(self, task_id: str) -> dict | None:
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return None
            duration = ""
            if task.started_at:
                end = task.finished_at or time.time()
                duration = f"{end - task.started_at:.1f}s"
            return {
                "task_id":  task.task_id,
                "goal":     task.goal,
                "status":   task.status.value,
                "result":   task.result,
                "error":    task.error,
                "duration": duration,
            }

    def get_all_statuses(self) -> list[dict]:
        with self._lock:
            statuses = []
            for task in self._tasks.values():
                statuses.append({
                    "task_id": task.task_id,
                    "goal":    task.goal[:50],
                    "status":  task.status.value,
                    "result":  (task.result or "")[:80] if task.result else "",
                })
            return statuses

    def pending_count(self) -> int:
        with self._lock:
            return sum(1 for t in self._queue if t.status == TaskStatus.PENDING)

    def active_count(self) -> int:
        with self._lock:
            return self._active

    def wait_for(self, task_id: str, timeout: float = 300) -> dict | None:
        """Block until a specific task completes. Returns its status dict."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            status = self.get_status(task_id)
            if status and status["status"] in ("completed", "failed", "cancelled"):
                return status
            time.sleep(0.5)
        return self.get_status(task_id)

    def _worker_loop(self) -> None:
        """Worker thread: picks up tasks and executes them."""
        while self._running:
            task = None
            with self._cond:
                while self._running and not self._can_pick():
                    self._cond.wait(timeout=1.0)
                if self._running:
                    task = self._next_task()
                    if task:
                        task.status   = TaskStatus.RUNNING
                        task.started_at = time.time()
                        self._active += 1
                        try:
                            self._queue.remove(task)
                        except ValueError:
                            pass

            if task:
                self._run_task(task)

    def _can_pick(self) -> bool:
        return (
            self._active < self._max and
            any(t.status == TaskStatus.PENDING and not t.cancel_flag.is_set()
                for t in self._queue)
        )

    def _next_task(self) -> Task | None:
        for task in self._queue:
            if task.status == TaskStatus.PENDING and not task.cancel_flag.is_set():
                return task
        return None

    def _run_task(self, task: Task) -> None:
        print(f"[TaskQueue] ▶️ Running [{task.task_id}]: {task.goal[:60]}")
        try:
            from agent.executor import AgentExecutor
            executor = AgentExecutor()
            result = executor.execute(
                goal        = task.goal,
                speak       = task.speak,
                cancel_flag = task.cancel_flag,
            )

            with self._lock:
                if task.cancel_flag.is_set():
                    task.status = TaskStatus.CANCELLED
                else:
                    task.status     = TaskStatus.COMPLETED
                    task.result     = result
                    task.finished_at = time.time()
                self._active -= 1

            if task.on_complete and not task.cancel_flag.is_set():
                try:
                    task.on_complete(task.task_id, result)
                except Exception as e:
                    print(f"[TaskQueue] on_complete error: {e}")

            dur = task.finished_at - task.started_at if task.finished_at else 0
            print(f"[TaskQueue] ✅ [{task.task_id}] Completed in {dur:.1f}s")

        except Exception as e:
            with self._lock:
                task.status     = TaskStatus.FAILED
                task.error      = str(e)
                task.finished_at = time.time()
                self._active   -= 1
            print(f"[TaskQueue] ❌ [{task.task_id}] Failed: {e}")
            traceback.print_exc()

        with self._cond:
            self._cond.notify_all()


import traceback

# ── Global singleton ───────────────────────────────────────────────────────

_queue         = TaskQueue(max_concurrent=3)
_started       = False
_start_lock    = threading.Lock()


def get_queue() -> TaskQueue:
    global _started
    with _start_lock:
        if not _started:
            _queue.start()
            _started = True
    return _queue
