# P135 — Execution Networked Shadow Read-Only Evidence Pack v1

Scope: shadow/paper only, networkless (transport_allow=NO), no secrets.
Goal: one-shot script that produces an evidence pack + bundle + DONE pin for read-only intents.
Inputs: none (operator runs from repo root).
Outputs:
- out/ops/p135_shadow_readonly_evidence_pack_<TS>/
- out/ops/p135_shadow_readonly_evidence_pack_<TS>.bundle.tgz (+ .sha256)
- out/ops/P135_EXEC_NET_SHADOW_READONLY_EVI_DONE_<TS>.txt (+ .sha256)
