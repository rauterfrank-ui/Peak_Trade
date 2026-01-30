# PR #222 — Merge Log

**Title:** feat(web): add merge+format-sweep workflow to ops hub  
**PR:** https://github.com/rauterfrank-ui/Peak_Trade/pull/222  
**Branch:** docs/ops-merge-format-sweep-nav  
**Squash Commit:** 9482e7e  
**Date (Europe/Berlin):** 2025-12-21  
**Risk:** 🟢 Low (additive router entry + test assertion update)

---

## Summary (Was wurde gemerged?)

Mit PR #222 wurde der neue **Merge + Format Sweep Workflow** in den Ops Workflow Hub integriert:

- **Workflow-Eintrag im Hub:** Neuer Workflow "Merge + Format Sweep" ist jetzt unter `/ops/workflows` sichtbar
- **2 Commands verfügbar:**
  - Standard: `PR_NUM=<nummer> .&#47;scripts&#47;workflows&#47;merge_and_format_sweep.sh`
  - Large-PR Simulation: `PR_NUM=<nummer> RUN_LARGE_SIM=1 LARGE_SIM_FILES=1250 .&#47;scripts&#47;workflows&#47;merge_and_format_sweep.sh`
- **3 Docs-Refs verlinkt:**
  - `docs/ops/WORKFLOW_MERGE_AND_FORMAT_SWEEP.md` (Runbook)
  - `docs/ops/CI_LARGE_PR_HANDLING.md` (CI-Handling)
  - `scripts/workflows/merge_and_format_sweep.sh` (Script)
- **README-Link:** Runbook ist im Guides-Abschnitt von `docs/ops/README.md` verlinkt

---

## Motivation (Warum?)

Der Merge+Format-Sweep Workflow wurde in PR #220 als Runbook dokumentiert und ist ein kritischer Ops-Workflow für sichere PR-Merges. Die Integration in den Ops Workflow Hub macht ihn:

- **One-Click discoverable:** Operatoren finden den Workflow direkt im Dashboard
- **Copy-paste ready:** Commands können direkt aus dem Hub kopiert werden
- **Dokumentiert:** Alle relevanten Docs (Runbook, CI-Handling, Script) sind verlinkt
- **Konsistent:** Folgt dem gleichen Pattern wie die anderen 4 Workflows im Hub

---

## Changes (Was wurde geändert?)

### Added

**1. Workflow-Definition in `src/webui/ops_workflows_router.py`:**
- Neuer Workflow-Eintrag mit ID `merge_and_format_sweep`
- Titel: "Merge + Format Sweep Workflow"
- 2 Commands (Standard + Large-PR Simulation)
- 3 Docs-Refs (Runbook, CI-Handling, Script)
- Kommentar aktualisiert: "4 core" → "5 core"

**2. README-Update in `docs/ops/README.md`:**
- Link zum Runbook im Guides-Abschnitt angepasst
- Stil: "Merge PRs safely + optional format sweep (pairs with...)"
- Verweist auf Script und CI-Large-PR-Handling-Doku

**3. Status-Overview in `docs/PEAK_TRADE_STATUS_OVERVIEW.md`:**
- Changelog-Eintrag bereits vorhanden (PR #220)

### Modified

**Tests in `tests/test_ops_workflows_router.py`:**
- Assertions aktualisiert: `== 4` → `== 5`
- Assertions aktualisiert: `>= 4` → `>= 5`
- Alle 5 Tests grün

---

## Verification (Wie wurde verifiziert?)

### CI (GitHub Actions)

- `lint`: ✅ pass (11s)
- `tests (3.11)`: ✅ pass  
- `audit`: ✅ pass  
- `CI Health Gate`: ✅ pass  
- `Quarto Smoke`: ❌ fail (non-blocking, wie erwartet)

### Lokal

```bash
# Ruff Check
ruff check .
# → All checks passed!

# Targeted Tests
python3 -m pytest tests/test_ops_workflows_router.py -v
# → 5 passed, 5 warnings
```

---

## Risk Assessment

**🟢 LOW RISK**

Begründung:
- **Additiv:** Kein Breaking Change, nur neuer Workflow-Eintrag
- **Read-only:** Ops Hub ist weiterhin read-only, keine Script-Ausführung
- **Getestet:** Alle Tests grün (5/5 Router-Tests)
- **Docs-only (größtenteils):** Nur Router-Definition + Test-Assertions erweitert
- **Konsistent:** Folgt dem Pattern der bestehenden 4 Workflows

---

## Operator How-To (Quick Usage)

### 1. Ops Hub öffnen

```bash
# Server starten
python3 -m uvicorn src.webui.app:app --reload --port 8000

# Browser öffnen
open http://localhost:8000/ops/workflows
```

### 2. Workflow finden

Im Ops Hub ist der Workflow jetzt als **erster Eintrag** sichtbar:
- **Titel:** Merge + Format Sweep Workflow
- **Beschreibung:** Standardisierter Merge-Prozess + optionaler Format-Sweep...
- **Commands:** 2 Copy-Buttons (Standard + Large-PR Simulation)
- **Docs:** 3 Links (Runbook, CI-Handling, Script)

### 3. Command kopieren & ausführen

```bash
# Standard-Merge + Format-Sweep
PR_NUM=123 ./scripts/workflows/merge_and_format_sweep.sh

# Mit Large-PR Simulation
PR_NUM=123 RUN_LARGE_SIM=1 LARGE_SIM_FILES=1250 \
  ./scripts/workflows/merge_and_format_sweep.sh
```

---

## Integration Chain (PR-Kette)

Dieser PR ist Teil einer 3-PR-Chain:

1. **PR #220** (`ef06550`) — docs(ops): add merge + format sweep workflow runbook  
   → Runbook erstellt (413 Zeilen, inkl. Quickstart, Scenarios, Troubleshooting, CI-Integration)

2. **PR #221** (`65a6065`) — docs(ops): wire merge+format-sweep runbook into indexes  
   → Runbook in `docs/PEAK_TRADE_STATUS_OVERVIEW.md` verlinkt (Abschnitt "Documentation & Governance")

3. **PR #222** (`9482e7e`) — feat(web): add merge+format-sweep workflow to ops hub  
   → Workflow in Ops Hub integriert (dieser PR)

**Status:** ✅ Chain vollständig abgeschlossen

---

## Follow-Up Tasks

- [x] Runbook erstellen (PR #220)
- [x] Runbook in Indexes verlinken (PR #221)
- [x] Workflow in Ops Hub integrieren (PR #222)
- [ ] Optional: Workflow-Usage-Tracking in Telemetrie (zukünftig)

---

## References

- PR: https://github.com/rauterfrank-ui/Peak_Trade/pull/222
- Squash Commit: `9482e7e`
- Related PRs: #220 (Runbook), #221 (Indexes)
- Test Coverage: `tests/test_ops_workflows_router.py` (5 tests)
- Runbook: `docs/ops/WORKFLOW_MERGE_AND_FORMAT_SWEEP.md`
- Script: `scripts/workflows/merge_and_format_sweep.sh`
- CI-Doku: `docs/ops/CI_LARGE_PR_HANDLING.md`

---

**Merge Operator:** Frank Rauter  
**Merge Date:** 2025-12-21  
**CI Status:** ✅ All Checks Passed (Quarto Smoke non-blocking)
