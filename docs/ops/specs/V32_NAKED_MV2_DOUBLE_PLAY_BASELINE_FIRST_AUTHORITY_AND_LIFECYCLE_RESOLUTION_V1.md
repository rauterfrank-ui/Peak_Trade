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
CURRENT_MV2_DP_DECISION_SSOT=run_integrated_offline_trading_logic_replay_v1
P5_ADJUDICATION=P5_CUTOVER_OBSOLETE_CURRENT_REPLAY_IS_CANONICAL
```

Machine-readable decision:
`config/governance/v32_naked_mv2_double_play_baseline_first_lifecycle_resolution_v1_decision_v1.json`

Code owner:
`src/trading/master_v2/naked_mv2_double_play_baseline_first_lifecycle_resolution_v1.py`

## 1. Purpose

Forensically **bind** Concept PDF v3.2 §22 baseline-first semantics to **existing** canonical
owners. This WP does **not** introduce a new runtime baseline gate, trading authority, or
research executor. It does **not** require P5 productive cutover.

## 2. Composite baseline-first owner (reuse)

| Role | Canonical owner (CURRENT main) |
| --- | --- |
| **Trading decision SSOT** | `run_integrated_offline_trading_logic_replay_v1` |
| **Productive cycle host** | `run_current_productive_master_v2_runtime_cycle_v1` → replay |
| Outward authority / mutation deny | `naked_mv2_double_play_core_authority_hardening_v1` |
| Layered L1–L10 (mechanical articulation) | `naked_mv2_dp_explicit_layered_core_v1` — **not** decision SSOT |
| Optional P5 bind / CZ-4 delegation | Inside replay input when explicitly requested; cutover **false** |
| Passive layer trace evidence | `layer_separation_evidence_v1.json` |
| Dynamic scope (productive) | `generate_deterministic_scope_event` within integrated replay |
| Bull/Bear / SideState switch | `double_play_state.transition_state` within integrated replay |
| Optimization surface ordering | Pre-test predecessor `NAKED_MV2_DOUBLE_PLAY_CORE_AUTHORITY_HARDENING_V1` |
| Learning → Optimization join | `optimization_universe_join_authorized=false` |
| F1 research counterfactual baseline | `BASELINE_CANDIDATE_ID=UNRESOLVED_MAX_AGE_NON_ENFORCING` |

**NAKED_BASELINE_OWNER** = `composite_baseline_first_binding_v1` (composite index, not a runtime gate).

## 3. Baseline completion semantics

`BASELINE_COMPLETION_SEMANTICS` = integrated replay SSOT reachable via the productive cycle
with canonical natural inputs, governance predecessor closed, passive layer evidence present,
F1 counterfactual research baseline defined, optimization productive join blocked.

**P5/layered-core productive cutover is explicitly not required** (`P5_AUTHORITY_CUTOVER_AUTHORIZED=false`).

## 4. D24–D27 adjudication (CURRENT main)

| ID | Expected verdict | Notes |
| --- | --- | --- |
| **D24** | `PROVEN_CURRENT` | Productive path → integrated replay; no optimization join |
| **D25** | `PROVEN_CURRENT` | Scope/switch owners in replay SSOT; cutover not required |
| **D26** | `PARTIAL_CURRENT` | Platform-wide native vs candidate baseline evidence not unified |
| **D27** | `PARTIAL_CURRENT` | TEST_ENTRY_GATE defined; not globally lifecycle-enforced |

`earliest_true_remaining_gap` = platform unified baseline evidence schema + PDF v3.2 wording alignment (separate docs task).

## 5. Non-goals

- P5 productive cutover enablement
- Layered core as parallel trading decision writer
- GAP-01 productive Learning→Optimization wiring
- M10 / F2 / F3 / F5 expansion
- PDF edits in this PR
