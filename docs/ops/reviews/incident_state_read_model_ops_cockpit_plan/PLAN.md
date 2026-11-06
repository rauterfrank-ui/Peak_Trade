# INCIDENT STATE READ MODEL OPS COCKPIT PLAN

## Purpose
Define how the incident-state read model should first be mapped into the ops cockpit without changing runtime behavior in this slice.

## Scope
- ops cockpit mapping plan only
- operator-authoritative wording
- no runtime mutation
- no paper/shadow/testnet mutation

## Why Ops Cockpit First
- already operator-facing
- already surfaces kill-switch-centric state
- best place to expose per-question authority without pretending global signal unification

## Core Questions To Surface
1. Was incident-stop invoked?
2. Is kill-switch active?
3. Can entry proceed?
4. Is risk-gate kill-switch denial active?
5. Which source is authoritative for each answer?

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

## Recommended Cockpit Layout
### Section 1 — Incident Stop
Show:
- invoked / not invoked
- source/artifact used
- PT_* env posture as observed

### Section 2 — Kill Switch
Show:
- active / inactive
- source used
- current cockpit-visible kill-switch posture

### Section 3 — Entry / Risk Authority
Show:
- entry-permitted answer
- risk-gate kill-switch answer
- explicit note that these answers may come from different authoritative sources

### Section 4 — Operator Summary
Show:
- `operator_authoritative_state`
- `operator_state_reason`
- brief text clarifying that stop semantics are question-specific today

## Wording Rules
- do not collapse PT_* and kill-switch into one "stopped" flag
- label each answer by source
- make uncertainty visible rather than hiding it

## Test Expectations
- ops cockpit payload includes mapped fields
- rendered HTML shows per-question state and reason
- blocked/degraded wording stays conservative

## Recommended Next Slice
- incident_state_read_model_ops_cockpit_mapping_review
