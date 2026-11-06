---
docs_token: DOCS_TOKEN_CURRENT_FULL_CORE_PRE_POST_CAPITAL_GUARD_JOIN_V1
status: active
scope: Full-Core PRE_EXTERNAL capital guard join (fail-closed, default disabled)
capability: CURRENT_FULL_CORE_PRE_POST_CAPITAL_GUARD_JOIN_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-10-12
---

# CURRENT_FULL_CORE_PRE_POST_CAPITAL_GUARD_JOIN_V1

Independent fail-closed capital veto for CURRENT Full-Core productive paths.

## Boundary

After: canonical trading decision, final sizing, venue plan, `FinalOrderEnvelopeV1`, PRE_EXTERNAL terminal.

Before: any external POST or exchange order submission.

Implementation owner: `full_core_pre_post_capital_guard_join_v1.py`.

## Default behavior

`PEAK_TRADE_FULL_CORE_CAPITAL_GUARD_JOIN_MODE` defaults to `DISABLED`. Productive PRE_EXTERNAL disposition is unchanged. `LIVE_POST` is never activated from this join.

Modes: `DISABLED`, `OFFLINE_STUB`, `OBSERVE_ONLY`.

## Authority separation

- Full-Core Owner-GO: `OWNER_GO_CURRENT_FULL_CORE_PRE_POST_CAPITAL_GUARD_JOIN_V1`
- §11.13.5 Canary Owner-GO must not authorize Full-Core (`CANARY_OWNER_GO_FORBIDDEN`)
- Numeric caps in `config/ops/current_full_core_capital_guard_v1.json` are UNRATIFIED until Owner ratification

## Reuse

Numeric guard rules reuse `CURRENT_LIVE_CANARY_CAPITAL_GUARD_V1` evaluation (no duplicated cap algebra). Atomic one-shot reuses `canary_capital_guard_atomic_one_shot_v1` durable mechanics with extended Full-Core binding digest.

## GHV

Read-only stages via `ghv_full_core_capital_guard_observability_v1.py` (`GHV_AUTHORITY=NONE`).

## Reconciliation

Stub-only: `full_core_capital_guard_reconciliation_stub_v1.py` (no private GET).
