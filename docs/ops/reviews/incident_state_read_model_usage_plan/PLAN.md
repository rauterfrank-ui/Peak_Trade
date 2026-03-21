# INCIDENT STATE READ MODEL USAGE PLAN

## Purpose
Define where and how the incident-state read model should be used before any implementation work.

## Scope
- usage plan only
- no runtime mutation
- no paper/shadow/testnet mutation

## Current Position
The contract now defines the minimum incident-state fields, but current consumers remain split:
- ops cockpit is kill-switch-centric
- entry contract is PT_ARMED-centric
- risk gate depends on caller-provided kill_switch state
- risk hook kill-switch behavior remains future work

## Primary Usage Questions
1. Was incident-stop invoked?
2. Is kill-switch active?
3. Can entry proceed?
4. Is risk denial active because of kill-switch?
5. Which source is authoritative for each answer?

## First Consumer Priority
### Phase 1 — Ops Cockpit Read-Model Mapping
Why first:
- already operator-facing
- already consumes kill-switch-centric state
- safest place to make per-question authority explicit without changing runtime gates

Target contract fields to surface or map:
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

### Phase 2 — Incident / Snapshot Surfaces
Why second:
- aligns evidence and operator interpretation
- makes post-stop review less ambiguous

### Phase 3 — Broader Runtime-Adjacent Surfaces
Why later:
- only after ops-cockpit wording and authority mapping are stable
- avoid premature pseudo-unification across entry/risk/runtime layers

## Usage Rules
### For Ops Cockpit
- show per-question authority explicitly
- do not imply one unified stop signal
- distinguish:
  - incident-stop invoked
  - kill-switch active
  - entry permitted
  - risk-gate kill-switch posture

### For Docs / Runbooks
- reference the read-model contract
- state which signal answers which operator question
- avoid shorthand like "stopped" unless scoped

### For Future Runtime Work
- do not change entry/risk/risk-hook behavior in this slice
- keep PT_* and kill-switch semantics distinct unless a later explicit unification decision is made

## Current Gap Matrix Summary
### Ops Cockpit
Missing today:
- `incident_stop_invoked`
- `incident_stop_source`
- `pt_force_no_trade`
- env-based `pt_enabled`
- env-based `pt_armed`
- `kill_switch_source`
- `entry_permitted`
- `risk_gate_kill_switch_active`
- `operator_authoritative_state`
- `operator_state_reason`

### Entry Contract
Current authority:
- `PT_ARMED`-centric deny posture

### Risk Gate
Current authority:
- caller-provided `limits.kill_switch`

### Risk Hook
Current authority:
- none yet for kill switch; still future work

## Recommended Next Slice
- `incident_state_read_model_ops_cockpit_plan`
