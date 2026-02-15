# P53 — Switch-Layer Orchestration Hook v1

## Goal
Expose the P52 switch-layer as a **read-only orchestration signal** (market regime + confidence) and optionally persist it as an evidence artifact.

## Safety invariants
- Deterministic (same inputs → same decision)
- **No model calls** (does not touch P49/P50 gates)
- **No execution impact** (regime is informational)
- No writes unless `out_dir` is provided

## API
- `src/ai_orchestration/switch_layer_orch_v1.py`
  - `run_switch_layer_orch_v1(returns, ctx) -> SwitchDecisionV1`
  - `SwitchLayerContextV1(symbol, timeframe, out_dir=None, meta=None)`

## Evidence
If `ctx.out_dir` is set, writes:
- `switch_layer_decision_v1.json`

Example:
```python
from src.ai_orchestration.switch_layer_orch_v1 import SwitchLayerContextV1, run_switch_layer_orch_v1

ctx = SwitchLayerContextV1(symbol="BTC/USDT", timeframe="1h", out_dir="out/ops/my_run")
decision = run_switch_layer_orch_v1(returns=[0.001]*120, ctx=ctx)
print(decision)
```
