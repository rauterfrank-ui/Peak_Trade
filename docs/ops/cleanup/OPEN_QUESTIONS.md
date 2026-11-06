# Open Questions — Repo Cleanup (Plan Review)

**Zweck:** Alles, was vor dem Merge der Execution (PR2) nochmal geprüft/abgesegnet werden soll.

**Status:** Plan-only PR (PR1) — Keine Änderungen ausgeführt, nur geplant.

---

## 1) Delete-Entscheidungen

### Geplante Deletes (3 Dateien) — Status: ✅ Ausgeführt in PR #367

| Datei | Grund | Evidenz | Status |
|-------|-------|---------|--------|
| `run_regime_experiments.sh` | Dublette (existiert in `archive&#47;legacy_scripts&#47;`) | rg: 6 hits (nur docs/archive refs) | ✅ Deleted |
| `REQUIRED_CHECKS_DRIFT_GUARD_v1_OPERATOR_NOTES.md` | Dublette (docs/ops/ ist source of truth) | rg: 20 hits → konsolidieren | ✅ Deleted |
| `gitignore` | Obsolet (`.gitignore` existiert) | rg: 0 hits | ✅ Deleted |

**Fragen:**
- [ ] Sind alle Deletes eindeutig unreferenziert und durch bessere Source-of-Truth ersetzt?
- [ ] Sollte `REQUIRED_CHECKS_DRIFT_GUARD_v1_OPERATOR_NOTES.md` archiviert statt gelöscht werden?
- [ ] Gibt es weitere Deletes, die historischen/operativen Wert haben könnten?

---

## 2) Konsolidierung / Source-of-Truth

### Identified Duplicates

1. **`REQUIRED_CHECKS_DRIFT_GUARD_v1_OPERATOR_NOTES.md`**
   - Root vs `docs/ops/REQUIRED_CHECKS_DRIFT_GUARD_v1_OPERATOR_NOTES.md`
   - **Differ!** Nicht identisch
   - **Plan:** Konsolidieren → docs/ops/ (source of truth), root löschen

2. **`config.toml`**
   - Root vs `config/config.toml`
   - **Differ!** Root ist "simplified" version
   - **Plan:** Beide behalten (unterschiedlicher Zweck)

**Fragen:**
- [ ] Welche Version von `REQUIRED_CHECKS_DRIFT_GUARD_v1_OPERATOR_NOTES.md` ist aktueller?
- [ ] Müssen wir die Root `config.toml` besser dokumentieren (warum zwei Versionen)?
- [ ] Gibt es weitere Dubletten, die wir übersehen haben?

---

## 3) Struktur- & Namenskonventionen

### Neue Ordner-Struktur (geplant)

```
docs/
├── architecture/        # NEU: ADRs & Design
├── dev/knowledge/       # NEU: Developer Guides
├── features/psychology/ # NEU: Feature-spezifisch
├── ops/reports/         # NEU: Implementation Reports
├── ops/reports/phases/  # NEU: Phase Reports
└── learning_promotion/  # NEU: Feature Changelogs

scripts/
├── run/                 # NEU: Runner Scripts
└── utils/               # NEU: Utility Scripts
```

**Fragen:**
- [ ] Passt die neue Ordnerstruktur zur Peak_Trade-Philosophie?
- [ ] Sind die Namen konsistent und selbsterklärend?
- [ ] Sollten wir `docs/dev/` anders nennen (z.B. `docs&#47;developer&#47;`)?
- [ ] Ist `scripts/run/` vs `scripts/ops/` klar genug abgegrenzt?

---

## 4) Docs-Link-Integrität

### Geplante Reference-Updates

- `README_REGISTRY.md` → alle Pfade aktualisieren
- `docs/ops/README.md` → Risk Layer Roadmap Pfad
- Root `README.md` → potentiell "Repository Structure" Sektion

**Fragen:**
- [ ] Wurden alle relativen Links identifiziert und aktualisiert?
- [ ] Gibt es "public entrypoints" (Root README), die angepasst werden müssen?
- [ ] Sollten wir einen automated link checker einführen?
- [ ] Wie gehen wir mit external links um (z.B. zu GitHub Issues)?

---

## 5) CI/Workflows/Tooling

### Potential Impact

- `.github/workflows/` könnte hardcoded Pfade haben
- `scripts/ops/` Scripts könnten auf verschobene Dateien referenzieren
- `Makefile` könnte Pfade enthalten

**Fragen:**
- [ ] Gibt es Workflows/Checks, die neue Pfade erwarten?
- [ ] Gibt es path-filter / required checks, die angepasst werden müssen?
- [ ] Sollten wir ein "post-cleanup smoke test" definieren?
- [ ] Wie testen wir, dass alle Scripts nach dem Move noch funktionieren?

---

## 6) Reports/Artefakte

### Current State

- `reports/` enthält viele `.tsv`, `.md`, generierte Artefakte
- `.gitignore` hat bereits: `/reports/`
- Aber einige Reports sind committed (z.B. audit reports)

**Fragen:**
- [ ] Welche Inhalte unter `reports/` sind "tracked by design" vs "generated and ignored"?
- [ ] Sollten wir ein `reports&#47;README.md` erstellen (was ist committed, was nicht)?
- [ ] Ist `.gitignore` vollständig (keine Dateileichen)?
- [ ] Sollten committed Reports in `docs/` statt `reports/` liegen?

---

## 7) Archive-Policy

### Current Archive

- `archive&#47;full_files_stand_02.12.2025&#47;`
- `archive&#47;legacy_docs&#47;`
- `archive&#47;legacy_scripts&#47;`
- `archive&#47;PeakTradeRepo&#47;` (komplett altes Repo!)

