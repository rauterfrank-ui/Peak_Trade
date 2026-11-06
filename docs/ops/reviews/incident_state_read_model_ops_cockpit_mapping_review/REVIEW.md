# INCIDENT STATE READ MODEL OPS COCKPIT MAPPING REVIEW

## Purpose
Define the docs-first mapping review for bringing the incident-state read model into the ops cockpit.

## Scope
- mapping review only
- no runtime mutation
- no paper/shadow/testnet mutation

## Mapping Goal
Translate the incident-state read model into cockpit-visible sections without pretending the underlying signals are fully unified.

## Contract Fields To Map
- `incident_stop_invoked`
- `incident_stop_source`
- `pt_force_no_trade`
- `pt_enabled`
- `pt_armed`
- `kill_switch_active`
- `kill_switch_source`
- `entry_permitted`
- `risk_gate_kill_switch_active`
- `operator_authoritative_state`
- `operator_state_reason`

## Recommended Cockpit Mapping
### Section 1 — Incident Stop
Map:
- `incident_stop_invoked`
- `incident_stop_source`
- `pt_force_no_trade`
- `pt_enabled`
- `pt_armed`

Purpose:
- show incident-stop posture and PT_* read posture explicitly

### Section 2 — Kill Switch
Map:
- `kill_switch_active`
- `kill_switch_source`

Purpose:
- show kill-switch posture as distinct from incident-stop posture

### Section 3 — Entry / Risk Authority
Map:
- `entry_permitted`
- `risk_gate_kill_switch_active`

Purpose:
- make per-question authority visible
- entry and risk answers may differ because they read different sources today

### Section 4 — Operator Summary
Map:
- `operator_authoritative_state`
- `operator_state_reason`

Purpose:
- give the operator one concise state explanation without hiding question-specific authority

## Wording Constraints
- do not present one global "stopped" boolean
- label source per section
- if fields are unavailable, show that explicitly instead of implying certainty

## Test Expectations
- payload contains mapped fields
- HTML contains section labels and values
- wording remains conservative when signals are mixed or partially unavailable

## Recommended Next Slice
- incident_state_read_model_ops_cockpit_implementation
