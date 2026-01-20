# PR #265 — feat(ops): add ops center (central operator entry point)

## Summary
PR #265 bringt den **Ops Center** als zentralen, safe-by-default Einstiegspunkt für Operator-Workflows.

## Why
Operator-Workflows waren verteilt über mehrere Skripte/Dokus. Der Ops Center vereinheitlicht Entry-Points (Status, PR-Review, Merge-Log-Referenz, Doctor) und bleibt dabei strikt nicht-destruktiv.

## Changes
- ✅ NEW: `scripts/ops/ops_center.sh` — zentraler Entry Point (help/status/pr/merge-log/doctor), robust bei fehlenden Tools
- ✅ NEW: `docs/ops/OPS_OPERATOR_CENTER.md` — vollständige Operator-Doku inkl. Troubleshooting
- ✅ NEW: `tests/ops/test_ops_center_smoke.py` — Smoke-Tests (passed)
- ✅ UPDATE: `docs/ops/README.md` — Ops Center prominent verlinkt

## Merge
- Branch: `feat/ops-center` → `main`
- PR: #265
- PR Commit: `0320103`
- Merge Commit (squash, main): `90f9a10`

## CI
PASSED (6/7):
- ✅ CI Health Gate (weekly_core) — 1m4s
- ✅ Guard tracked files — 5s
- ✅ Render Quarto Smoke Report — 28s + 31s
- ✅ lint — 12s
- ✅ strategy-smoke — 1m13s
- ✅ tests (3.11) — 5m8s

ALLOWED FAIL (1/7):
- ⚠️ audit — fail 3m4s — bekanntes Issue, via allow-fail Policy

## Verification (post-merge)
- `bash scripts&#47;ops&#47;ops_center.sh help` (exit 0)
- `bash scripts&#47;ops&#47;ops_center.sh status` (exit 0)
- `bash scripts&#47;ops&#47;ops_center.sh merge-log` (exit 0)
- `pytest -q tests&#47;ops&#47;test_ops_center_smoke.py` (pass)

## Risk
Low — additive Änderung, safe-by-default, keine destruktiven Aktionen.

## Operator How-To
- Daily: `scripts&#47;ops&#47;ops_center.sh status`
- PR review: `scripts&#47;ops&#47;ops_center.sh pr <NUM>`
- Health: `scripts&#47;ops&#47;ops_center.sh doctor`

## References
- `docs/ops/OPS_OPERATOR_CENTER.md`
- `docs/ops/README.md`
