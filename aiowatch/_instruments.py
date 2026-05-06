from __future__ import annotations

from dataclasses import dataclass

from opentelemetry.metrics import Meter


@dataclass(slots=True)
class LoopInstruments:
    lag_histogram: object
    pending_tasks_gauge: object
    tasks_created_counter: object
    tasks_done_counter: object


@dataclass(slots=True)
class ThreadPoolInstruments:
    active_gauge: object
    queued_gauge: object
    max_workers_gauge: object
    utilization_gauge: object


def create_loop_instruments(meter: Meter, gauge_callback: object) -> LoopInstruments:
    return LoopInstruments(
        lag_histogram=meter.create_histogram(
            name="aiowatch.loop.lag",
            unit="s",
            description="call_soon to callback execution delay.",
        ),
        pending_tasks_gauge=meter.create_observable_gauge(
            name="aiowatch.loop.tasks",
            callbacks=[gauge_callback],
            unit="{task}",
            description="Current number of pending asyncio tasks.",
        ),
        tasks_created_counter=meter.create_counter(
            name="aiowatch.loop.tasks.created",
            unit="{task}",
            description="Total asyncio tasks created while aiowatch is active.",
        ),
        tasks_done_counter=meter.create_counter(
            name="aiowatch.loop.tasks.done",
            unit="{task}",
            description="Total asyncio tasks completed while aiowatch is active.",
        ),
    )


def create_threadpool_instruments(meter: Meter, gauge_callback: object) -> ThreadPoolInstruments:
    return ThreadPoolInstruments(
        active_gauge=meter.create_observable_gauge(
            name="aiowatch.threadpool.active",
            callbacks=[gauge_callback],
            unit="{thread}",
            description="Busy worker threads per thread pool.",
        ),
        queued_gauge=meter.create_observable_gauge(
            name="aiowatch.threadpool.queued",
            callbacks=[gauge_callback],
            unit="{task}",
            description="Queued tasks waiting for thread pool workers.",
        ),
        max_workers_gauge=meter.create_observable_gauge(
            name="aiowatch.threadpool.max_workers",
            callbacks=[gauge_callback],
            unit="{thread}",
            description="Configured max worker threads per pool.",
        ),
        utilization_gauge=meter.create_observable_gauge(
            name="aiowatch.threadpool.utilization",
            callbacks=[gauge_callback],
            unit="1",
            description="active / max_workers ratio per pool.",
        ),
    )
