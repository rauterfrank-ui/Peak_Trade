# P137 — Exec-Net Shadow Read-Only Finish Pack v1

## Scope
Create a single **finish pack** that bundles the latest shadow read-only chain artifacts:
- P135 shadow read-only evidence pack (DONE pin + EVI dir + bundle)
- P136 finish snapshot (DONE pin + EVI dir + bundle)
- Repo baseline pins (REPO_CLEAN_BASELINE_DONE, FINAL_DONE)

Networkless, mocks/stubs only:
- MODE=shadow|paper only
- DRY_RUN=YES only
- transport_allow=NO enforced upstream
- No secrets / deny-env guards remain in effect

## Entry
- `bash scripts&#47;ops&#47;p137_exec_net_shadow_readonly_finish_pack_v1.sh`

## Outputs
- EVI: out&#47;ops&#47;p137_exec_net_shadow_readonly_finish_pack_<TS>&#47;
- Bundle: out&#47;ops&#47;p137_exec_net_shadow_readonly_finish_pack_<TS>.bundle.tgz (+ .sha256)
- DONE pin: out&#47;ops&#47;P137_EXEC_NET_SHADOW_READONLY_FINISH_PACK_DONE_<TS>.txt (+ .sha256)

## Verify
- shasum -a 256 -c <DONE>.sha256
- shasum -a 256 -c <EVI>&#47;SHA256SUMS.txt   (run from repo root)
- shasum -a 256 -c <BUNDLE>.sha256
