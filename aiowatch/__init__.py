from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any

from .__about__ import __version__
from ._loop import LoopMonitor
from ._task import TaskTracker
from ._threadpool import ThreadPoolMonitor

__all__ = ["AioWatch", "__version__"]


class AioWatch:
    def __init__(
        self,
        meter: object,
        tracer: object | None = None,
        collect_interval: float = 5.0,
        slow_callback_threshold: float = 0.1,
        thread_pools: dict[str, ThreadPoolExecutor] | None = None,
        trace_filter: object | None = None,
        patch_to_thread: bool = False,
        include_coroutine_name: bool = False,
    ) -> None:
        self._meter = meter
        self._tracer = tracer
        self._collect_interval = collect_interval
        self._slow_callback_threshold = slow_callback_threshold
        self._trace_filter = trace_filter
        self._patch_to_thread = patch_to_thread
        self._running = False

        self._loop_monitor = LoopMonitor(meter=meter, collect_interval=collect_interval)
        self._task_tracker = TaskTracker(
            instruments=self._loop_monitor.instruments,
            include_coroutine_name=include_coroutine_name,
        )
        self._thread_pool_monitor = ThreadPoolMonitor(meter=meter, pools=thread_pools)

    async def __aenter__(self) -> "AioWatch":
        await self.start()
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        await self.stop()

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        await self._task_tracker.start()
        await self._loop_monitor.start()

    async def stop(self) -> None:
        if not self._running:
            return
        self._running = False
        await self._loop_monitor.stop()
        await self._task_tracker.stop()

    def register_thread_pool(self, name: str, executor: ThreadPoolExecutor) -> None:
        self._thread_pool_monitor.register(name, executor)

    def unregister_thread_pool(self, name: str) -> None:
        self._thread_pool_monitor.unregister(name)

    def snapshot(self) -> dict[str, Any]:
        loop_snapshot = self._loop_monitor.snapshot()
        return {
            "loop_lag_seconds": loop_snapshot["loop_lag_seconds"],
            "pending_tasks": loop_snapshot["pending_tasks"],
            "thread_pools": self._thread_pool_monitor.snapshot(),
            "slow_callbacks_last_minute": 0,
        }
