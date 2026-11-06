---
docs_token: DOCS_TOKEN_GHV_CURRENT_EXCHANGE_RECONCILIATION_INTEGRATION_V1
status: active
scope: Full-Core exchange reconciliation (offline fixtures and injected read-only transport)
capability: GHV_CURRENT_EXCHANGE_RECONCILIATION_INTEGRATION_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-11-02
---

# GHV_CURRENT_EXCHANGE_RECONCILIATION_INTEGRATION_V1

Offline-only Full-Core exchange reconciliation after submit boundary. `GHV_AUTHORITY=NONE`.

## Boundary

After: Full-Core capital guard join, atomic reservation, submit transport boundary (simulated offline).

Before: any productive private GET or live POST.

## Provider

`OFFLINE_STUB` uses supplied fixtures. `OKX_EEA_READ_ONLY_GET_V1` uses an explicitly
injected GET transport. `PRODUCTION_PROVIDER_WIRING=NOT_AUTHORIZED`; importing the
adapter does not create a transport, access credentials, or contact the venue.

Local dependency repair on 2026-11-02 restores the adapter and integration from
commit `b48094917d2575e806610cb2d9569bf75929ebc9` (PR #7094), including fail-closed
identity-conflict handling. The post-submit observation stage comes from preserved
stash commit `d70f527fc7351a4941930a256748a2ea8162ab8f`. Existing lifecycle joins now
import successfully; automatic host wiring and productive execution remain unproven.

## Owners

- Identity + FSM: `full_core_exchange_reconciliation_v1.py`
- Offline fixtures: `full_core_exchange_reconciliation_offline_provider_v1.py`
- Injected GET adapter: `full_core_exchange_reconciliation_okx_read_only_provider_v1.py`
- Handoff: `full_core_exchange_reconciliation_integration_v1.py`
- GHV stages: `ghv_full_core_exchange_reconciliation_observability_v1.py`

## Invariants

`UNKNOWN_REMAINS_UNKNOWN`, no automatic resubmit, no automatic flatten, `POST_COUNT=0`, reconciliation does not reauthorize Owner-GO.

Local post-close feedback extension, 2026-11-03: lifecycle reconciliation can
explicitly forward a typed close request into the existing position, budget and
membership owners. Providers retain the original scoped positions/pending responses.
Successful empty pending plus a chronologically confirmed explicit flat row and
the exact filled closing order are required before review or capital retirement.
Missing position rows remain unknown. The budget refresh requires fresh admissible
Treasury/Q0 capital and the exact committed same-lane reservation set, with replay
protection; no quantity/PnL-to-money arithmetic is added. Ranking review remains a
proposal without assignment persistence. Productive read-only mode rejects these
mutations. Default lifecycle calls and production-provider authorization are unchanged.
