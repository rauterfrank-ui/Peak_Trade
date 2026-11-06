---
docs_token: DOCS_TOKEN_P5_2_PRODUCTIVE_CYCLE_SEAM_INVOKE_AND_AUTHORITY_BIND_V1
status: active
scope: P5.2 bind contract only (no productive seam invoke; no cutover)
---

# P5.2 Productive Cycle Seam Invoke and Authority Bind v1

```text
PRODUCTIVE_CYCLE_LAYERED_CORE_BIND_ENABLED=true
P5_AUTHORITY_CUTOVER_AUTHORIZED=false
PRODUCTIVE_DECISION_PATH_CUTOVER_ENABLED=false
P4_PRODUCTIVE_BINDING=false
REGIME_SIDESTATE_MAPPING_CONTRACT_AUTHORIZED=true
FINAL_D_T_FORMULA_SELECTED=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

Prepares a later productive L1–L10 authority bind without activating it. Adjudicates
POST_P5_1 census items I-01..I-07 via explicit fail-closed contracts and tests.

| Surface | Owner |
| --- | --- |
| Bind contract + guards | `ops.p5_2_productive_cycle_seam_invoke_and_authority_bind_v1` |
| Productive cycle (unchanged) | `ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1` |
| P5 seam (not invoked by cycle) | `ops.p5_productive_layered_core_authority_seam_v1` |
| CZ-4 delegation gate | `trading.master_v2.integrated_offline_replay_p5_cz4_delegation_v1` |

## Decision authority (exactly one)

- `legacy_double_play_integrated_replay` — CURRENT productive path; SideState via
  `transition_state`; scope via `initialize_canonical_scope` / generator / boundaries.
- `layered_core_seal_delegated` — future bind: L1–L10 + valid seal; legacy I-1..I-3
  writers must not run as decision authority.

Never both as writers. No fallback from missing core state to legacy scope/state.

## I-01..I-07 disposition (contractual)

| ID | Disposition |
| --- | --- |
| I-01 | Dual stack forbidden when bind enabled; disabled-by-default preserves CURRENT legacy path |
| I-02 | Layered mode forbids legacy canonical scope writer as authority |
| I-03 | Layered mode forbids legacy anchor/boundary writer as R_t authority |
| I-04 | Layered mode forbids legacy scope-event switch writer when core switch applies |
| I-05 | No implicit `regime_post` → SideState; mapping contract absent → fail-closed on switch |
| I-06 | Venue/cursor SideState is observation/occupancy input only |
| I-07 | Layered mode forbids canonical fixed distances as D_t authority |

## CZ-4

Valid seal required. Regime switch on seal without authorized mapping contract rejects
delegation (fail-closed).

Code: `src/ops/p5_2_productive_cycle_seam_invoke_and_authority_bind_v1/contract_v1.py`
