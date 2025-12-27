# Merge Log — PR #342 — Ops Risk Hub Links + PR341 Merge Log

- PR: #342 — docs(ops): risk hub links + PR341 merge log
- Merge: 2025-12-25 → main
- Merge commit: d3891a2
- Source branch: docs/ops-risk-hub-link-pr341
- Diff: +56 / −0 (2 files)
- CI: 13 checks passed
- Label: documentation

## Summary
Docs-only PR: Fügt einen kompakten Merge-Log für PR #341 hinzu und verlinkt die Risk Gate Runbooks zentral aus dem Ops Hub (README).

## Why
Operator:innen sollen die Risk-Gates (VaR/Stress/Liquidity) schnell finden; außerdem ist PR #341 (Liquidity Gate v1) im Ops-Hub nachvollziehbar dokumentiert.

## Changes
- ADD: `docs/ops/merge_logs/2025-12-25_pr-341_liquidity-gate-v1.md`
  - Kompakter Merge-Log für PR #341 (Summary/Why/Changes/Verification/Risk/Operator How-To/Refs)
- UPDATE: `docs/ops/README.md`
  - Neuer Abschnitt „Risk & Safety Gates (Operator Hub)" mit Links:
    - VaR Gate Runbook
    - Stress Gate Runbook
    - Liquidity Gate Runbook
    - Risk Layer Roadmap
  - Hinweis auf disabled-by-default Rollout (Paper/Shadow → Monitoring → Live)

## Verification
- GitHub CI: 13 checks passed (docs-only Änderungen).

## Risk
LOW
- Docs-only (keine Code-/Runtime-Änderungen)
- Verbessert Auffindbarkeit & Operator-Workflow, keine Systemverhaltensänderung

## Operator How-To
1) Ops Hub öffnen: `docs/ops/README.md` → Abschnitt „Risk & Safety Gates (Operator Hub)"
2) Runbooks direkt aufrufen (VaR/Stress/Liquidity)
3) Merge-Log für Liquidity Gate v1 nachlesen:
   `docs/ops/merge_logs/2025-12-25_pr-341_liquidity-gate-v1.md`

## References
- PR #342 (merged) — docs(ops): risk hub links + PR341 merge log
- PR #341 — Liquidity Gate v1
- Runbooks: `docs/risk/VAR_GATE_RUNBOOK.md`, `docs/risk/STRESS_GATE_RUNBOOK.md`, `docs/risk/LIQUIDITY_GATE_RUNBOOK.md`
- Roadmap: `docs/risk/roadmaps/RISK_LAYER_ROADMAP.md`
