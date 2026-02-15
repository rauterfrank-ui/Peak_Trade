# Switch-Layer Paper/Shadow Runbook v1

## Overview
P57 runner: Switch-Layer orchestration for **paper** and **shadow** only. Live/record is hard-denied.

## Safety Model
- `paper`, `shadow`: allowed (compute + route + optional evidence)
- `live`, `record`: **PermissionError** at P57 (deny-by-default)

## Entrypoint
```python
from src.ops.p57.switch_layer_paper_shadow_v1 import (
    P57RunContextV1,
    run_switch_layer_paper_shadow_v1,
)

ctx = P57RunContextV1(
    mode="paper",  # or "shadow"
    run_id="run-001",
    out_dir=Path("out/ops/p57_demo"),
    allow_bull_strategies=["strategy_a"],
    allow_bear_strategies=["strategy_b"],
)
result = run_switch_layer_paper_shadow_v1(prices=[...], ctx=ctx)
```

## Evidence
When `out_dir` is set, writes evidence pack (manifest, switch_regime, routing, etc.).

## Tests
```bash
pytest tests/p57/test_switch_layer_paper_shadow_v1.py -v
```
