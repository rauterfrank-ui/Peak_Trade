# MERGE LOG — PR #736 — docs(ops): reintegrate legacy workflow notes into current frontdoor

**PR:** https://github.com/rauterfrank-ui/Peak_Trade/pull/736  
**Merged (UTC):** 2026-01-14T19:47:07Z  
**Merge Commit:** `4e0f7be3`  
**Scope:** docs-only  
**Risk:** LOW  

---

## Zusammenfassung
- Legacy Workflow Notes (Stand 03.12.2025) wurden **KEEP EVERYTHING**-konform als stabiler Docs-Asset archiviert und in die Navigation integriert.
- Ergebnis: historische Workflow-Notizen sind **auffindbar, verlinkbar und gates-kompatibel** (Token Policy / Reference Targets).

## Warum
- Es existierte Legacy-Workflow-Kontext (Dec 2025), der für Chat-/Ops-Kontinuität relevant ist, aber nicht als „stabiler, verlinkbarer“ Asset im aktuellen Setup verankert war.
- Ziel war **Reintegration ohne Semantik-Änderung** (KEEP EVERYTHING) und ohne neue Docs-Gate-Risiken.

## Änderungen
**Geändert**
- `docs/WORKFLOW_FRONTDOOR.md` — Frontdoor-Link auf archivierte Legacy Notes ergänzt.
- `WORKFLOW_RUNBOOK_OVERVIEW_2026-01-12.md` — Quick-Reference um Runbook-Link erweitert (PR #736 Operator Runbook).
- `docs/ops/runbooks/README.md` — Runbooks Index um PR #736 Operator Runbook ergänzt.
- `docs/ops/runbooks/RUNBOOK_PR736_CI_SNAPSHOT_AUTOMERGE_POST_MERGE_VERIFY_CURSOR_MULTI_AGENT.md` — PR #736 Operator Runbook (CI Snapshot → Auto-Merge → Post-Merge Verify).

**Neu**
- `docs/ops/archives/Peak_Trade_WORKFLOW_NOTES_2025-12-03.md` — Canonical Legacy Snapshot (KEEP EVERYTHING) + additiver Header + Appendix.
- `docs/ops/runbooks/RUNBOOK_LEGACY_WORKFLOW_NOTES_REINTEGRATION_CURSOR_MULTI_AGENT.md` — Operator Runbook für die Reintegration (snapshot-only, token-policy-safe).

---

## Verifikation
**CI (PR #736) — Snapshot**
- Required checks: **PASS** (10/10)
- Optional signals:
  - Docs Token Policy Gate: **FAIL** (non-required signal im PR-Kontext)
  - Cursor Bugbot: PASS/INFO (non-required)

**Lokal — Snapshot-only**

```bash
# Pre-Flight
cd /Users/frnkhrz/Peak_Trade 2>/dev/null || cd "$HOME/Peak_Trade" 2>/dev/null || pwd
pwd
git rev-parse --show-toplevel
git status -sb
git log -1 --oneline

# Docs Gates Snapshot für den PR-736 Merge-Range:
# Base = Parent von `4e0f7be3` (hier: 86137af5)
bash scripts/ops/pt_docs_gates_snapshot.sh --changed --base 86137af5
```

- Ergebnis (lokal): **PASS** (Docs Token Policy / Docs Reference Targets / Docs Diff Guard Policy)

---

## Risiko
**Risk:** LOW  
**Begründung**
- Docs-only, additive Änderungen; Legacy Notes bleiben vollständig erhalten (KEEP EVERYTHING).
- Gate-sensibler Content (Inline-Code Tokens mit “/”) wurde policy-konform behandelt (real vs illustrative).

## Operator How-To
- Öffne Frontdoor: `docs/WORKFLOW_FRONTDOOR.md` → Legacy Section.
- Nutze die Reintegration als Vorlage: `docs/ops/runbooks/RUNBOOK_LEGACY_WORKFLOW_NOTES_REINTEGRATION_CURSOR_MULTI_AGENT.md`.
- Für PR-Abschluss: `docs/ops/runbooks/RUNBOOK_PR736_CI_SNAPSHOT_AUTOMERGE_POST_MERGE_VERIFY_CURSOR_MULTI_AGENT.md` (snapshot-only).

## Referenzen
- PR: https://github.com/rauterfrank-ui/Peak_Trade/pull/736
- Merge Commit: `4e0f7be3`
- Canonical Legacy Notes: `docs/ops/archives/Peak_Trade_WORKFLOW_NOTES_2025-12-03.md`
- Frontdoor: `docs/WORKFLOW_FRONTDOOR.md`
