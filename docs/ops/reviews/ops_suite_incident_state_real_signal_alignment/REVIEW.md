# OPS SUITE INCIDENT STATE REAL SIGNAL ALIGNMENT

## Purpose
Align the current incident-stop, kill-switch, runtime-gate, and operator-visibility signals into one docs-first read-model view.

## Scope
- signal map only
- read-model / operator-authority clarification
- no runtime mutation
- no paper/shadow/testnet mutation

## Current Signal Inputs
### PT_* incident-stop path
- `PT_FORCE_NO_TRADE`
- `PT_ENABLED`
- `PT_ARMED`

### kill-switch path
- kill-switch state controlled by `scripts&#47;ops&#47;kill_switch_ctl.sh`
- operator-visible kill-switch state consumed via `data&#47;kill_switch&#47;state.json`

### runtime consumers
- entry contract reads `PT_ARMED`
- risk gate reads kill-switch state
- risk hook kill-switch policy remains future work

## Alignment Goal
Define one operator-facing signal map that makes clear:
1. which signals exist
2. which surfaces read them today
3. which signal is authoritative for which question
4. where the current gaps still are

## Recommended Read-Model Position
### Question: "Can entry proceed?"
- primary current signal: `PT_ARMED`
- consumed by entry contract

### Question: "Is kill-switch active for risk denial?"
- primary current signal: kill-switch state
- consumed by risk gate and surfaced in ops cockpit

### Question: "Was incident-stop invoked?"
- primary current signal: incident-stop artifact/env output
- currently adjacent to, but not the same as, kill-switch state

## Operator-Visible Clarification
Operators should not assume:
- incident-stop automatically equals kill-switch state
- kill-switch state automatically proves PT_* incident-stop posture
- one surface alone proves full end-to-end stop alignment

## Current Gaps
- PT_* and kill-switch are related but not unified into one authoritative runtime signal
- ops cockpit is kill-switch-centric
- incident-stop visibility is not yet the same as kill-switch visibility
- risk hook kill-switch policy remains future work

## Recommended Next Slice
- incident_state_read_model_contract
