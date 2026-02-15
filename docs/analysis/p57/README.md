# P57 — Switch-Layer Paper/Shadow Integration v1

## Goal
Provide a **single**, **deterministic**, **deny-by-default** entrypoint to run the Switch-Layer pipeline in **paper/shadow**:
- compute market regime (read-only signal)
- decide switch regime
- route via allowlists (deny-by-default)
- optionally write an evidence pack when `out_dir` is set

## Safety
- **live/record** is hard-denied at P57 (`PermissionError`).
- Strategy routing is deny-by-default unless allowlists are explicitly provided.

## API
```python
from pathlib import Path
from src.ops.p57.switch_layer_paper_shadow_v1 import run_switch_layer_paper_shadow_v1, P57RunContextV1

prices = [0.001] * 160
ctx = P57RunContextV1(
    mode="paper",
    run_id="demo",
    out_dir=Path("out/ops/p57_demo"),
    allow_bull_strategies=["demo_strategy_a"],
    allow_bear_strategies=[],
)
out = run_switch_layer_paper_shadow_v1(prices, ctx)
print(out["decision"].regime, out["routing"].ai_mode)
```
