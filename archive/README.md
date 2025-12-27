# Archive — Historische Snapshots & Legacy-Code

**Stand:** 2025-12-27

Dieser Ordner enthält historische Snapshots und Legacy-Code, der nicht mehr aktiv verwendet wird, aber aus Dokumentations- oder Referenzzwecken aufbewahrt wird.

---

## 📦 Inhalt

### `full_files_stand_02.12.2025/`

**Was:** Vollständiger Snapshot des Projekts vom 02.12.2025  
**Warum archiviert:** Snapshot vor größeren Refactorings  
**Enthält:** Komplette peak_trade_export/ mit 19 Dateien (17 Python, 1 MD, 1 TXT)

### `legacy_docs/`

**Was:** Alte Dokumentation aus früheren Phasen  
**Warum archiviert:** Überholt durch neuere Docs, aber historisch wertvoll  
**Enthält:**
- `README.before_phase58.md` — README-Stand vor Phase 58

### `legacy_scripts/`

**Was:** Alte Scripts, die durch neuere Versionen ersetzt wurden  
**Warum archiviert:** Referenz für alte Workflows  
**Enthält:**
- `run_regime_experiments.sh` — Alte Version des Regime-Experiment-Runners

### `PeakTradeRepo/`

**Was:** Komplettes altes Repository-Layout  
**Warum archiviert:** Vollständiger Snapshot eines früheren Repo-Stands  
**Enthält:**
- Komplette alte Struktur: docs/, scripts/, src/, tests/
- CONTRIBUTING.md, README.md, pyproject.toml
- 6 Python-Dateien in src/, 1 Test

**Note:** Dieses Archiv ist sehr umfangreich. Prüfen, ob es langfristig behalten werden soll.

---

## 🔍 Wann ins Archive?

Dateien/Ordner gehören ins Archive wenn:

1. **Ersetzt:** Durch neuere Version ersetzt, aber alte Version hat historischen Wert
2. **Überholt:** Nicht mehr relevant, aber dokumentiert wichtige Entwicklungsschritte
3. **Snapshot:** Vollständiger Stand zu einem wichtigen Zeitpunkt
4. **Referenz:** Könnte für Vergleiche oder Nachvollziehbarkeit nützlich sein

**Nicht archivieren:**
- Temporäre Dateien (→ löschen)
- Generierte Artefakte (→ .gitignore)
- Redundante Kopien ohne historischen Wert (→ löschen)

---

## 🗑️ Cleanup-Policy

Archive sollte regelmäßig überprüft werden:

- **Jährlich:** Sind alte Snapshots noch relevant?
- **Nach Major Releases:** Neue Snapshots hinzufügen wenn sinnvoll
- **Bei Repo-Cleanups:** Prüfen ob Archive-Inhalte noch Wert haben

---

## 📚 Siehe auch

- **Repo-Struktur:** `docs/architecture/REPO_STRUCTURE.md`
- **Cleanup-Report:** `docs/ops/cleanup/CLEANUP_REPORT.md`
