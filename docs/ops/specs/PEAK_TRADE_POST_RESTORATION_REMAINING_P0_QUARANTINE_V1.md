# Peak_Trade — Post-Restoration Remaining P0 Quarantine v1

status: ACTIVE
last_updated: 2026-08-29
owner: Peak_Trade
purpose: Quarantine the two remaining post-PR-6141 P0 residual surfaces against productive reactivation. Not a second SSOT. Not restoration reopen. Not runtime core mutation. Not live or execution authority.
docs_token: DOCS_TOKEN_PEAK_TRADE_POST_RESTORATION_REMAINING_P0_QUARANTINE_V1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
CANONICAL_AUTHORITY=docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md
PARENT_CONTRACT=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_BASELINE_PRESERVATION_AND_COMPATIBILITY_CONTRACT_V1.md
PRIOR_QUARANTINE=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_PARALLEL_OWNER_AND_SKIP_SAFETY_PATH_QUARANTINE_V1.md
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
CHANGED_RUNTIME_FILES=NONE
RUNTIME_DECOUPLING_REQUIRED=false
```

This document is subordinate to the Master Runbook and to the post-restoration
preservation contract. It does not replace Master §5.3, Appendix A, C4, or
existing owner contracts. It quarantines the two remaining P0 surfaces left
explicitly unmutated by PR 6141 so they cannot silently re-enter the
productive host / owner graph as a second Risk owner or a second Safety owner.

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
STEP_29P_BEFORE_SAFETY=true
SAFETY_BEFORE_STEP_29Q=true
NO_29Q_BEFORE_SAFETY=true
ENTER_HARD_BLOCK_SKIPS_ENTER_29Q=true
ENTER_HARD_BLOCK_PRODUCES_NO_ENTER_COI=true
ENTER_WITHOUT_CANONICAL_ORDER_INTENT_CANNOT_BUY_OR_SELL=true
SAFETY_PASS_IS_NOT_EXECUTION_PERMISSION=true
```

Canonical productive order remains STEP-29P → Replay Safety → STEP-29Q
PLAN_ONLY. Tests are guards, not a second semantic SSOT.

## 3) Adjudicated remaining P0 surfaces

### 3.1 LEGACY_STRATEGY_POSITION_SIZERS

```text
COMPONENT=LEGACY_STRATEGY_POSITION_SIZERS
PROVENANCE=
  src/risk/position_sizer.py
  src/core/position_sizing.py
  src/core/risk.py
  src/portfolio/equal_weight.py
  src/portfolio/vol_target.py
  src/portfolio/fixed_weights.py
  src/portfolio/manager.py
CURRENT_ROLE=RESEARCH_BACKTEST_NON_PRODUCTIVE
HISTORICAL_ROLE=classic backtest / research / portfolio-strategy sizing helpers
AUTHORITY_SOURCE=NONE_FOR_RESTORED_PRODUCTIVE_OWNER_GRAPH
OVERALL_COMPATIBILITY=COMPATIBLE_WITH_CONSTRAINTS
KEEP_AS_IS=true_as_research_backtest_non_productive
ADAPT_DOWNSTREAM=false
DECOUPLE=true_from_productive_risk_owner_graph
DEGRADE=false
REMOVE=false
REWIRE=false
CORE_MUTATION_REQUIRED=false
NEW_OWNER_REQUIRED=false
NEW_POLICY_REQUIRED=false
LEGACY_STRATEGY_POSITION_SIZERS_PRODUCTIVE_HOST_REACHABLE=false
LEGACY_STRATEGY_POSITION_SIZERS_CANONICAL_RISK_OWNER=false
LEGACY_STRATEGY_POSITION_SIZERS_ROLE=RESEARCH_BACKTEST_NON_PRODUCTIVE
LEGACY_STRATEGY_POSITION_SIZERS_ALLOWED_ROLE=RESEARCH_BACKTEST_ONLY_OR_NON_PRODUCTIVE
```

