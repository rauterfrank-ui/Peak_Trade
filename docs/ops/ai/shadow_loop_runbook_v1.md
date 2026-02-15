# Shadow Loop Runbook v1 (Paper/Shadow only)

## Purpose
Run a deterministic, paper/shadow-only loop that produces evidence packs for:
- Online readiness (P61)
- Shadow session plan (P62)
- Shadow runner (P63)
- Runner wrapper (P64)
- Loop runner (P65)
- Operator entrypoint (P66)
- Scheduler wrapper (P67)

**Safety invariant:** `mode=live` and `mode=record` must remain blocked and will raise `PermissionError`.

## Recommended entrypoint
Use the scheduler (P67) which wraps the operator entrypoint (P66) for both single-shot and loop.

### One-shot
```bash
python3 -m src.ops.p67.shadow_session_scheduler_cli_v1 \
  --mode paper \
  --run-id shadow_demo \
  --out-dir out/ops/shadow_demo \
  --iterations 1 \
  --interval-seconds 0
```

### Loop (e.g. 3 runs, 60s between)
```bash
python3 -m src.ops.p67.shadow_session_scheduler_cli_v1 \
  --mode shadow \
  --run-id shadow_loop \
  --out-dir out/ops/shadow_loop \
  --iterations 3 \
  --interval-seconds 60
```

### Python API (P66 operator entrypoint)
```python
from pathlib import Path
from src.ops.p66 import P66RunContextV1, run_online_readiness_operator_entrypoint_v1

prices = [0.001] * 200
ctx = P66RunContextV1(
    mode="paper",
    run_id="demo",
    out_dir=Path("out/ops/shadow_demo"),
    allow_bull_strategies=["s1"],
    allow_bear_strategies=["s1"],
)
out = run_online_readiness_operator_entrypoint_v1(prices, ctx)
```

## Evidence layout
When `--out-dir` is set, evidence is written under:
- `out/ops/<run_id>/p67_shadow_session_<run_id>/meta.json`
- `out/ops/<run_id>/p67_shadow_session_<run_id>/events.json`
- `out/ops/<run_id>/p67_shadow_session_<run_id>/manifest.json`

## Cron / launchd
Schedule the P67 CLI with your preferred interval. Example (cron, every hour):
```
0 * * * * cd /path/to/Peak_Trade && python3 -m src.ops.p67.shadow_session_scheduler_cli_v1 --mode shadow --run-id hourly --out-dir out/ops/hourly --iterations 1
```