**Fragen:**
- [ ] Ist `archive&#47;PeakTradeRepo&#47;` noch nützlich? (sehr groß)
- [ ] Sollten wir eine Retention-Policy definieren (z.B. "Archive older than 1 year → review")?
- [ ] Gibt es Dateien, die wir löschen statt archivieren sollten?
- [ ] Brauchen wir ein "Archive-Index" mit Begründungen?

---

## 8) Breaking Changes / Migration

### Risk Assessment

- **Code:** ✅ Keine Änderungen in `src/` oder `tests/`
- **Imports:** ✅ Keine Python-Imports geändert
- **Scripts:** ⚠️ Pfade ändern sich (aber Scripts nutzen meist relative Pfade)
- **Docs:** ⚠️ Links können brechen

**Fragen:**
- [ ] Gibt es Scripts, die absolute Pfade zu verschobenen Dateien nutzen?
- [ ] Gibt es Bookmarks/Wiki-Links/External-Refs, die wir aktualisieren müssen?
- [ ] Sollten wir ein "Migration Guide" für das Team erstellen?
- [ ] Wie kommunizieren wir die Änderungen (Slack, Meeting, Email)?

---

## 9) Validation-Strategie

### Planned Checks

- `python -m compileall src` → Python-Syntax
- `ruff check .` → Linter
- `pytest` → Tests
- Spot-check: wichtige Doc-Links

**Fragen:**
- [ ] Reicht die Validation oder brauchen wir mehr?
- [ ] Sollten wir ein "Smoke-Test-Script" erstellen?
- [ ] Wie prüfen wir Doc-Link-Integrität automatisch?
- [ ] Sollte CI einen "structure health check" bekommen?

---

## 10) Rollback-Plan

### If Things Go Wrong

- Branch: `chore/repo-cleanup-structured-20251227` kann gelöscht werden
- Oder: `git reset --hard a4850c66` (Base Commit)
- Safety Snapshot dokumentiert in `SAFETY_SNAPSHOT.md`

**Fragen:**
- [ ] Ist der Rollback-Plan ausreichend dokumentiert?
- [ ] Sollten wir ein Backup-Tag erstellen vor dem Merge?
- [ ] Wie schnell können wir rollen-back wenn Issues auftauchen?

---

## 11) Follow-up Tasks (nach Merge)

### Identified Follow-ups

1. `docs/README.md` Navigation-Hub erstellen
2. `archive&#47;PeakTradeRepo&#47;` evaluieren
3. Weitere root-level docs in Subfolder sortieren (falls noch welche)
4. Automated link checker einführen

**Fragen:**
- [ ] Welche Follow-ups sind P0 (must have) vs P1 (nice to have)?
- [ ] Sollten wir Issues für Follow-ups erstellen?
- [ ] Wer ist Owner für Follow-up-Implementierung?

---

## 12) Team Communication

### Communication Plan

- [ ] PR-Review mit Team (walk through CLEANUP_PLAN.md)
- [ ] Neue Struktur vorstellen (REPO_STRUCTURE (wird in PR2 erzeugt))
- [ ] Bookmarks aktualisieren lassen
- [ ] Wiki-Links aktualisieren (falls vorhanden)

**Fragen:**
- [ ] Wie kommunizieren wir die Änderungen am besten?
- [ ] Brauchen wir ein Meeting oder reicht asynchron (Slack)?
- [ ] Sollten wir ein "Structure-Guide Video" machen?

---

## 13) Config-Konsolidierung

### `config.toml` Situation

- Root: "simplified version" (871 Zeilen)
- `config/config.toml`: "full version" (1499 Zeilen)

**Fragen:**
- [ ] Ist die Rolle von Root `config.toml` klar dokumentiert?
- [ ] Sollten beide in `config/README.md` erklärt werden?
- [ ] Gibt es Verwechslungsgefahr?
- [ ] Könnte man sie umbenennen (z.B. `config.simplified.toml`)?

---

## 14) Documentation Quality

### New Docs Created

- `REPO_STRUCTURE (wird in PR2 erzeugt)` (400+ Zeilen)
- `archive&#47;README.md`
- `config/README.md`

**Fragen:**
- [ ] Ist die Doku verständlich für neue Team-Mitglieder?
- [ ] Gibt es zu viel oder zu wenig Detail?
- [ ] Sollten wir Examples/Screenshots hinzufügen?
- [ ] Ist die Doku wartbar (wird sie aktualisiert wenn sich Struktur ändert)?

---

## 15) Long-term Maintenance

### Keeping Repo Clean

**Fragen:**
- [ ] Wie verhindern wir, dass Root-Level wieder voll wird?
- [ ] Sollten wir einen CI-Check für "no root-level docs" haben?
- [ ] Sollten wir eine "File-Platzierungs-Policy" im CONTRIBUTING.md festhalten?
- [ ] Wie oft sollten wir Cleanup-Reviews machen (jährlich, quarterly)?

---

## Summary

**Total Questions:** 15 Kategorien, ~50+ einzelne Fragen

**Kritische Fragen (vor PR2):**
1. Delete-Evidenz verifizieren (besonders `REQUIRED_CHECKS_DRIFT_GUARD_v1_OPERATOR_NOTES.md`)
2. Struktur-Naming absegnen
3. CI/Workflow-Impact prüfen
4. Archive-Policy (besonders `archive&#47;PeakTradeRepo&#47;`)

**Follow-up Fragen (nach PR2):**
- Communication-Strategie
- Long-term Maintenance
- Documentation Quality

---

**Next Step:** Review CLEANUP_PLAN.md und diese Open Questions → Entscheiden → PR2 (Execution)
