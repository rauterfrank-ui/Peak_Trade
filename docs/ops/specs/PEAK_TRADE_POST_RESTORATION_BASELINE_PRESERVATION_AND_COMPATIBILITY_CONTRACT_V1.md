# Peak_Trade — Post-Restoration Baseline Preservation and Compatibility Contract v1

status: ACTIVE
last_updated: 2026-08-29
owner: Peak_Trade
purpose: Subordinate preservation and compatibility-adjudication contract for the restored Master V2 / Double Play baseline. Not a second SSOT. Not runtime mutation. Not live or execution authority.
docs_token: DOCS_TOKEN_PEAK_TRADE_POST_RESTORATION_BASELINE_PRESERVATION_AND_COMPATIBILITY_CONTRACT_V1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
CANONICAL_AUTHORITY=docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md
PARALLEL_SSOT_CREATED=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
RUNTIME_MUTATION=false
NEW_SEMANTIC_POLICY=false
NEW_RUNTIME_OWNER=false
NEW_STAGE=false
COMPATIBILITY_CONTRACT_GRANTS_EXECUTION_AUTHORITY=false
COMPATIBILITY_CONTRACT_DOES_NOT_GRANT_EXECUTION_AUTHORITY=true
LIVE_AUTHORIZED=false
TESTNET_AUTHORIZED=false
CANARY_AUTHORIZED=false
ORDERS_AUTHORIZED=false
NO_TRADING=true
NO_LIVE_AUTHORITY=true
NO_EXECUTION_AUTHORITY=true
```

This document is subordinate to the Master Runbook. It does not replace
Master §5.3, Appendix A, C4, restoration-admission class, or existing
owner contracts. It preserves the restored baseline and defines how later
or already-present Current-/Host-/Hardening-/Feature-components must be
adjudicated before keep/adapt/decouple/degrade/remove/rewire.

## 1) Restoration completion checkpoint

```text
RESTORATION_COMPLETION_CHECKPOINT_SHA=21452016ff998c1af63f24c36060f2a54020c0df
RESTORATION_COMPLETION_CHECKPOINT=true
MAIN_MUST_FOREVER_EQUAL_CHECKPOINT_SHA=false
RESTORED_BASELINE_MUST_NOT_REGRESS=true
HISTORICAL_CORE_SEMANTICS_MUST_NOT_BE_REWRITTEN=true
HISTORICAL_MASTER_V2_DOUBLE_PLAY_BASELINE=IMMUTABLE_NORMATIVE_BASELINE
CURRENT_SYSTEM_MUST_CONFORM_TO_HISTORICAL_CORE=true
NO_CURRENT_FIRST_ARCHITECTURE=true
```

The SHA is a historical completion checkpoint, not a prohibition of later
legitimate `main` development. Future `main` may evolve if and only if
protected semantics/invariants are preserved or a new explicit Owner
decision authorizes a change.

## 2) Checkpoint attestation (precision-bounded)

Attested at `RESTORATION_COMPLETION_CHECKPOINT_SHA` only. These are
preservation claims, not an epistemic overclaim that every historical
artifact that ever existed was recovered.

```text
MASTER_V2_DOUBLE_PLAY_CORE_RUNTIME_COMPLETE=true
MASTER_V2_DOUBLE_PLAY_CORE_PROOF_COMPLETE=true
MASTER_V2_DOUBLE_PLAY_CORE_DOC_COMPLETE=true
MASTER_V2_DOUBLE_PLAY_RESTORATION_COMPLETE=true
ACTIVE_PATH_CORE_CHAIN_STATUS=RESTORED
FULL_CHAIN_HISTORICAL_CONTINUITY_STATUS=PROVEN
APPENDIX_A_CORE_LOGIC_PARITY_POST_6135_STATUS=PASS
HARDENING_V2_SAFETY_SEAM_STATUS=RESTORED_TO_HISTORICAL_BASELINE
HOST_GRAPH_SSOT_STATUS=CORRECTED
DOC_RUNTIME_MATCH=true
O051_POST_STATUS=DOC_CLOSED
OPEN_RUNTIME_GAPS=NONE
OPEN_PROOF_GAPS=NONE
OPEN_DOC_GAPS=NONE
OPEN_GOVERNANCE_GAPS=NONE_THAT_BLOCK_RESTORATION
ALL_HISTORICALLY_ATTESTED_MASTER_V2_DOUBLE_PLAY_MATERIAL_AVAILABLE_IN_THE_PRESERVED_RECOVERY_CORPUS_HAS_BEEN_ADJUDICATED_FOR_RESTORATION_RELEVANCE=true
ALL_HISTORICALLY_REQUIRED_CORE_RUNTIME_SEMANTICS_RESTORED=true
ALL_HISTORICALLY_REQUIRED_CORE_PROOF_OBLIGATIONS_CLOSED=true
ALL_HISTORICALLY_REQUIRED_CORE_DOC_OBLIGATIONS_CLOSED=true
KNOWN_NON_BLOCKING_FORENSIC_AMBIGUITIES_REMAIN_ARCHIVAL=true
EVERYTHING_THAT_EVER_EXISTED_WAS_RECOVERED=false
RESTORATION_CLAIM_PRECISION_STATUS=BOUNDED_NO_OVERCLAIM
```

## 3) Normative preservation principle

Historically attested Core has precedence over later incompatible
Current-system / Host / Hardening components.

Later components may be kept or integrated only if compatible.
Incompatible later components may be removed, decoupled, degraded,
rewired, or simplified. They may **not** force a rewrite of historical
Core in order to preserve themselves.

## 4) Protected core chain

```text
PROTECTED_CORE_CHAIN=
  CMC / Market State
  → C2/C3
  → Survival
  → Suitability
  → Composition
  → Double Play SideState / EntryExit
  → STEP-29P Risk/Sizing
  → Replay Safety
  → STEP-29Q PLAN_ONLY Intent
  → Recon Evidence Binder
  → KillSwitch Evidence Binder
  → Intended Action Mapper
  → SimulatedExecutionPort
  → simulated Accounting / Portfolio effects
