# INCIDENT STATE READ MODEL USAGE PLAN

## Purpose
Define where and how the incident-state read model should be used before any implementation work.

## Scope
- usage plan only
- no runtime mutation
- no paper/shadow/testnet mutation

## Current Position
The contract defines the minimum incident-state fields. Consumer authority remains **split by question** (non-authorizing read-model only):
- **ops cockpit** — `incident_state` payload on main implements all 11 contract fields in `src/webui/ops_cockpit.py`; per-question authority visible in payload and partial HTML (see gap matrix below). Still observation-only; does not grant entry, Live, broker, or exchange permission.
- **entry contract** — `PT_ARMED`-centric deny posture (separate authority)
- **risk gate** — caller-provided `limits.kill_switch`
- **risk hook** — kill-switch behavior remains future work

Canonical implementation evidence: `tests/webui/test_ops_cockpit.py` (payload + HTML assertions). Wave closeout: `docs/ops/reviews/incident_state_read_model_ops_cockpit_closeout&#47;CLOSEOUT.txt`.

## Primary Usage Questions
1. Was incident-stop invoked?
2. Is kill-switch active?
3. Can entry proceed?
4. Is risk denial active because of kill-switch?
5. Which source is authoritative for each answer?

## First Consumer Priority
### Phase 1 — Ops Cockpit Read-Model Mapping
Status on main: **implemented (payload)** — all target contract fields present in `incident_state`; tests in `tests/webui/test_ops_cockpit.py`.

Why first (historical):
- already operator-facing
- already consumes kill-switch-centric state
- safest place to make per-question authority explicit without changing runtime gates

Target contract fields surfaced in ops cockpit payload (`incident_state`):
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
**Implemented on main (payload, read-model / non-authorizing):**
- `incident_stop_invoked` — `_detect_incident_stop` in `src/webui/ops_cockpit.py`
- `incident_stop_source`
- `pt_force_no_trade`, `pt_enabled`, `pt_armed` — env observation
- `kill_switch_active`, `kill_switch_source`
- `entry_permitted`, `risk_gate_kill_switch_active`
- `operator_authoritative_state`, `operator_state_reason`

Also present (rollup, not CONTRACT minimum): `status`, `blocked`, `degraded`, `requires_operator_attention`, `summary`.

**Partial / optional follow-ons (not payload gaps):**
- **4-section PLAN HTML IA** — fields render in HTML; explicit Section 1–4 layout per `incident_state_read_model_ops_cockpit_plan&#47;PLAN.md` may still be refined (display-only).
- **`safety_state` projection** — `src/ops/safety_state.py` exposes a **subset** of `incident_state` in `incident_signal_subset`; full contract field projection not required for observation.

**Still out of scope / unchanged:**
- Cockpit observation does **not** authorize Live, broker, exchange, scheduler, or runtime execution.
- Entry/risk/risk-hook authority split unchanged (see below).

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
- Hold incident-state ops-cockpit payload stable unless a concrete follow-up need arises (see `incident_state_read_model_ops_cockpit_closeout&#47;CLOSEOUT.txt`).
- Optional docs-only: sync downstream review artifacts if drift reappears.
- Optional bounded follow-ons (separate slices): 4-section HTML IA polish; `safety_state` full contract-field projection (read-only).
