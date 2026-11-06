---
docs_token: DOCS_TOKEN_CAPABILITY_6_1_STATEFUL_CONFIRMATION_AND_C1_PRODUCTIVE_BINDING_V1
status: active
scope: productive C1/C2/C3 confirmation binding + minimal durable confirmation state; no activation
capability: CAPABILITY_6_1_STATEFUL_CONFIRMATION_AND_C1_PRODUCTIVE_BINDING_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-02
---

# Capability 6.1 — Stateful Confirmation and C1 Productive Binding V1

## Goal

Bind existing C1/C2/C3 confirmation domain contracts into the productive
single-future no-order host and persist the minimal confirmation cursor
required for restart continuity.

```text
CORE_LOGIC_CHANGE=false
RUNTIME_ACTIVATED=false
LIVE_TESTNET_ORDERS=false
```

## Target graph

```text
Public Market Observation
→ Observation Identity
→ DistinctMarketObservationAcceptor
→ ObservationAcceptanceResult
→ Observation Epoch
→ Directional Confirmation Progress
→ C3 Directional Assessment Integration
→ Candidate / Confirmed state
→ canonical confirmation state commit
→ next productive cycle / restart reload
```

## Productive owners

| Surface | Owner |
| --- | --- |
| C1 | `trading.market_state.distinct_market_observation_acceptor_v1` |
| C2 | `trading.market_state.directional_confirmation_progress_v1` |
| C3 | `trading.master_v2.directional_assessment_confirmation_integration_v1` |
| Decision | `run_integrated_offline_trading_logic_replay_v1` |
| Host binding | `ops.stateful_confirmation_and_c1_productive_binding_v1` |
| Productive host | `decision_economics_cycle_bridge_v1.run_bridge_cycle_v1` |

## Persistence

Schema is derived from C1 `ObservationAcceptanceStateV1` and C3
`DirectionalConfirmationSideStateCarrierV1` only. No parallel Master V2 or
Double Play persistence domain is introduced.
