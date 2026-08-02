---
docs_token: DOCS_TOKEN_CAPABILITY_6_5_EXIT_POLICY_PRODUCER_BINDING_V1
status: active
scope: exit policy producer binding into productive decision path; no activation; no core-logic mutation
capability: CAPABILITY_6_5_EXIT_POLICY_PRODUCER_BINDING_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-02
---

# Capability 6.5 — Exit Policy Producer Binding V1

## Goal

Replace unbound `PolicySignalV0(triggered=False)` stubs in the productive
wallclock decision host with productively evaluated canonical exit-policy
producers, without changing Exit rules, thresholds, precedence, or core
trading logic.

```text
EXIT_POLICY_PRODUCERS_BOUND=true
PLACEHOLDER_FALSE_SIGNAL_USED_AS_UNBOUND_STUB=false
EXIT_PATH_RUNTIME_REACHABLE=true
EXIT_INDEPENDENCE_PROVEN=true
EXIT_END_TO_END_EVIDENCE_PROVEN=false
CORE_LOGIC_CHANGE=false
RUNTIME_ACTIVATED=false
```

## Productive consumers

| Surface | Owner |
| --- | --- |
| Exit producer binding | `ops.exit_policy_producer_binding_v1` |
| Entry/Exit policy authority | `evaluate_double_play_entry_exit_policy_v0` |
| Adverse foundation | `derive_scope_adverse_exit_signal_v0` / host adverse distance eval |
| Safety / hard-risk | `evaluate_bridge_safety_v2` |
| Time foundation | `wallclock_time_exit_due_v1` |
| Decision config distances | Cap 6.3 `adverse_exit_distance` / `up_distance` |
| Atomic restart boundary | Cap 6.4 coordinator (same host cycle commit) |
| Productive host | `decision_economics_cycle_bridge_v1.run_bridge_cycle_v1` |

## Claim semantics

Cap 6.5 proves producer binding and restart continuity. It does **not** claim
end-to-end simulated exit fill evidence (`EXIT_END_TO_END_EVIDENCE_PROVEN` remains
false until Capability 7.1).

## Activation

```text
RUNTIME_ACTIVATED=false
LIVE_TESTNET_ORDERS=false
```
