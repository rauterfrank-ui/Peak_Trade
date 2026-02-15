# P71 — Online Readiness Health Gate v1

Goal: one deterministic PASS/FAIL gate for **paper/shadow** readiness based on P64→P63→P62→P61 pipeline.
- live/record: **hard-blocked** (PermissionError)
- deny-by-default routing: PASS only if ai_mode ∈ {disabled, shadow} and allowlist behavior is consistent.

Entrypoints:
- Python: `src.ops.p71.run_online_readiness_health_gate_v1`
- Bash: `scripts/ops/p71_health_gate_v1.sh`

Evidence:
- `p71_health_gate_report.json`
- `p71_health_gate_manifest.json`