```

Host / post-core components are not automatically historical Core
authority. Guards must distinguish historical owners from downstream
consumers.

## 5) Owner / authority invariants

```text
CANONICAL_COMPUTE_OWNER=trading.master_v2.integrated_offline_trading_logic_replay_v1
CANONICAL_RISK_SIZING_OWNER=STEP-29P / capital_risk_sizing_v1
CANONICAL_REPLAY_SAFETY_OWNER=safety_kernel_offline_replay_binding_adapter_v0.evaluate_offline_safety_kernel_boundary_v0
CANONICAL_INTENT_OWNER=STEP-29Q / canonical_order_intent_v1
CANONICAL_SIDESTATE_WRITER=double_play_state.transition_state
CANONICAL_ENTRY_EXIT_OWNER=evaluate_double_play_entry_exit_policy_v0
SECOND_COMPUTE_OWNER_EXISTS=false
SECOND_RISK_OWNER_EXISTS=false
SECOND_SAFETY_OWNER_EXISTS=false
SECOND_INTENT_OWNER_EXISTS=false
INTENDED_ACTION_MAPPER_ROLE=DOWNSTREAM_CONSUMER_TRANSLATOR
INTENDED_ACTION_MAPPER_COMPUTE_OWNER=false
INTENDED_ACTION_MAPPER_RISK_OWNER=false
INTENDED_ACTION_MAPPER_SAFETY_OWNER=false
INTENDED_ACTION_MAPPER_INTENT_OWNER=false
C4_NEW_STAGE=false
C4_NEW_OWNER=false
```

## 6) Ordering / safety invariants

```text
STEP_29P_BEFORE_SAFETY=true
SAFETY_BEFORE_STEP_29Q=true
NO_29Q_BEFORE_SAFETY=true
29P_CALL_COUNT_PER_REPLAY=1
SAFETY_CALL_COUNT_PER_REPLAY=1
29Q_CALL_COUNT_MAX_PER_REPLAY=1
ENTER_HARD_BLOCK_SKIPS_ENTER_29Q=true
ENTER_HARD_BLOCK_PRODUCES_NO_ENTER_COI=true
EXIT_NOT_BLANKET_SUPPRESSED=true
SAFETY_EXIT_PRESERVES_EXIT=true
EXIT_PRECEDENCE_PRESERVED=true
FLAT_BEFORE_OPPOSITE_REVERSAL_SAFETY_PRESERVED=true
SAFETY_DOES_NOT_GRANT_EXECUTION_PERMISSION=true
PLAN_ONLY_BOUNDARY_PRESERVED=true
```

## 7) Downstream host / hardening invariants (Model B)

```text
MODEL_B=
  Historical Core
  → downstream host consumption
  → compatible/fail-closed execution guards
  → simulated execution
