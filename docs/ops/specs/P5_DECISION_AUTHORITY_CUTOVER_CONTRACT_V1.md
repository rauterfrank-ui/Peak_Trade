---
docs_token: DOCS_TOKEN_P5_DECISION_AUTHORITY_CUTOVER_CONTRACT_V1
status: active
scope: P5.1 infrastructure contract only (no productive cutover)
---

# P5 Decision Authority Cutover Contract v1 (P5.1 Infrastructure)

```text
P5_AUTHORITY_CUTOVER_AUTHORIZED=false
P4_PRODUCTIVE_BINDING=false
AUTHORITY_CUTOVER_OCCURRED=false
PRODUCTIVE_DECISION_PATH_CUTOVER_ENABLED=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

P5.1 delivers **capability only**: layered-core authority seam, immutable seal,
and CZ-4 delegated-replay branch. It does **not** switch the CURRENT productive
decision path.

| Surface | Owner |
| --- | --- |
| Seal DTO + validation | `trading.master_v2.layered_core_authority_seal_v1` |
| Authority seam | `ops.p5_productive_layered_core_authority_seam_v1` |
| CZ-4 delegation | `trading.master_v2.integrated_offline_replay_p5_cz4_delegation_v1` |
| Cursor v2 provenance | `ops.p5_productive_layered_core_authority_seam_v1.cursor_v2_capability_v1` |

Sole writers for Regime/NullLine/D_t/Scope/R_t/CM_t remain L1–L10 modules
(geometry unchanged). Integrated replay I-1..I-3 writers are skipped only when
a **valid** `LayeredCoreAuthoritySealV1` is supplied on replay input.
