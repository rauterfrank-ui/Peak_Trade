# Peak_Trade — Post-Restoration Accounting / Portfolio Alignment Adjudication v1

status: ACTIVE
last_updated: 2026-08-29
owner: Peak_Trade
purpose: Adjudicate the two simulated accounting/portfolio write paths after the closed P0-quarantine cluster. Not a second SSOT. Not restoration reopen. Not core runtime mutation. Not live or execution authority.
docs_token: DOCS_TOKEN_PEAK_TRADE_POST_RESTORATION_ACCOUNTING_PORTFOLIO_ALIGNMENT_ADJUDICATION_V1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
CANONICAL_AUTHORITY=docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md
PARENT_CONTRACT=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_BASELINE_PRESERVATION_AND_COMPATIBILITY_CONTRACT_V1.md
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
RUNTIME_ALIGNMENT_REQUIRED=false
```

This document is subordinate to the Master Runbook and to the post-restoration
preservation contract. It does not replace Master §5.3, Appendix A, C4, Cap 3.1,
Hardening-v2, or existing owner contracts. It adjudicates two already-present
downstream simulated write paths so they cannot be misread as a second Core
owner or as an unresolved dual writer of one canonical account state.

## 1) Restoration boundary

```text
RESTORATION_COMPLETION_CHECKPOINT_SHA=21452016ff998c1af63f24c36060f2a54020c0df
HISTORICAL_MASTER_V2_DOUBLE_PLAY_BASELINE=IMMUTABLE_NORMATIVE_BASELINE
CURRENT_SYSTEM_MUST_CONFORM_TO_HISTORICAL_CORE=true
NO_CURRENT_FIRST_ARCHITECTURE=true
HISTORICAL_CORE_SEMANTICS_MUST_NOT_BE_REWRITTEN=true
P0_QUARANTINE_REMAINS_CLOSED=true
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

Accounting / portfolio layers must not recompute Compute, Risk/Sizing, Safety,
Intent, SideState, or EntryExit; must not degrade EXIT/REDUCE to HOLD; and must
not invent BUY/SELL without CanonicalOrderIntent (mapper already fail-closes
that case to HOLD).

Canonical productive order remains:

```text
STEP-29P
→ Replay Safety
→ STEP-29Q PLAN_ONLY
→ downstream mapping
→ simulated execution/accounting
```

## 3) Target A — Productive Futures Accounting

```text
COMPONENT=PRODUCTIVE_FUTURES_ACCOUNTING
PROVENANCE=
  src/ops/productive_futures_accounting_runtime_binding_v1/**
  src/execution/paper/futures_accounting.py
PRODUCTIVE_FUTURES_ACCOUNTING_ROLE=CANONICAL_DOWNSTREAM_FUTURES_ACCOUNTING_WRITER_FOR_WALLCLOCK_V1_AND_CAP72
PRODUCTIVE_FUTURES_ACCOUNTING_WRITE_SURFACE=
  ProductiveFuturesAccountingSessionV1
  → optional atomic persist of productive_futures_accounting_state_v1
  → projection into SimulatedPortfolioEconomicsModelV1 shell
PRODUCTIVE_FUTURES_ACCOUNTING_INPUT_OWNER=Intended Action Mapper (BUY|SELL|HOLD + quantity + mark)
PRODUCTIVE_FUTURES_ACCOUNTING_STATE_PERSISTENCE=SESSION_PERSISTENT_SINGLE_WRITER_OPTIONAL_ATOMIC_DURABLE
PRODUCTIVE_FUTURES_ACCOUNTING_IDEMPOTENCE=FILL_ID_REPLAY_RETURNS_PRIOR_RESULT
PRODUCTIVE_FUTURES_ACCOUNTING_EXECUTION_AUTHORITY=NONE_SIMULATED_ONLY
CANONICAL_KERNEL_OWNER=src.execution.paper.futures_accounting
AUTHORITY_OWNER=ops.productive_futures_accounting_runtime_binding_v1
HOST=
  WALLCLOCK_V1 / Cap 7.2 decision_economics_cycle_bridge_v1
  → SimulatedExecutionPortV1 when activation_binding.enabled
  → apply_intended_action_via_canonical_accounting_v1 when activation disabled (Cap 7.1 path)
OVERALL_COMPATIBILITY=COMPATIBLE
KEEP_AS_IS=true_as_canonical_downstream_futures_writer_for_wallclock_v1_cap72
ADAPT_DOWNSTREAM=false
DECOUPLE=false
REMOVE=false
REWIRE=false
CORE_MUTATION_REQUIRED=false
NEW_OWNER_REQUIRED=false
NEW_POLICY_REQUIRED=false
```