```

Downstream guards MAY fail-closed prevent new exposure, refuse
non-actionable results, and protect technical host limits.

Downstream guards MUST NOT recompute SideState, rewrite EntryExit,
convert historical EXIT/REDUCE to HOLD, recompute Risk/Sizing, replace
CanonicalOrderIntent, form a second Safety owner, or redefine Safety-PASS.

```text
NO_GENERIC_POST_MAPPER_EXIT_TO_HOLD=true
ENTER_WITHOUT_CANONICAL_ORDER_INTENT_CANNOT_BUY_OR_SELL=true
CAP65_EXIT_PRODUCERS_REMAIN_CONSUMED=true
BRIDGE_SAFETY_ROLE=INPUT_PRODUCER_ONLY
HOST_MAPPER_ROLE=CONSUMER_TRANSLATOR_ONLY
```

## 8) C4 / host graph / full-chain preservation

C4 remains the existing Post-Confirmation Binding
Survival → Suitability → Composition.

Spec: `docs/ops/specs/MV2_C4_POST_CONFIRMATION_SURVIVAL_SUITABILITY_COMPOSITION_BINDING_V1.md`

Runtime surface: `trading.master_v2.post_confirmation_survival_suitability_composition_binding_v1`

Integrated Replay consumes C4. No new stage. No new owner.

§5.3 Host Graph must not represent post-Replay Risk/Safety/Intent labels
as second owner calls.

```text
FULL_CHAIN_GOLDEN_VECTOR_STRATEGY=OWNER_COMPOSED
GOLDEN_VECTOR_CORPUS_STATUS=ABSENT
NEW_GOLDEN_VECTOR_CORPUS=false
TESTS_PROVE_IMPLEMENTATION_CONSISTENCY=true
TESTS_DEFINE_HISTORICAL_TRUTH=false
```

No frozen Golden-JSON corpus may become a second semantic SSOT.

## 9) Forensic authority boundary

```text
FORENSIC_REFERENCE_AUTHORITY=NONE
MAP_OF_TRUTH_STATUS=NAVIGATION_ONLY
FORENSIC_REFERENCE_PACKAGE=forensics/historical_reference/sha256-a5a468f761e24e17fc0402dbf056df7d45090b3c58f0e9a2ad469569e908e212/
O046_GATE_3_MATRIX_CANONICALIZED=false
UQ1_UQ8_IDS_CANONICALIZED=false
O059_UNRESOLVED_TOKEN_ALIASES_CANONICALIZED=false
FORENSIC_EVIDENCE_IS_NOT_CANONICAL_POLICY=true
```

Only a separate future Owner authorization could create new policy from
archival forensic material.

## 10) Compatibility adjudication contract

Every component under future or already-present Current-/Host-/Hardening-/Feature
review must be adjudicated on all of the following dimensions:

```text
COMPATIBILITY_DIMENSIONS=
  A. HISTORICAL_SEMANTIC_COMPATIBILITY
  B. AUTHORITY_COMPATIBILITY
  C. OWNER_COMPATIBILITY
  D. CALL_ORDER_COMPATIBILITY
  E. SAFETY_COMPATIBILITY
  F. INTENT_COMPATIBILITY
  G. EXIT_PRECEDENCE_COMPATIBILITY
  H. STATE_WRITER_COMPATIBILITY
  I. RISK_SIZING_COMPATIBILITY
  J. FAIL_CLOSED_COMPATIBILITY
  K. SIMULATED_EXECUTION_BOUNDARY_COMPATIBILITY
  L. FORENSIC_AUTHORITY_COMPATIBILITY
  M. LIVE_TRADING_AUTHORITY_COMPATIBILITY
COMPATIBILITY_OUTCOMES_SUPPORTED=
  COMPATIBLE
  COMPATIBLE_WITH_CONSTRAINTS
  INCOMPATIBLE
  UNKNOWN_INSUFFICIENT_EVIDENCE
