# Online Readiness Operator Runbook v1 (P66)

## Contract
- **Modes:** `paper` / `shadow` only
- **Hard blocks:** `live` / `record` raise `PermissionError`
- **Determinism:** `sleep_seconds` must be `0.0` (v1 contract)
- **Return type:** dict-only (JSON-serializable boundary)

## Python usage (single-shot)
```python
from pathlib import Path
from src.ops.p66 import run_online_readiness_operator_entrypoint_v1, P66RunContextV1

prices = [0.001] * 200
ctx = P66RunContextV1(
    mode="paper",
    run_id="demo",
    out_dir=Path("out/ops/p66_demo"),
    allow_bull_strategies=["s1"],
)
out = run_online_readiness_operator_entrypoint_v1(prices, ctx)
print(out["meta"], out["p64"].keys())
```
