# Strategy Layer vNext - Implementation Report

**Datum**: 2025-12-23  
**Status**: ✅ Abgeschlossen (Phase 1: Foundation)  
**Ziel**: Tooling Hooks für Optuna/MLflow/Polars/DuckDB vorbereiten, ohne bestehende API zu brechen

---

## Executive Summary

Die Phase 1 "Foundation" für Strategy Layer vNext ist abgeschlossen. Wir haben erfolgreich:

1. ✅ **Tracking Interface** implementiert (Protocol + NoopTracker + MLflowTracker-Stub)
2. ✅ **Config Hooks** hinzugefügt (`tracking.*` in default.toml)
3. ✅ **BacktestEngine Integration** mit optionalem Tracker-Parameter
4. ✅ **Parameter Schema** für Strategy-Tuning definiert
5. ✅ **Placeholder Scripts** für zukünftige Optuna-Integration
6. ✅ **Unit-Tests** geschrieben (11/11 Tests bestanden)
7. ✅ **Dokumentation** erstellt (`docs/STRATEGY_LAYER_VNEXT.md`)

**Keine Breaking Changes**: Alle bestehenden Tests bleiben grün, alte API funktioniert unverändert.

---

## Implementierte Files

### Neue Dateien

| Datei | Zeilen | Beschreibung |
|-------|--------|--------------|
| `src/core/tracking.py` | 400+ | Tracking Interface (Protocol, NoopTracker, MLflowTracker) |
| `src/strategies/parameters.py` | 350+ | Parameter Schema für Strategy-Tuning |
| `scripts/run_study_optuna_placeholder.py` | 200+ | Placeholder für Optuna Study Runner |
| `tests/test_tracking_noop.py` | 200+ | Unit-Tests für Tracking + BacktestEngine Integration |
| `docs/STRATEGY_LAYER_VNEXT.md` | 600+ | Vollständige Dokumentation + Roadmap |

### Geänderte Dateien

| Datei | Änderung | Beschreibung |
|-------|----------|--------------|
| `src/core/__init__.py` | +10 Zeilen | Tracking-Exports hinzugefügt |
| `src/backtest/engine.py` | +80 Zeilen | Tracker-Parameter + Logging-Hooks |
| `config/default.toml` | +20 Zeilen | `[tracking]` Sektion hinzugefügt |

**Total**: ~1900 neue Zeilen Code + Dokumentation

---

## Features im Detail

### 1. Tracking Interface (`src/core/tracking.py`)

**Protocol-basiert**: Flexibel für verschiedene Backends (MLflow, W&B, Comet)

```python
from src.core.tracking import Tracker, NoopTracker, build_tracker_from_config

# Tracker aus Config erstellen
tracker = build_tracker_from_config(config)

# Usage
tracker.start_run("ma_crossover_backtest")
tracker.log_params({"fast_window": 20, "slow_window": 50})
tracker.log_metrics({"sharpe": 1.8, "win_rate": 0.55})
tracker.end_run()
```

**Implementierungen**:
- `NoopTracker`: Default, kein Overhead
- `MLflowTracker`: Optional, nur wenn mlflow installiert
- `build_tracker_from_config()`: Factory mit Fallback-Logik

**Key Features**:
- ✅ Kein Overhead wenn disabled (NoopTracker)
- ✅ Graceful Degradation (MLflow nicht installiert → NoopTracker)
- ✅ Type-Safe (Protocol)
- ✅ Helper: `log_backtest_metadata()` für Standard-Logging

### 2. BacktestEngine Integration

**Optionaler Tracker-Parameter** (Backward-Compatible):

```python
from src.backtest import BacktestEngine
from src.core.tracking import build_tracker_from_config

# Ohne Tracker (wie bisher)
engine = BacktestEngine()

# Mit Tracker (neu, opt-in)
tracker = build_tracker_from_config(config)
engine = BacktestEngine(tracker=tracker)
```