```

Definitions:

- `COMPATIBLE` — may be kept/integrated without changing the protected baseline.
- `COMPATIBLE_WITH_CONSTRAINTS` — substance may be kept, but needs downstream
  adaptation, decoupling, or restriction.
- `INCOMPATIBLE` — would violate protected historical semantics or authority;
  must not rewrite Core to preserve the component.
- `UNKNOWN_INSUFFICIENT_EVIDENCE` — no plausible assumption; fail-closed;
  no integration until evidence suffices.

This slice does **not** adjudicate any concrete larger component.

## 11) Required future adjudication output

```text
COMPONENT=
PROVENANCE=
CURRENT_ROLE=
HISTORICAL_ROLE=
AUTHORITY_SOURCE=
HISTORICAL_SEMANTIC_COMPATIBILITY=
AUTHORITY_COMPATIBILITY=
OWNER_COMPATIBILITY=
CALL_ORDER_COMPATIBILITY=
SAFETY_COMPATIBILITY=
INTENT_COMPATIBILITY=
EXIT_PRECEDENCE_COMPATIBILITY=
STATE_WRITER_COMPATIBILITY=
RISK_SIZING_COMPATIBILITY=
FAIL_CLOSED_COMPATIBILITY=
SIMULATED_EXECUTION_BOUNDARY_COMPATIBILITY=
FORENSIC_AUTHORITY_COMPATIBILITY=
LIVE_TRADING_AUTHORITY_COMPATIBILITY=
OVERALL_COMPATIBILITY=
KEEP_AS_IS=
ADAPT_DOWNSTREAM=
DECOUPLE=
DEGRADE=
REMOVE=
REWIRE=
CORE_MUTATION_REQUIRED=
NEW_OWNER_REQUIRED=
NEW_POLICY_REQUIRED=
EVIDENCE_GAPS=
PROPOSED_SAFE_ACTION=
```

## 12) Existing guards reused (not duplicated)

| Invariant | Canonical source | Current guard | Guard complete |
|---|---|---|---|
| 29P → Safety → 29Q call order and counts | Master §5.3; Safety-before-Intent restore spec | `tests/trading/master_v2/test_master_v2_integrated_replay_safety_before_intent_restore_contract_v1.py` | true |
| ENTER hard-block skips 29Q / no ENTER COI | Safety-before-Intent restore spec | same restore contract | true |
| EXIT not blanket-suppressed / PLAN_ONLY | Safety-before-Intent restore spec | same restore contract | true |
| Appendix-A core-logic parity | Master Appendix A; Appendix-A post-6135 spec | `tests/trading/master_v2/test_master_v2_integrated_replay_appendix_a_core_logic_parity_post_6135_contract_v1.py` | true |
| §5.3 post-Replay labels are not second owners | Master §5.3; host-graph SSOT spec | `tests/ops/test_master_v2_section_5_3_host_graph_ssot_adjudication_v1.py` | true |
| C4 named pointer / not new owner or stage | Master §5.3; C4 spec | `tests/ops/test_master_v2_c4_named_master_ssot_pointer_v1.py` | true |
| Hardening-v2 EXIT preservation / mapper / Cap 6.5 | Hardening-v2 safety-seam spec | `tests/ops/test_hardening_v2_historical_safety_seam_contracts_v1.py` | true |
| Owner-composed full-chain; no golden JSON corpus | host-graph SSOT spec | `tests/trading/master_v2/test_master_v2_owner_composed_full_chain_host_consumption_proof_v1.py` | true |
| Restoration admission; forensic AUTHORITY=NONE | restoration admission spec + JSON grant | `tests/governance/test_historically_attested_current_system_semantic_restoration_authorization_v1.py` | true |
| Forensic package AUTHORITY=NONE | `AUTHORITY_NONE.txt` in historical-reference package | package files + restoration grant | true |
| Parallel-owner / skip-safety residual quarantine | Master §5.3; parallel-owner quarantine spec | `tests/ops/test_peak_trade_post_restoration_parallel_owner_and_skip_safety_path_quarantine_v1.py` | true |

## 13) Missing protection closed by this contract

Previously incomplete as a durable post-restoration preservation layer:

- restoration completion checkpoint SHA semantics (`MUST_NOT_REGRESS` without freezing `main`)
- compatibility adjudication dimensions, outcomes, and required output schema
- restoration claim precision (no overclaim)
- explicit Current-must-conform / no Core rewrite principle
- meta-presence of the reused guards as a non-silent-deletion layer
- explicit non-canonicalization of O046 Gate-3, UQ1–UQ8, O059 aliases

Exact proof file:

`tests/ops/test_peak_trade_post_restoration_baseline_preservation_and_compatibility_contract_v1.py`

## 14) Negative contract

```text
RUNTIME_CORE_MUTATION=false
TRADING_LOGIC_MUTATION=false
COMPUTE_OWNER_MUTATION=false
RISK_OWNER_MUTATION=false
SAFETY_OWNER_MUTATION=false
INTENT_OWNER_MUTATION=false
SIDESTATE_WRITER_MUTATION=false
ENTRY_EXIT_OWNER_MUTATION=false
HOST_RUNTIME_MUTATION=false
HARDENING_RUNTIME_MUTATION=false
EXECUTION_RUNTIME_MUTATION=false
COMPONENT_ADJUDICATION_PERFORMED=false
WORKSTREAM_B_RUNTIME_START=false
CAP_11_RUNTIME_START=false
RECOVERY_TRACK_TOUCHED=false
PR_6129_TOUCHED=false
GATE_3_CANONICALIZED=false
UQ_BINDING_PERFORMED=false
O059_INFERENCE_PERFORMED=false
MULTI_FUTURE_ACTIVATED=false
LIVE_READINESS_MUTATION=false
ORDER_SUBMIT_PERFORMED=false
FLATTEN_PERFORMED=false
TRADING_PERFORMED=false
LIVE_AUTHORITY_CHANGED=false
```
