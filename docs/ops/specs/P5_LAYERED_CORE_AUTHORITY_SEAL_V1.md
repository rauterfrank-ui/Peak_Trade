---
docs_token: DOCS_TOKEN_P5_LAYERED_CORE_AUTHORITY_SEAL_V1
status: active
---

# P5 Layered Core Authority Seal v1

Immutable seal emitted by `run_p5_layered_core_authority_seam_v1` after a
successful L1–L10 mechanical step and atomic episode persist.

```text
SEAL_CONTRACT_VERSION=layered_core_authority_seal.v1
CZ4_DELEGATION_ACTIVE=true
PRODUCTIVE_BINDING_AUTHORIZED=false
```

Required fields: `seal_digest`, `episode_snapshot_id`, `store_manifest_digest`,
`instrument_id`, `regime_pre&#47;post`, `nullline_price`, `d_t`, `r_t`, `cm_t`.

Validation is fail-closed. Tampered digests or inactive delegation flag reject
CZ-4 delegated replay.

Code: `src/trading/master_v2/layered_core_authority_seal_v1.py`
