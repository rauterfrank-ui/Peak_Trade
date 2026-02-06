# AI Matrix Gate — TODO / Backlog

Scope: Improve `src/governance/validate_ai_matrix_vs_registry.py` and the CI gate integration to be stricter, more informative, and future-proof.

## P0 — Fail-closed correctness (block merges on drift)

- [ ] Parse the matrix MD table and cross-check against `config/model_registry.toml`:
  - Layer IDs present (L0..L6)
  - `autonomy`, `primary`, `fallback`, `critic` per layer match exactly
  - Enforce Separation-of-Duties: `critic != primary` where applicable
- [ ] Validate the registry reference is authoritative:
  - `Reference:` points to `docs/governance/matrix/AI_AUTONOMY_LAYER_MAP_MODEL_MATRIX.md`
  - No remaining references to `docs/governance/ai_autonomy/AI_AUTONOMY_LAYER_MAP_MODEL_MATRIX.md`
- [ ] Make validator outputs CI-friendly:
  - Single-line `[FAIL] CODE: message` entries
  - Summary line with count of violations
  - Exit codes: `0=pass`, `2=fail` (reserve `1` for unexpected error)

## P1 — Schema/structure checks (reduce footguns)

- [ ] Matrix schema guardrails:
  - Required columns exist in the MD table header
  - No duplicate layer rows
  - Models referenced are defined in `model_registry.toml` (or a machine-readable model list)
- [ ] Capability scopes cross-check:
  - If a layer declares a scope file, ensure it exists and contains the matching `layer_id`
  - Optionally enforce allowed tools vs. scope policy (web/files)

## P2 — Developer ergonomics

- [ ] Add `make governance-gate` target that runs:
  - ruff format check (optional)
  - `bash scripts/governance/ai_matrix_consistency_gate.sh`
- [ ] Add `--explain` mode to print remediation suggestions per violation
- [ ] Unit tests for validator:
  - Missing headers
  - Drifted primary model
  - SoD violation
  - Missing scope file

## Notes

- CI wiring: `lint_gate.yml` runs `bash scripts/governance/ai_matrix_consistency_gate.sh` on every PR.
- Current validator is minimal (presence/reference). The above upgrades make it a real single-source-of-truth enforcer.