**Auto-Logging**:
- Config Snapshot (Parameter, Initial Capital, Mode)
- Git Commit SHA (wenn verfügbar)
- Metriken (Sharpe, Total Return, Win Rate, etc.)

**Beide Backtest-Modi unterstützt**:
- ✅ Legacy-Modus (ohne ExecutionPipeline)
- ✅ ExecutionPipeline-Modus (mit Order-Layer)

### 3. Parameter Schema (`src/strategies/parameters.py`)

**Leichtgewichtig**: Nur Dataclasses, keine schweren Dependencies

```python
from src.strategies.parameters import Param

# Numerischer Parameter
Param(name="fast_window", type="int", default=20, low=5, high=50)

# Float mit Log-Scale (für Learning-Rates)
Param(name="lr", type="float", default=0.01, low=0.001, high=0.1, log_scale=True)

# Kategorisch
Param(name="mode", type="categorical", default="fast", choices=["fast", "slow"])

# Boolean
Param(name="use_filter", type="bool", default=True)
```

**Optional für Strategien**:
```python
class MyStrategy(BaseStrategy):
    @property
    def parameter_schema(self) -> list[Param]:
        return [
            Param(name="window", type="int", default=20, low=5, high=50),
        ]
```

**Keine Pflicht**: Bestehende Strategien funktionieren ohne Schema.

**Utility-Funktionen**:
- `extract_param_dict()`: Default-Werte extrahieren
- `validate_param_dict()`: Werte validieren
- `Param.to_optuna_suggest()`: Optuna Trial-Integration (später)

### 4. Config Integration

**Neue Sektion in `config/default.toml`**:

```toml
[tracking]
enabled = false
backend = "noop"  # oder "mlflow"

[tracking.mlflow]
tracking_uri = "./mlruns"
experiment_name = "strategy_optimization"
```

**Fallback-Logik**:
1. `enabled=false` → NoopTracker
2. `backend="noop"` → NoopTracker
3. `backend="mlflow"` + installiert → MLflowTracker
4. `backend="mlflow"` + nicht installiert → NoopTracker + Warning

### 5. Placeholder Scripts

**`scripts/run_study_optuna_placeholder.py`**:

```bash
python3 scripts/run_study_optuna_placeholder.py \
    --strategy ma_crossover \
    --config config/config.toml \
    --n-trials 100
```

**Output**:
- Hilfreiche Meldung + Verweis auf Doku
- CLI-Args bereits definiert (für zukünftige Implementation)
- Exit-Code 0 (kein Error)

**Status**: Placeholder, noch nicht funktional

---

## Tests

### Test-Suite: `tests/test_tracking_noop.py`

**11 Tests, alle bestanden** ✅

```bash
python3 -m pytest tests/test_tracking_noop.py -v
# ============================== 11 passed in 0.22s ==============================
```

#### Test-Coverage:

**NoopTracker**:
- ✅ `test_noop_tracker_does_nothing`: Keine Exceptions
- ✅ `test_noop_tracker_with_large_data`: Performance (1000+ Params/Metrics)

**Config Builder**:
- ✅ `test_build_tracker_disabled`: tracking.enabled=false
- ✅ `test_build_tracker_noop_backend`: backend="noop"
- ✅ `test_build_tracker_missing_config`: Fehlende Config
- ✅ `test_build_tracker_unknown_backend`: Unbekanntes Backend

**Helper**:
- ✅ `test_log_backtest_metadata_with_noop`: log_backtest_metadata()

**BacktestEngine Integration**:
- ✅ `test_backtest_with_noop_tracker_no_exceptions`: Keine Exceptions
- ✅ `test_backtest_determinism_with_tracker`: Identische Ergebnisse mit/ohne Tracker
- ✅ `test_backtest_with_tracker_execution_pipeline`: ExecutionPipeline-Modus
- ✅ `test_backtest_tracker_none_works`: Backward-Compatibility (tracker=None)

