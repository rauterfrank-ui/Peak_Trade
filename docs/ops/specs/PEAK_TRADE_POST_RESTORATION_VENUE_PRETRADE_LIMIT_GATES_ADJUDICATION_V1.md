# Peak_Trade — Post-Restoration Venue Pretrade Limit Gates Adjudication v1

status: ACTIVE
last_updated: 2026-08-29
owner: Peak_Trade
purpose: Persist the already-adjudicated venue-pretrade limit-gate surface after closed live-safety admission (#6145). Not a second SSOT. Not restoration reopen. Not core runtime mutation. Not live or execution authority. Not metadata-runtime binding. Not max-size implementation.
docs_token: DOCS_TOKEN_PEAK_TRADE_POST_RESTORATION_VENUE_PRETRADE_LIMIT_GATES_ADJUDICATION_V1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
AUTHORITY_RELATION=SUBORDINATE_TO_MASTER_RUNBOOK_SECTION_5_3
CANONICAL_AUTHORITY=docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md
PARENT_CONTRACT=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_BASELINE_PRESERVATION_AND_COMPATIBILITY_CONTRACT_V1.md
PRIOR_LIVE_SAFETY_GATES_ADJUDICATION=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_LIVE_SAFETY_GATES_ADJUDICATION_V1.md
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
NEW_VENUE_PRETRADE_COMPONENT_REQUIRED=false
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
Safety, Cap 7.2, live-safety #6145, simulated-execution #6144, accounting/portfolio
#6143, or the closed P0 quarantines. It persists the already-proven venue-pretrade
owner model so later hosts cannot be misread as a second Core Risk or Safety
owner, as standing Live authorization, or as venue-pretrade completeness.

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
LIVE_SAFETY_GATES_REMAIN_CLOSED=true
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
SECOND_VENUE_PRETRADE_OWNER_EXISTS=false
CLOSED_OWNER_GRAPH_PRESERVED=true
PRODUCTIVE_ORDERING=29P → Replay Safety → 29Q PLAN_ONLY → mapper → simulated execution
STEP_29P_BEFORE_SAFETY=true
SAFETY_BEFORE_STEP_29Q=true
NO_29Q_BEFORE_SAFETY=true
SAFETY_PASS_IS_NOT_EXECUTION_PERMISSION=true
VENUE_PRETRADE_IS_NOT_REPLAY_SAFETY=true
VENUE_PRETRADE_IS_NOT_CORE_RISK_AUTHORITY=true
VENUE_PRETRADE_IS_NOT_EXECUTION_AUTHORITY=true
VENUE_PRETRADE_IS_DOWNSTREAM_OF_LIVE_SAFETY=true
VENUE_PRETRADE_IS_UPSTREAM_OF_POST=true
```

Canonical productive order remains STEP-29P → Replay Safety → STEP-29Q
PLAN_ONLY. Venue pretrade is not in that sequence. It is a downstream
OKX-EEA-Canary validator after Live Safety admission and before POST.
Tests are guards, not a second semantic SSOT.

## 3) Adjudication result

```text
ADJUDICATION_RESULT=VENUE_METADATA_BINDING_ALIGNMENT_REQUIRED
VENUE_PRETRADE_LIMIT_GATES_COMPLETE=false
EARLIEST_INCOMPLETE_VENUE_PRETRADE_EDGE=MAX_SIZE
VENUE_PRETRADE_GATE_COUNT=12
PRODUCTIVELY_REACHABLE_VENUE_PRETRADE_GATES=0
CANONICAL_VENUE_PRETRADE_OWNER=section_11_13_5.order_plan_v1+exposure_v1@submit_transport_v1
VENUE_PRETRADE_OWNER_MODEL=OKX_EEA_CANARY_VENUE_CONSTRAINT_PLAN_OWNER_NOT_A_SECOND_CORE_RISK_OR_SAFETY_OWNER
SECOND_VENUE_PRETRADE_OWNER_EXISTS=false
BYPASS_PATH_CONFLICT=false
RUNTIME_ALIGNMENT_REQUIRED=false
RUNTIME_MUTATION_JUSTIFIED=false
NEW_VENUE_PRETRADE_COMPONENT_REQUIRED=false
RESTORATION_REOPEN_REQUIRED=false
PREEXISTING_CALL_GRAPH_DRIFT_CLASS=LABEL_ONLY
PREEXISTING_CALL_GRAPH_DRIFT_IN_SCOPE=false
PREEXISTING_CALL_GRAPH_DRIFT_REPAIRED=false
CURRENT_SELECTED_INSTRUMENT=SUI-USD_UM_XPERP-310404
CURRENT_VENUE=OKX_EEA
INSTRUMENT_BIND_PROVEN=true
KRAKEN_CURRENT_CANONICAL_ROLE=NONE
KRAKEN_EVIDENCE_USED_FOR_CURRENT_OKX_PRETRADE=false
NEXT_DISTINCT_SURFACE=VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT
NEXT_DISTINCT_SURFACE_AUTHORIZED=false
```

Not `VENUE_PRETRADE_LIMIT_GATES_ALREADY_COMPLETE`: bound lot/min/tick/instrument
gates exist; venue-native max-size and later metadata remain unbound.

Not `DISTINCT_COMPATIBLE_VENUE_PRETRADE_RESPONSIBILITIES` as completeness:
the owner model is distinct and compatible, but the gate matrix is incomplete.

Not `VENUE_PRETRADE_RUNTIME_ALIGNMENT_REQUIRED`: the bound canary order-plan
owner is already statically consumed by submit_transport. This persist does
not authorize or require runtime mutation.

Not `DUPLICATE_VENUE_PRETRADE_OWNER_CONFLICT`: Flatten is a separate emergency
authority, not a second entry venue-pretrade owner.

Not `VENUE_PRETRADE_BYPASS_CONFLICT`: inventoried live-capable families either
fail closed at Live Safety or are declared unreachable.

This slice persists the already-true incomplete owner model. Completeness of
the gates remains `false`. Metadata-binding alignment beginning at `MAX_SIZE`
remains a later named surface and is not authorized here.

## 4) Owner separation

```text
CANONICAL_VENUE_PRETRADE_ROLE=OKX_EEA_CANARY_VENUE_CONSTRAINT_PLAN_VALIDATOR_NOT_CORE_AUTHORITY
LIVE_ADMISSION_ROLE=DOWNSTREAM_HOST_FAMILY_ADMISSION_NOT_VENUE_PRETRADE
OKX_CANARY_VENUE_PLAN_ROLE=extract_instrument_constraints_v1 + build_canary_exposure_binding_v1 + quantize_limit_price_v1
OKX_CANARY_VENUE_PLAN_CONSUMER=run_canary_submit_transport_v1
PIPELINE_KRAKEN_ROLE=LEGACY_OR_ALTERNATE_HOST_FAMILY_LIVE_ADMISSION_FAIL_CLOSED_NO_CURRENT_OKX_VENUE_METADATA_AUTHORITY
NETWORKED_ONRAMP_ROLE=FAIL_CLOSED_NETWORKLESS
NO_ORDER_HOST_BARRIER_ROLE=validate_no_order_mode_v1
FLATTEN_ROLE=SEPARATE_EMERGENCY_AUTHORITY_NOT_ENTRY_VENUE_PRETRADE_OWNER
INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_ROLE=NON_AUTHORIZING_QUARANTINED
CAP11_LIVE_TESTNET_FIXTURE_PORTS_ROLE=DECLARED_UNREACHABLE_CONTRACTS_ONLY
RISK_ENVELOPE_ROLE=NOT_VENUE_PRETRADE_OWNER
```

Live admission is not venue-pretrade validity. SafetyGuard on the
pipeline/Kraken family is Live admission, not an OKX venue-metadata owner.
Kraken is not the current canonical venue and must not source current OKX
pretrade. Flatten reuses instrument-bind and tick ideas as emergency
authority only.

## 5) Current venue and instrument

```text
CURRENT_SELECTED_INSTRUMENT=SUI-USD_UM_XPERP-310404
CURRENT_VENUE=OKX_EEA
VENUE=OKX
ENTITY=OKX Europe Limited
REST_HOST=eea.okx.com
INST_TYPE=FUTURES
RULE_TYPE=xperp
INSTRUMENT_FAMILY=SUI-USD_UM_XPERP
SETTLEMENT_ACCOUNT_TRUTH=USDC
PUBLIC_SETTLE_NOTE=USD_PUBLIC_VS_USDC_ACCOUNT_TRUTH
INSTRUMENT_BIND_PROVEN=true
HISTORICAL_SUPERSEDED_CANONICAL_INSTRUMENT_ID=BTC-USD_UM_XPERP-310404
HISTORICAL_REJECTED_SWAP_INSTRUMENT_ID=BTC-USDT-SWAP
DEMO_XPERP_INSTRUMENT_ID=BTC-USD_UM_XPERP-310328
BTC_MUST_NOT_BE_CURRENT_INSTRUMENT_RESURRECTED=true
NO_BTC_TO_SUI_EVIDENCE_SUBSTITUTION=true
NO_USD_EQUALS_USDC_NORMALIZATION=true
NO_ABSENCE_EQUALS_ZERO_NORMALIZATION=true
KRAKEN_IS_NOT_CURRENT_CANONICAL_VENUE=true
KRAKEN_METADATA_MUST_NOT_SOURCE_CURRENT_OKX_PRETRADE=true
KRAKEN_CURRENT_CANONICAL_ROLE=NONE
KRAKEN_EVIDENCE_USED_FOR_CURRENT_OKX_PRETRADE=false
```

Scope is the current selected SUI identity on OKX EEA. Historical BTC values,
Demo 310328, and superseded BTC-310404 remain isolated.

## 6) Completeness / gap matrix

Bound existing canary-entry fail-closed checks. Names are labels, not
authority. Standing Live flags currently prevent productive reachability.

```text
INSTRUMENT_BIND=true
INST_TYPE=true
RULE_TYPE=true
MIN_SIZE=true
LOT_SIZE=true
TICK_SIZE=true
PRICE_ALIGNMENT=true
LIMIT_PRICE_REQUIRED=true
LIMIT_ONLY_ENTRY=true
NO_ENTRY_REDUCE_ONLY=true
```

Unbound / incomplete:

```text
MAX_SIZE=false
MAX_AVAILABLE=false
PRICE_BAND=false
LEVERAGE=false
POS_MODE=false
MARGIN_MODE=false
AVAILABLE_MARGIN=false
INSTRUMENT_STATE=false
MAX_LMT_SZ_CONSUMER_BOUND=false
MAX_MKT_SZ_CONSUMER_BOUND=false
MAX_AVAIL_SIZE_CONSUMER_BOUND=false
ACCOUNT_MODE_CURRENT_SUI_PROOF_COMPLETE=false
SUI_LEVERAGE_PROOF_COMPLETE=false
PRICE_BAND_PROOF_COMPLETE=false
INSTRUMENT_STATE_RUNTIME_PROOF_COMPLETE=false
```

Partial:

```text
POS_SIDE=partial
TD_MODE=partial
ORDER_FIELD_COMPATIBILITY=partial
REDUCE_ONLY_SHAPE=true_FOR_ENTRY_OMIT
EXCHANGE_ACCEPTANCE=NOT_INTERNALLY_PROVABLE
```

`maxLmtSz`, `maxMktSz`, and `maxAvailSize` have no Python consumer on current
`origin/main`. Default `tdMode=cross` serialization is not account-mode proof.
Historical `posMode=net` GET is not current SUI reobservation. Historical BTC
leverage `3` is not SUI leverage.

This persist does not implement those unbound gates.

## 7) Negative / non-equivalence contracts

```text
LIVE_ADMISSION_IS_NOT_VENUE_PRETRADE_VALIDITY=true
VENUE_METADATA_EXISTENCE_IS_NOT_GATE_BINDING=true
STATIC_FIELD_EXISTENCE_IS_NOT_RUNTIME_VALIDATION=true
INSTRUMENT_BIND_IS_NOT_SIZE_VALIDITY=true
MIN_SIZE_IS_NOT_MAX_SIZE=true
LOT_SIZE_IS_NOT_MAX_AVAILABLE=true
TICK_ALIGNMENT_IS_NOT_PRICE_BAND_VALIDITY=true
DEFAULT_TDMODE_CROSS_IS_NOT_ACCOUNT_MODE_PROOF=true
HISTORICAL_BTC_LEVERAGE_IS_NOT_SUI_LEVERAGE=true
HISTORICAL_ACCOUNT_GET_IS_NOT_CURRENT_SUI_REOBSERVATION=true
RISK_ENVELOPE_IS_NOT_VENUE_PRETRADE_OWNER=true
EXCHANGE_ACCEPTANCE_IS_NOT_INTERNALLY_PROVEN=true
KRAKEN_IS_NOT_CURRENT_CANONICAL_VENUE=true
KRAKEN_METADATA_MUST_NOT_SOURCE_CURRENT_OKX_PRETRADE=true
VENUE_PRETRADE_COMPLETE_IS_NOT_IMPLIED_BY_BOUND_LOT_MIN_TICK=true
METADATA_BINDING_ALIGNMENT_REQUIRED_IS_NOT_RUNTIME_MUTATION_AUTHORIZATION=true
METADATA_BINDING_ALIGNMENT_REQUIRED_IS_NOT_RUNTIME_MUTATION_NECESSITY=true
POSITION_ABSENCE_IS_NOT_ZERO=true
EMPTY_DATA_IS_NOT_ZERO=true
ABSENT_TARGET_ROW_IS_NOT_ZERO=true
FLATTEN_IS_NOT_ENTRY_VENUE_PRETRADE_OWNER=true
```

## 8) Host-family classification

```text
OKX_EEA_CANARY=CURRENT_VENUE_PRETRADE_SURFACE
OKX_EEA_CANARY_PATH=runner → submit_transport → evaluate_canary_submit_gates_v1 → GET instruments+ticker → build_minimum_valid_canary_order_plan_v1 → post_entry_order
OKX_EEA_CANARY_PATH_EDGE_CLASS=PROVEN_STATIC_BINDING
PIPELINE_KRAKEN=LEGACY_OR_ALTERNATE_HOST_FAMILY
PIPELINE_KRAKEN_LIVE_ADMISSION=FAIL_CLOSED
PIPELINE_KRAKEN_CURRENT_OKX_VENUE_METADATA_AUTHORITY=false
PIPELINE_KRAKEN_PATH=ExecutionPipeline.submit_order → SafetyGuard.ensure_may_place_order → execute_with_safety
PIPELINE_KRAKEN_PATH_EDGE_CLASS=PROVEN_STATIC_BINDING
NETWORKED_ONRAMP=FAIL_CLOSED_NETWORKLESS
NETWORKED_ONRAMP_PATH=onramp_cli → guard_transport_gate_v1 → evaluate_canary_live_gate_v1
NETWORKED_ONRAMP_PATH_EDGE_CLASS=PROVEN_STATIC_BINDING
CAP11_FIXTURES=DECLARED_UNREACHABLE
FLATTEN=SEPARATE_EMERGENCY_AUTHORITY
FLATTEN_IS_ENTRY_VENUE_PRETRADE_OWNER=false
INDEPENDENT_PRETRADE_KERNEL=NON_AUTHORIZING_QUARANTINED
INFERRED_EDGES_ARE_NOT_PROVEN=true
```

## 9) Live-safety input / venue-pretrade output boundary

```text
LIVE_SAFETY_INPUT_BOUNDARY=AFTER_HOST_ADMISSION_AUTH_ARM_ELIG_ENV_CONFIRM_CYBER_CREDENTIAL_CLASS_INSTRUMENT_BIND_OPEN_STATE
VENUE_PRETRADE_OUTPUT_BOUNDARY=VENUE_NATIVE_SIZE_PRICE_LEVERAGE_POSMODE_MARGIN_MAXAVAIL_LOT_TICK_INSTRUMENT_STATE_ORDER_SHAPE_BEFORE_POST_NOT_EXCHANGE_ACCEPTANCE
LIVE_SAFETY_GATES_COMPLETE=true
LIVE_SAFETY_DOES_NOT_IMPLY_QUANTITY_VALID=true
LIVE_SAFETY_DOES_NOT_IMPLY_PRICE_VALID=true
LIVE_SAFETY_DOES_NOT_IMPLY_LEVERAGE_VALID=true
LIVE_SAFETY_DOES_NOT_IMPLY_POSMODE_VALID=true
LIVE_SAFETY_DOES_NOT_IMPLY_MARGIN_SUFFICIENT=true
LIVE_SAFETY_DOES_NOT_IMPLY_MAXAVAIL_SUFFICIENT=true
LIVE_SAFETY_DOES_NOT_IMPLY_LOT_TICK_COMPLIANT=true
LIVE_SAFETY_DOES_NOT_IMPLY_EXCHANGE_ACCEPTANCE=true
```

## 10) Guards (not SSOT)

Exact proof file:

`tests/ops/test_peak_trade_post_restoration_venue_pretrade_limit_gates_adjudication_v1.py`

Guards must keep:

- Master §5.3 names this spec and `VENUE_PRETRADE_ADJUDICATION_RESULT=VENUE_METADATA_BINDING_ALIGNMENT_REQUIRED`
- venue-pretrade complete false; earliest incomplete edge `MAX_SIZE`; second owner false; bypass false; runtime alignment false
- current selected instrument remains `SUI-USD_UM_XPERP-310404`; current venue remains OKX EEA
- Kraken is not current canonical venue and does not source current OKX pretrade
- BTC must not be resurrected as current instrument
- instrument / minSz / lotSz / tickSz / price alignment remain described as bound
- MAX_SIZE, MAX_AVAILABLE, PRICE_BAND, LEVERAGE, account mode, instrument state remain unresolved
- Exchange acceptance remains not internally provable
- minSz is not maxSz; lotSz is not maxAvail; tick alignment is not price-band validity
- historical BTC leverage is not SUI leverage; default tdMode is not observed account truth
- Live Safety is not venue validity
- Replay Safety remains the sole Core Safety owner; 29P → Safety → 29Q remains
- #6143, #6144, and #6145 remain closed
- metadata-binding alignment required does not authorize or necessitate runtime mutation
- preexisting CALL_GRAPH equality test is not repaired in this slice

## 11) Out of scope this slice

```text
PREEXISTING_CALL_GRAPH_DRIFT_IN_SCOPE=false
CALL_GRAPH_V1_HARMONIZATION=NOT_THIS_SLICE
REQUIRED_CALL_GRAPH_HARMONIZATION=NOT_THIS_SLICE
TEST_CONSTANTS_AND_CALL_GRAPH_BOUND_REPAIR=NOT_THIS_SLICE
VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT=NOT_THIS_SLICE
SEE_ALSO_VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_ADJUDICATION=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_ADJUDICATION_V1.md
SEE_ALSO_EXACT_VENUE_METADATA_GET_CURRENT_SUI_PRETRADE_MAX_SIZE=docs/ops/specs/PEAK_TRADE_EXACT_VENUE_METADATA_GET_CURRENT_SUI_PRETRADE_MAX_SIZE_V1.md
SEE_ALSO_POST_6148_MAX_SIZE_UNIT_ADJUDICATION=docs/ops/specs/PEAK_TRADE_POST_6148_MAX_SIZE_UNIT_ADJUDICATION_V1.md
SEE_ALSO_POST_6149_MAX_SIZE_NORMALIZATION_ADJUDICATION=docs/ops/specs/PEAK_TRADE_POST_6149_MAX_SIZE_NORMALIZATION_ADJUDICATION_V1.md
SEE_ALSO_ORDER_PLAN_TYPED_CONTRACT_COUNT_DOMAIN_CLOSURE=docs/ops/specs/PEAK_TRADE_ORDER_PLAN_TYPED_CONTRACT_COUNT_DOMAIN_CLOSURE_V1.md
SEE_ALSO_MAX_SIZE_FRESHNESS_OWNER_POLICY_DECISION=docs/ops/specs/PEAK_TRADE_MAX_SIZE_FRESHNESS_OWNER_POLICY_DECISION_V1.md
SEE_ALSO_MAX_SIZE_FRESH_OBSERVATION_AND_CONSUMER_WIRING=docs/ops/specs/PEAK_TRADE_MAX_SIZE_FRESH_OBSERVATION_AND_CONSUMER_WIRING_V1.md
MAX_SIZE_IMPLEMENTATION=NOT_THIS_SLICE
MAX_AVAILABLE_IMPLEMENTATION=NOT_THIS_SLICE
PRICE_BAND_IMPLEMENTATION=NOT_THIS_SLICE
LEVERAGE_GATE_IMPLEMENTATION=NOT_THIS_SLICE
ACCOUNT_MODE_GATE_IMPLEMENTATION=NOT_THIS_SLICE
INSTRUMENT_STATE_GATE_IMPLEMENTATION=NOT_THIS_SLICE
AUTHENTICATED_GET=NOT_THIS_SLICE
PUBLIC_VENUE_GET=NOT_THIS_SLICE
NETWORK_GET=NOT_THIS_SLICE
POST=NOT_THIS_SLICE
CANARY_EXECUTE=NOT_THIS_SLICE
FLATTEN=NOT_THIS_SLICE
MULTI_FUTURE=NOT_THIS_SLICE
CAP_11_2_TO_11_12_ACTIVATION=NOT_THIS_SLICE
PR_6129=NOT_THIS_SLICE
RECOVERY_TRACK=NOT_THIS_SLICE
ORDER_PLAN_RUNTIME_MUTATION=NOT_THIS_SLICE
EXPOSURE_RUNTIME_MUTATION=NOT_THIS_SLICE
SUBMIT_TRANSPORT_RUNTIME_MUTATION=NOT_THIS_SLICE
SAFETYGUARD_RUNTIME_MUTATION=NOT_THIS_SLICE
KRAKEN_RUNTIME_MUTATION=NOT_THIS_SLICE
CORE_RUNTIME_MUTATION=false
```

Historical `VENUE_PRETRADE_LIMIT_GATES=NOT_THIS_SLICE` rows in prior
post-restoration specs remain historically true for those slices. Later
venue-pretrade adjudication is recorded here. Later venue-pretrade
metadata-binding alignment adjudication is recorded in
`SEE_ALSO_VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_ADJUDICATION`.
Historical `VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT=NOT_THIS_SLICE`
remains true for this limit-gates slice. This persist does not close
venue-pretrade completeness and does not implement venue limit gates.

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
| Live safety gates adjudication | `tests/ops/test_peak_trade_post_restoration_live_safety_gates_adjudication_v1.py` |
| Empty/absent is not zero | `tests/ops/test_section_11_13_5_z2cm_position_state_predicate_contract_v1.py` |
| Cap 11.9 fixture unreachable | `tests/ops/test_capability_11_9_live_canary_order_execution_v1.py` |
| Canary submit transport / order plan | `tests/ops/test_section_11_13_5_canary_submit_transport_v1.py` |

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
ORDER_PLAN_MUTATED=false
EXPOSURE_MUTATED=false
QUANTIZE_LIMIT_PRICE_MUTATED=false
SUBMIT_TRANSPORT_MUTATED=false
HTTP_CLIENT_MUTATED=false
SAFETYGUARD_MUTATED=false
KRAKEN_RUNTIME_MUTATED=false
FLATTEN_LOGIC_MUTATED=false
MAX_SIZE_IMPLEMENTED=false
MAX_AVAILABLE_IMPLEMENTED=false
PRICE_BAND_IMPLEMENTED=false
LEVERAGE_GATE_IMPLEMENTED=false
ACCOUNT_MODE_GATE_IMPLEMENTED=false
INSTRUMENT_STATE_GATE_IMPLEMENTED=false
VENUE_PRETRADE_IMPLEMENTED=false
VENUE_PRETRADE_LIMIT_GATES_COMPLETE=false
CHANGED_RUNTIME_FILES_EXPECTED=NONE
RUNTIME_DECOUPLING_REQUIRED=false
NEW_VENUE_PRETRADE_COMPONENT_REQUIRED=false
RECOVERY_TRACK_TOUCHED=false
PR_6129_TOUCHED=false
LIVE_READINESS_MUTATION=false
ORDER_SUBMIT_PERFORMED=false
FLATTEN_PERFORMED=false
TRADING_PERFORMED=false
LIVE_AUTHORITY_CHANGED=false
NETWORK_GET_PERFORMED=false
NETWORK_POST_PERFORMED=false
FORENSIC_REFERENCE_AUTHORITY=NONE
MAP_OF_TRUTH_STATUS=NAVIGATION_ONLY
SECOND_CORE_OWNER_CREATED=false
SECOND_VENUE_PRETRADE_OWNER_CREATED=false
PREEXISTING_CALL_GRAPH_DRIFT_REPAIRED=false
```
