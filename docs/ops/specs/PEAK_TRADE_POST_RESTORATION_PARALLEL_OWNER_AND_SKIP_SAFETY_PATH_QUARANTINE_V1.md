# Peak_Trade — Post-Restoration Parallel-Owner and Skip-Safety Path Quarantine v1

status: ACTIVE
last_updated: 2026-08-29
owner: Peak_Trade
purpose: Quarantine post-restoration P0 residual parallel-owner and skip-safety paths against productive reactivation. Not a second SSOT. Not restoration reopen. Not runtime core mutation. Not live or execution authority.
docs_token: DOCS_TOKEN_PEAK_TRADE_POST_RESTORATION_PARALLEL_OWNER_AND_SKIP_SAFETY_PATH_QUARANTINE_V1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
CANONICAL_AUTHORITY=docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md
PARENT_CONTRACT=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_BASELINE_PRESERVATION_AND_COMPATIBILITY_CONTRACT_V1.md
PARALLEL_SSOT_CREATED=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
CORE_RUNTIME_MUTATION=false
NEW_SEMANTIC_POLICY=false
NEW_RUNTIME_OWNER=false
NEW_STAGE=false
RESTORATION_REOPEN_REQUIRED=false
MASTER_V2_DOUBLE_PLAY_RESTORATION_COMPLETE=true
COMPATIBILITY_CONTRACT_DOES_NOT_GRANT_EXECUTION_AUTHORITY=true
LIVE_AUTHORIZED=false
TESTNET_AUTHORIZED=false
CANARY_AUTHORIZED=false
ORDERS_AUTHORIZED=false
NO_TRADING=true
NO_LIVE_AUTHORITY=true
NO_EXECUTION_AUTHORITY=true
```

This document is subordinate to the Master Runbook and to the post-restoration
preservation contract. It does not replace Master §5.3, Appendix A, C4, or
existing owner contracts. It quarantines four already-present residual
surfaces so they cannot silently re-enter the productive host / execution
graph as second owners or as a skip-safety path.

## 1) Restoration boundary

```text
RESTORATION_COMPLETION_CHECKPOINT_SHA=21452016ff998c1af63f24c36060f2a54020c0df
HISTORICAL_MASTER_V2_DOUBLE_PLAY_BASELINE=IMMUTABLE_NORMATIVE_BASELINE
CURRENT_SYSTEM_MUST_CONFORM_TO_HISTORICAL_CORE=true
NO_CURRENT_FIRST_ARCHITECTURE=true
HISTORICAL_CORE_SEMANTICS_MUST_NOT_BE_REWRITTEN=true
```

## 2) Protected productive owner graph

```text
COMPUTE_OWNER=trading.master_v2.integrated_offline_trading_logic_replay_v1
RISK_OWNER=STEP-29P / src.governance.capital_risk_sizing_v1
SAFETY_OWNER=trading.master_v2.safety_kernel_offline_replay_binding_adapter_v0
INTENT_OWNER=STEP-29Q / src.governance.canonical_order_intent_v1
SIDESTATE_WRITER=trading.master_v2.double_play_state.transition_state
ENTRY_EXIT_OWNER=evaluate_double_play_entry_exit_policy_v0
SECOND_COMPUTE_OWNER_EXISTS=false
SECOND_RISK_OWNER_EXISTS=false
SECOND_SAFETY_OWNER_EXISTS=false
SECOND_INTENT_OWNER_EXISTS=false
PRODUCTIVE_ORDERING=29P → Replay Safety → 29Q PLAN_ONLY
NO_29Q_BEFORE_SAFETY=true
ENTER_HARD_BLOCK_SKIPS_ENTER_29Q=true
ENTER_HARD_BLOCK_PRODUCES_NO_ENTER_COI=true
CAP65_EXIT_PRODUCERS_REMAIN_CONSUMED=true
CAP_6_5_EXIT_POLICY_PRODUCERS=INPUT_PRODUCERS_ONLY
BRIDGE_SAFETY_ROLE=INPUT_PRODUCER_ONLY
```

Cap 6.5 producers may supply inputs to the historical EntryExit / Replay path.
They are `NOT_SAFETY_OWNER`, `NOT_ENTRY_EXIT_OWNER`, `NOT_INTENT_OWNER`, and
`NOT_EXECUTION_AUTHORITY`.

## 3) Adjudicated residual surfaces

### 3.1 Hardening Safety residual — `evaluate_bridge_safety_v2`

```text
COMPONENT=evaluate_bridge_safety_v2
PROVENANCE=src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2/safety_binding_v2.py
CURRENT_ROLE=NON_PRODUCTIVE_DIAGNOSTIC_AND_CAP65_INPUT_PRODUCER
HISTORICAL_ROLE=Hardening-v2 SafetyMode / TradingGate input producer
AUTHORITY_SOURCE=Cap 6.5 producer bundle; BRIDGE_SAFETY_ROLE=INPUT_PRODUCER_ONLY
OVERALL_COMPATIBILITY=COMPATIBLE_WITH_CONSTRAINTS
KEEP_AS_IS=true_as_non_productive_input_producer
ADAPT_DOWNSTREAM=false
DECOUPLE=true_from_productive_safety_owner_graph
DEGRADE=false
REMOVE=false
REWIRE=false
CORE_MUTATION_REQUIRED=false
NEW_OWNER_REQUIRED=false
NEW_POLICY_REQUIRED=false
EVALUATE_BRIDGE_SAFETY_V2_PRODUCTIVE_OWNER=false
EVALUATE_BRIDGE_SAFETY_V2_PRODUCTIVE_HOST_REACHABLE=false
SAFETY_PASS_IS_NOT_EXECUTION_PERMISSION=true
```

The function may remain for tests, historical evidence, Cap 6.5 input
production, and diagnostics. It must not be bound as a productive Safety
owner. A PASS / BLOCKED result from this evaluator is not execution
permission.

### 3.2 Cap 6.5 stale Current-first binding language

```text
COMPONENT=CAP_6_5_STALE_BIND_EVALUATE_BRIDGE_SAFETY_V2_INTO_PRODUCTIVE_HOST
PROVENANCE=authority_matrix_v1.py and Cap 6.5 historical closeout evidence
OVERALL_COMPATIBILITY=INCOMPATIBLE_AS_CURRENT_FIRST_BINDING_REQUIREMENT
KEEP_AS_IS=false_as_current_requirement
HISTORICAL_EVIDENCE_MAY_RETAIN_STALE_STRING=true
CURRENT_BINDING_REQUIREMENT_STATUS=REJECTED_BY_RESTORED_BASELINE
CAP65_STALE_BIND_LANGUAGE_RESOLVED=true
```

The restored baseline forbids treating

`bind evaluate_bridge_safety_v2 into productive host`

as a current or future productive Safety-owner binding requirement.
Historical Cap 6.5 closeout JSON and the Cap 6.5 authority-matrix snapshot
may retain the string as closeout language. Current specs must mark that
requirement `REJECTED_BY_RESTORED_BASELINE`. Productive hosts must not
implement it as a Safety-owner bind.

### 3.3 Intent Pipeline Bridge v0

```text
COMPONENT=CANONICAL_CORE_RUNTIME_INTENT_PIPELINE_BRIDGE_V0
PROVENANCE=src/trading/master_v2/canonical_core_runtime_integration_intent_pipeline_bridge_v0.py
CURRENT_ROLE=NON_PRODUCTIVE_PARALLEL_CONTRACT_SLICE
HISTORICAL_ROLE=Slice B 29P → 29Q without Replay Safety
AUTHORITY_SOURCE=NONE_FOR_PRODUCTIVE_OWNER_GRAPH
OVERALL_COMPATIBILITY=INCOMPATIBLE_AS_PRODUCTIVE_OWNER_GRAPH
KEEP_AS_IS=true_as_quarantined_contract_helper
DECOUPLE=true_from_productive_host
REMOVE=false
REWIRE=false
CORE_MUTATION_REQUIRED=false
PRODUCTIVE_REPLAY_PATH_ALLOWED=false
INTENT_PIPELINE_BRIDGE_PRODUCTIVE_REACHABLE=false
XP03_ACTIVATED=false
```

Do not repair this slice by inserting an extra Safety call. Integrated Replay
remains the only productive owner graph. Mapping helpers in this module may
be reused by tests and historical restore composers. The `run_*` owner-graph
entrypoints must not be invoked by productive hosts.

Frozen inventory files that still label this surface
`REACHABLE_PRODUCTIVE` remain historical technical-capability inventories.
They are not productive owner-graph authorization.

### 3.4 CRS_INTENT_RESTORE_V1

```text
COMPONENT=CRS_INTENT_RESTORE_V1
PROVENANCE=src/trading/master_v2/capital_risk_sizing_intent_restore_v1.py
CURRENT_ROLE=NON_PRODUCTIVE_HISTORICAL_RESTORE_PROOF_COMPOSER
HISTORICAL_ROLE=A06 29P → 29Q without Safety
OVERALL_COMPATIBILITY=INCOMPATIBLE_AS_PRODUCTIVE_OWNER_GRAPH
KEEP_AS_IS=true_as_quarantined_composer
DECOUPLE=true_from_productive_host
REMOVE=false
REWIRE=false
CORE_MUTATION_REQUIRED=false
CRS_INTENT_RESTORE_V1_PRODUCTIVE_PATH=false
CRS_INTENT_RESTORE_PRODUCTIVE_REACHABLE=false
```

The composer may exist for tests and restoration evidence. It must not become
a productive Replay orchestrator, must not re-execute 29P or 29Q as a
productive owner, must not skip Safety in a productive path, and must not
form a second Risk or Intent owner.

### 3.5 CRS_SAFETY_INTENT_RESTORE_V1

```text
COMPONENT=CRS_SAFETY_INTENT_RESTORE_V1
PROVENANCE=src/trading/master_v2/capital_risk_sizing_safety_intent_restore_v1.py
CURRENT_ROLE=PROOF_OR_RESTORE_COMPOSER_ONLY
HISTORICAL_ROLE=sibling 29P → Safety → 29Q composition
OVERALL_COMPATIBILITY=COMPATIBLE_WITH_CONSTRAINTS
KEEP_AS_IS=true_as_proof_composer
DECOUPLE=true_from_productive_host
REMOVE=false
REWIRE=false
CORE_MUTATION_REQUIRED=false
CRS_SAFETY_INTENT_RESTORE_V1_ROLE=PROOF_OR_RESTORE_COMPOSER_ONLY
PRODUCTIVE_OWNER=false
```

This composer maps the correct order 29P → Safety → 29Q, but it is not the
productive owner graph. Integrated Replay remains the sole productive
compute owner. Any extra `evaluate_quantity_chain_v1` call is composer /
test / proof context only.

## 4) Productive-host non-reachability

The following productive host / owner surfaces must not call the quarantined
owner-graph entrypoints:

- `trading.master_v2.integrated_offline_trading_logic_replay_v1`
- Hardening-v2 `hardening_cycle_bridge_v2`
- Cap 7.2 `decision_economics_cycle_bridge_v1`
- Intended Action Mapper

Forbidden as productive owner-graph calls:

- `evaluate_bridge_safety_v2(` as Safety owner
- `run_canonical_core_runtime_integration_intent_pipeline_bridge_v0(`
- `run_canonical_core_runtime_integration_intent_pipeline_from_harness_v0(`
- `compose_capital_risk_sizing_intent_from_core_evidence_v1(`
- `compose_capital_risk_sizing_safety_intent_from_core_evidence_v1(`

Allowed:

- Cap 6.5 `producers_v1` calling `evaluate_bridge_safety_v2` as
  `INPUT_PRODUCER_ONLY`
- tests and historical restore / proof composers
- mapping helpers that do not form a second owner graph

## 5) Out of scope this slice

```text
LEGACY_STRATEGY_POSITION_SIZERS=NOT_MUTATED_THIS_SLICE
INDEPENDENT_PRE_TRADE_SAFETY_KERNEL=NOT_MUTATED_THIS_SLICE
SEE_ALSO_REMAINING_P0=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_REMAINING_P0_QUARANTINE_V1.md
ACCOUNTING_PORTFOLIO_ALIGNMENT=NOT_THIS_SLICE
SEE_ALSO_ACCOUNTING_PORTFOLIO_ALIGNMENT=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_ACCOUNTING_PORTFOLIO_ALIGNMENT_ADJUDICATION_V1.md
SIMULATED_EXECUTION_PIPELINE_ADJUDICATION=NOT_THIS_SLICE
SEE_ALSO_SIMULATED_EXECUTION_PIPELINE_ADJUDICATION=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_SIMULATED_EXECUTION_PIPELINE_ADJUDICATION_V1.md
LIVE_EXECUTION_BOUNDARY=NOT_THIS_SLICE
VENUE_PRETRADE_LIMIT_GATES=NOT_THIS_SLICE
MULTI_FUTURE=NOT_THIS_SLICE
CANARY=NOT_THIS_SLICE
FLATTEN=NOT_THIS_SLICE
PR_6129=NOT_THIS_SLICE
RECOVERY_TRACK=NOT_THIS_SLICE
```

Historical `SIMULATED_EXECUTION_PIPELINE_ADJUDICATION=NOT_THIS_SLICE` remains
true for this quarantine slice. Later simulated-execution pipeline
adjudication is recorded in the SEE_ALSO spec. Safety-before-Intent remains
protected. This quarantine does not reopen, add a second execution owner, or
require a runtime rewire.

## 6) Existing guards reused (not duplicated)

| Invariant | Current guard |
|---|---|
| 29P → Safety → 29Q productive Replay order | `tests/trading/master_v2/test_master_v2_integrated_replay_safety_before_intent_restore_contract_v1.py` |
| Appendix-A core parity | `tests/trading/master_v2/test_master_v2_integrated_replay_appendix_a_core_logic_parity_post_6135_contract_v1.py` |
| Hardening-v2 does not call `evaluate_bridge_safety_v2(` | `tests/ops/test_hardening_v2_historical_safety_seam_contracts_v1.py` |
| A06 is composition-only and skips Safety | `tests/trading/master_v2/test_master_v2_a06_capital_risk_sizing_intent_restore_contract_v1.py` |
| Sibling composer is not Replay owner | `tests/trading/master_v2/test_master_v2_capital_risk_sizing_safety_intent_restore_contract_v1.py` |
| Preservation / compatibility contract | `tests/ops/test_peak_trade_post_restoration_baseline_preservation_and_compatibility_contract_v1.py` |

Exact additional proof file for this quarantine:

`tests/ops/test_peak_trade_post_restoration_parallel_owner_and_skip_safety_path_quarantine_v1.py`

## 7) Negative contract

```text
RUNTIME_CORE_MUTATION=false
TRADING_LOGIC_MUTATION=false
COMPUTE_OWNER_MUTATION=false
RISK_OWNER_MUTATION=false
SAFETY_OWNER_MUTATION=false
INTENT_OWNER_MUTATION=false
SIDESTATE_WRITER_MUTATION=false
ENTRY_EXIT_OWNER_MUTATION=false
CHANGED_RUNTIME_FILES_EXPECTED=NONE
RECOVERY_TRACK_TOUCHED=false
PR_6129_TOUCHED=false
LIVE_READINESS_MUTATION=false
ORDER_SUBMIT_PERFORMED=false
FLATTEN_PERFORMED=false
TRADING_PERFORMED=false
LIVE_AUTHORITY_CHANGED=false
```
