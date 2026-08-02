---
docs_token: DOCS_TOKEN_CAPABILITY_7_1_SIMULATED_ENTRY_REDUCE_EXIT_ACTIONABILITY_EVIDENCE_V1
status: active
scope: simulated entry/reduce/exit actionability evidence over productive Cap 6.1-6.5 path; no activation; no core-logic mutation
capability: CAPABILITY_7_1_SIMULATED_ENTRY_REDUCE_EXIT_ACTIONABILITY_EVIDENCE_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
authority_matrix: docs/evidence/capability_7_1_simulated_entry_reduce_exit_actionability_evidence_v1/productive_binding/authority_evidence_matrix_v1.json
last_updated: 2026-08-02
---

# Capability 7.1 — Simulated Entry / Reduce / Exit Actionability Evidence V1

## Problem

Capabilities 6.1–6.5 productively bind confirmation, dynamic scope, decision
config, atomic restart, and exit-policy producers, but Cap 6.5 explicitly leaves
`EXIT_END_TO_END_EVIDENCE_PROVEN=false`. Peak_Trade still lacked deterministic
end-to-end evidence that the canonical stateful single-future no-order runtime
can complete full simulated trade lifecycles with nonzero fees/slippage,
accounting reconstruction, and restart continuity.

## Ausgangszustand

- Cap 6.1–6.5 merged on `origin/main`
- Exit producers bound; exit fills not yet proven end-to-end
- Productive host: `run_bridge_cycle_v1`
- Offline / no-order / no activation

## Zielzustand

```text
ENTRY_END_TO_END_EVIDENCE_PROVEN=true
EXIT_END_TO_END_EVIDENCE_PROVEN=true
NONZERO_FEE_EVIDENCE_PROVEN=true
NONZERO_SLIPPAGE_EVIDENCE_PROVEN=true
ACCOUNTING_RECONSTRUCTION_MATCH=true
RESTART_DURING_OPEN_POSITION_PROVEN=true
CORE_LOGIC_CHANGE=false
RUNTIME_ACTIVATED=false
```

## Scope / Out of Scope

In scope:

- Deterministic fixtures controlling market observations, prices, event time,
  observation order, and restart boundaries
- Productive consumption of Cap 6.1–6.5 surfaces
- Simulated fills via productive accounting binding
- Restart / failure-injection / deterministic replay evidence
- Authority/evidence matrix artifact

Out of scope:

- Live / testnet / exchange orders / credentials / real capital
- Master V2 / Double Play / Bull-Bear / confirmation / scope / risk / safety /
  exit-rule / threshold / precedence mutations
- Forced intent or direct fill injection
- Runtime activation (Cap 7.2)

## Productive call graph

See `CALL_GRAPH_V1` in
`src/ops/simulated_entry_reduce_exit_actionability_evidence_v1/constants_v1.py`.

Key productive callers:

| Role | Owner |
| --- | --- |
| Host | `decision_economics_cycle_bridge_v1.run_bridge_cycle_v1` |
| Entry / reduce | `evaluate_double_play_entry_exit_policy_v0` |
| Exit producers | Cap 6.5 `evaluate_host_exit_policy_producers_v1` |
| Simulated execution | `apply_intended_action_via_canonical_accounting_v1` |
| Accounting | Cap 3.1 `AccountingSessionV1.apply_fill` |
| Persistence | Cap 6.4 atomic coordinator |
| Reconciliation | productive reconciliation startup gate |

## State / config / event-time ownership

- Confirmation / C1–C3: Cap 6.1
- Dynamic scope: Cap 6.2
- Decision numerics: Cap 6.3 TOML owner
- Atomic commit / pending evidence: Cap 6.4
- Exit producers: Cap 6.5
- Event time: host cycle `event_ts_unix` (fixture-controlled)

## Lifecycle fixtures

Fixtures may only control market observations, prices, event time, observation
order, and restart boundaries. Catalog:
`lifecycle_fixture_spec_v1.json`.

Mandatory proven classes include long, short, partial reduce, restart while
flat / open / confirmation / dynamic scope, adverse exit, profit exit, time
exit (Cap 6.5 producer), duplicate observation, duplicate replay, corrupt
checkpoint, config digest mismatch, writer conflict, and evidence
materialization recovery.

## Restart / atomicity model

Unchanged Cap 6.4 atomic commit boundary. Cap 7.1 proves continuation across
that boundary without inventing recovery policy.

## Failure semantics

Fail-closed for corrupt checkpoint, config digest mismatch, and writer
conflict. Evidence materialization faults after runtime commit leave a pending
cursor and recover idempotently without duplicating economic effects.

## Safety invariants

```text
NETWORK_SESSION_STARTED=false
AUTHORIZATION_CONSUMED=false
ACTIVATION_CHANGED=false
ORDER_SIDE_EFFECT_OCCURRED=false
POSITION_FLIP_ALLOWED=false
FORCED_INTENT_ALLOWED=false
DIRECT_FILL_INJECTION_ALLOWED=false
```

## Entry / reduce / exit evidence ladder

Closes Cap 6.5’s open exit ladder and the symmetric entry ladder through
productive intent → simulated fill → accounting → portfolio → restart.

## Fee / slippage / accounting proof

Fees and slippage originate only from productive simulated execution /
accounting fill construction. No ledger injection.

## Tests

- `tests/ops/test_simulated_entry_reduce_exit_actionability_evidence_v1.py`
- Cap 6.1–6.5 suites (regression)
- Relevant accounting / portfolio / reconciliation / evidence tests
- Deterministic replay digest comparison

## Failure injection

Corrupt checkpoint, config digest mismatch, writer conflict, evidence
materialization fault after runtime commit.

## Evidence

`docs/evidence/capability_7_1_simulated_entry_reduce_exit_actionability_evidence_v1/`

Authority matrix referenced above is a first-class evidence artifact.

## Claim semantics

Claims are true only when covered by durable evidence artifacts and verifier
pass. Cap 7.1 does not activate the runtime.

## Activation state

```text
RUNTIME_ACTIVATED=false
LIVE_TESTNET_ORDERS=false
```

## Rollback

Delete Cap 7.1 package/evidence/spec and revert the sizing
`decision_outcome` propagation binding fix if required. No Cap 6.x semantics
are altered beyond propagating the already-decided outcome into sizing input.

## Core logic unchanged

```text
CORE_LOGIC_CHANGED=false
MASTER_V2_CHANGED=false
DOUBLE_PLAY_CHANGED=false
EXIT_RULES_CHANGED=false
EXIT_THRESHOLDS_CHANGED=false
EXIT_PRECEDENCE_CHANGED=false
EFFECTIVE_NUMERIC_VALUES_UNCHANGED=true
```

The only productive binding completeness fix is passing
`decision.decision_outcome` into `CapitalRiskSizingInputV1` so short/reduce/
exit remain side-consistent with the already-produced canonical decision
(default was incorrectly `enter_long`).
