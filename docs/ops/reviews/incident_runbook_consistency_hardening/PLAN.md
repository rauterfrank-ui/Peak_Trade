# INCIDENT RUNBOOK CONSISTENCY HARDENING PLAN

## Purpose
Harden incident / stop / freeze / rollback operator documentation as one docs-only consistency slice.

## Scope
- incident_stop_freeze_rollback
- risk_limit_breach
- rollback references
- kill-switch / incident-stop operator references
- no runtime mutation

## Intended Outcomes
- one clearer operator path for stop / freeze / rollback
- explicit references to current scripts and evidence capture paths
- risk_limit_breach no longer left as an unclear stub
- rollback and incident snapshot flow linked coherently

## Candidate Changes
1. update `docs/ops/runbooks/incident_stop_freeze_rollback.md`
2. expand `docs/ops/runbooks/risk_limit_breach.md`
3. align references to:
   - `scripts/ops/incident_stop_now.sh`
   - `scripts/ops/kill_switch_ctl.sh`
   - `scripts/ops/build_incident_snapshot.sh`
   - `docs/runbooks/ROLLBACK_PROCEDURE.md`

## Constraints
- exactly one PR
- docs only
- no paper/shadow/testnet disturbance

## Recommended Next Step
- implement the runbook consistency edits in this branch
