# P65 — Online Readiness Loop Runner v1

## Goal
Provide a single operator-friendly entrypoint to run **P64** repeatedly in **paper/shadow** mode, producing deterministic outputs and optional evidence directories, while keeping **live/record hard-blocked**.

## Public API
```python
from pathlib import Path
from src.ops.p65 import P65RunContextV1, run_online_readiness_loop_runner_v1

prices = [0.001] * 200
ctx = P65RunContextV1(mode="paper", run_id="demo", loops=3, out_dir=Path("out/ops/p65_demo"))
out = run_online_readiness_loop_runner_v1(prices, ctx)
```