Input is already downstream of CanonicalOrderIntent / Intended Action. The
kernel is futures-style: unsigned quantity plus explicit side, contract
multiplier, tick/min-qty quantization, reduce-only / over-reduce fail-closed,
and `POSITION_FLIP_ALLOWED=false`. Cash/equity are futures-margin economics
(`initial + realized + unrealized - fees - slippage`), not spot notional cash
movement. The portfolio shell on this host is a projection, not a second
independent economics writer.

## 4) Target B — Hardening Idempotent Portfolio / Paper-Shadow Economics

```text
COMPONENT=HARDENING_IDEMPOTENT_PORTFOLIO_AND_PAPER_SHADOW_ECONOMICS
PROVENANCE=
  src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2/idempotent_portfolio_v2.py
  src/ops/integrated_paper_shadow_observation_session_v1/portfolio_economics_model_v1.py
HARDENING_PORTFOLIO_ROLE=MODE_SPECIFIC_ANALYTICAL_PAPER_SHADOW_PORTFOLIO_WRITER
HARDENING_PORTFOLIO_WRITE_SURFACE=
  IdempotentPortfolioV2
  → SimulatedPortfolioEconomicsModelV1 (operative writer on hardening-v2 host)
HARDENING_PORTFOLIO_INPUT_OWNER=Intended Action Mapper (BUY|SELL|HOLD + quantity + mark)
HARDENING_PORTFOLIO_STATE_PERSISTENCE=SESSION_PERSISTENT_IN_MEMORY_HOST_STATE
HARDENING_PORTFOLIO_IDEMPOTENCE=INTENT_ID_AND_FILL_ID_FAIL_CLOSED_RAISE_ON_DUPLICATE
HARDENING_PORTFOLIO_EXECUTION_AUTHORITY=NONE_SIMULATED_ONLY
HOST=HARDENING_V2_HOST hardening_cycle_bridge_v2
OVERALL_COMPATIBILITY=COMPATIBLE_WITH_CONSTRAINTS
KEEP_AS_IS=true_as_mode_specific_analytical_writer
ADAPT_DOWNSTREAM=false
DECOUPLE=true_from_canonical_futures_account_state
REMOVE=false
REWIRE=false
CORE_MUTATION_REQUIRED=false
NEW_OWNER_REQUIRED=false
NEW_POLICY_REQUIRED=false
```

This path is not Evidence-only. It is a real simulated portfolio writer for
the hardening-v2 analytical host. It is not the Cap 7.2 / wallclock-v1
canonical futures account writer. Signed quantity, spot-like cash ± notional,
and fail-closed duplicate intent/fill ids are mode-specific paper-shadow
economics. Crossing zero in one reduce that exceeds open quantity is allowed
here and forbidden on Target A.

`ops.integrated_paper_shadow_economic_validity_pipeline_v1` remains a
readiness/evidence gate, not a portfolio writer.

## 5) Dual-writer topology

```text
WALLCLOCK_V1_HOST
  → Intended Action Mapper
  → SimulatedExecutionPortV1 | apply_intended_action_via_canonical_accounting_v1
  → PRODUCTIVE_FUTURES_ACCOUNTING
  → projection shell SimulatedPortfolioEconomicsModelV1

HARDENING_V2_HOST
  → Intended Action Mapper
  → IdempotentPortfolioV2.apply_intended_action
  → PAPER_SHADOW SimulatedPortfolioEconomicsModelV1 (operative)

DUAL_PORTFOLIO_WRITER_PATHS_EXIST=true_as_separate_host_modes
BOTH_PATHS_PRODUCTIVELY_REACHABLE=true_as_separate_hosts
BOTH_PATHS_CAN_PROCESS_EQUIVALENT_DECISION=true_mapper_buy_sell_hold
BOTH_PATHS_CAN_WRITE_EQUIVALENT_ACCOUNT_STATE=false
SAME_CANONICAL_ACCOUNT_STATE_DOUBLE_WRITTEN_IN_ONE_CYCLE=false
TWO_FILES_EXIST_IS_NOT_DUAL_WRITER_PROOF=true
```

