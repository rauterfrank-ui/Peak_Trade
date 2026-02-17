# P91 — Shadow Soak Audit v1

Goal: Read-only audit summary over a supervisor run directory (ticks), producing a JSON-friendly report.

Non-goals: No live/record, no execution, no model calls.

## Output location
P91 evidence (`p91_shadow_soak_audit_snapshot_*`, `P91_AUDIT_SNAPSHOT_DONE_*.txt`) lives under `out&#47;ops&#47;`. The supervisor folder `out&#47;ops&#47;online_readiness_supervisor&#47;` holds only `run_*` and LAUNCHD logs.
