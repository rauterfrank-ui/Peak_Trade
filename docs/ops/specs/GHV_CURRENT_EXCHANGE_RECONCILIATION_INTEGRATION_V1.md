---
docs_token: DOCS_TOKEN_GHV_CURRENT_EXCHANGE_RECONCILIATION_INTEGRATION_V1
status: active
scope: Full-Core exchange reconciliation (offline stub integration)
capability: GHV_CURRENT_EXCHANGE_RECONCILIATION_INTEGRATION_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-10-13
---

# GHV_CURRENT_EXCHANGE_RECONCILIATION_INTEGRATION_V1

Offline-only Full-Core exchange reconciliation after submit boundary. `GHV_AUTHORITY=NONE`.

## Boundary

After: Full-Core capital guard join, atomic reservation, submit transport boundary (simulated offline).

Before: any productive private GET or live POST.

## Provider

`RECONCILIATION_PROVIDER=OFFLINE_STUB` for fixture-only runs.

`RECONCILIATION_PROVIDER=OKX_EEA_READ_ONLY_GET_V1` via
`full_core_exchange_reconciliation_okx_read_only_provider_v1.py` uses injected
`FullCoreFreshPretradeGetTransportV1` only (tests and offline reproof). No new HTTP
client. `PRODUCTION_PROVIDER_WIRING=NOT_AUTHORIZED` until scoped Owner-GO.

## Owners

- Identity + FSM: `full_core_exchange_reconciliation_v1.py`
- Offline fixtures: `full_core_exchange_reconciliation_offline_provider_v1.py`
- Handoff: `full_core_exchange_reconciliation_integration_v1.py`
- Post-submit lifecycle join: `full_core_post_submit_exchange_reconciliation_lifecycle_join_v1.py`
  (Cap 11.1 / §11.2.1.DW → `LocalSubmitOutcome` → reconciliation pipeline → atomic recovery)
- Orchestration entry: `full_core_orchestrated_post_submit_lifecycle_reconciliation_v1.py`
- Productive GET validation (explicit session): `ghv_current_okx_productive_read_only_reconciliation_get_validation_v1.py`
- GHV stages: `ghv_full_core_exchange_reconciliation_observability_v1.py`

## Invariants

`UNKNOWN_REMAINS_UNKNOWN`, no automatic resubmit, no automatic flatten, `POST_COUNT=0`, reconciliation does not reauthorize Owner-GO.

OKX adapter records `identity_conflicts` on the snapshot when relevant contradictory
venue identity is observed (same `clOrdId`, mismatched `instId`/`ordId`). Adjudication
fail-closes before terminal reconciliation; contradictory evidence must not be silently
dropped.
