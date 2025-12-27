# PR #261 — Merge Log

**Title:** chore(ops): add stash triage helper (export-first)  
**Merged:** 2025-12-23  
**Commit:** `552c790`  
**Author:** rauterfrank-ui  
**PR URL:** https://github.com/rauterfrank-ui/Peak_Trade/pull/261

---

## Summary

PR #261 **chore(ops): add stash triage helper (export-first)** wurde erfolgreich gemerged.

- Squash-Commit: **552c790**
- Änderungen: **5 Dateien**, **+632 / -2**
- Ziel: Safe-by-default Stash-Triage inkl. Export, Session-Report und Tests.

---

## Why

Stashes sind häufige "Hygiene-Schulden" (Vergessen, Kontextverlust, riskante Drops).
Dieser PR liefert ein **standardisiertes, dokumentiertes und testbares** Stash-Handling:

- Export-first als Default
- Drop nur mit expliziter Bestätigung
- Durables Archiv-Format (Patch + Meta + Report)

---

## Changes

### New

- **`scripts/ops/stash_triage.sh`** (372 Zeilen)
  - `--list` / `--export-all` / `--filter "<keyword>"`
  - Export nach `docs/ops/stash_refs/` inkl. Patch + Meta + Session-Report
  - **Drop nur mit `--drop-after-export` + `--confirm-drop`**
  - Sourced `run_helpers.sh` (optional, mit Fallback)

- **`tests/ops/test_stash_triage_script.py`** (125 Zeilen)
  - 5 robuste Tests (CI-friendly, safe defaults)
  - Tests: help, list, export-all, drop-safety, custom-dir

- **`docs/ops/stash_refs/README.md`** (13 Zeilen)
  - Kurz-Doku zur Export-Struktur und Konventionen

### Updated

- **`docs/ops/STASH_HYGIENE_POLICY.md`** (+80 Zeilen)
  - Sektion "Automation (Ops Helper)" mit Beispielen / Warnings
  - Export-Format erklärt
  - Sicherheitsmechanismen dokumentiert

- **`docs/ops/README.md`** (+42 Zeilen)
  - Neue Sektion "🗂️ Stash Hygiene & Triage" + Links
  - Quick Start Beispiele
  - Features-Übersicht

---

## Verification

### CI (6/7 passed, 1 allowed fail)

**Passed:**
- ✅ CI Health Gate (weekly_core) — 1m8s
- ✅ Guard tracked files — 6s
- ✅ Render Quarto Smoke Report — 26s
- ✅ lint — 11s
- ✅ strategy-smoke — 1m9s
- ✅ tests (3.11) — 5m3s

**Allowed fail:**
- ⚠️ audit — fail (2m59s) — bekanntes Issue; Merge mit `--allow-fail audit`

### Post-Merge Checks (lokal)

- `bash -n scripts/ops/stash_triage.sh` ✅
- `uv run pytest -q tests/ops/test_stash_triage_script.py` ✅ (5/5 passed)
- `git stash list` → leer ✅
- Working directory clean, main synchronized ✅

---

## Risk

**Niedrig.**

- Keine Changes an produktiven Runtime-Pfaden.
- Tool ist safe-by-default, verhindert versehentliches Löschen durch Confirm-Gate.
- Dokumentation + Tests decken Kernpfade ab.
- Exit 2 bei unsicherer Nutzung (Drop ohne Confirm).

---

## Operator How-To

### Basics

```bash
# Help / Übersicht
scripts/ops/stash_triage.sh --help
scripts/ops/stash_triage.sh --list

# Export aller Stashes (safe: kein Drop)
scripts/ops/stash_triage.sh --export-all

# Export gefiltert (Keyword in stash message)
scripts/ops/stash_triage.sh --export-all --filter "knowledge"
```

### Danger Zone (Drop)

```bash
# Drop NUR nach Export + explicit confirm
scripts/ops/stash_triage.sh --export-all \
  --drop-after-export \
  --confirm-drop
```

**⚠️ WARNUNG:** Ohne `--confirm-drop` wird der Drop verweigert (Exit 2).

### Export-Struktur

```
docs/ops/stash_refs/
├── stash_ref_20251223-120000_0.patch    # git stash show -p
├── stash_ref_20251223-120000_0.md       # Ref, Message, Diffstat, Files
└── STASH_TRIAGE_SESSION_20251223-120000.md  # Session Report
```

---

## Follow-Up Actions

- [ ] Optional: Integriere Tool in regulären Ops-Workflow (z.B. monatlich)
- [ ] Optional: CI-Job für automatische Stash-Warnungen (falls > N Stashes)
- [ ] Optional: Knowledge-DB-Integration für Stash-Archiv-Suche

---

## References

- **Policy:** [STASH_HYGIENE_POLICY.md](STASH_HYGIENE_POLICY.md)
- **Tool:** [scripts/ops/stash_triage.sh](../../scripts/ops/stash_triage.sh)
- **Tests:** [tests/ops/test_stash_triage_script.py](../../tests/ops/test_stash_triage_script.py)
- **Ops README:** [README.md](README.md)

---

**Merge Method:** Squash  
**Branch Deleted:** ✅ Yes  
**Local Main Updated:** ✅ Yes
