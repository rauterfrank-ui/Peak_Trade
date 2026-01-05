# MLflow Tracking Guide

**Last Updated:** 2026-01-05  
**MLflow Version:** ≥3.0,<4  
**Related:** PR #569, `src/core/tracking.py`, `tests/test_tracking_mlflow_integration.py`

---

## Scope

Dieses Dokument beschreibt die Nutzung des MLflow Trackings in Peak_Trade (mlflow>=3.0,<4), inkl. Run-Lifecycle, Param/Metric Logging, Artifacts und Troubleshooting.

**Was du hier findest:**
- ✅ Installation & Setup
- ✅ Run Lifecycle Best Practices
- ✅ Context Manager Usage (empfohlen)
- ✅ Params/Metrics/Tags/Artifacts Logging
- ✅ Troubleshooting & Common Pitfalls
- ✅ Integration mit BacktestEngine
- ✅ Referenzen & Weiterführende Docs

**Was du hier NICHT findest:**
- ❌ MLflow Server Setup (siehe [MLflow Official Docs](https://mlflow.org/docs/latest/tracking.html#tracking-server))
- ❌ MLflow Models Registry (außerhalb des Scopes)
- ❌ MLflow Projects/Deployment

---

## Installation

### Local Development

```bash
# Via pip
pip install "mlflow>=3.0,<4"

# Via uv (empfohlen für Peak_Trade)
uv pip install "mlflow>=3.0,<4"

# Mit Peak_Trade tracking extra
pip install -e ".[tracking]"
# oder
uv sync --extra tracking
```

### CI/CD

MLflow wird automatisch in CI installiert, wenn die Tracking-Extras/Requirements aktiv sind. Dadurch laufen die MLflow-Integrationstests standardmäßig mit.

**Verification:**

```bash
# Check MLflow Installation
python -c "import mlflow; print(mlflow.__version__)"
# Expected: 3.x.x

# Run MLflow Integration Tests
pytest -q tests/test_tracking_mlflow_integration.py
# Expected: 18 passed in ~1s
```

---

## MLflowTracker: Run Lifecycle (Best Practice)

### Grundprinzip

**Critical Rules:**
1. ⚠️ Es darf nicht „blind" mehrfach `start_run()` aufgerufen werden, wenn bereits ein Run aktiv ist
2. ⚠️ `end_run()` darf nur ausführen, wenn ein Run aktiv ist
3. ✅ Tracking-Code muss gegen `mlflow.active_run()` robust sein
4. ✅ Verwende Context Manager für deterministische Run-Beendigung

**Warum ist das wichtig?**
- MLflow ≥3.0 wirft `Exception: Run with UUID ... is already active` bei doppeltem `start_run()`
- Vergessene `end_run()` Calls führen zu Test-Flakiness und Run-State-Leakage
- Context Manager garantiert Cleanup auch bei Exceptions

---

## Usage Patterns

### Pattern 1: Context Manager (Empfohlen ✅)

```python
from src.core.tracking import MLflowTracker

# Auto-start und auto-end
with MLflowTracker(
    tracking_uri="file:///path/to/mlruns",
    experiment_name="my_experiment",
) as tracker:
    # Run wird automatisch gestartet beim __enter__
    tracker.log_params({"strategy": {"name": "ma_crossover", "version": "v1"}})
    tracker.log_metrics({"sharpe": 1.23, "max_dd": -0.12})
    tracker.log_artifact("results/equity_curve.png")
    # Run wird automatisch beendet beim __exit__ (auch bei Exception!)
```

**Vorteile:**
- ✅ Automatisches Cleanup (auch bei Exceptions)
- ✅ Kein vergessener `end_run()` Call
- ✅ Pythonic und idiomatisch

### Pattern 2: Explicit Start/End

```python
from src.core.tracking import MLflowTracker

tracker = MLflowTracker(
    tracking_uri="file:///path/to/mlruns",
    experiment_name="my_experiment",
)

try:
    tracker.start_run("my_run")
    tracker.log_params({"strategy": "buy_and_hold"})
    tracker.log_metrics({"total_return": 0.25})
finally:
    tracker.end_run()  # Garantiert auch bei Exception
```

**Use Cases:**
- Lange Runs mit mehreren Phasen
- Manuelle Kontrolle über Run-Lifecycle
- Legacy-Code-Integration

### Pattern 3: Auto-Start Run

```python
from src.core.tracking import MLflowTracker

# Run wird automatisch beim __init__ gestartet
tracker = MLflowTracker(
    tracking_uri="file:///path/to/mlruns",
    experiment_name="my_experiment",
    auto_start_run=True,  # ⚠️ Achtung: Run bleibt aktiv bis end_run()
    run_name="auto_started_run",
)

tracker.log_params({"fast": 20, "slow": 50})
tracker.end_run()  # Explizit beenden nicht vergessen!
```

**⚠️ Vorsicht:**
- Run bleibt aktiv bis `end_run()` aufgerufen wird
- Risiko von vergessenen Cleanups
- Nur für kurze Scripts empfohlen

---

## Logging API

### Params: Konfiguration & Hyperparameter

```python
# Simple params
tracker.log_params({
    "strategy": "ma_crossover",
    "fast_window": 20,
    "slow_window": 50,
})

# Nested params (werden automatisch geflattened)
tracker.log_params({
    "strategy": {
        "name": "ma_crossover",
        "params": {
            "fast": 20,
            "slow": 50,
        }
    },
    "risk": {
        "max_position_size": 0.1,
    }
})
# → MLflow: strategy.name=ma_crossover, strategy.params.fast=20, ...
```

**Wichtig:**
- ✅ Params werden als Strings gespeichert (MLflow-Requirement)
- ✅ Nested Dicts werden automatisch via `_flatten()` geflattened
- ✅ Lists/Tuples werden als JSON serialisiert
- ⚠️ Params sind **immutable** (können nach Logging nicht geändert werden)

### Metrics: Performance & Ergebnisse

```python
# Single metrics
tracker.log_metrics({
    "sharpe_ratio": 1.8,
    "total_return": 0.25,
    "max_drawdown": -0.15,
    "win_rate": 0.55,
})

# Progressive metrics mit Steps (z.B. Training Progress)
for epoch in range(10):
    tracker.log_metrics({
        "train_loss": loss_train,
        "val_loss": loss_val,
    }, step=epoch)
```

**Wichtig:**
- ✅ Metrics müssen numerisch sein (int, float)
- ✅ Booleans werden **nicht** automatisch konvertiert (filtern!)
- ✅ Metrics können mehrfach geloggt werden (mit/ohne Step)

### Tags: Metadaten & Labels

```python
tracker.set_tags({
    "environment": "paper",
    "market": "BTC-EUR",
    "strategy_family": "trend_following",
    "operator": "frank",
})
```

**Use Cases:**
- Gruppierung von Runs (Filter in MLflow UI)
- Git Commit SHA, Branch Name
- Execution Environment (paper/live/backtest)

### Artifacts: Dateien & Plots

```python
# Simple file
tracker.log_artifact("results/equity_curve.png")

# Mit custom artifact_path (Unterordner in MLflow)
tracker.log_artifact("results/stats.json", artifact_path="reports/stats.json")

# Multiple artifacts
tracker.log_artifact("results/equity_curve.png")
tracker.log_artifact("results/stats.json")
tracker.log_artifact("results/trades.csv")
```

**Wichtig:**
- ✅ Graceful degradation: fehlende Dateien werfen **keine** Exception
- ✅ Artifacts werden erst nach `end_run()` verfügbar (Flush)
- ⚠️ Große Dateien (>100MB) können Performance-Probleme verursachen

---

## Integration mit BacktestEngine

### Minimal Integration

```python
from src.core.tracking import MLflowTracker
from src.backtest import BacktestEngine

with MLflowTracker(...) as tracker:
    engine = BacktestEngine(tracker=tracker)

    result = engine.run_realistic(
        df=data,
        strategy_signal_fn=my_strategy,
        strategy_params={"fast": 20, "slow": 50},
    )

    # Metrics manuell loggen
    tracker.log_metrics(result.stats)
```

### Mit Helper-Funktionen

```python
from src.core.tracking import (
    MLflowTracker,
    log_backtest_metadata,
    log_backtest_artifacts,
)

with MLflowTracker(...) as tracker:
    engine = BacktestEngine(tracker=None)  # Kein auto-logging

    result = engine.run_realistic(...)

    # Helper: Params/Metrics/Tags aus result extrahieren
    log_backtest_metadata(tracker, config=config, result=result, tags={"env": "paper"})

    # Helper: Stats & Equity Curve als Artifacts
    log_backtest_artifacts(tracker, result=result)
```

**Helper-Funktionen:**
- `log_backtest_metadata()`: Tolerant, crasht nie, extrahiert Params/Metrics/Tags
- `log_backtest_artifacts()`: Schreibt `stats.json` und `equity_curve.csv` als Artifacts

---

## Factory: build_tracker_from_config()

```python
from src.core.tracking import build_tracker_from_config

# Config: Dict oder PeakConfig
config = {
    "enabled": True,
    "backend": "mlflow",
    "mlflow": {
        "tracking_uri": "file:///path/to/mlruns",
        "experiment_name": "my_experiment",
        "auto_start_run": False,
        "run_name": "backtest_run",
    },
}

tracker = build_tracker_from_config(config)
# → Returns MLflowTracker instance

# NoopTracker Fallback
config_noop = {"enabled": False}
tracker_noop = build_tracker_from_config(config_noop)
# → Returns NoopTracker (no-op, crasht nie)
```

**Fallback-Strategie:**
- `enabled=False` → NoopTracker
- `backend="noop"` → NoopTracker
- `mlflow` nicht installiert → RuntimeError (in MLflowTracker.__init__)
- Ungültige Config → NoopTracker (safe default)

---

## Troubleshooting & Common Pitfalls

### Problem 1: "Run already active" Exception

**Symptom:**
```python
Exception: Run with UUID ... is already active
```

**Ursache:**
- Vergessener `end_run()` Call
- Mehrfache `start_run()` Calls ohne zwischenzeitliches `end_run()`

**Lösung:**
```python
import mlflow

# Check if run is active
if mlflow.active_run():
    mlflow.end_run()  # Cleanup

# Oder: Context Manager verwenden (auto-cleanup)
with MLflowTracker(...) as tracker:
    # ...
```

**Prevention:**
- ✅ Verwende Context Manager (Pattern 1)
- ✅ Immer `try/finally` für explizite `start_run()`/`end_run()`

---

### Problem 2: AttributeError: '_run_started'

**Symptom:**
```python
AttributeError: 'MLflowTracker' object has no attribute '_run_started'
```

**Ursache:**
- Alte Tracker-Instanz (vor PR #569 Fix)
- Veraltete Installation

**Lösung:**
```bash
# Repo aktualisieren
git pull origin main

# Dependencies sync
uv sync
# oder: pip install -e ".[tracking]"

# Verification
python -c "from src.core.tracking import MLflowTracker; print('OK')"
```

---

### Problem 3: MlflowException: Run '...' not found

**Symptom:**
```python
mlflow.exceptions.MlflowException: Run '...' not found
```

**Ursache:**
- Run wurde bereits beendet
- Falscher `tracking_uri` (zeigt auf anderes Backend)
- Run-ID aus altem/gelöschtem Experiment

**Lösung:**
```python
# Run-ID erst nach start_run() verwenden
tracker.start_run()
run_id = tracker._run_id  # Jetzt verfügbar

# Query erst nach end_run() (run_id bleibt erhalten)
tracker.end_run()
run = mlflow.get_run(tracker._run_id)  # OK
```

**Wichtig:**
- `_run_id` bleibt nach `end_run()` erhalten (für Post-Run-Queries)
- Prüfe `tracking_uri` (file:// vs. remote server)

---

### Problem 4: Tests schlagen lokal fehl

**Symptom:**
```bash
pytest tests/test_tracking_mlflow_integration.py
# → FAILED: some tests fail
```

**Diagnose:**
```bash
# 1. MLflow installiert?
python -c "import mlflow; print(mlflow.__version__)"

# 2. Aktive Runs cleanup
python -c "import mlflow; [mlflow.end_run() for _ in range(10)]"

# 3. Tests mit verbose output
pytest tests/test_tracking_mlflow_integration.py -v --tb=short

# 4. Nur einen Test laufen lassen
pytest tests/test_tracking_mlflow_integration.py::TestMLflowTrackerBasics::test_mlflow_tracker_initialization -v
```

**Common Fixes:**
- ✅ `pip install "mlflow>=3.0,<4"`
- ✅ Cleanup aktive Runs (siehe oben)
- ✅ `pytest` installiert? (`pip install pytest`)

---

### Problem 5: Artifacts nicht sichtbar in MLflow UI

**Symptom:**
- `log_artifact()` wird aufgerufen, aber Artifacts fehlen in MLflow UI

**Ursache:**
- Artifacts werden erst nach `end_run()` geflushed
- Falscher `artifact_path` (optional parameter)
- Datei existiert nicht (graceful degradation → kein Fehler)

**Lösung:**
```python
with MLflowTracker(...) as tracker:
    tracker.log_artifact("path/to/file.png")
    # Artifacts werden beim __exit__ geflushed

# Oder explizit:
tracker.start_run()
tracker.log_artifact("path/to/file.png")
tracker.end_run()  # Flush!

# Verify
run = mlflow.get_run(tracker._run_id)
print(run.info.artifact_uri)  # Artifact-Speicherort
```

---

## Advanced: Nested Params & Flattening

MLflow speichert Params als **flache String-Keys**. Peak_Trade flattened nested Dicts automatisch:

```python
# Input
tracker.log_params({
    "strategy": {
        "name": "ma_crossover",
        "params": {
            "fast": 20,
            "slow": 50,
        }
    }
})

# MLflow Storage (automatisch geflattened)
{
    "strategy.name": "ma_crossover",
    "strategy.params.fast": "20",
    "strategy.params.slow": "50",
}
```

**Implementation:**
- `_flatten()` helper in `src/core/tracking.py`
- Recursive Flattening mit `.` als Separator
- Listen/Tuples werden als JSON serialisiert

---

## Testing

### MLflow Integration Tests

```bash
# Alle MLflow-Integration-Tests
pytest tests/test_tracking_mlflow_integration.py -v

# Nur Basics
pytest tests/test_tracking_mlflow_integration.py::TestMLflowTrackerBasics -v

# Nur Logging
pytest tests/test_tracking_mlflow_integration.py::TestMLflowTrackerLogging -v

# Mit Coverage
pytest tests/test_tracking_mlflow_integration.py --cov=src.core.tracking --cov-report=term-missing
```

### Test Structure

```
tests/test_tracking_mlflow_integration.py
├── TestMLflowTrackerBasics (3 tests)
│   ├── test_mlflow_tracker_initialization
│   ├── test_mlflow_tracker_start_end_run
│   └── test_mlflow_tracker_context_manager
├── TestMLflowTrackerLogging (5 tests)
│   ├── test_log_params
│   ├── test_log_params_nested_dict
│   ├── test_log_metrics
│   ├── test_log_metrics_with_step
│   └── test_set_tags
├── TestMLflowTrackerArtifacts (2 tests)
├── TestMLflowTrackerErrorHandling (4 tests)
├── TestBuildTrackerFromConfigMLflow (1 test)
└── TestBacktestIntegration (2 tests)
```

**Total:** 18 Tests, ~1.1s Laufzeit

---

## Configuration Examples

### Local File-Based Tracking

```python
tracker = MLflowTracker(
    tracking_uri="file:///Users/you/mlruns",
    experiment_name="my_backtests",
)
```

### Remote MLflow Server

```python
tracker = MLflowTracker(
    tracking_uri="http://localhost:5000",
    experiment_name="production_backtests",
)
```

### Config-Based (TOML)

```toml
# config/tracking.toml
[tracking]
enabled = true
backend = "mlflow"

[tracking.mlflow]
tracking_uri = "file:///path/to/mlruns"
experiment_name = "my_experiment"
auto_start_run = false
run_name = "backtest_run"
```

```python
import toml
from src.core.tracking import build_tracker_from_config

config = toml.load("config/tracking.toml")
tracker = build_tracker_from_config(config["tracking"])
```

---

## MLflow UI

### Start MLflow UI

```bash
# Local file-based tracking
mlflow ui --backend-store-uri file:///path/to/mlruns --port 5000

# Remote tracking server
mlflow server --backend-store-uri postgresql://... --default-artifact-root s3://... --port 5000
```

### Access UI

```
http://localhost:5000
```

**Features:**
- Compare Runs (Metrics, Params)
- Download Artifacts
- Filter by Tags
- Visualize Metrics over Time

---

## Best Practices Summary

### Do's ✅

1. **Verwende Context Manager** für automatisches Cleanup
2. **Flatten Nested Params** (automatisch in Peak_Trade)
3. **Nutze Tags** für Run-Gruppierung (environment, market, strategy_family)
4. **Log Metrics als numerische Werte** (keine Booleans/Strings)
5. **End Run explizit** (oder via Context Manager)
6. **Teste MLflow-Integration lokal** vor CI-Push

### Don'ts ❌

1. ❌ **Kein mehrfaches `start_run()`** ohne zwischenzeitliches `end_run()`
2. ❌ **Kein auto_start_run=True** ohne explizite Cleanup-Strategie
3. ❌ **Keine großen Artifacts (>100MB)** ohne Performance-Überlegungen
4. ❌ **Keine hardcoded Tracking URIs** (verwende Config)
5. ❌ **Keine Params nach Run-Start ändern** (immutable!)

---

## References

### Internal Docs
- **Implementation:** `src/core/tracking.py`
- **Tests:** `tests/test_tracking_mlflow_integration.py`
- **Test Noop-Tracker:** `tests/test_tracking.py`
- **Merge Log:** `docs/ops/PR_569_MERGE_LOG.md` (PR #569 Fix)
- **Worktree Rescue:** `docs/ops/WORKTREE_PATCHES_RECOVERY_20260105_REPORT.md`

### External Resources
- **MLflow Docs:** https://mlflow.org/docs/latest/
- **MLflow Tracking:** https://mlflow.org/docs/latest/tracking.html
- **MLflow Python API:** https://mlflow.org/docs/latest/python_api/mlflow.html

### Related PRs
- **PR #569:** MLflow CI Failures Fix (MLflow ≥3.0 Run Lifecycle Hardening)
- **PR #558:** Phase 16C Experiment Tracking (Optional MLflow Integration)

---

## Changelog

### 2026-01-05 - Initial Version
- Created after PR #569 merge (MLflow CI Failures Fix)
- Documented Run Lifecycle Best Practices
- Added Troubleshooting Section
- Included BacktestEngine Integration Examples

---

**Maintained by:** Peak_Trade DevOps Team  
**Questions?** Check `tests/test_tracking_mlflow_integration.py` for working examples  
**Issues?** See Troubleshooting section above or create GitHub Issue
