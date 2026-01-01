## Summary
Shadow Track execution improvements with safety defaults + governance alignment.

## What changed
- Shadow-only execution wiring/telemetry.
- Live remains blocked by default.

## Verification
- `ruff format/check`, `pytest -q`
- Shadow drill smoke (paper/sim) if available
- Governance/Policy gates green

## Risk
Medium (execution-adjacent). Default-block + tests mitigate.

## Rollback
Revert PR commit(s).
