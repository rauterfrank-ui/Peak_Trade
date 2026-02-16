# P92 — P91 Audit Snapshot Retention v1

## Goal
Keep `out/ops/` bounded by deleting older `p91_shadow_soak_audit_snapshot_*` evidence directories (and related bundles/pins if present).

## Script
`scripts/ops/p92_p91_audit_snapshot_retention_v1.sh`

### Example
```bash
KEEP_N=48 bash scripts/ops/p92_p91_audit_snapshot_retention_v1.sh
```
