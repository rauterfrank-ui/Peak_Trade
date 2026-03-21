# RISK LIMIT BREACH RUNBOOK

## Purpose
Operator runbook for risk-limit breach handling.

## Trigger
Use this runbook when a limit breach, hard risk denial, or operator-visible risk stop condition occurs.

## Immediate Operator Flow
1. stop new exposure increase
2. inspect current operator-visible state
3. decide whether incident-stop is required
4. use evidence capture before broader rollback decisions
5. escalate if risk posture remains unclear

## Current Operator Commands
- incident stop:
  `scripts&#47;ops&#47;incident_stop_now.sh`
- kill switch control:
  `scripts&#47;ops&#47;kill_switch_ctl.sh`
- incident snapshot:
  `scripts&#47;ops&#47;build_incident_snapshot.sh`

## Related Runbooks
- incident stop / freeze / rollback:
  `docs&#47;ops&#47;runbooks&#47;incident_stop_freeze_rollback.md`
- rollback procedure:
  `docs&#47;runbooks&#47;ROLLBACK_PROCEDURE.md`

## Evidence To Capture
- active mode
- breach condition or denial reason
- current operator-visible state
- whether incident-stop or kill-switch was used
- snapshot / artifact location
- follow-up decision

## Notes
- do not assume incident-stop and kill-switch are the same signal
- prefer conservative operator posture under ambiguity
