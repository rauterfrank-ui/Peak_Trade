# P108 — OKX Adapter v1 (mocks only)

## Goal
Provide a provider-specific execution adapter implementation that conforms to `ExecutionAdapterV1` (P106), **mocks only**.

## Non-goals
- No API keys
- No HTTP/WebSocket calls
- No live trading

## Usage
```python
from src.execution.adapters.providers.okx_v1 import OKXExecutionAdapterV1
ad = OKXExecutionAdapterV1()
print(ad.capabilities())
```
