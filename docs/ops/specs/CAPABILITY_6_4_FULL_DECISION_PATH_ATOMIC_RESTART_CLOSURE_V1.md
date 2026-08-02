---
docs_token: DOCS_TOKEN_CAPABILITY_6_4_FULL_DECISION_PATH_ATOMIC_RESTART_CLOSURE_V1
status: active
scope: full decision-path atomic restart closure; versioned multi-record transaction; no activation
capability: CAPABILITY_6_4_FULL_DECISION_PATH_ATOMIC_RESTART_CLOSURE_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-02
---

# Capability 6.4 — Full Decision-Path Atomic Restart Closure V1

## Goal

Prove that the complete required decision state survives crash and restart
without semantic drift, mixed state-root commits, or duplicated economic
effects.

```text
CORE_LOGIC_CHANGE=false
RUNTIME_ACTIVATED=false
LIVE_TESTNET_ORDERS=false
ATOMICITY_MODEL=VERSIONED_MULTI_RECORD_TRANSACTION_WITH_COMMIT_MARKER_AND_REPLAY
```

## Atomicity model

```text
PREPARE(WAL journal)
→ stage member writes (Cap 3.1 / 6.1 / 6.2 / 6.3 owners)
→ COMMIT_MARKER
→ promote staged members
→ PENDING_EVIDENCE_CURSOR
→ evidence materialization (failure does not roll back runtime commit)
```

Member state roots retain their Cap 6.1 / 6.2 / 6.3 / 3.1 owners. The Cap 6.4
coordinator owns only the cross-root journal, commit marker, pending-evidence
cursor, and writer fencing for the transaction boundary.

## Productive consumers

| Surface | Owner |
| --- | --- |
| Confirmation | `ops.stateful_confirmation_and_c1_productive_binding_v1` |
| Dynamic Scope | `ops.dynamic_scope_persistence_binding_v1` |
| Decision config | `ops.decision_config_ownership_and_consumer_closure_v1` |
| Accounting/portfolio | `ops.productive_futures_accounting_runtime_binding_v1` |
| Atomic coordinator | `ops.full_decision_path_atomic_restart_closure_v1` |
| Productive host | `decision_economics_cycle_bridge_v1.run_bridge_cycle_v1` |

## Activation

```text
RUNTIME_ACTIVATED=false
LIVE_TESTNET_ORDERS=false
```
