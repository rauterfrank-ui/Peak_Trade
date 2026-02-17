# P136 — Exec Net Shadow Read-Only Finish Snapshot v1

## Scope
- shadow/paper only
- DRY_RUN=YES only
- networkless default-deny remains intact (transport_allow=NO)

## Entry
- `bash scripts/ops/p136_exec_net_shadow_readonly_finish_snapshot_v1.sh`

## Outputs (out/ops)
- Evidence dir: `out/ops/p136_exec_net_shadow_readonly_finish_snapshot_<ts>/`
- Bundle: `out/ops/p136_exec_net_shadow_readonly_finish_snapshot_<ts>.bundle.tgz`
- DONE pin: `out/ops/P136_EXEC_NET_SHADOW_READONLY_FINISH_SNAPSHOT_DONE_<ts>.txt`

## Verifications
- `shasum -a 256 -c <pin>.sha256`
- `shasum -a 256 -c <evi>/SHA256SUMS.txt` (run from repo root)
