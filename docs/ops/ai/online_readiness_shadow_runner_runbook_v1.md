# Online Readiness Shadow Runner v1 (P63)

Canonical entrypoint combining P61 readiness + P62 shadow plan.

## Usage

```python
from pathlib import Path
from src.ops.p63 import run_online_readiness_shadow_runner_v1, P63RunContextV1

prices = [0.001] * 220
ctx = P63RunContextV1(mode="paper", run_id="demo", out_dir=Path("out/ops/p63_demo"))
out = run_online_readiness_shadow_runner_v1(prices, ctx)
print(out["shadow_plan"])
```

## Safety

- `paper` | `shadow` only. `live`/`record` → `PermissionError`.
- Evidence written only when `out_dir` is set (via P62).
