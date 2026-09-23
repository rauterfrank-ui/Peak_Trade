---
docs_token: DOCS_TOKEN_V32_NAKED_MV2_DOUBLE_PLAY_BASELINE_FIRST_AUTHORITY_AND_LIFECYCLE_RESOLUTION_V1
status: active
scope: Concept v3.2 §22 baseline-first composite binding and D24–D27 adjudication (no runtime gate)
capability: V32_NAKED_MV2_DOUBLE_PLAY_BASELINE_FIRST_AUTHORITY_AND_LIFECYCLE_RESOLUTION_V1
last_updated: 2026-09-23
---

# V3.2 Naked MV2 + Double Play Baseline-First — Authority & Lifecycle Resolution v1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
WORKPACKAGE_ID=V32_NAKED_MV2_DOUBLE_PLAY_BASELINE_FIRST_AUTHORITY_AND_LIFECYCLE_RESOLUTION_V1
NEW_BASELINE_GATE_RUNTIME_AUTHORITY=false
EXTERNAL_EFFECT_AUTHORIZED=false
TRADING_DECISION_AUTHORITY_CHANGED=false
```

Machine-readable decision:
`config/governance/v32_naked_mv2_double_play_baseline_first_lifecycle_resolution_v1_decision_v1.json`

Code owner:
`src/trading/master_v2/naked_mv2_double_play_baseline_first_lifecycle_resolution_v1.py`

## 1. Purpose

Forensically **bind** Concept PDF v3.2 §22 baseline-first semantics to **existing** canonical
owners. This WP does **not** introduce a new runtime baseline gate, trading authority, or
research executor.

## 2. Composite baseline-first owner (reuse)

| Role | Canonical owner (already on main) |
| --- | --- |
| Trading decision SSOT | `run_integrated_offline_trading_logic_replay_v1` (hardening decision) |
| Outward authority / mutation deny | `naked_mv2_double_play_core_authority_hardening_v1` |
| Native L1–L10 semantics | `naked_mv2_dp_explicit_layered_core_v1` |
| Passive layer trace evidence | `layer_separation_evidence_v1.json` |
| Optimization surface ordering | `OPTIMIZATION_SURFACE_FAMILIES_PRE_TEST_PREPARATION_V1` (`predecessor_closed=NAKED_MV2…`) |
| Learning → Optimization join | `learning_outcome_evidence_ingest_and_state` (`optimization_universe_join_authorized=false`) |
| F1 research counterfactual baseline | `BASELINE_CANDIDATE_ID=UNRESOLVED_MAX_AGE_NON_ENFORCING` |
| Governed parameter return | M10 seam join + optional seam on integrated replay (non-enforcing) |

**NAKED_BASELINE_OWNER** = composite binding function `composite_baseline_first_binding_v1`
(not a new runtime decision engine).

## 3. Baseline completion semantics

`BASELINE_COMPLETION_SEMANTICS` = governance predecessor chain closed + passive layer
separation evidence present + research counterfactual baseline defined for F1 + **no**
P5/layered-core productive cutover (`P5_AUTHORITY_CUTOVER_AUTHORIZED=false`).

Baseline completion is **not** equivalent to parameter promotion or enforcement activation.

## 4. D24–D27 adjudication

Use `adjudicate_v32_baseline_first_requirements_v1()` for machine-readable verdicts.
Expected CURRENT main posture after this WP:

- **D24–D27**: `PARTIAL_CURRENT` (capability present; productive layered-core cutover and global
  test-phase enforcement not proven).
- **No new Baseline Gate Owner** required for authority semantics.

## 5. Non-goals

- P5 productive cutover enablement
- GAP-01 productive Learning→Optimization wiring
- M10 scope expansion, F2/F3/F5 surface changes
- Optimization search/OOS execution
- External effect or self-deploy