### Qualitätschecks

**Linter**: ✅ Keine Fehler
```bash
ruff check src/core/tracking.py src/strategies/parameters.py \
    scripts/run_study_optuna_placeholder.py tests/test_tracking_noop.py
# → No linter errors found
```

**Bestehende Tests**: ✅ Keine Regression
- Alle bestehenden Backtest-Tests laufen weiter
- Keine Breaking Changes

---

## Aktivierung & Usage

### Für Entwickler

**1. Tracking aktivieren** (optional):

```toml
# config.toml
[tracking]
enabled = true
backend = "noop"  # oder "mlflow"
```

**2. MLflow installieren** (optional):

```bash
pip install mlflow
# oder: uv pip install mlflow
```

**3. Backtest mit Tracking**:

```python
from src.core.tracking import build_tracker_from_config
from src.backtest import BacktestEngine
from src.core.peak_config import load_config

config = load_config()
tracker = build_tracker_from_config(config)

engine = BacktestEngine(tracker=tracker)
result = engine.run_realistic(df, strategy_fn, params)

# → Config + Metrics werden geloggt (wenn tracker != NoopTracker)
```

**4. MLflow UI öffnen** (wenn MLflow installiert):

```bash
mlflow ui --backend-store-uri ./mlruns
# → http://localhost:5000
```

### Für CI/CD

**Keine Änderungen nötig**:
- Tracking ist per Default disabled
- NoopTracker ist immer verfügbar (kein Install nötig)
- Bestehende Pipelines funktionieren unverändert

### Für Research

**Optuna-Integration (später)**:

```bash
# Phase 2: Optuna installieren
pip install optuna

# Phase 3: Study Runner nutzen
python3 scripts/run_study_optuna_placeholder.py \
    --strategy ma_crossover \
    --n-trials 100
```

---

## Backward Compatibility

### Garantien

✅ **Keine Breaking Changes**:
- `BacktestEngine()` ohne tracker funktioniert wie bisher
- `BaseStrategy` ohne `parameter_schema` funktioniert wie bisher
- Alle bestehenden Tests bleiben grün

✅ **Opt-In**:
- Tracking ist per Default disabled
- Parameter-Schema ist optional
- Keine neuen Required-Dependencies

✅ **Graceful Degradation**:
- MLflow nicht installiert → NoopTracker (keine Errors)
- Config fehlt → NoopTracker
- Tracking-Fehler → Warning, kein Crash

### Test-Beweis

```python
# Test: test_backtest_determinism_with_tracker
# Ergebnis: Identische Equity-Curves mit/ohne Tracker
assert result_without_tracker == result_with_noop_tracker
```

---

## Roadmap

### Phase 1: Foundation (✅ Abgeschlossen)
- [x] Tracking Interface
- [x] Config Hooks
- [x] BacktestEngine Integration
- [x] Parameter Schema
- [x] Placeholder Scripts
- [x] Unit-Tests
- [x] Dokumentation

### Phase 2: MLflow Integration (🔜 Next)
- [ ] MLflowTracker vollständige Implementation
- [ ] Auto-Logging für BacktestEngine
- [ ] Artifact Upload (Plots, Reports)
- [ ] MLflow UI Integration-Tests
- [ ] Best-Practices Dokumentation

### Phase 3: Optuna Integration (🔜 Later)
- [ ] Study Runner Implementation
- [ ] Parameter-Schema → Optuna Search Space
- [ ] Multi-Objective Optimization
- [ ] Pruning-Callback
- [ ] Distributed Optimization (optional)

### Phase 4: Acceleration (⏳ Future)
- [ ] Polars Backend für Backtests
- [ ] DuckDB für Multi-Symbol Queries
- [ ] Benchmarks (Pandas vs Polars)
- [ ] Incremental Data Loading

---

## Dependencies