These modules may remain for classic backtest, research, sweeps, and
portfolio-strategy experiments. They must not:

- overwrite STEP-29P quantity / sizing in a productive host
- recompute quantity after 29P on a productive path
- count as an alternative Risk owner
- be silently reactivated through host / execution imports into the
  restored owner graph

Historical inventory files that still label
`src.risk.position_sizer` or `src.core.position_sizing` as
`REACHABLE_PRODUCTIVE` or that keep
`CANONICAL_RISK_SIZING_OWNER=UNRESOLVED` remain historical technical
capability inventories. They are not productive owner-graph
authorization.

```text
REACHABLE_PRODUCTIVE_IN_THIS_INVENTORY=HISTORICAL_TECHNICAL_CAPABILITY_INVENTORY_NOT_OWNER_GRAPH_AUTHORIZATION
CURRENT_BINDING_REQUIREMENT_STATUS=REJECTED_BY_RESTORED_BASELINE
```

Classic Backtest, offline-eval sizing, and Execution
`execute_from_signals` remain out-of-scope non-canonical paths. This
slice does not consolidate repo-wide sizing and does not mutate
execution pipeline.

### 3.2 INDEPENDENT_PRE_TRADE_SAFETY_KERNEL

```text
COMPONENT=INDEPENDENT_PRE_TRADE_SAFETY_KERNEL
PROVENANCE=src/meta/learning_loop/independent_pre_trade_safety_kernel_v1.py
CURRENT_ROLE=NON_AUTHORIZING_NON_REPLAY_SAFETY
HISTORICAL_ROLE=RUNBOOK_STEP_22 learning-loop offline pre-trade safety contract
AUTHORITY_SOURCE=NONE_FOR_RESTORED_PRODUCTIVE_OWNER_GRAPH
AUTHORITY_LEVEL=NON_AUTHORITIZING
OVERALL_COMPATIBILITY=COMPATIBLE_WITH_CONSTRAINTS
KEEP_AS_IS=true_as_non_authorizing_learning_loop_contract
ADAPT_DOWNSTREAM=false
DECOUPLE=true_from_productive_replay_safety_owner_graph
DEGRADE=false
REMOVE=false
REWIRE=false
CORE_MUTATION_REQUIRED=false
NEW_OWNER_REQUIRED=false
NEW_POLICY_REQUIRED=false
INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_PRODUCTIVE_REPLAY_REACHABLE=false
INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_REPLAY_SAFETY_OWNER=false
INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_ROLE=NON_AUTHORIZING_NON_REPLAY_SAFETY
```

The kernel may remain for learning-loop / test / research context. It
must not:

- replace Replay Safety
- redefine Safety epistemically in the productive owner graph
- appear as a second Safety owner in the decision graph
- reinterpret Safety PASS / APPROVE as execution permission
- change the 29P → Safety → 29Q order

Approve produces no execution permission. A later live-boundary use
would require a separate future Owner / policy slice. This GO does not
authorize that.

Diagnostic owner-maps that cluster this module under a `SAFETY_KERNEL`
path prefix remain non-canonical as Replay-Safety-owner identity.
Historical progress-registry rows that name this module
`CANONICAL_OWNER` for RUNBOOK_STEP_22 remain historical learning-loop
contract ownership, not Replay Safety ownership.

## 4) Productive-host non-reachability

The following productive host / owner surfaces must not import or call
the quarantined modules as Quantity owner or Replay-Safety owner:

- `trading.master_v2.integrated_offline_trading_logic_replay_v1`
- Hardening-v2 `hardening_cycle_bridge_v2`
- Cap 7.2 `decision_economics_cycle_bridge_v1`
- Cap 7.2 `host_binding_v1`
- Intended Action Mapper
- STEP-29P `src.governance.capital_risk_sizing_v1`
- Replay Safety `safety_kernel_offline_replay_binding_adapter_v0`
- STEP-29Q `src.governance.canonical_order_intent_v1`

