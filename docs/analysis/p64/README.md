# P64 — online-readiness-runner-v1

## Goal
Single canonical entrypoint to run Online Readiness end-to-end in **paper/shadow only**.

## Safety
- `mode in {"live","record"}` hard-blocked (raises `PermissionError`).
- Evidence writing remains controlled by downstream (P63/P62) and only occurs when `out_dir` is set.

## Public API
```py
from pathlib import Path
from src.ops.p64 import P64RunContextV1, run_online_readiness_runner_v1

prices = [0.001] * 200
out = run_online_readiness_runner_v1(prices, P64RunContextV1(mode="paper", run_id="demo", out_dir=Path("out/ops/p64_demo")))
```
