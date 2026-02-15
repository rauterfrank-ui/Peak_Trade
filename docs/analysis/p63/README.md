# P63 — Online Readiness Shadow Runner v1

## Goal
Single canonical entrypoint combining:
- P61 readiness contract report (paper/shadow only)
- P62 shadow session plan (deny-by-default routing + allowlists)

## Safety
- `mode in {"paper","shadow"}` only. `live/record` raises `PermissionError`.
- No model calls required. Outputs are dict-only JSON boundary.

## API
```python
from pathlib import Path
from src.ops.p63 import run_online_readiness_shadow_runner_v1, P63RunContextV1

prices = [0.001] * 220
ctx = P63RunContextV1(mode="paper", run_id="demo", out_dir=Path("out/ops/p63_demo"))
out = run_online_readiness_shadow_runner_v1(prices, ctx)
```
