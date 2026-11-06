---
docs_token: DOCS_TOKEN_PEAK_TRADE_META_LEARNING_OPTIMIZATION_UNIVERSE_CONCEPT_V3_2_CURRENT_MV2_DP_ALIGNMENT_ADDENDUM_V1
status: active
scope: Repo-hosted CURRENT alignment addendum for external Concept v3/v3.1/v3.2 PDF
capability: V32_CURRENT_MV2_DP_CONCEPT_ALIGNMENT_V1
last_updated: 2026-09-23
---

# Concept v3 / v3.1 / v3.2 — CURRENT MV2+Double-Play Alignment Addendum v1

```text
DOCUMENT_CLASS=CONCEPT_ALIGNMENT_ADDENDUM
SUPERSEDES_PDF_BODY=false
REPLACES_EXTERNAL_PDF=false
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
WORKPACKAGE_ID=V32_CURRENT_MV2_DP_CONCEPT_ALIGNMENT_V1
BOUND_ORIGIN_MAIN_SHA=2dba1355c9907c57fa330aed01a4072faeaf048f
EXTERNAL_SOURCE=Peak_Trade_Meta_Learning_Optimization_Universe_Concept_v3_2_Expanded.pdf
NORMATIVE_REPO_BINDING=docs/ops/specs/V32_CURRENT_MV2_DP_CONCEPT_ALIGNMENT_V1.md
ATLAS_AUTHORITY=NONE
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

Dieses Addendum **ergänzt** Concept v3, v3.1 und v3.2. Es **entfernt oder ersetzt**
keine historischen PDF-Aussagen. Bei Widerspruch zwischen PDF-Implikation und CURRENT
kanonischer Adjudication (PR **#6764**, V32 lifecycle resolution) gilt die **CURRENT**
Binding-Tabelle unten plus Master Runbook.

## A. CURRENT trading-decision SSOT

```text
CURRENT_MV2_DP_DECISION_SSOT=trading.master_v2.integrated_offline_trading_logic_replay_v1.run_integrated_offline_trading_logic_replay_v1
CURRENT_PRODUCTIVE_ENTRYPOINT=ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1.run_current_productive_master_v2_runtime_cycle_v1
```

Der produktive Zyklus **ruft** den integrierten Offline-Replay-SSOT auf. Kein paralleler
Layered-L1–L10-Orchestrator ist Productive Decision-SSOT.

## B. „Naked MV2 + Double Play“ (v3.2 §22)

**Naked** bezeichnet die unverfälschte CURRENT kanonische MV2+DP-Trading-Decision-Semantik
**vor** Optimization-/Self-Learning-Parameter-/Candidate-Einfluss.

**Naked bedeutet nicht:**

- dass `naked_mv2_dp_explicit_layered_core_v1` (L1–L10) die Productive Decision-SSOT sein muss;
- dass ein P5-Authority-Cutover Voraussetzung für Baseline-first, D24 oder D25 ist.

**Naked bedeutet:**

- `run_integrated_offline_trading_logic_replay_v1` entscheidet mit kanonischen natürlichen Inputs;
- Optimization/Learning mutieren die Trading-Core-Decision-Semantik nicht (`OPTIMIZATION_BASELINE_MUTATION=FORBIDDEN` bleibt).

## C. Layered L1–L10 und P5

| Artifact | CURRENT role |
| --- | --- |
| `naked_mv2_dp_explicit_layered_core_v1` | Explizite mechanische Artikulation; passive layer-separation evidence; optional P5 bind/seal **source** |
| P5 bind/seal/CZ-4 | Optional **per cycle** innerhalb des **bestehenden** Replay-SSOT, wenn explizit angefordert |
| P5 productive cutover | `P5_AUTHORITY_CUTOVER_AUTHORIZED=false` |

## D. Owner graph (productive decision path)

| Concern | CURRENT symbol |
| --- | --- |
| Dynamic scope | `trading.master_v2.deterministic_scope_event_generator_v1.generate_deterministic_scope_event` |
| Bull/Bear / SideState | `trading.master_v2.double_play_state.transition_state` |
| Composition | `trading.master_v2.double_play_composition_matrix_v1.evaluate_double_play_composition_matrix_v1` |
| Entry/Exit | `trading.master_v2.double_play_entry_exit_policy_v0.evaluate_double_play_entry_exit_policy_v0` |

## E. Terminology clarifications (PDF disambiguation)

| PDF phrase | CURRENT reading |
| --- | --- |
| v3 §13 „Closed-Loop-Replay“ | Offline Learning/Optimization evidence loop only — **not** trading decision replay SSOT |
| v3 §1 `CLEAN_CORE_SEAL_V1` | Immutability **boundary** concept; v3.1 §19 `TRADING_CORE_IMMUTABILITY_BOUNDARY` is the precise architecture term |
| v3.2 §22 „vollständig verdrahtet“ | End-to-end **via integrated replay SSOT + productive cycle**; not layered-core cutover |
| v3 §1 census SHA / surface counts | Historical snapshot at PDF authoring — mark `STALE_IF_HEAD_DIFFERS` |

## F. D24–D29 adjudication overlay (v3.2 §22.3)

| ID | CURRENT status | Reader note |
| --- | --- | --- |
| D24 | `PROVEN_CURRENT` | Productive path → integrated replay; optimization join blocked |
| D25 | `PROVEN_CURRENT` | Scope/switch owners in replay SSOT |
| D26 | `PROVEN_CURRENT` | Closed via `V32_D26_PLATFORM_UNIFIED_NATIVE_VS_CANDIDATE_BASELINE_EVIDENCE_CLOSURE_V1` (read-only composition) |
| D27 | `PROVEN_CURRENT` | F1/F2 executors + F5 shadow campaign lifecycle-enforced (#6767–#6771); global closure WP composes proofs |
| D28–D29 | F1/M9 scoped join `PROVEN_CURRENT`; D29 promotion `OWNER_POLICY_REQUIRED` | Scoped registry SSOT: `V32_D28_D29_SCOPED_OPTIMIZATION_PRODUCTIVE_JOIN_F1_M9_MAX_BUILD_V1`; global boolean legacy-only |

## G. Baseline-first sequence (unchanged intent, CURRENT wiring)

1. Naked trading baseline — replay SSOT, no optimization/learning backflow into decisions.
2. Baseline evidence — passive observation (`PASSIVE_BASELINE_OBSERVATION`); includes layer separation evidence where present.
3. Test/research — counterfactual/isolated against baseline reference (F1 counterfactual id).
4. Supporting intelligence — optimization/learning proposals only.
5. Governed return — authorized parameter seams only; trading decision authority unchanged.

Composite index (read-only): `governance.naked_mv2_double_play_baseline_first_lifecycle_resolution_v1.composite_baseline_first_binding_v1`

## H. Historical fidelity statement

Concept v3/v3.1/v3.2 PDF text remains an external historical artifact. This addendum is the
**in-repo** CURRENT alignment surface for autonomous agents and reviewers. Master Runbook
retains operational SSOT; Map of Truth and System Atlas remain navigation only.
