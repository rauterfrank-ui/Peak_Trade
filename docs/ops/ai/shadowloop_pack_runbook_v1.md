# Shadow Loop Pack v1 (P72)

## Purpose
Unified flow: P71 health gate first, then P68 shadow loop. One deterministic pack for AI+Switch + Online-Readiness validation (paper/shadow only).

## Run (shell)
```bash
OUT_DIR_OVERRIDE=out/ops/p72_demo \
RUN_ID_OVERRIDE=p72_demo \
ALLOW_BULL_STRATEGIES_OVERRIDE=s1 \
ALLOW_BEAR_STRATEGIES_OVERRIDE=s1 \
ITERATIONS_OVERRIDE=1 \
bash scripts/ops/p72_shadowloop_pack_v1.sh
```

## Python API
```python
from pathlib import Path
from src.ops.p72 import P72PackContextV1, run_shadowloop_pack_v1

ctx = P72PackContextV1(
    mode="shadow",
    run_id="demo",
    out_dir=Path("out/ops/p72_demo"),
    allow_bull_strategies=["s1"],
    allow_bear_strategies=["s1"],
    iterations=1,
    interval_seconds=0.0,
)
out = run_shadowloop_pack_v1(ctx)
assert out["gate_ok"]
```

## Environment contract (canonical)
- Supported variables:
  - Preferred: `OUT_DIR_OVERRIDE`, `RUN_ID_OVERRIDE`, `MODE_OVERRIDE`, `ITERATIONS_OVERRIDE`, `INTERVAL_OVERRIDE`
  - Legacy: `OUT_DIR`, `RUN_ID`, `MODE`, `ITERATIONS`, `INTERVAL`
- Precedence: if both are set, `*_OVERRIDE` **wins**.

## Evidence layout
- `p71_health_gate_report.json`, `p71_health_gate_manifest.json`
- `p67_shadow_session_<run_id>&#47;` (meta.json, events.json, manifest.json)