Two files existing is not a dual-writer proof. A conflict would require two
productive host paths to own the same simulated account state differently in
one cycle. That is not the case: wallclock-v1 does not call
`IdempotentPortfolioV2`; hardening-v2 does not call Cap 3.1. Same model class
on both hosts is not identity of write authority.

## 6) Owner-composed economics comparison

No frozen Golden-JSON corpus. Comparison uses owner-composed deterministic
inputs against the live writer APIs. Dimensions that are not the same
fachliche Verantwortung are marked `DISTINCT_RESPONSIBILITY`, never artificial
`PASS`.

```text
ACCOUNT_STATE_PARITY=DISTINCT_RESPONSIBILITY
POSITION_PARITY=DISTINCT_RESPONSIBILITY
CASH_PARITY=DISTINCT_RESPONSIBILITY
EQUITY_PARITY=DISTINCT_RESPONSIBILITY
FEE_PARITY=DISTINCT_RESPONSIBILITY
REALIZED_PNL_PARITY=DISTINCT_RESPONSIBILITY
UNREALIZED_PNL_PARITY=DISTINCT_RESPONSIBILITY
IDEMPOTENCE_PARITY=DISTINCT_RESPONSIBILITY
EXIT_SEMANTICS_PARITY=COMPATIBLE_AS_OPPOSITE_SIDE_REDUCE_WHEN_QTY_DOES_NOT_EXCEED_OPEN
REVERSAL_SEMANTICS_PARITY=DISTINCT_RESPONSIBILITY
```

Comparable as consumption of mapper BUY/SELL/HOLD:

- A/B FLAT → ENTER LONG/SHORT: both open from flat on BUY/SELL.
- C/D/O HOLD / no-action: both mark-to-market, no fill.
- E/F EXIT when close quantity equals open: both reduce to flat.
- G partial REDUCE: both support a same-instrument opposite-side reduce that
  does not exceed open quantity.
- J/K/L fee / realized / unrealized: both compute values, but formulas and
  cash coupling differ.

Not the same account economics:

- H flat-before-opposite reversal in one fill: Cap 3.1 fail-closed
  (`OVER_REDUCE` / `POSITION_FLIP_BLOCKED`); paper-shadow may cross zero.
- I duplicate cycle: Cap 3.1 fill-id replay returns prior result; hardening
  raises `DUPLICATE_INTENT_ID` / `DUPLICATE_FILL_ID`.
- M cash/equity: futures residual vs spot-like notional cash movement.

## 7) Adjudication result

```text
ADJUDICATION_RESULT=DISTINCT_COMPATIBLE_RESPONSIBILITIES
ACCOUNTING_PORTFOLIO_OWNER_MODEL=DISTINCT_NON_OVERLAPPING_RESPONSIBILITIES
PORTFOLIO_WRITER_DUPLICATION_UNRESOLVED=false
ACCOUNTING_SEMANTIC_DIVERGENCE_UNRESOLVED=false
RUNTIME_ALIGNMENT_REQUIRED=false
CHANGED_RUNTIME_FILES=NONE
```

Not `SINGLE_CANONICAL_WRITER_ALREADY_EXISTS`: hardening-v2 is a real
mode-specific writer, not a pure evidence projection.

Not `COMPATIBLE_WITH_ADAPTER_ALIGNMENT`: unifying economics would require a
Core-near or writer-kernel rewrite, which this GO forbids.

Not `INCOMPATIBLE_DUAL_WRITER`: the two paths do not own the same canonical
account state on one productive cycle.

Not `UNKNOWN_INSUFFICIENT_EVIDENCE`: hosts, inputs, write surfaces, and
owner-composed deltas are proven.

Do not canonicalize a writer because it is newer. Historical Cap 3.1
`futures_accounting` remains the canonical futures kernel for wallclock-v1 /
Cap 7.2. Hardening-v2 remains the later mode-specific analytical host
classified by §5.3 / host-graph SSOT as
`MODE_SPECIFIC_ANALYTICAL_HOST`.

## 8) Compatibility dimensions (required schema)

