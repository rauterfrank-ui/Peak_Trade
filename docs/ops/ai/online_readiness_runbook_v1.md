# Online Readiness Runbook v1 (Paper/Shadow only)

Definition of "ONLINE" in Peak_Trade:
- System can run deterministic **paper/shadow** orchestration end-to-end
- Evidence packs are emitted under out/ops when out_dir is set
- Live/record remains hard-blocked unless explicitly enabled via policy gates (P49/P50) — not part of this runbook.

Example (Python):
```python
from pathlib import Path
from src.ops.p61.run_online_readiness_v1 import run_online_readiness_v1, P61RunContextV1

prices = [0.001] * 200
out = run_online_readiness_v1(prices, P61RunContextV1(mode="paper", run_id="demo", out_dir=Path("out/ops/p61_demo")))
print(out["report"])
```
