---
docs_token: DOCS_TOKEN_GHV_CURRENT_EXCHANGE_RECONCILIATION_INTEGRATION_V1
status: active
scope: Full-Core exchange reconciliation (offline stub integration)
capability: GHV_CURRENT_EXCHANGE_RECONCILIATION_INTEGRATION_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-10-12
---

# GHV_CURRENT_EXCHANGE_RECONCILIATION_INTEGRATION_V1

Offline-only Full-Core exchange reconciliation after submit boundary. `GHV_AUTHORITY=NONE`.

## Boundary

After: Full-Core capital guard join, atomic reservation, submit transport boundary (simulated offline).

Before: any productive private GET or live POST.

## Provider

`RECONCILIATION_PROVIDER=OFFLINE_STUB` only. Production provider interface exists but `PRODUCTION_PROVIDER_WIRING=NOT_AUTHORIZED`.

## Owners

- Identity + FSM: `full_core_exchange_reconciliation_v1.py`
- Offline fixtures: `full_core_exchange_reconciliation_offline_provider_v1.py`
- Handoff: `full_core_exchange_reconciliation_integration_v1.py`
- GHV stages: `ghv_full_core_exchange_reconciliation_observability_v1.py`

## Invariants

`UNKNOWN_REMAINS_UNKNOWN`, no automatic resubmit, no automatic flatten, `POST_COUNT=0`, reconciliation does not reauthorize Owner-GO.