```text
COMPONENT=PRODUCTIVE_FUTURES_ACCOUNTING
PROVENANCE=Cap 3.1 + src.execution.paper.futures_accounting
CURRENT_ROLE=CANONICAL_DOWNSTREAM_FUTURES_ACCOUNTING_WRITER_FOR_WALLCLOCK_V1_AND_CAP72
HISTORICAL_ROLE=Canonical futures PnL/margin kernel after simulated fill
AUTHORITY_SOURCE=CAPABILITY_3_1_PRODUCTIVE_FUTURES_ACCOUNTING_RUNTIME_BINDING_V1
HISTORICAL_SEMANTIC_COMPATIBILITY=COMPATIBLE
AUTHORITY_COMPATIBILITY=COMPATIBLE
OWNER_COMPATIBILITY=COMPATIBLE
CALL_ORDER_COMPATIBILITY=COMPATIBLE
SAFETY_COMPATIBILITY=COMPATIBLE
INTENT_COMPATIBILITY=COMPATIBLE
EXIT_PRECEDENCE_COMPATIBILITY=COMPATIBLE
STATE_WRITER_COMPATIBILITY=COMPATIBLE
RISK_SIZING_COMPATIBILITY=COMPATIBLE
FAIL_CLOSED_COMPATIBILITY=COMPATIBLE
SIMULATED_EXECUTION_BOUNDARY_COMPATIBILITY=COMPATIBLE
FORENSIC_AUTHORITY_COMPATIBILITY=COMPATIBLE
LIVE_TRADING_AUTHORITY_COMPATIBILITY=COMPATIBLE
OVERALL_COMPATIBILITY=COMPATIBLE
KEEP_AS_IS=true
ADAPT_DOWNSTREAM=false
DECOUPLE=false
DEGRADE=false
REMOVE=false
REWIRE=false
CORE_MUTATION_REQUIRED=false
NEW_OWNER_REQUIRED=false
NEW_POLICY_REQUIRED=false
EVIDENCE_GAPS=NONE
PROPOSED_SAFE_ACTION=KEEP_AS_CANONICAL_DOWNSTREAM_FUTURES_WRITER
```

```text
COMPONENT=HARDENING_IDEMPOTENT_PORTFOLIO_AND_PAPER_SHADOW_ECONOMICS
PROVENANCE=Hardening-v2 IdempotentPortfolioV2 + paper-shadow economics model
CURRENT_ROLE=MODE_SPECIFIC_ANALYTICAL_PAPER_SHADOW_PORTFOLIO_WRITER
HISTORICAL_ROLE=Hardening-v2 session-persistent analytical portfolio
AUTHORITY_SOURCE=WALLCLOCK_HARDENING_V2 MODE_SPECIFIC_ANALYTICAL_HOST
HISTORICAL_SEMANTIC_COMPATIBILITY=COMPATIBLE_WITH_CONSTRAINTS
AUTHORITY_COMPATIBILITY=COMPATIBLE
OWNER_COMPATIBILITY=COMPATIBLE
CALL_ORDER_COMPATIBILITY=COMPATIBLE
SAFETY_COMPATIBILITY=COMPATIBLE
INTENT_COMPATIBILITY=COMPATIBLE
EXIT_PRECEDENCE_COMPATIBILITY=COMPATIBLE
STATE_WRITER_COMPATIBILITY=COMPATIBLE_WITH_CONSTRAINTS
RISK_SIZING_COMPATIBILITY=COMPATIBLE
FAIL_CLOSED_COMPATIBILITY=COMPATIBLE
SIMULATED_EXECUTION_BOUNDARY_COMPATIBILITY=COMPATIBLE
FORENSIC_AUTHORITY_COMPATIBILITY=COMPATIBLE
LIVE_TRADING_AUTHORITY_COMPATIBILITY=COMPATIBLE
OVERALL_COMPATIBILITY=COMPATIBLE_WITH_CONSTRAINTS
KEEP_AS_IS=true_as_mode_specific_analytical_writer
ADAPT_DOWNSTREAM=false
DECOUPLE=true_from_canonical_futures_account_state
DEGRADE=false
REMOVE=false
REWIRE=false
CORE_MUTATION_REQUIRED=false
NEW_OWNER_REQUIRED=false
NEW_POLICY_REQUIRED=false
EVIDENCE_GAPS=NONE
PROPOSED_SAFE_ACTION=KEEP_AS_DISTINCT_NON_OVERLAPPING_HOST_MODE_WRITER
```

## 9) Guards (not SSOT)

Exact proof file:

`tests/ops/test_peak_trade_post_restoration_accounting_portfolio_alignment_adjudication_v1.py`

