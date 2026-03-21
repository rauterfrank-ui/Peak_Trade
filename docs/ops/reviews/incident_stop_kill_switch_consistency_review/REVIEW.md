# INCIDENT STOP ↔ KILL SWITCH CONSISTENCY REVIEW

## Purpose
Review whether the incident-stop path, kill-switch path, runtime guards, and operator-visible read models are consistent enough for safety-first operations.

## Scope
- docs / read-model / signal consistency only
- no new runtime gates in this slice
- no paper/shadow/testnet mutation

## Surfaces Under Review
- `scripts&#47;ops&#47;incident_stop_now.sh`
- `scripts&#47;ops&#47;kill_switch_ctl.sh`
- `src&#47;webui&#47;ops_cockpit.py`
- `src&#47;execution&#47;networked&#47;entry_contract_v1.py`
- `src&#47;ops&#47;gates&#47;risk_gate.py`
- `src&#47;execution&#47;risk_hook_impl.py`
- `docs&#47;ops&#47;specs&#47;OPS_SUITE_INCIDENT_STATE_REAL_SIGNAL_REVIEW.md`

## Review Questions
1. Does incident-stop set the same effective safety posture that runtime and operator surfaces actually read?
2. Are PT_* env signals and kill-switch state signals clearly mapped?
3. Can operators tell from the cockpit which signal is authoritative?
4. Are there gaps where incident-stop appears active in one surface but not another?

## Signal Map
### Incident Stop Path
- `scripts&#47;ops&#47;incident_stop_now.sh` writes:
  - `PT_FORCE_NO_TRADE=1`
  - `PT_ENABLED=0`
  - `PT_ARMED=0`
- output is written into an incident evidence/state artifact under `out&#47;ops&#47;incident_stop_*`

### Kill Switch Path
- `scripts&#47;ops&#47;kill_switch_ctl.sh` controls kill-switch state
- runtime and operator surfaces read kill-switch-specific state separately from PT_* incident-stop env values

### Runtime / Operator Read Path
- `src&#47;execution&#47;networked&#47;entry_contract_v1.py` reads `PT_ARMED`
- `src&#47;ops&#47;gates&#47;risk_gate.py` maps kill-switch state to `RiskDenyReason.KILL_SWITCH`
- `src&#47;webui&#47;ops_cockpit.py` reads `data&#47;kill_switch&#47;state.json`
- `src&#47;execution&#47;risk_hook_impl.py` still describes `KillSwitchPolicy` as future work

## Findings
### Finding 1 — Incident Stop and Kill Switch Are Not Yet One Unified Signal Path
Category:
- docs/read-model drift

Observation:
- incident-stop writes PT_* environment state
- kill-switch tooling and cockpit visibility rely on a different state path

Why It Matters:
- operators may assume one stop action updates every surface
- in reality, incident-stop and kill-switch are adjacent but not fully unified

### Finding 2 — Entry Guard and Risk Gate Read Different Safety Inputs
Category:
- future runtime integration gap

Observation:
- entry contract consumes `PT_ARMED`
- risk gate consumes kill-switch state
- these are related safety controls, but not obviously one common source of truth

Why It Matters:
- one surface may reflect a blocked posture while another reflects a different input source
- this increases the chance of partial-stop ambiguity

### Finding 3 — Ops Cockpit Visibility Is Kill-Switch-Centric, Not Incident-Stop-Centric
Category:
- operator visibility ambiguity

Observation:
- ops cockpit reads `data&#47;kill_switch&#47;state.json`
- incident-stop artifact/env output is not obviously the same operator-visible source

Why It Matters:
- operators may not know whether PT_* or kill-switch state is the authoritative stop signal
- this weakens fast incident interpretation

### Finding 4 — RiskHook KillSwitchPolicy Remains Future Work
Category:
- future runtime integration gap

Observation:
- `src&#47;execution&#47;risk_hook_impl.py` still marks kill-switch policy integration as future work

Why It Matters:
- the documented safety posture is stronger than the fully unified runtime story
- this should remain explicit in docs and operator expectations

## Overall Review Outcome
Current posture:
- incident-stop and kill-switch both exist as safety mechanisms
- they are not yet a single clearly unified real-signal path
- operator visibility and runtime consumption should be treated as related but not identical today

## Recommendations
1. document one explicit signal map across PT_* env, kill-switch state, entry guard, risk gate, and ops cockpit
2. state clearly which surface is operator-authoritative for stop status today
3. keep incident-stop and kill-switch expectations conservative until alignment is tighter
4. do not imply full stop-signal unification while RiskHook kill-switch integration remains future work

## Preferred Next Slice
- `ops_suite_incident_state_real_signal_alignment`

## References
- `docs&#47;ops&#47;runbooks&#47;incident_stop_freeze_rollback.md`
- `scripts&#47;ops&#47;incident_stop_now.sh`
- `scripts&#47;ops&#47;kill_switch_ctl.sh`
- `docs&#47;ops&#47;specs&#47;OPS_SUITE_INCIDENT_STATE_REAL_SIGNAL_REVIEW.md`
