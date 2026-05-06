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
