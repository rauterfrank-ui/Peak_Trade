# Workflow Officer v0 – Minimal Implementation Slice

## Goal
A deterministic, read-only wrapper entrypoint that reuses existing helpers and emits a JSON report under `out/ops/workflow_officer/<ts>/`.

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
- no paper/shadow/evidence data writes outside dedicated `out/ops/workflow_officer/<ts>/`
- no LLM runtime authority
- no live execution authority

## Existing helpers to wrap first
- `src/ops/doctor.py`
- `scripts/ops/ops_doctor.sh`
- `scripts/ops/docker_desktop_preflight_readonly.sh`
- `scripts/ops/mcp_smoke_preflight.sh`
- `scripts/ops/analyze_failures.sh`
- `scripts/audit/check_error_taxonomy_adoption.py`
- `scripts/ops/docs_graph_triage.py`
- `scripts/ops/validate_docs_token_policy.py`

## v0 report contract
- `report.json`
- `events.jsonl`
- `stdout.log`
- `stderr.log`
- `manifest.json`

## Safety rules
- read-only by default
- only write below `out/ops/workflow_officer/<ts>/`
- never touch paper/shadow/evidence run directories
