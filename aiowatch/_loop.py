from __future__ import annotations

import asyncio
import time
from typing import Iterable

from opentelemetry.metrics import Observation

from ._instruments import LoopInstruments, create_loop_instruments


class LoopMonitor:
    def __init__(self, meter: object, collect_interval: float) -> None:
        self._loop: asyncio.AbstractEventLoop | None = None
        self._collect_interval = collect_interval
        self._running = False
        self._collector_task: asyncio.Task[None] | None = None
        self._last_lag_seconds = 0.0
        self._pending_tasks = 0
        self.instruments: LoopInstruments = create_loop_instruments(
            meter=meter, gauge_callback=self._observe_pending_tasks
        )

    @property
    def last_lag_seconds(self) -> float:
        return self._last_lag_seconds

    @property
    def pending_tasks(self) -> int:
        return self._pending_tasks

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._loop = asyncio.get_running_loop()
        self._collector_task = asyncio.create_task(self._run(), name="aiowatch-loop-monitor")

    async def stop(self) -> None:
        if not self._running:
            return
        self._running = False
        if self._collector_task is not None:
            self._collector_task.cancel()
            try:
                await self._collector_task
            except asyncio.CancelledError:
                pass
        self._collector_task = None

    def snapshot(self) -> dict[str, float | int]:
        return {
            "loop_lag_seconds": self._last_lag_seconds,
            "pending_tasks": self._pending_tasks,
        }

    async def _run(self) -> None:
        while self._running:
            await self._sample_once()
            await asyncio.sleep(self._collect_interval)

    async def _sample_once(self) -> None:
        if self._loop is None:
            return
        self._last_lag_seconds = await self._measure_lag(self._loop)
        self.instruments.lag_histogram.record(self._last_lag_seconds)
        self._pending_tasks = sum(
            1 for task in asyncio.all_tasks(self._loop) if task is not asyncio.current_task() and not task.done()
        )

    async def _measure_lag(self, loop: asyncio.AbstractEventLoop) -> float:
        scheduled_at = time.monotonic()
        future: asyncio.Future[float] = loop.create_future()

        def callback() -> None:
            if not future.done():
                future.set_result(time.monotonic() - scheduled_at)

        loop.call_soon(callback)
        return await future

    def _observe_pending_tasks(self, _options: object) -> Iterable[Observation]:
        return [Observation(self._pending_tasks)]