### Core (keine neuen Hard-Dependencies)
- ✅ Nur Standard-Library + bestehende Dependencies
- ✅ `tomllib` / `tomli` (schon vorhanden)
- ✅ `pandas` (schon vorhanden)

### Optional (nicht required)
- ⏳ `mlflow` (für MLflowTracker, später)
- ⏳ `optuna` (für Study Runner, später)
- ⏳ `polars` (für Acceleration, viel später)
- ⏳ `duckdb` (für Acceleration, viel später)

**Empfehlung**: Optional Dependencies in `pyproject.toml` definieren:

```toml
[project.optional-dependencies]
research = ["mlflow>=2.10", "optuna>=3.5"]
acceleration = ["polars>=0.20", "duckdb>=0.10"]
```

---

## Known Limitations

### Aktuell (Phase 1)

1. **MLflowTracker**: Nur Stub, noch nicht vollständig implementiert
   - Lösung: Phase 2 (MLflow Integration)

2. **Optuna Study Runner**: Nur Placeholder
   - Lösung: Phase 3 (Optuna Integration)

3. **Parameter Schema**: Nur 0 Strategien haben Schema definiert
   - Lösung: Schrittweise bestehende Strategien erweitern (optional)

4. **Tracking in Live**: Noch nicht implementiert
   - Lösung: Nicht geplant (Tracking nur für R&D, nicht für Live)

### Design-Entscheidungen

**"Not Now" Liste**:
- ❌ Harte ML-Integration (sklearn/torch) → Später, wenn Use-Case klar
- ❌ Feature Store → Später, wenn >100 Features
- ❌ Distributed Backtesting (Ray/Dask) → Später, wenn >10.000 Trials

**Grund**: Wir wollen leichtgewichtig bleiben und nur bei Bedarf erweitern.

---

## Risiken & Mitigations

### Risiko 1: MLflow als Dependency zu schwer

**Mitigation**:
- Optional Install
- Graceful Fallback zu NoopTracker
- Klare Fehlermeldungen

### Risiko 2: Tracking-Overhead in Backtests

**Mitigation**:
- NoopTracker hat nahezu keinen Overhead
- MLflow-Logging ist async (später)
- Tracking nur für R&D, nicht für Live

### Risiko 3: Parameter-Schema wird nicht genutzt

**Mitigation**:
- Optional, keine Pflicht
- Klare Use-Cases in Doku (Optuna, MLflow)
- Schrittweise Migration bestehender Strategien

---

## Erfolgsmetriken

### Phase 1 (Foundation)

✅ **Tracking Interface funktioniert**:
- 11/11 Tests bestanden
- Keine Linter-Errors
- Backward-Compatible

✅ **Keine Performance-Regression**:
- NoopTracker hat keinen Overhead
- Bestehende Backtests laufen gleich schnell

✅ **Dokumentation vollständig**:
- 600+ Zeilen Doku
- Roadmap definiert
- Usage-Beispiele vorhanden

### Phase 2 (MLflow Integration) - Geplant

🔜 **MLflow Integration funktioniert**:
- [ ] MLflow UI zeigt Runs an
- [ ] Artifacts werden hochgeladen
- [ ] Comparison-View funktioniert

🔜 **Performance akzeptabel**:
- [ ] MLflow-Logging <100ms pro Run
- [ ] Keine Blockierung des Backtests

### Phase 3 (Optuna Integration) - Geplant

🔜 **Optuna Study läuft**:
- [ ] Parameter-Schema → Search Space funktioniert
- [ ] Trials werden zu MLflow geloggt
- [ ] Pruning funktioniert

---

## Nächste Schritte

### Sofort (User)

1. **Tracking testen**:
   ```bash
   python3 -m pytest tests/test_tracking_noop.py -v
   ```

2. **Placeholder Script testen**:
   ```bash
   python3 scripts/run_study_optuna_placeholder.py --strategy ma_crossover
   ```

