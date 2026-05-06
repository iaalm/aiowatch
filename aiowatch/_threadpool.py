from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Iterable

from opentelemetry.metrics import Observation

from ._instruments import create_threadpool_instruments


class ThreadPoolMonitor:
    def __init__(self, meter: object, pools: dict[str, ThreadPoolExecutor] | None = None) -> None:
        self._pools: dict[str, ThreadPoolExecutor] = dict(pools or {})
        self.instruments = create_threadpool_instruments(meter=meter, gauge_callback=self._observe)

    def register(self, name: str, executor: ThreadPoolExecutor) -> None:
        self._pools[name] = executor

    def unregister(self, name: str) -> None:
        self._pools.pop(name, None)

    def snapshot(self) -> dict[str, dict[str, float | int]]:
        return {
            pool_name: {
                "active": stats["active"],
                "queued": stats["queued"],
                "max": stats["max"],
                "utilization": stats["utilization"],
            }
            for pool_name, stats in self._collect().items()
        }

    def _observe(self, options: object) -> Iterable[Observation]:
        metric_name = getattr(getattr(options, "instrument", None), "name", "")
        observations: list[Observation] = []
        for pool_name, stats in self._collect().items():
            attributes = {"pool.name": pool_name}
            if metric_name == "aiowatch.threadpool.active":
                observations.append(Observation(stats["active"], attributes=attributes))
            elif metric_name == "aiowatch.threadpool.queued":
                observations.append(Observation(stats["queued"], attributes=attributes))
            elif metric_name == "aiowatch.threadpool.max_workers":
                observations.append(Observation(stats["max"], attributes=attributes))
            elif metric_name == "aiowatch.threadpool.utilization":
                observations.append(Observation(stats["utilization"], attributes=attributes))
        return observations

    def _collect(self) -> dict[str, dict[str, float | int]]:
        results: dict[str, dict[str, float | int]] = {}
        for pool_name, executor in self._pools.items():
            max_workers = int(getattr(executor, "_max_workers", -1))
            queued = _queue_size(getattr(executor, "_work_queue", None))
            active = _active_threads(executor)
            utilization = float(active / max_workers) if active >= 0 and max_workers > 0 else -1.0
            results[pool_name] = {
                "active": active,
                "queued": queued,
                "max": max_workers,
                "utilization": utilization,
            }
        return results


def _queue_size(work_queue: object) -> int:
    if work_queue is None or not hasattr(work_queue, "qsize"):
        return -1
    try:
        return int(work_queue.qsize())
    except Exception:
        return -1


def _active_threads(executor: ThreadPoolExecutor) -> int:
    threads = getattr(executor, "_threads", None)
    idle_semaphore = getattr(executor, "_idle_semaphore", None)
    if not isinstance(threads, set):
        return -1
    total = len(threads)
    idle = getattr(idle_semaphore, "_value", None)
    if not isinstance(idle, int):
        return -1
    active = total - idle
    return active if active >= 0 else 0
