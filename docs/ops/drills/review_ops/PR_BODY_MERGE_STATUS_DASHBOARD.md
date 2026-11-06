## Scope
- Add `scripts/ops/merge_status_dashboard.sh` to report merge readiness for Docs gatepacks + B1/B2/C via semantic checks.
- Document usage and interpretation in `docs/ops/drills/PHASE_D4_MERGE_STATUS_DASHBOARD.md`.

## Evidence
- Script: `scripts/ops/merge_status_dashboard.sh`
- Drill: `docs/ops/drills/PHASE_D4_MERGE_STATUS_DASHBOARD.md`

## Notes
- Checks are intentionally semantic (string markers) to avoid false positives from file existence.
- No runtime changes; ops/docs only.
