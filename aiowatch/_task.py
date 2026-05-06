from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

from ._instruments import LoopInstruments

TaskFactory = Callable[..., asyncio.Task[Any]]


class TaskTracker:
    def __init__(self, instruments: LoopInstruments, include_coroutine_name: bool = False) -> None:
        self._loop: asyncio.AbstractEventLoop | None = None
        self._instruments = instruments
        self._include_coroutine_name = include_coroutine_name
        self._original_factory: TaskFactory | None = None
        self._installed = False

    async def start(self) -> None:
        if self._installed:
            return
        loop = asyncio.get_running_loop()
        self._loop = loop
        self._original_factory = loop.get_task_factory()
        loop.set_task_factory(self._factory)
        self._installed = True

    async def stop(self) -> None:
        if not self._installed:
            return
        if self._loop is not None:
            self._loop.set_task_factory(self._original_factory)
        self._installed = False
        self._loop = None

    def _factory(self, loop: asyncio.AbstractEventLoop, coro: object, **kwargs: Any) -> asyncio.Task[Any]:
        task: asyncio.Task[Any]
        if self._original_factory is not None:
            task = self._original_factory(loop, coro, **kwargs)
        else:
            task = asyncio.Task(coro, loop=loop, **kwargs)
        self._instruments.tasks_created_counter.add(1)
        task.add_done_callback(self._on_task_done)
        return task

    def _on_task_done(self, task: asyncio.Task[Any]) -> None:
        if task.cancelled():
            status = "cancelled"
        elif task.exception() is not None:
            status = "failed"
        else:
            status = "completed"
        attributes = {"task.status": status}
        if self._include_coroutine_name:
            attributes["task.coroutine"] = _coroutine_qualname(task.get_coro())
        self._instruments.tasks_done_counter.add(1, attributes=attributes)


def _coroutine_qualname(coro: object) -> str:
    qualname = getattr(coro, "__qualname__", None)
    module = getattr(coro, "__module__", None)
    if isinstance(module, str) and isinstance(qualname, str):
        return f"{module}.{qualname}"
    if isinstance(qualname, str):
        return qualname
    return type(coro).__name__
