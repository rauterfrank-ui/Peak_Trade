# AI Matrix Validator v1 (Governance)

This milestone establishes a single-source AI autonomy matrix and enforces drift prevention in CI.

## What shipped

- Authoritative matrix location:
  - `docs/governance/matrix/AI_AUTONOMY_LAYER_MAP_MODEL_MATRIX.md`
  - Redirect stub: `docs/governance/ai_autonomy/README.md`
- CI enforcement:
  - `lint_gate.yml` runs `bash scripts/governance/ai_matrix_consistency_gate.sh` on every PR
- Validator:
  - `src/governance/validate_ai_matrix_vs_registry.py`
  - P0: matrix↔registry drift checks + SoD + authoritative Reference enforcement + CI-friendly output
  - P1: matrix schema tokens + duplicate row detection + model existence + best-effort capability scope checks
  - P2: `make governance-gate` + `--explain` remediation hints
  - Help: `--help/-h`
- Local developer enablement:
  - `.githooks/pre-commit` gate on matrix/registry changes
  - Bootstrap: `./scripts/dev/bootstrap.sh` (sets `core.hooksPath=.githooks`)

## Tags

- `governance-ai-matrix-v1`
- `governance-ai-matrix-backlog-v1`
- `governance-ai-matrix-gate-passline-v1`
- `governance-ai-matrix-validator-p2-v1`
- `governance-ai-matrix-validator-help-v1`
- `governance-ai-matrix-validator-v1`
