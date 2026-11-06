# INCIDENT STATE READ MODEL CONTRACT

## Purpose
Define the docs-first read-model contract for incident-state visibility across incident-stop, kill-switch, runtime-gate, and operator-facing surfaces.

## Scope
- read-model contract only
- operator-authoritative vs indicative fields
- no runtime mutation
- no paper/shadow/testnet mutation

## Contract Goal
A future or current operator-facing read model should answer:
1. was incident-stop invoked?
2. is kill-switch active?
3. can entry proceed?
4. is risk denial active because of kill-switch?
5. which surface is authoritative for each answer?

## Candidate Read-Model Fields
Minimum contract fields:

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

## Field Meaning
### Incident-stop fields
- indicate whether the incident-stop path was invoked and from which source/artifact that conclusion is drawn

### PT_* fields
- expose current PT env posture as observed by the read model
- these are informative and entry-adjacent, not automatically equivalent to kill-switch state

### Kill-switch fields
- expose whether kill-switch is active and from which source the conclusion is drawn
- these are risk-gate / cockpit-adjacent

### Operator-authoritative fields
- summarize which state operators should trust for the current question
- must make scope explicit rather than pretending all signals are unified

## Question → Authoritative Surface
### "Can entry proceed?"
- current authoritative signal: `PT_ARMED`
- current consumer: entry contract

### "Is kill-switch active for risk denial?"
- current authoritative signal: kill-switch state
- current consumer: risk gate / ops cockpit

### "Was incident-stop invoked?"
- current authoritative signal: incident-stop artifact/env output
- not identical to kill-switch state

## Contract Constraints
- do not collapse incident-stop and kill-switch into one field unless truly unified
- do not imply full end-to-end signal unification where it does not yet exist
- make authority per question explicit
- prefer conservative operator wording under ambiguity

## Non-Goals
- no implementation in this slice
- no live-expansion work
- no weakening of existing guardrails

## Recommended Next Slice
- incident_state_read_model_usage_plan
