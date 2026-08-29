# Peak_Trade — Post-Restoration Live Safety Gates Adjudication v1

status: ACTIVE
last_updated: 2026-08-29
owner: Peak_Trade
purpose: Persist the already-adjudicated live-safety admission layer after closed simulated-execution pipeline alignment (#6144). Not a second SSOT. Not restoration reopen. Not core runtime mutation. Not live or execution authority. Not venue-pretrade adjudication.
docs_token: DOCS_TOKEN_PEAK_TRADE_POST_RESTORATION_LIVE_SAFETY_GATES_ADJUDICATION_V1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
AUTHORITY_RELATION=SUBORDINATE_TO_MASTER_RUNBOOK_SECTION_5_3
CANONICAL_AUTHORITY=docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md
PARENT_CONTRACT=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_BASELINE_PRESERVATION_AND_COMPATIBILITY_CONTRACT_V1.md
PRIOR_SIMULATED_EXECUTION_PIPELINE_ADJUDICATION=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_SIMULATED_EXECUTION_PIPELINE_ADJUDICATION_V1.md
PRIOR_ACCOUNTING_PORTFOLIO_ADJUDICATION=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_ACCOUNTING_PORTFOLIO_ALIGNMENT_ADJUDICATION_V1.md
PRIOR_QUARANTINE_PARALLEL_OWNER=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_PARALLEL_OWNER_AND_SKIP_SAFETY_PATH_QUARANTINE_V1.md
PRIOR_QUARANTINE_REMAINING_P0=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_REMAINING_P0_QUARANTINE_V1.md
HOST_GRAPH_SSOT=docs/ops/specs/MASTER_V2_DOUBLE_PLAY_HOST_GRAPH_SSOT_AND_OWNER_COMPOSED_FULL_CHAIN_PROOF_V1.md
PARALLEL_SSOT_CREATED=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
CORE_RUNTIME_MUTATION=false
DEFAULT_RUNTIME_MUTATION=false
NEW_SEMANTIC_POLICY=false
NEW_RUNTIME_OWNER=false
NEW_STAGE=false
NEW_LIVE_SAFETY_COMPONENT_REQUIRED=false
RESTORATION_REOPEN_REQUIRED=false
MASTER_V2_DOUBLE_PLAY_RESTORATION_COMPLETE=true
COMPATIBILITY_CONTRACT_DOES_NOT_GRANT_EXECUTION_AUTHORITY=true
LIVE_AUTHORIZED=false
TESTNET_AUTHORIZED=false
CANARY_AUTHORIZED=false
LIVE_ENABLED=false
LIVE_ARMED=false
EXECUTION_ELIGIBLE=false
LIVE_READINESS=EVALUATED_NOT_READY
ORDERS_AUTHORIZED=false
NO_TRADING=true
NO_LIVE_AUTHORITY=true
NO_EXECUTION_AUTHORITY=true
CHANGED_RUNTIME_FILES=NONE
RUNTIME_ALIGNMENT_REQUIRED=false
RUNTIME_MUTATION_JUSTIFIED=false
```

This document is subordinate to the Master Runbook and to the post-restoration
preservation contract. It does not replace Master §5.3, Appendix A, C4, Replay
Safety, Cap 7.2, simulated-execution #6144, accounting/portfolio #6143, or the
closed P0 quarantines. It persists the already-proven live-safety owner model
so later hosts cannot be misread as a second Core Safety owner, as standing
Live authorization, or as venue-pretrade completeness.

## 1) Restoration boundary

```text
RESTORATION_COMPLETION_CHECKPOINT_SHA=21452016ff998c1af63f24c36060f2a54020c0df
HISTORICAL_MASTER_V2_DOUBLE_PLAY_BASELINE=IMMUTABLE_NORMATIVE_BASELINE
CURRENT_SYSTEM_MUST_CONFORM_TO_HISTORICAL_CORE=true
NO_CURRENT_FIRST_ARCHITECTURE=true
HISTORICAL_CORE_SEMANTICS_MUST_NOT_BE_REWRITTEN=true
P0_QUARANTINE_REMAINS_CLOSED=true
ACCOUNTING_PORTFOLIO_ALIGNMENT_REMAINS_CLOSED=true
SIMULATED_EXECUTION_PIPELINE_REMAINS_CLOSED=true
```

## 2) Protected productive owner graph

```text
COMPUTE_OWNER=trading.master_v2.integrated_offline_trading_logic_replay_v1
RISK_OWNER=STEP-29P / src.governance.capital_risk_sizing_v1
SAFETY_OWNER=trading.master_v2.safety_kernel_offline_replay_binding_adapter_v0
INTENT_OWNER=STEP-29Q / src.governance.canonical_order_intent_v1
SIDESTATE_WRITER=trading.master_v2.double_play_state.transition_state
ENTRY_EXIT_OWNER=evaluate_double_play_entry_exit_policy_v0
INTENDED_ACTION_MAPPER_ROLE=DOWNSTREAM_TRANSLATOR_ONLY
CANONICAL_EXECUTION_OWNER=SimulatedExecutionPortV1_DELEGATE_CAP3_1
SECOND_COMPUTE_OWNER_EXISTS=false
SECOND_RISK_OWNER_EXISTS=false
SECOND_SAFETY_OWNER_EXISTS=false
SECOND_INTENT_OWNER_EXISTS=false
SECOND_EXECUTION_OWNER_EXISTS=false
SECOND_ACCOUNTING_OWNER_CONFLICT=false
CLOSED_OWNER_GRAPH_PRESERVED=true
PRODUCTIVE_ORDERING=29P → Replay Safety → 29Q PLAN_ONLY → mapper → simulated execution
STEP_29P_BEFORE_SAFETY=true
SAFETY_BEFORE_STEP_29Q=true
NO_29Q_BEFORE_SAFETY=true
SAFETY_PASS_IS_NOT_EXECUTION_PERMISSION=true
```

Canonical productive order remains STEP-29P → Replay Safety → STEP-29Q
PLAN_ONLY. Live admission is not in that sequence. Tests are guards, not a
second semantic SSOT.

## 3) Adjudication result

```text
ADJUDICATION_RESULT=DISTINCT_COMPATIBLE_LIVE_SAFETY_RESPONSIBILITIES
LIVE_SAFETY_GATES_COMPLETE=true
EARLIEST_INCOMPLETE_LIVE_SAFETY_EDGE=NONE
LIVE_SAFETY_GATE_COUNT=18
PRODUCTIVELY_REACHABLE_LIVE_SAFETY_GATES=12
LIVE_GATE_OWNER_MODEL=DISTINCT_NON_OVERLAPPING_HOST_FAMILY_ADMISSION_GATES_NOT_A_SECOND_CORE_SAFETY_OWNER
SECOND_LIVE_SAFETY_OWNER_EXISTS=false
SECOND_CORE_SAFETY_OWNER_EXISTS=false
BYPASS_PATH_CONFLICT=false
RUNTIME_ALIGNMENT_REQUIRED=false
RUNTIME_MUTATION_JUSTIFIED=false
NEW_LIVE_SAFETY_COMPONENT_REQUIRED=false
RESTORATION_REOPEN_REQUIRED=false
PREEXISTING_CALL_GRAPH_DRIFT_CLASS=LABEL_ONLY
PREEXISTING_CALL_GRAPH_DRIFT_IN_SCOPE=false
PREEXISTING_CALL_GRAPH_DRIFT_REPAIRED=false
VENUE_PRETRADE_ADJUDICATION_IN_SCOPE=false
VENUE_PRETRADE_WORK_REMAINS=true
NEXT_DISTINCT_SURFACE=VENUE_PRETRADE_LIMIT_GATES
```

Not `DUPLICATE_LIVE_SAFETY_OWNER_CONFLICT`: two host-family admission
implementations are not a second Core Safety owner.

Not `LIVE_SAFETY_RUNTIME_ALIGNMENT_REQUIRED`: standing fail-closed admission
already exists on inventoried submit paths.

Not `LIVE_SAFETY_GATES_ALREADY_COMPLETE` as a persist-skip: this slice persists
the already-true owner model. Completeness of the gates is `true`; venue
pretrade remains a later named surface.

## 4) Owner separation

```text
CORE_REPLAY_SAFETY_ROLE=SOLE_CORE_SAFETY_OWNER_FOR_MASTER_V2_DOUBLE_PLAY_REPLAY_SEQUENCE
LIVE_ADMISSION_ROLE=DOWNSTREAM_HOST_FAMILY_ADMISSION_NOT_CORE_REPLAY_SAFETY
OKX_CANARY_ADMISSION_ROLE=evaluate_canary_submit_gates_v1
PIPELINE_KRAKEN_ADMISSION_ROLE=SafetyGuard.ensure_may_place_order
NETWORKED_ONRAMP_ROLE=guard_transport_gate_v1 + evaluate_canary_live_gate_v1
NO_ORDER_HOST_BARRIER_ROLE=validate_no_order_mode_v1
FLATTEN_ROLE=SEPARATE_EMERGENCY_AUTHORITY_NOT_LIVE_ADMISSION_OWNER
INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_ROLE=NON_AUTHORIZING_NON_REPLAY_SAFETY
CAP11_LIVE_TESTNET_FIXTURE_PORTS_ROLE=DECLARED_UNREACHABLE_CONTRACTS_ONLY
```

Live admission is not Replay Safety. SafetyGuard on the pipeline/Kraken family
is a downstream admission gate. Canary submit gates are OKX-Canary-family
admission. Networkless onramp remains deny. Flatten is a separate emergency
authority and is not the Live Admission owner.

## 5) Named live-admission families (count=18)

Standing constants and host-family evaluators that prevent, allow, or
condition Live execution. Names are labels, not authority:

```text
GATE_01=STANDING_LIVE_AUTHORIZED
GATE_02=STANDING_TESTNET_AUTHORIZED
GATE_03=STANDING_CANARY_AUTHORIZED
GATE_04=STANDING_LIVE_ENABLED
GATE_05=STANDING_LIVE_ARMED
GATE_06=STANDING_ENABLE_LIVE_TRADING
GATE_07=STANDING_SUBMIT_UNLOCKED
GATE_08=SAFETYGUARD_ENSURE_MAY_PLACE_ORDER
GATE_09=LIVE_MODE_GATE_ENFORCE
GATE_10=CANARY_SUBMIT_GATES_V1
GATE_11=CANARY_LIVE_GATE_NETWORKLESS_V1
GATE_12=TRANSPORT_GATE_NETWORKLESS_V1
GATE_13=ARMED_GATE
GATE_14=STRATEGY_PORTFOLIO_LIVE_ELIGIBILITY
GATE_15=DATA_QUALITY_LIVE_GATE
GATE_16=PLAN_ONLY_EXECUTION_ELIGIBLE
GATE_17=NO_ORDER_ACTIVATION_LIVE_FLAG_REFUSAL
GATE_18=CAP11_LIVE_TESTNET_FIXTURE_PORTS
```

Replay Safety is not in this count. Flatten pre-send / flatten-execute
authority is not in this count. Independent pre-trade kernel is not in this
count.

Productively reachable as fail-closed deny evaluators on current
`origin/main` hosts: standing flags, SafetyGuard, Canary submit, networkless
transport/canary-live gates, plan-only eligibility, and no-order activation
refusal (12). Cap 11 fixture ports remain `LIVE_EXECUTION_REACHABLE=false`.

## 6) Current authorization state

Do not collapse these planes:

```text
AUTHORIZATION_LIVE_AUTHORIZED=false
AUTHORIZATION_TESTNET_AUTHORIZED=false
AUTHORIZATION_CANARY_AUTHORIZED=false
AUTHORIZATION_ORDER_SUBMIT_AUTHORIZED=false
ARMING_LIVE_ENABLED=false
ARMING_LIVE_ARMED=false
ARMING_ENABLE_LIVE_TRADING=false
ELIGIBILITY_EXECUTION_ELIGIBLE=false
READINESS_SECTION_11_13_LIVE_READINESS_EVALUATION_COMPLETED=true
READINESS_FULLY_AUTONOMOUS_LIVE_TRADING_READY=false
LIVE_READINESS=EVALUATED_NOT_READY
HOST_REACHABILITY_CANARY_SUBMIT_TRANSPORT_IMPLEMENTED=true
HOST_REACHABILITY_CANARY_SUBMIT_TRANSPORT_ACTIVATED=false
HOST_REACHABILITY_CAP11_LIVE_EXECUTION_REACHABLE=false
CREDENTIAL_AVAILABILITY_IS_NOT_AUTHORIZATION=true
VENUE_ACCEPTANCE_NOT_ADJUDICATED_THIS_SLICE=true
```

## 7) Negative claims

```text
LIVE_ADMISSION_IS_NOT_REPLAY_SAFETY=true
SAFETY_PASS_IS_NOT_EXECUTION_PERMISSION=true
READINESS_IS_NOT_AUTHORIZATION=true
CREDENTIAL_PRESENCE_IS_NOT_AUTHORIZATION=true
ENABLED_IS_NOT_AUTHORIZED=true
ARMED_IS_NOT_AUTHORIZED=true
TESTNET_IS_NOT_LIVE=true
CANARY_IS_NOT_STANDING_LIVE_AUTHORITY=true
SIMULATED_EXECUTION_IS_NOT_LIVE_PERMISSION=true
POSITION_ABSENCE_IS_NOT_ZERO=true
CYBERSECURITY_PASS_IS_NOT_LIVE_AUTHORIZATION=true
MULTIPLE_HOST_ADMISSION_GATES_DO_NOT_IMPLY_DUPLICATE_CORE_SAFETY_OWNER=true
PRE_LIVE_CYBERSECURITY_GATE_PASS_IS_NOT_LIVE_ENABLED=true
PRE_LIVE_CYBERSECURITY_GATE_PASS_IS_NOT_LIVE_ARMED=true
EMPTY_DATA_IS_NOT_ZERO=true
ABSENT_TARGET_ROW_IS_NOT_ZERO=true
FLATTEN_IS_NOT_LIVE_ADMISSION_OWNER=true
PAPER_EXECUTION_ENGINE_IS_NOT_LIVE_SUBMIT_PATH=true
```

## 8) Path graph (static; currently disabled)

The restored no-order path terminates at simulated execution. Live submit is
a separate host family.

```text
RESTORED_NO_ORDER_PATH=MasterV2 → 29P → Replay Safety → 29Q PLAN_ONLY → mapper → SimulatedExecutionPortV1
RESTORED_NO_ORDER_TO_LIVE_SUBMIT=DECLARED_UNREACHABLE
OKX_CANARY_PATH=runner → submit_transport → evaluate_canary_submit_gates_v1 → refuse_submit_unless_gates_pass_v1 → post_entry_order
OKX_CANARY_PATH_EDGE_CLASS=PROVEN_STATIC_BINDING
PIPELINE_KRAKEN_PATH=ExecutionPipeline.submit_order → SafetyGuard.ensure_may_place_order → execute_with_safety
PIPELINE_KRAKEN_PATH_EDGE_CLASS=PROVEN_STATIC_BINDING
NETWORKED_ONRAMP_PATH=onramp_cli → guard_transport_gate_v1 → evaluate_canary_live_gate_v1
NETWORKED_ONRAMP_PATH_EDGE_CLASS=PROVEN_STATIC_BINDING
CAP11_FIXTURE_PORTS_EDGE_CLASS=DECLARED_UNREACHABLE
FLATTEN_PATH_CLASS=SEPARATE_EMERGENCY_AUTHORITY
INFERRED_EDGES_ARE_NOT_PROVEN=true
```

`SimulatedExecutionPortV1` does not import SafetyGuard or Canary submit
gates. Integrated Replay does not place orders.

## 9) Venue-pretrade boundary

Live-safety responsibility ends at host admission. Venue-native checks remain
a later named surface.

```text
LIVE_SAFETY_TO_VENUE_PRETRADE_BOUNDARY=AFTER_HOST_ADMISSION_AUTH_ARM_ELIG_ENV_CONFIRM_CYBER_CREDENTIAL_CLASS_INSTRUMENT_BIND_OPEN_STATE_BEFORE_VENUE_NATIVE_SIZE_PRICE_LEVERAGE_POSMODE_MARGIN_MAXAVAIL_LOT_TICK
VENUE_PRETRADE_WORK_REMAINS=true
VENUE_PRETRADE_ADJUDICATION_IN_SCOPE=false
VENUE_PRETRADE_LIMIT_GATES=NOT_THIS_SLICE
NEXT_DISTINCT_SURFACE=VENUE_PRETRADE_LIMIT_GATES
VENUE_NATIVE_SIZE_PRICE_LEVERAGE_POSMODE_MARGIN_MAXAVAIL_LOT_TICK=NEXT_NAMED_SURFACE
```

This slice does not close venue-pretrade completeness and does not implement
venue limit gates.

## 10) Guards (not SSOT)

Exact proof file:

`tests/ops/test_peak_trade_post_restoration_live_safety_gates_adjudication_v1.py`

Guards must keep:

- Master §5.3 names this spec and `LIVE_SAFETY_GATES_ADJUDICATION_RESULT=DISTINCT_COMPATIBLE_LIVE_SAFETY_RESPONSIBILITIES`
- live-safety complete; second core safety owner false; bypass false; runtime alignment false
- Replay Safety remains the sole Core Safety owner; 29P → Safety → 29Q remains
- Live admission is not classified as Replay Safety
- standing `LIVE_AUTHORIZED` / `TESTNET_AUTHORIZED` / `CANARY_AUTHORIZED` / `LIVE_ENABLED` / `LIVE_ARMED` remain false
- Readiness, cybersecurity PASS, and credential presence are not authorization
- OKX Canary gates remain admission-specific; SafetyGuard remains downstream admission
- networkless onramp remains deny; no-order host refuses live/testnet flags
- Cap 11 live/testnet fixtures remain declared unreachable
- simulated execution has no productive live-submit edge
- PaperEngine / PaperBroker are not bound as a live path
- Flatten remains separate emergency authority
- empty/absent position data is not zero
- venue-native size/price/leverage/posMode/margin/maxAvail/lot/tick remain the next separate surface
- #6143 and #6144 remain closed
- preexisting CALL_GRAPH equality test is not repaired in this slice

## 11) Out of scope this slice

```text
PREEXISTING_CALL_GRAPH_DRIFT_IN_SCOPE=false
CALL_GRAPH_V1_HARMONIZATION=NOT_THIS_SLICE
REQUIRED_CALL_GRAPH_HARMONIZATION=NOT_THIS_SLICE
TEST_CONSTANTS_AND_CALL_GRAPH_BOUND_REPAIR=NOT_THIS_SLICE
VENUE_PRETRADE_LIMIT_GATES=NOT_THIS_SLICE
VENUE_PRETRADE_ADJUDICATION_IN_SCOPE=false
SEE_ALSO_VENUE_PRETRADE_LIMIT_GATES_ADJUDICATION=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_VENUE_PRETRADE_LIMIT_GATES_ADJUDICATION_V1.md
SEE_ALSO_VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_ADJUDICATION=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_ADJUDICATION_V1.md
SEE_ALSO_EXACT_VENUE_METADATA_GET_CURRENT_SUI_PRETRADE_MAX_SIZE=docs/ops/specs/PEAK_TRADE_EXACT_VENUE_METADATA_GET_CURRENT_SUI_PRETRADE_MAX_SIZE_V1.md
CANARY_EXECUTE=NOT_THIS_SLICE
FLATTEN=NOT_THIS_SLICE
MULTI_FUTURE=NOT_THIS_SLICE
CAP_11_2_TO_11_12_ACTIVATION=NOT_THIS_SLICE
PR_6129=NOT_THIS_SLICE
RECOVERY_TRACK=NOT_THIS_SLICE
SAFETYGUARD_RUNTIME_MUTATION=NOT_THIS_SLICE
REPLAY_SAFETY_RUNTIME_MUTATION=NOT_THIS_SLICE
CANARY_SUBMIT_GATES_RUNTIME_MUTATION=NOT_THIS_SLICE
TRANSPORT_NETWORKLESS_RUNTIME_MUTATION=NOT_THIS_SLICE
NO_ORDER_ACTIVATION_RUNTIME_MUTATION=NOT_THIS_SLICE
CORE_RUNTIME_MUTATION=false
```

Historical `LIVE_SAFETY_GATES=NOT_THIS_SLICE` rows in prior post-restoration
specs remain historically true for those slices. Later live-safety
adjudication is recorded here. Later venue-pretrade limit-gates adjudication
is recorded in `SEE_ALSO_VENUE_PRETRADE_LIMIT_GATES_ADJUDICATION`. Historical
`VENUE_PRETRADE_LIMIT_GATES=NOT_THIS_SLICE` remains true for this live-safety
slice. Later venue-pretrade metadata-binding alignment adjudication is
recorded in `SEE_ALSO_VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_ADJUDICATION`.

## 12) Existing guards reused (not duplicated)

| Invariant | Current guard |
|---|---|
| 29P → Safety → 29Q productive Replay order | `tests/trading/master_v2/test_master_v2_integrated_replay_safety_before_intent_restore_contract_v1.py` |
| Appendix-A core parity | `tests/trading/master_v2/test_master_v2_integrated_replay_appendix_a_core_logic_parity_post_6135_contract_v1.py` |
| Hardening-v2 historical safety seam | `tests/ops/test_hardening_v2_historical_safety_seam_contracts_v1.py` |
| Owner-composed full-chain host consumption | `tests/trading/master_v2/test_master_v2_owner_composed_full_chain_host_consumption_proof_v1.py` |
| §5.3 host-graph SSOT | `tests/ops/test_master_v2_section_5_3_host_graph_ssot_adjudication_v1.py` |
| C4 named Master pointer | `tests/ops/test_master_v2_c4_named_master_ssot_pointer_v1.py` |
| Historically attested restoration authorization | `tests/governance/test_historically_attested_current_system_semantic_restoration_authorization_v1.py` |
| Parallel-owner / skip-safety quarantine | `tests/ops/test_peak_trade_post_restoration_parallel_owner_and_skip_safety_path_quarantine_v1.py` |
| Remaining P0 quarantine | `tests/ops/test_peak_trade_post_restoration_remaining_p0_quarantine_v1.py` |
| Preservation / compatibility contract | `tests/ops/test_peak_trade_post_restoration_baseline_preservation_and_compatibility_contract_v1.py` |
| Accounting / portfolio alignment | `tests/ops/test_peak_trade_post_restoration_accounting_portfolio_alignment_adjudication_v1.py` |
| Simulated execution pipeline adjudication | `tests/ops/test_peak_trade_post_restoration_simulated_execution_pipeline_adjudication_v1.py` |
| Empty/absent is not zero | `tests/ops/test_section_11_13_5_z2cm_position_state_predicate_contract_v1.py` |
| Cap 11.9 fixture unreachable | `tests/ops/test_capability_11_9_live_canary_order_execution_v1.py` |

## 13) Negative contract

```text
RUNTIME_CORE_MUTATION=false
TRADING_LOGIC_MUTATION=false
COMPUTE_OWNER_MUTATION=false
RISK_OWNER_MUTATION=false
SAFETY_OWNER_MUTATION=false
INTENT_OWNER_MUTATION=false
SIDESTATE_WRITER_MUTATION=false
ENTRY_EXIT_OWNER_MUTATION=false
SAFETYGUARD_MUTATED=false
CANARY_SUBMIT_GATES_MUTATED=false
TRANSPORT_NETWORKLESS_GATES_MUTATED=false
NO_ORDER_ACTIVATION_MUTATED=false
FLATTEN_LOGIC_MUTATED=false
VENUE_PRETRADE_IMPLEMENTED=false
CHANGED_RUNTIME_FILES_EXPECTED=NONE
RUNTIME_DECOUPLING_REQUIRED=false
NEW_LIVE_SAFETY_COMPONENT_REQUIRED=false
RECOVERY_TRACK_TOUCHED=false
PR_6129_TOUCHED=false
LIVE_READINESS_MUTATION=false
ORDER_SUBMIT_PERFORMED=false
FLATTEN_PERFORMED=false
TRADING_PERFORMED=false
LIVE_AUTHORITY_CHANGED=false
FORENSIC_REFERENCE_AUTHORITY=NONE
MAP_OF_TRUTH_STATUS=NAVIGATION_ONLY
SECOND_CORE_OWNER_CREATED=false
SECOND_LIVE_SAFETY_OWNER_CREATED=false
PREEXISTING_CALL_GRAPH_DRIFT_REPAIRED=false
```
