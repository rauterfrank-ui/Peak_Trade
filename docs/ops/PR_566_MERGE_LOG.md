# PR #566 — Merge Log

**PR:** https://github.com/rauterfrank-ui/Peak_Trade/pull/566  
**Merge-Commit (main):** `842518c7`  
**Datum:** 2026-01-05  
**Scope:** Tooling/Docs only (AI-Ops Eval Toolchain)  
**Governance:** no-live, operator-controlled, `src/` untouched

## Summary
- Audit-stabile AI-Ops Toolchain für Cursor Multi-Agent + promptfoo evals unter **canonical Node v25.2.1**.
- Behebung einer promptfoo/SQLite-Instabilität durch Pin auf **promptfoo 0.120.8** (statt 0.95.0).
- Vollständige Evidenz/Closeout-Dokumentation (Skip-Path + Full-Eval, Telemetry, Governance Compliance).

## Why
- Root Cause: **promptfoo 0.95.0** in Kombination mit **Node v25.2.1** führte zu **SQLite Foreign Key constraint** Fehlern (instabiler Eval-Runner).
- Ziel: reproduzierbare, auditierbare Evaluationsläufe ohne Eingriff in Trading-Logik.

## Changes
- `scripts/aiops/run_promptfoo_e
  - promptfoo Pin im Runner aktualisiert: **0.95.0 → 0.120.8**
  - Telemetry: SHA/Node/npx/promptfoo/timestamps/config-path (audit-grade)
  - Graceful Skip: fehlender `OPENAI_API_KEY` ⇒ **Exit 0**, keine promptfoo-artifacts
- `docs/ai/AI_EVALS_RUNBOOK.md`
  - Runbook/Operator-Workflow aktualisiert (Pre-Flight, Governance Notes, Runner-Verhalten)
- `docs/ai/AI_EVALS_SCOREBOARD.md`
  - Scoreboard-Struktur/Guidance aktualisiert (Evals nachvollziehbar dokumentierbar)
- `docs/ops/WORKTREE_RESCUE_SESSION_20260105_CLOSEOUT.md`
  - „Baseline (Operational Acceptance) — 2026-01-05"
  - Post-Update State inkl. Evidenz (Skip-Path + Full-Eval)

## Verification
- **Skip-Path (no key):** `OPENAI_API_KEY` fehlt ⇒ Runner beendet **Exit 0**, keine promptfoo artifacts, Telemetry vorhanden.
- **Full Eval (with key):** dokumentiert im Closeout (erfolgreicher Run; PASS/FAIL Evidence je Governance-Testcase).
- CI: keine Python-/`src/`-Änderungen; PR lief durch Standard-Gates (Policy Critic, Lint, Docs Guard, Python MaRisk
- **Low (🟢):** ausschließlich tooling/docs; keine Änderungen in `src/`, keine Risk/Portfolio/Strategy configs.
- Kein Live-Trading Enablement; Governance bleibt **operator-controlled**.

## Operator How-To
- Canonical Node sicherstellen (Repo hat `.nvmrc`):
  - `node -v` muss zur canonical Version passen (v25.2.1).
- Eval Runner:
  - `scripts/aiops/run_promptfoo_eval.sh`
  - Optional `OPENAI_API_KEY` setzen für Full-Eval; ohne Key ist Skip-Path erwartetes Verhalten.

## References
- PR #566: https://github.com/rauterfrank-ui/Peak_Trade/pull/566
- Closeout: `docs/ops/WORKTREE_RESCUE_SESSION_20260105_CLOSEOUT.md`
- Runner: `scripts/aiops/run_promptfoo_eval.sh`
