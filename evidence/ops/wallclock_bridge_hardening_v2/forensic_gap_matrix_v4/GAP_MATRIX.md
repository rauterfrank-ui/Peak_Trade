# Forensic Gap Matrix — Runbook v4 vs origin/main (pre → post this PR)

Authority base: origin/main@fe8cf2d636a09ba5bbb6a796abb6fd516f9b104c
Capability: WALLCLOCK_FULL_CANONICAL_DECISION_TO_SIMULATED_ECONOMICS_RUNTIME_BRIDGE_V1 (hardened by V2)

| REQUIREMENT | CURRENT_IMPLEMENTATION (pre) | GAP | TARGET_COMPONENT | TEST_OR_EVIDENCE |
|---|---|---|---|---|
| Productive feature_trace / regime_trace | Offline probes only via persist_hardening_evidence_bundle_v2 | Productive wallclock did not append | append_productive_cycle_evidence_streams_v2 + session_runtime | test_productive_evidence_streams_bound_in_wallclock_schema |
| risk_sizing_trace / order_intent_trace | risk_telemetry only | Missing runbook stream names | wallclock_evidence APPEND_ONLY + binder | stub scan PRODUCTIVE_APPEND_STREAM_* |
| simulated_fill_trace / portfolio_snapshots / equity_curve / runtime_events | bridge_fill_ledger / portfolio_snapshot.json only | Incomplete productive schema | binder + APPEND_ONLY | probe + owner tests |
| completion_verdict.json | terminal_verdict.json only | Name/schema gap | session_runtime finalize | completion_verdict write |
| authorization_consumption.json | authorization_consumption_record.json only | Runbook name gap | authorization_consumption_runtime_v1 | dual-write |
| Default HOLD / qty=0 adapter params | Defaults present (unguarded call risk) | Adapter defaults forbidden | observation_cycle_adapter_v1 required kwargs | test_observation_adapter_no_default_hold |
| AI_LAYER_NON_AUTHORITY attestation | Implicit absence only | No explicit cycle attestation | hardening_cycle_bridge_v2 cycle fields | test_ai_layer_non_authority_on_cycle |
| Economics stub writers | Wrote stub JSON without quality_fail | Placeholder PASS risk | finalize quality_fail=True | stub scan |
| Master V2 / Double Play per cycle | Bound via hardening cycle | CLOSED | run_hardened_bridge_cycle_v2 | canonical strategy probe |
| Forced wiring isolation | Present | CLOSED | forced_wiring_fixture_v2 unreachable from wallclock | stub scan + fixture probe |
| Full economic reconstruction | Verifier v2 | CLOSED for probes; productive now emits completion_verdict | verifier_v2 | FULL_ECONOMIC_RECONSTRUCTION_PASS |
