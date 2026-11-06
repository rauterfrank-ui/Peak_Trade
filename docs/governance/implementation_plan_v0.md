# Implementation Plan v0 — Trend Following v2 Mandatory Boundary Rewire

**Scope:** `TREND_FOLLOWING_V2_MANDATORY_BOUNDARY_STATE_FILE_BINDING_REWIRE`  
**Frozen:** true  
**Not a second norm SSOT.**

Maschinenlesbar: [`implementation_plan_v0.json`](implementation_plan_v0.json)  
Wiring-Map: [`../architecture/TREND_FOLLOWING_V2_CANONICAL_WIRING.md`](../architecture/TREND_FOLLOWING_V2_CANONICAL_WIRING.md)

## Sequence (summary)

1. Config binding at `trend_following_v2_economic_evaluation_v1.json` (reference parity)
2. Materializer overlay in `build_runtime_step31f_config_v0`
3. Sparse-signal materializer delegation
4. Runtime config preservation through baseline owner
5. Evidence builder mandatory binding resolution + fail-closed
6. MV2 wiring kwargs propagation
7. Fail-closed negative matrix
8. Productive five-gate bounded RVN/240 E2E
9. Repo-side wiring map contract tests
10. Manifest-verified durable evidence
11. PR open — stop before merge

## Stop conditions

- No merge without separate operator GO
- No economic adjudication
- `RUNTIME_EFFECT=NONE`, `AUTHORITY_EFFECT=NONE`
