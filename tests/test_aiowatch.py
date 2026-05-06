from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor

import pytest
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader

from aiowatch import AioWatch


async def _noop() -> None:
    return None


@pytest.mark.asyncio
async def test_aiowatch_collects_loop_and_task_metrics() -> None:
    reader = InMemoryMetricReader()
    meter_provider = MeterProvider(metric_readers=[reader])
    meter = meter_provider.get_meter("tests.aiowatch")

    async with AioWatch(meter=meter, collect_interval=0.02):
        await asyncio.sleep(0.05)
        task = asyncio.create_task(_noop())
        await task
        await asyncio.sleep(0.05)

    data = reader.get_metrics_data()
    metric_names = {
        metric.name
        for resource_metric in data.resource_metrics
        for scope_metric in resource_metric.scope_metrics
        for metric in scope_metric.metrics
    }
    assert "aiowatch.loop.lag" in metric_names
    assert "aiowatch.loop.tasks" in metric_names
    assert "aiowatch.loop.tasks.created" in metric_names
    assert "aiowatch.loop.tasks.done" in metric_names


@pytest.mark.asyncio
async def test_threadpool_snapshot_register_unregister() -> None:
    reader = InMemoryMetricReader()
    meter_provider = MeterProvider(metric_readers=[reader])
    meter = meter_provider.get_meter("tests.threadpool")
    pool = ThreadPoolExecutor(max_workers=2)

    watch = AioWatch(meter=meter)
    watch.register_thread_pool("worker", pool)
    snapshot = watch.snapshot()
    assert "worker" in snapshot["thread_pools"]

    watch.unregister_thread_pool("worker")
    snapshot_after = watch.snapshot()
    assert "worker" not in snapshot_after["thread_pools"]

    pool.shutdown(wait=True)
