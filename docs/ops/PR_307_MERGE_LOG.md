# PR #307 — docs(ops): document README_REGISTRY guardrail for ops doctor

## Summary
PR #307 wurde gemerged am 2025-12-25 02:58:23 UTC.
Squash-Commit: d0e8daf — "docs(ops): document README_REGISTRY guardrail for ops doctor (#307)".
Branch: docs/ops-doctor-registry-guardrail (auto-gelöscht)

## Why
Dokumentiert die README_REGISTRY-Anforderung des Ops-Doctor-Registry-Checks, um Regressionen/Verwirrung zu vermeiden.

## Changes
- docs/ops/OPS_DOCTOR_README.md (+9)

## Verification
CI (alle PASS):
- ✅ tests (3.11) — 5m29s
- ✅ audit — 2m42s
- ✅ strategy-smoke — 1m9s
- ✅ Lint Gate — 7s
- ✅ Policy Critic Gate — 6s
- ✅ CI Health Gate — 1m5s
- ✅ Guard tracked files — 5s
- ✅ Render Quarto — 26s

Post-Merge (Ops Doctor / Pages):
- ✅ [docs.registry] README_REGISTRY.md found (3 docs referenced)
- ✅ Dashboard: https://rauterfrank-ui.github.io/Peak_Trade/

## Risk
Low (Docs-only).

## Operator How-To
- `ops doctor` ausführen
- Im Dashboard prüfen: PASS + [docs.registry] OK

## References
- PR #307
- Commit d0e8daf
