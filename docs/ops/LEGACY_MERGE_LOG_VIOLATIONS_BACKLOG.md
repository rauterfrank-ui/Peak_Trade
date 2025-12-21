# Legacy Merge Log Violations Backlog

**Status:** legacy-only (non-blocking CI guard aktiv)  
**Letzter Audit-Run:** 2025-12-21  
**Gesamt-Violations:** 27 von 28 Logs haben Violations

## Ziel

- **Forward-only Policy:** Neue Merge Logs müssen dem kompakten Standard entsprechen
- Legacy-Logs werden nur nach Bedarf/priorisiert migriert
- CI Guard ist non-blocking, um bestehende Workflows nicht zu blockieren

## Standard-Requirements

Alle neuen `PR_*_MERGE_LOG.md` Dateien müssen folgende Requirements erfüllen:

### Header-Felder (Pflicht)
- `**Title:**` — PR-Titel
- `**PR:**` — PR-Nummer (#XXX)
- `**Merged:**` — Merge-Datum (YYYY-MM-DD)
- `**Merge Commit:**` — Commit-Hash (kurz)
- `**Branch:**` — Branch-Name (deleted/aktiv)
- `**Change Type:**` — Art der Änderung (additiv, breaking, etc.)

### Sections (Pflicht)
- `## Summary` — Kurze Zusammenfassung (2-3 Sätze)
- `## Motivation` — Warum diese Änderung?
- `## Changes` — Was wurde geändert? (strukturiert)
- `## Files Changed` — Dateiliste mit Checksums
- `## Verification` — CI-Checks, lokale Tests
- `## Risk Assessment` — Risikobewertung

### Kompaktheit
- **< 200 Zeilen** (Richtwert)
- Fokus auf Essentials, keine ausschweifenden Details

## Hinweise

- **Source of Truth:** `scripts/audit/check_ops_merge_logs.py`
- **CI Guard:** `.github/workflows/audit.yml` (non-blocking step)
- **Reports:** `reports/ops/merge_log_violations_*.txt`

## Top Violations (nach Schwere)

### Kategorie 1: Komplett inkomplette Logs (>10 Violations)
- `PR_112_MERGE_LOG.md` — 11 Violations
- `PR_154_MERGE_LOG.md` — 11 Violations
- `PR_186_MERGE_LOG.md` — 11 Violations
- `PR_87_MERGE_LOG.md` — 12 Violations
- `PR_90_MERGE_LOG.md` — 12 Violations
- `PR_93_MERGE_LOG.md` — 11 Violations

### Kategorie 2: Fehlende Header + Sections (9-10 Violations)
- `PR_110_MERGE_LOG.md` — 10 Violations
- `PR_114_MERGE_LOG.md` — 9 Violations
- `PR_116_MERGE_LOG.md` — 10 Violations
- `PR_121_MERGE_LOG.md` — 10 Violations
- `PR_136_MERGE_LOG.md` — 9 Violations
- `PR_161_MERGE_LOG.md` — 10 Violations
- `PR_180_MERGE_LOG.md` — 10 Violations
- `PR_182_MERGE_LOG.md` — 10 Violations
- `PR_185_MERGE_LOG.md` — 9 Violations
- `PR_193_MERGE_LOG.md` — 9 Violations
- `PR_199_MERGE_LOG.md` — 10 Violations
- `PR_201_MERGE_LOG.md` — 10 Violations
- `PR_204_MERGE_LOG.md` — 9 Violations
- `PR_76_MERGE_LOG.md` — 9 Violations
- `PR_78_MERGE_LOG.md` — 9 Violations
- `PR_80_MERGE_LOG.md` — 9 Violations
- `PR_85_MERGE_LOG.md` — 9 Violations

### Kategorie 3: Teilweise konform (7-8 Violations)
- `PR_143_MERGE_LOG.md` — 8 Violations
- `PR_183_MERGE_LOG.md` — 7 Violations
- `PR_195_MERGE_LOG.md` — 8 Violations
- `PR_197_MERGE_LOG.md` — 8 Violations

### Kategorie 4: Konform ✅
- `PR_206_MERGE_LOG.md` — 0 Violations (Referenz-Implementierung)

## Backlog-Strategie

1. **Forward-only:** Alle neuen PRs (ab PR #207) müssen konform sein
2. **Legacy-Migration:** Optional, priorisiert nach Bedarf
3. **Templates:** `PR_206_MERGE_LOG.md` als Vorlage für neue Logs verwenden
4. **Automation:** CI Guard warnt bei Violations, blockiert aber nicht

## Migration-Priorität (optional)

Falls Legacy-Migration gewünscht:

1. **Hoch:** Kategorie 1 (komplett inkomplett)
2. **Mittel:** Kategorie 2 (9-10 Violations)
3. **Niedrig:** Kategorie 3 (7-8 Violations)

## Referenz

- **Template:** `docs/ops/PR_206_MERGE_LOG.md`
- **Audit-Tool:** `scripts/audit/check_ops_merge_logs.py`
- **Workflow:** `scripts/workflows/pr_merge_with_ops_audit.sh`
