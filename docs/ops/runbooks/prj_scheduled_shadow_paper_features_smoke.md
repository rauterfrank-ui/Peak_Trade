# PR-J — Scheduled Shadow/Paper Smoke with Feature Flags (Artifacts + Evidence)

## Goal
Run a deterministic scheduled smoke that:
- Executes a **shadow session** (dry/replay) and **paper session** (dry/replay)
- Injects operator wiring feature flags:
  - double-play specialists
  - dynamic leverage (cap 50×)
- Exports a compact JSON summary artifact + an evidence pack with validation token.

## Safety
- **No live execution**. Uses existing shadow/paper runners only.
- Feature flags only affect `details`/sizing hints, not eligibility.

## Outputs (uploaded as artifacts)
- `out/ops/prj_smoke/<run_id>/summary.json`
- `out/ops/prj_smoke/<run_id>/shadow/` (run outputs)
- `out/ops/prj_smoke/<run_id>/paper/` (run outputs)
- Evidence pack: `out/ops/evidence_packs/pack_prj_smoke_<run_id>/manifest.json` + VALIDATION_OK

## Config
Workflow supports:
- `PT_PRJ_FEATURES_SMOKE_ENABLED=true|false` (repo variable)
- manual dispatch inputs: enabled/armed/confirm_present + allow flags, strength, switch_score