Forbidden as productive owner-graph imports / calls:

- `src.risk.position_sizer` as Quantity owner
- `src.core.position_sizing` as Quantity owner
- `src.core.risk` as Quantity owner
- `src.portfolio.equal_weight` / `vol_target` / `fixed_weights` / `manager`
  as Quantity owner
- `calc_position_size(` / `build_position_sizer_from_config(` as
  productive Quantity owner
- `src.meta.learning_loop.independent_pre_trade_safety_kernel_v1` as
  Replay-Safety owner
- `produce_independent_pre_trade_safety_kernel_v1(` /
  `build_independent_pre_trade_safety_kernel_v1(` as Replay-Safety owner

Allowed:

- classic backtest / research / sweeps / portfolio-strategy experiments
- learning-loop tests and `scripts/run_independent_pre_trade_safety_kernel_v1.py`
- historical inventory JSON that retains `REACHABLE_PRODUCTIVE` as a
  technical snapshot
- STEP-29P bypass-scan path existence check that names
  `src/risk/position_sizer.py` without importing it

## 5) Out of scope this slice

```text
ACCOUNTING_PORTFOLIO_ALIGNMENT=NOT_THIS_SLICE
PRODUCTIVE_FUTURES_ACCOUNTING=NOT_THIS_SLICE
HARDENING_IDEMPOTENT_PORTFOLIO=NOT_THIS_SLICE
SEE_ALSO_ACCOUNTING_PORTFOLIO_ALIGNMENT=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_ACCOUNTING_PORTFOLIO_ALIGNMENT_ADJUDICATION_V1.md
SIMULATED_EXECUTION_COMPLETION=NOT_THIS_SLICE
EXECUTION_PIPELINE=NOT_THIS_SLICE
SEE_ALSO_SIMULATED_EXECUTION_PIPELINE_ADJUDICATION=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_SIMULATED_EXECUTION_PIPELINE_ADJUDICATION_V1.md
LIVE_SAFETY_GATES=NOT_THIS_SLICE
VENUE_PRETRADE_LIMIT_GATES=NOT_THIS_SLICE
CANARY=NOT_THIS_SLICE
FLATTEN=NOT_THIS_SLICE
MULTI_FUTURE=NOT_THIS_SLICE
CAP_11_2_TO_11_12_ACTIVATION=NOT_THIS_SLICE
PR_6129=NOT_THIS_SLICE
RECOVERY_TRACK=NOT_THIS_SLICE
```

Historical `SIMULATED_EXECUTION_COMPLETION=NOT_THIS_SLICE` and
`EXECUTION_PIPELINE=NOT_THIS_SLICE` remain true for this quarantine slice.
Later simulated-execution pipeline adjudication is recorded in the SEE_ALSO
spec. This quarantine does not reopen, add a second execution owner, or
require a runtime rewire.

## 6) Existing guards reused (not duplicated)

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
| Preservation / compatibility contract | `tests/ops/test_peak_trade_post_restoration_baseline_preservation_and_compatibility_contract_v1.py` |
| Independent kernel non-authorizing APPROVE | `tests/meta/test_independent_pre_trade_safety_kernel_v1.py` |
| Legacy sizer inventory freeze (historical) | `tests/governance/test_risk_sizing_owner_inventory_ssot_v1.py` |

Exact additional proof file for this quarantine:

`tests/ops/test_peak_trade_post_restoration_remaining_p0_quarantine_v1.py`

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
RUNTIME_DECOUPLING_REQUIRED=false
RECOVERY_TRACK_TOUCHED=false
PR_6129_TOUCHED=false
LIVE_READINESS_MUTATION=false
ORDER_SUBMIT_PERFORMED=false
FLATTEN_PERFORMED=false
TRADING_PERFORMED=false
LIVE_AUTHORITY_CHANGED=false
FORENSIC_REFERENCE_AUTHORITY=NONE
MAP_OF_TRUTH_STATUS=NAVIGATION_ONLY
```
