# Merge Log — PR #342 — Ops Risk Hub Links + PR341 Merge Log

- PR: #342 — docs(ops): risk hub links + PR341 merge log
- Merge: 2025-12-25 → main
- Merge commit: d3891a2
- Source branch: docs/ops-risk-hub-link-pr341
- Diff: +56 / −0 (2 files)
- CI: 13 checks passed
- Label: documentation

## Summary
Dokumentations-PR: Fügt einen kompakten Merge-Log für PR #341 hinzu und verlinkt die Risk Gate Runbooks zentral aus dem Ops Hub (README).

## Why
Operator:innen sollen die Risk-Gates (VaR/Stress/Liquidity) schnell finden und PR #341 (Liquidity Gate v1) ist im Ops-Hub sauber nachvollziehbar dokumentiert.

## Changes
- ADD: `docs/ops/merge_logs/2025-12-25_pr-341_liquidity-gate-v1.md`
- UPDATE: `docs/ops/README.md` — Abschnitt „Risk & Safety Gates (Operator Hub)" + Links + Rollout-Hinweis

## Verification
- GitHub CI: 13 checks passed (docs-only Änderungen).

## Risk
LOW (Docs-only)

## Operator How-To
1) `docs/ops/README.md` → „Risk & Safety Gates (Operator Hub)"
2) Runbooks öffnen (VaR/Stress/Liquidity)
3) PR #341 Merge-Log lesen: `docs/ops/merge_logs/2025-12-25_pr-341_liquidity-gate-v1.md`

## References
- PR #342 (merged)
- PR #341
- Runbooks: `docs/risk/VAR_GATE_RUNBOOK.md`, `docs/risk/STRESS_GATE_RUNBOOK.md`, `docs/risk/LIQUIDITY_GATE_RUNBOOK.md`
- Roadmap: `docs/risk/RISK_LAYER_ROADMAP.md`
