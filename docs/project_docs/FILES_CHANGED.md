# Peak_Trade - Geänderte/Neue Dateien

## Neue Dateien

### Risk-Layer
- ✅ `src/risk/limits.py` - Portfolio Risk Limits & Guards
- ✅ `src/risk/position_sizer.py` - Erweitert (vorher vorhanden, jetzt mit Kelly)
- ✅ `src/risk/position_sizer_old_backup.py` - Backup der alten Version

### Data-Layer
- ✅ `src/data/kraken_pipeline.py` - Vollständige Kraken-Pipeline

### Demo-Scripts
- ✅ `scripts/demo_complete_pipeline.py` - Vollständiges Demo aller Features
- ✅ `scripts/demo_kraken_simple.py` - Kraken-Pipeline Demo

### Dokumentation
- ✅ `docs/NEW_FEATURES.md` - Detaillierte Feature-Dokumentation
- ✅ `IMPLEMENTATION_SUMMARY.md` - Zusammenfassung der Implementierung
- ✅ `FILES_CHANGED.md` - Diese Datei

## Geänderte Dateien

### Config
- ✅ `config.toml` - Erweitert mit neuen Risk-Parametern

### Module Exports
- ✅ `src/risk/__init__.py` - Neue Exports hinzugefügt
- ✅ `src/data/__init__.py` - Kraken-Pipeline Exports hinzugefügt

## Unverändert (bestehende Integration)

- ✅ `src/core/config.py` - Config-System (bereits vorhanden)
- ✅ `src/data/kraken.py` - Kraken-Client (bereits vorhanden)
- ✅ `src/data/normalizer.py` - Data Normalizer (bereits vorhanden)
- ✅ `src/data/cache.py` - Parquet Cache (bereits vorhanden)
- ✅ `src/backtest/engine.py` - Backtest Engine (bereits vorhanden)

## Zusammenfassung

**Neue Dateien:** 9
**Geänderte Dateien:** 3
**Backup-Dateien:** 1

Alle Änderungen sind rückwärtskompatibel und brechen bestehenden Code nicht.
