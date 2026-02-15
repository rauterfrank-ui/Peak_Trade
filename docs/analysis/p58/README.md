# P58 — Switch-layer online readiness v1

## Goal
Provide an end-to-end **paper/shadow** readiness probe for the switch-layer stack (P52–P57) with **deny-by-default** semantics.

## Safety
- **Hard deny** for `mode in {live, record}`.
- Evidence is written **only** when `out_dir` is set.
- Routing remains **deny-by-default** unless explicit allowlists + AI gates (P49/P50) allow it.

## Usage
```python
from pathlib import Path
from src.ops.p58 import run_switch_layer_online_readiness_v1, P58RunContextV1

prices = [0.001] * 200
ctx = P58RunContextV1(mode="paper", run_id="demo", out_dir=Path("out/ops/p58_demo"), allow_bull_strategies=["s1"])
out = run_switch_layer_online_readiness_v1(prices, ctx)
# Returns JSON-dicts only (P59 boundary): out["regime"], out["routing"]["ai_mode"]
```
