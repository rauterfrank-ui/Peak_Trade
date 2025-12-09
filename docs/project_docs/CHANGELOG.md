# CHANGELOG

> Hinweis: Datum und Versionen kannst du nach Bedarf anpassen.
> Dieser Eintrag fasst die Änderungen aus `FILES_CHANGED.md` und
> später `archive/full_files_stand_02.12.2025` zusammen.

---

## 2025-12-09 – R&D-Strategien Dokumentation

### Docs

* Verfeinerte Beschreibung der R&D-Strategien **ArmstrongCycleStrategy** und **ElKarouiVolModelStrategy** in `docs/PHASE_75_STRATEGY_LIBRARY_V1_1.md`
  * Klarer R&D-Scope (Hypothesen- und Regime-Research, keine Live-/Paper-/Testnet-Freigabe)
  * Dokumentierte typische Nutzungsszenarien für beide Strategien

---

## 2025-12-02 – Risk- & Data-Layer Erweiterungen (Phase 2)

### Neue Dateien

**Risk-Layer**

- `src/risk/limits.py`
  Portfolio Risk Limits & Guards (globale Risiko-Limits und Schutzmechanismen für das Portfolio).

- `src/risk/position_sizer.py`
  Erweiterte Version des Position Sizers (inkl. Kelly-Logik und flexibler Parametrisierung).

- `src/risk/position_sizer_old_backup.py`
  Backup der alten Position-Sizing-Implementierung (nur zur Referenz, nicht produktiv genutzt).

**Data-Layer**

- `src/data/kraken_pipeline.py`
  Vollständige Kraken-Datenpipeline (End-to-End-Flow von Raw-Daten bis normalisierten OHLCV-Serien).

**Demo-Scripts**

- `scripts/demo_complete_pipeline.py`
  Demo-Skript für die komplette Pipeline (Data + Risk + Backtest).

- `scripts/demo_kraken_simple.py`
  Vereinfachte Demo der Kraken-Pipeline.

**Dokumentation**

- `docs/NEW_FEATURES.md`
  Detaildokumentation der neuen Features.

- `docs/project_docs/IMPLEMENTATION_SUMMARY.md`
  Zusammenfassung der Implementierung (Architektur, Module, Datenfluss).

- `docs/project_docs/FILES_CHANGED.md`
  Technische Änderungsübersicht für diese Phase.

### Geänderte Dateien

**Config**

- `config/config.toml`
  Erweiterung um neue Risk-Parameter (z.B. Limits, Kelly-Faktoren, Safety-Grenzen).

**Module Exports**

- `src/risk/__init__.py`
  Exports für neue Risk-Module (`limits`, erweiterter `position_sizer`) ergänzt.

- `src/data/__init__.py`
  Exports für `kraken_pipeline.py` ergänzt, damit die Pipeline über den Data-Namespace verfügbar ist.

### Unverändert (aber Teil der bestehenden Integration)

- `src/core/config.py` – zentrales Config-System (bereits in Produktion).
- `src/data/kraken.py` – Kraken-Client.
- `src/data/normalizer.py` – Data Normalizer.
- `src/data/cache.py` – Parquet Cache.
- `src/backtest/engine.py` – Backtest Engine.

> Zusammenfassung:
> **Neue Dateien:** 9
> **Geänderte Dateien:** 3
> **Backup-Dateien:** 1
> Alle Änderungen sind rückwärtskompatibel und brechen bestehenden Code nicht.

---

## 2025-12-01 – Archivierter Stand (aus `full_files_stand_02.12.2025`)

*(Platzhalter – hier die wichtigsten Änderungen aus `archive/full_files_stand_02.12.2025` eintragen, sobald der Inhalt konsolidiert ist. Vorschlag: nach Themenblöcken „Backtest", „Daten", „Strategien", „Projektorganisation" zusammenfassen.)*
