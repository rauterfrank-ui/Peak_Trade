# P62 — Online Readiness → Shadow Session v1

## Intent
Provide a **single ops entrypoint** to:
- run P61 readiness,
- derive a deterministic **shadow session plan** (no execution),
- optionally write evidence under `out/ops/*`.

## Safety Invariants
- `mode in {"live","record"}` → **PermissionError**
- No exchange/network/order placement
- Deny-by-default routing remains unchanged
- Evidence writes only when `out_dir` is provided

## Public API
```python
from pathlib import Path
from src.ops.p62 import run_online_readiness_shadow_session_v1, P62RunContextV1

ctx = P62RunContextV1(
    mode="paper",
    run_id="demo",
    out_dir=Path("out/ops/p62_demo"),
    allow_bull_strategies=["s1"],
    allow_bear_strategies=["s1"],
)
out = run_online_readiness_shadow_session_v1(prices=[0.001]*200, ctx=ctx)
```
