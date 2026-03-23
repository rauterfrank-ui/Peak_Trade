# Workflow Officer v0 – Minimal Implementation Slice

## Goal
A deterministic, read-only wrapper entrypoint that reuses existing helpers and emits a JSON report under `out&#47;ops&#47;workflow_officer&#47;<ts>&#47;`.

## Included in v0
- CLI entrypoint
- modes: `audit`, `preflight`, `advise`
- profiles: `docs_only_pr`, `ops_local_env`, `live_pilot_preflight`
- subprocess wrapping of existing scripts/tools
- normalized JSON report
- optional JSONL events
- non-zero exit on hard failures only

## Explicitly excluded
- no auto-remediation
- no mutation of repo state
- no paper/shadow/evidence data writes outside dedicated `out&#47;ops&#47;workflow_officer&#47;<ts>&#47;`
- no LLM runtime authority
- no live execution authority

## Existing helpers to wrap first
- `src/ops/doctor.py`
- `scripts&#47;ops&#47;ops_doctor.sh`
- `scripts&#47;ops&#47;docker_desktop_preflight_readonly.sh`
- `scripts&#47;ops&#47;mcp_smoke_preflight.sh`
- `scripts&#47;ops&#47;analyze_failures.sh`
- `scripts&#47;audit&#47;check_error_taxonomy_adoption.py`
- `scripts&#47;ops&#47;docs_graph_triage.py`
- `scripts&#47;ops&#47;validate_docs_token_policy.py`

## v0 report contract
- `report.json`
- `events.jsonl`
- `stdout.log`
- `stderr.log`
- `manifest.json`

## Safety rules
- read-only by default
- only write below `out&#47;ops&#47;workflow_officer&#47;<ts>&#47;`
- never touch paper/shadow/evidence run directories