3. **Doku lesen**:
   ```bash
   cat docs/STRATEGY_LAYER_VNEXT.md
   ```

### Phase 2 (MLflow Integration)

1. **MLflowTracker vollständig implementieren**:
   - Lazy Import
   - Error Handling
   - Artifact Upload

2. **Integration-Tests schreiben**:
   - MLflow UI Check
   - Artifact Verification
   - Run Comparison

3. **Best-Practices Doku**:
   - MLflow Setup
   - Experiment Naming
   - Run Organization

### Phase 3 (Optuna Integration)

1. **Study Runner implementieren**:
   - Parameter-Schema auslesen
   - Optuna Objective-Function
   - MLflow Integration

2. **Multi-Objective Support**:
   - Mehrere Ziele (Sharpe, Drawdown, Win-Rate)
   - Pareto-Front Visualization

3. **Distributed Optimization** (optional):
   - Parallel Trials
   - Database Storage (sqlite → postgres)

---

## Maintenance

### Code-Owner
- **Primary**: Peak_Trade Strategy Team
- **Reviewer**: Core Team (für Breaking Changes)

### Update-Policy
- **Tracking Interface**: Stabil (Protocol-basiert, erweiterbar)
- **Parameter Schema**: Erweiterbar (neue Typen hinzufügen)
- **Config**: Backward-Compatible (neue Keys optional)

### Deprecation-Policy
- Keine Deprecations geplant
- Alle Features sind opt-in
- Breaking Changes nur mit Major-Version-Bump

---

## Referenzen

### Dokumentation
- **Main Doc**: `docs/STRATEGY_LAYER_VNEXT.md`
- **Tracking**: `src/core/tracking.py` (Docstrings)
- **Parameter Schema**: `src/strategies/parameters.py` (Docstrings)

### Code
- **Tracking Interface**: `src/core/tracking.py`
- **BacktestEngine**: `src/backtest/engine.py`
- **Parameter Schema**: `src/strategies/parameters.py`
- **Tests**: `tests/test_tracking_noop.py`

### Related ADRs
- `ADR_0001_Peak_Tool_Stack.md` (Tool-Auswahl)

---

## Changelog

### 2025-12-23: Phase 1 Complete

**Added**:
- ✅ Tracking Interface (Protocol, NoopTracker, MLflowTracker-Stub)
- ✅ Config Hooks (`[tracking]` in default.toml)
- ✅ BacktestEngine Integration (optional tracker parameter)
- ✅ Parameter Schema (`src/strategies/parameters.py`)
- ✅ Placeholder Scripts (`run_study_optuna_placeholder.py`)
- ✅ Unit-Tests (11 Tests, alle bestanden)
- ✅ Dokumentation (`docs/STRATEGY_LAYER_VNEXT.md`)

**Changed**:
- ✅ `src/core/__init__.py`: Tracking-Exports
- ✅ `src/backtest/engine.py`: Tracker-Parameter + Logging
- ✅ `config/default.toml`: `[tracking]` Sektion

**No Breaking Changes**: Alle bestehenden Tests grün ✅

---

## Fazit

Phase 1 "Foundation" ist erfolgreich abgeschlossen. Wir haben:

1. ✅ **Tooling Hooks vorbereitet** für MLflow/Optuna/Polars/DuckDB
2. ✅ **Keine Breaking Changes** eingeführt (Backward-Compatible)
3. ✅ **Opt-In Design** implementiert (Tracking disabled per Default)
4. ✅ **Tests geschrieben** (11/11 bestanden, keine Regression)
5. ✅ **Dokumentation erstellt** (600+ Zeilen, vollständig)

**Ready for Phase 2**: MLflow Integration kann beginnen 🚀

---

**Maintainer**: Peak_Trade Team  
**Last Updated**: 2025-12-23  
**Status**: ✅ Phase 1 Complete
