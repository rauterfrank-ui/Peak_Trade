# P136 — Exec Net Shadow Read-Only Finish Snapshot v1

## Scope
- shadow/paper only
- DRY_RUN=YES only
- networkless default-deny remains intact (transport_allow=NO)

## Entry
- `bash scripts&#47;ops&#47;p136_exec_net_shadow_readonly_finish_snapshot_v1.sh`

## Outputs (out&#47;ops)
- Evidence dir: `out&#47;ops&#47;p136_exec_net_shadow_readonly_finish_snapshot_<ts>&#47;`
- Bundle: `out&#47;ops&#47;p136_exec_net_shadow_readonly_finish_snapshot_<ts>.bundle.tgz`
- DONE pin: `out&#47;ops&#47;P136_EXEC_NET_SHADOW_READONLY_FINISH_SNAPSHOT_DONE_<ts>.txt`

## Verifications
- `shasum -a 256 -c <pin>.sha256`
- `shasum -a 256 -c <evi>&#47;SHA256SUMS.txt` (run from repo root)
