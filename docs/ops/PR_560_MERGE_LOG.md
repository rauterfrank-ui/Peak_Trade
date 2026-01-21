# PR #560 — Cursor Multi-Agent Integration V1 (AI-Ops Toolchain)

## Summary
Cursor Multi-Agent v1 als AI-Ops Toolchain in Peak_Trade integriert (governance-first, audit-stabil). Keine Änderungen an Trading-Logik, keine autonome Live-Execution.

## Why
Operator-Workflow in Cursor standardisieren (Rules + Slash-Commands) und Eval-Skeleton (promptfoo) für reproduzierbare, auditierbare Qualitätssicherung etablieren.

## Changes
- Cursor Rules: Governance + Delivery Contract (`.cursor&#47;rules&#47;peak-trade-*`)
- Cursor Commands: `/pt-preflight`, `/pt-plan`, `/pt-split`, `/pt-verify`, `/pt-merge-log`, `/pt-eval`
- Evals: `evals/aiops/` promptfoo Skeleton, `evals/aiops/testcases/` vereinheitlicht
- Docs: Canonical Runbook unter `docs/ops/runbooks/`, Redirect Stub in `docs/ai/`

## Verification
- Cursor Restart → `/pt-` zeigt 6 Commands
- `/pt-preflight` ausgeführt
-grün (PR merge-ready)

## Risk
LOW — Tooling/Doku/Evals-only. Keine `src/` Änderungen.

## Merge
- PR: #560
- Merge-Methode: Squash
- Main Commit: `13d94ed1`
