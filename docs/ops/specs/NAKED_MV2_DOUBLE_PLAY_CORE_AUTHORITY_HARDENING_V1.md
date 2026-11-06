---
docs_token: DOCS_TOKEN_NAKED_MV2_DOUBLE_PLAY_CORE_AUTHORITY_HARDENING_V1
status: active
scope: Outward-only authority hardening for naked MV2+Double Play trading core
capability: NAKED_MV2_DOUBLE_PLAY_CORE_AUTHORITY_HARDENING_V1
last_updated: 2026-09-19
---

# Naked Master V2 + Double Play Core Authority Hardening v1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
WORKPACKAGE_ID=NAKED_MV2_DOUBLE_PLAY_CORE_AUTHORITY_HARDENING_V1
HARDENING_DIRECTION=OUTWARD_ONLY
CORE_HOT_PATH_MUTATION=false
EXTERNAL_EFFECT_AUTHORIZED=false
```

Machine-readable decision: `config/governance/naked_mv2_double_play_core_authority_hardening_v1_decision_v1.json`

Code owner: `src/trading/master_v2/naked_mv2_double_play_core_authority_hardening_v1.py`

## 1. Purpose

Freeze the **already-adjudicated** productive trading-decision authority established by
integrated offline replay + Double Play composition/state/entry-exit. Harden **outward**
against Learning, Optimization, Meta-Learning, Autonomy, Legacy evaluators, and downstream
redecision — **without** changing core trading semantics.

## 2. Canonical authority (reuse; not redefined)

| Claim | Owner |
|-------|--------|
| Sole productive trading decision | `run_integrated_offline_trading_logic_replay_v1` |
| Terminal field | `CanonicalTradingDecisionEvidenceV1.decision_outcome` |
| Terminal producer | `evaluate_double_play_entry_exit_policy_v0` |
| Core end | Immediately after entry/exit; 29P/safety/intent/venue are downstream |

Related quarantine (Slice E + sole authority): `DOUBLE_PLAY_SOLE_AUTHORITY_FAIL_CLOSED_QUARANTINE_CONTRACT_V1.md`,
`evaluate_double_play_authority_boundary_v0`.

## 3. Non-interference

For identical canonical inputs and initial core state, hardening must not alter:

- directional assessment, composition result, next side state, or decision outcome.

No new gates inside the integrated replay hot path.

## 4. Ingress firewall (summary)

Forbidden productive claims:

- Learning / Optimization / Meta-Learning / Autonomy → independent `TradingDecision`
- Legacy Double Play evaluators → productive decision or SideState write
- Execution → redecision (translation/DENY/veto only)

Enforcement: `deny_independent_trading_decision_authority_v1` and existing quarantine helpers.

## 5. Downstream non-redecision

| Layer | Allowed | Forbidden |
|-------|---------|-----------|
| 29P sizing | size / admit / deny execution | rewrite `decision_outcome` |
| Safety / kill / recon | veto intent / add reason codes | rewrite terminal decision |
| `compose_core_live_execution_intent_v1` | consume outcome, DENY | independent opposite/new decision |
| Venue translation | translation | decision authority |

## 6. Future optimization touch (F3 not built)

Core-touching optimization surfaces require all ten admission keys on
`assert_optimization_core_touch_surface_admitted_v1`. Unknown or partial metadata =>
`NOT_ADMITTED`. Does not change F1/F2 authorized surface semantics.

## 7. Acceptance exclusions (baseline drift)

The integrated-replay safety-restore contract test
`test_call_order_pass_path_enter_long` is **not** an acceptance gate for this WP.
Long/short proof uses entry/exit policy contract owners and deterministic
non-interference replay vectors only (`LONG_SHORT_REGRESSION_ROLE=NON_INTERFERENCE_AND_ENTRY_EXIT_CONTRACT_OWNER_ONLY`).

## 8. Non-goals

- No F3/M10 build, no productive parameter mutation, no ranking/selection change, no POST/permit minting.