Guards must keep:

- wallclock-v1 host accounting call path is Cap 3.1 / SimulatedExecutionPort
- hardening-v2 host portfolio call path is IdempotentPortfolioV2
- neither accounting layer writes SideState
- neither accounting layer builds CanonicalOrderIntent
- neither accounting layer re-invokes STEP-29P
- neither accounting layer replaces Replay Safety
- ENTER without COI cannot be accounted as simulated BUY/SELL (mapper HOLD)
- EXIT/REDUCE remain mapper-preserved; accounting does not rewrite them to HOLD
- duplicate operation/cycle follows the chosen writer model
- no double mutation of the same canonical account state in one cycle

## 10) Out of scope this slice

```text
EXECUTION_PIPELINE_INTEGRATION=NOT_THIS_SLICE
SEE_ALSO_SIMULATED_EXECUTION_PIPELINE_ADJUDICATION=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_SIMULATED_EXECUTION_PIPELINE_ADJUDICATION_V1.md
LIVE_EXECUTION_BOUNDARY=NOT_THIS_SLICE
LIVE_SAFETY_GATES=NOT_THIS_SLICE
SEE_ALSO_LIVE_SAFETY_GATES_ADJUDICATION=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_LIVE_SAFETY_GATES_ADJUDICATION_V1.md
VENUE_PRETRADE_LIMIT_GATES=NOT_THIS_SLICE
SEE_ALSO_VENUE_PRETRADE_LIMIT_GATES_ADJUDICATION=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_VENUE_PRETRADE_LIMIT_GATES_ADJUDICATION_V1.md
SEE_ALSO_VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_ADJUDICATION=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_ADJUDICATION_V1.md
SEE_ALSO_EXACT_VENUE_METADATA_GET_CURRENT_SUI_PRETRADE_MAX_SIZE=docs/ops/specs/PEAK_TRADE_EXACT_VENUE_METADATA_GET_CURRENT_SUI_PRETRADE_MAX_SIZE_V1.md
SEE_ALSO_POST_6148_MAX_SIZE_UNIT_ADJUDICATION=docs/ops/specs/PEAK_TRADE_POST_6148_MAX_SIZE_UNIT_ADJUDICATION_V1.md
CANARY=NOT_THIS_SLICE
FLATTEN=NOT_THIS_SLICE
MULTI_FUTURE=NOT_THIS_SLICE
CAP_11_2_TO_11_12_ACTIVATION=NOT_THIS_SLICE
PR_6129=NOT_THIS_SLICE
RECOVERY_TRACK=NOT_THIS_SLICE
LEGACY_STRATEGY_POSITION_SIZERS=ALREADY_QUARANTINED_NOT_THIS_SLICE
INDEPENDENT_PRETRADE_SAFETY=ALREADY_QUARANTINED_NOT_THIS_SLICE
CORE_RUNTIME_MUTATION=false
```

P0-quarantine remains closed. Historical
`ACCOUNTING_PORTFOLIO_ALIGNMENT=NOT_THIS_SLICE` rows in the prior quarantine
specs remain historically true for those slices. Historical
`EXECUTION_PIPELINE_INTEGRATION=NOT_THIS_SLICE` remains true for this
accounting slice; later simulated-execution pipeline adjudication is
recorded in the SEE_ALSO spec. Later live-safety gates adjudication is
recorded in `SEE_ALSO_LIVE_SAFETY_GATES_ADJUDICATION`. Historical
`LIVE_SAFETY_GATES=NOT_THIS_SLICE` remains true for this accounting slice.
Later venue-pretrade limit-gates adjudication is recorded in
`SEE_ALSO_VENUE_PRETRADE_LIMIT_GATES_ADJUDICATION`. Historical
`VENUE_PRETRADE_LIMIT_GATES=NOT_THIS_SLICE` remains true for this accounting
slice. Later venue-pretrade metadata-binding alignment adjudication is
recorded in `SEE_ALSO_VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_ADJUDICATION`.

## 11) Existing guards reused (not duplicated)

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
| Productive futures accounting | `tests/ops/test_productive_futures_accounting_runtime_binding_v1.py` |
| Hardening-v2 portfolio/idempotence | `tests/ops/test_wallclock_bridge_hardening_v2.py` |

## 12) Negative contract

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
SECOND_CORE_OWNER_CREATED=false
```
