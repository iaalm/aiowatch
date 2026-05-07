# aiowatch

`aiowatch` provides lightweight runtime observability for asyncio applications and
ThreadPoolExecutors through OpenTelemetry metrics.

## Install

```bash
pip install aiowatch
```

## Quick Start

```python
from concurrent.futures import ThreadPoolExecutor

from aiowatch import AioWatch
from opentelemetry.metrics import get_meter

meter = get_meter("my-service")
executor = ThreadPoolExecutor(max_workers=20)

async def main() -> None:
    async with AioWatch(
        meter=meter,
        collect_interval=5.0,
        thread_pools={"worker": executor},
    ):
        ...
```

## FastAPI Integration

Use one `AioWatch` per process/event loop and manage it in the app lifespan.
Do not start a new watcher for every API request.

```python
from contextlib import asynccontextmanager

from aiowatch import AioWatch
from fastapi import FastAPI
from opentelemetry.metrics import get_meter

meter = get_meter("my-fastapi-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    watch = AioWatch(meter=meter, collect_interval=5.0)
    await watch.start()
    app.state.aiowatch = watch
    try:
        yield
    finally:
        await watch.stop()


app = FastAPI(lifespan=lifespan)
```
