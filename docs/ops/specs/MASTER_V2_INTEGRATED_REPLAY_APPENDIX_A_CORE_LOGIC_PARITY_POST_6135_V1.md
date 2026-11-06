# MASTER V2 — Integrated Replay Appendix-A core-logic parity post-6135 v1

status: ACTIVE
last_updated: 2026-08-29
owner: Peak_Trade
purpose: Semantics-neutral proof-only closeout of remaining Appendix-A axes after PR #6135. Not canonical authority. Not a new semantic owner. Not a restoration grant.
docs_token: DOCS_TOKEN_MASTER_V2_INTEGRATED_REPLAY_APPENDIX_A_CORE_LOGIC_PARITY_POST_6135_V1

```text
PROOF_SLICE_ID=MASTER_V2_INTEGRATED_REPLAY_APPENDIX_A_CORE_LOGIC_PARITY_POST_6135_V1
BASELINE_ORIGIN_MAIN_SHA=6ad52f7b762da8da12b0d26056e6a9fd3dab4f11
CLOSED_WIRING_PR=6135
CLOSED_WIRING_SLICE=INTEGRATED_REPLAY_SAFETY_BEFORE_INTENT_COMPUTE_OWNER_REWIRE_V1
NORMATIVE_PARITY_SUBJECT=ACTIVE_INTEGRATED_REPLAY_POST_6135
COMPUTE_OWNER=trading.master_v2.integrated_offline_trading_logic_replay_v1
PROOF_ONLY=true
RUNTIME_MUTATION=false
NEW_SEMANTIC_POLICY=false
NEW_RUNTIME_OWNER=false
NEW_GRANT_REQUIRED=false
RESTORATION_CLASS_REQUIRED=false
NEW_GOLDEN_VECTOR_CORPUS=false
A07_HISTORICAL_STAGE_CREATED=false
A08_HISTORICAL_STAGE_CREATED=false
A07_LABEL_DISPOSITION=RETIRE_AS_HISTORICAL_STAGE_LABEL
A08_LABEL_DISPOSITION=PROGRAM_BOOKKEEPING_ONLY_NOT_A_STAGE
```

This document is proof attestation. It is not Restoration SSOT, not class
SSOT, not historical authority, and not a Master V2 / Double Play E2E
runtime restoration claim.

## 1) Baseline and closed wiring

PR #6135 restored Integrated Replay call order to 29P → Safety → 29Q
PLAN_ONLY on `origin/main` SHA
`6ad52f7b762da8da12b0d26056e6a9fd3dab4f11`.

This slice does not rewire Replay. It proves remaining Appendix-A
core-logic preservation after that authorized semantic-delta wiring.

LEFT-HAND surface: active Integrated Replay after #6135.

## 2) Appendix-A axes

Canonical source: Master Runbook Appendix A Core Logic Preservation
Contract.

| Axis | Status before this slice | Comparator | Status after tests |
|---|---|---|---|
| GOLDEN_VECTOR | ABSENT frozen corpus / UNPROVEN for this delta | Owner-composed expected tuple from existing 29P / Safety / 29Q binders on captured Replay inputs | PASS |
| CALL_ORDER | PASS (#6135 contract) | Historical graph 29P→Safety→29Q | PASS (not re-scoped) |
| INPUT_OUTPUT | PARTIAL | Isolated binders on identical captured inputs | PASS |
| STATE_TRANSITION | PASS | `transition_state` unchanged by #6135 | PASS (not re-scoped) |
| DECISION_REASON | PASS (#6135 outcome vs intent) | — | PASS (not re-scoped) |
| RISK | PASS (existing CRS binder tests) | `capital_risk_sizing_v1` via CRS binder | PASS (not re-scoped) |
| SAFETY | PARTIAL (orchestration PASS; owner-result equality open) | Isolated Safety binder on the same captured context | PASS |
| EXIT_PRECEDENCE | PASS (policy owner tests) | — | PASS (not re-scoped) |
| INTENT | PARTIAL | Isolated 29Q on pass; absence of ENTER intent on hard-block | PASS |

## 3) Comparators that are not normative E2E RHS

| Surface | Why excluded as E2E RHS |
|---|---|
| A06 `capital_risk_sizing_intent_restore_v1` | Bounded 29P→29Q without Safety; closed prior slice, not compute owner |
| XP-03 intent pipeline bridge | BOUND_NOT_ACTIVATED CRS→COI glue without Safety |
| Sibling `capital_risk_sizing_safety_intent_restore_v1` | Independent reference composition; Replay does not route through it |
| 4-way `canonical_order_intent_path` | OWNER_UNIT_REFERENCE; CRS→Intent bypasses Safety |
| Cap 6/7 frozen GOLDEN_VECTOR JSON | Other capability SHA; host graph, not Replay-internal 29P→Safety→29Q |
| Host intended-action mapper | Downstream consumer, not Replay authority |
| Simulated execution | Economic transition; out of Appendix-A Replay core-logic slice |

## 4) Owner-composed golden vector

No new JSON / snapshot corpus.

For fixed post-#6135 test inputs (CASE_A pass ENTER, CASE_B hard-block ENTER,
CASE_C EXIT):

```text
captured 29P input  → isolated CRS binder → expected 29P semantic fields
captured Safety input → isolated Safety binder → expected Safety semantic fields
captured 29Q input OR None if ENTER hard-block skipped 29Q
  → isolated 29Q binder on pass/EXIT
  → None for blocked ENTER orchestration
```

Replay LEFT values are compared to that owner-composed expected tuple.
The vector is derived from existing canonical owners, not a second frozen
runtime SSOT.

Compared semantic fields exclude wrapper identity, object id, digest,
stage-id, and binder ref hashes.

## 5) Exact proof file

`tests/trading/master_v2/test_master_v2_integrated_replay_appendix_a_core_logic_parity_post_6135_contract_v1.py`

Cases:

- CASE_A = SAFETY_PASS_ENTER (ENTER_LONG; ENTER_SHORT is the same contract)
- CASE_B = SAFETY_HARDBLOCK_ENTER
- CASE_C = EXIT_PATH (ENTER-specific skip must not blanket-suppress EXIT)

## 6) Negative contracts

```text
RUNTIME_FILE_MUTATED=false
COMPUTE_OWNER_CHANGED=false
RISK_OWNER_CHANGED=false
SAFETY_OWNER_CHANGED=false
INTENT_OWNER_CHANGED=false
SIDESTATE_OWNER_CHANGED=false
SECOND_COMPUTE_OWNER_CREATED=false
SAFETY_POLICY_REIMPLEMENTED=false
SAFETY_BLOCK_TABLE_DUPLICATED=false
XP03_ACTIVATED=false
EV_BOUND_INTO_REPLAY=false
A06_PROMOTED=false
SIBLING_ADAPTER_PROMOTED=false
FOUR_WAY_HARNESS_RESCOPED=false
HOST_MAPPER_CHANGED=false
SIMULATED_EXECUTION_CHANGED=false
EXECUTION_AUTHORITY_CHANGED=false
LIVE_AUTHORITY_CHANGED=false
TRADING_AUTHORITY_CHANGED=false
RECOVERY_MUTATION=false
PR_6129_TOUCHED=false
CURRENT_6135_GRANT_REUSED_AS_WILDCARD=false
```

## 7) Authority / recovery

```text
AUTHORITY_CHANGE=false
RUNTIME_MUTATION=false
RECOVERY_TOUCH=false
NO_TRADING=true
NO_LIVE_AUTHORITY=true
NO_EXECUTION_AUTHORITY=true
```
