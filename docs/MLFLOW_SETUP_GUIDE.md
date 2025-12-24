# MLflow Setup & Best Practices Guide

**Ziel**: MLflow für Experiment-Tracking in Peak_Trade nutzen  
**Audience**: Research Team, Strategy Developers  
**Status**: Production-Ready (Phase 2)

---

## Quick Start (5 Minuten)

### 1. Installation

```bash
# Via pip
pip install mlflow

# Via uv (empfohlen)
uv pip install mlflow

# Optional: Mit Extras für Remote-Backends
pip install mlflow[extras]  # PostgreSQL, S3, etc.
```

### 2. Config aktivieren

```toml
# config.toml
[tracking]
enabled = true
backend = "mlflow"

[tracking.mlflow]
tracking_uri = "./mlruns"  # Lokal
experiment_name = "strategy_optimization"
```

### 3. Backtest mit Tracking

```python
from src.core.tracking import build_tracker_from_config
from src.backtest import BacktestEngine
from src.core.peak_config import load_config

# Config laden
config = load_config()

# Tracker erstellen
tracker = build_tracker_from_config(config)

# Backtest mit Tracking
tracker.start_run("ma_crossover_20_50")

engine = BacktestEngine(tracker=tracker)
result = engine.run_realistic(df, strategy_fn, params)

tracker.end_run()
```

### 4. MLflow UI öffnen

```bash
mlflow ui --backend-store-uri ./mlruns
# → http://localhost:5000
```

**Fertig!** Deine Backtests werden jetzt in MLflow geloggt.

---

## MLflow Konzepte

### Experiments

**Was**: Container für verwandte Runs (z.B. "MA Crossover Optimization")

```python
tracker = MLflowTracker(
    tracking_uri="./mlruns",
    experiment_name="ma_crossover_optimization"  # ← Experiment
)
```

**Best Practice**: Ein Experiment pro Strategie oder Optimization-Kampagne.

### Runs

**Was**: Ein einzelner Backtest/Training-Lauf

```python
tracker.start_run("ma_crossover_fast20_slow50")  # ← Run
tracker.log_params({"fast_window": 20, "slow_window": 50})
tracker.log_metrics({"sharpe": 1.8})
tracker.end_run()
```

**Best Practice**: Beschreibende Run-Namen (inkl. Key-Parameter).

### Parameters

**Was**: Input-Config (Hyperparameter, Settings)

```python
tracker.log_params({
    "strategy": "ma_crossover",
    "fast_window": 20,
    "slow_window": 50,
    "stop_pct": 0.02,
    "initial_cash": 10000,
})
```

**Best Practice**: Alle relevanten Config-Werte loggen (für Reproduzierbarkeit).

### Metrics

**Was**: Output-Metriken (Sharpe, Win-Rate, etc.)

```python
tracker.log_metrics({
    "sharpe": 1.8,
    "total_return": 0.25,
    "max_drawdown": -0.15,
    "win_rate": 0.55,
})
```

**Best Practice**: Konsistente Metrik-Namen über alle Runs.

### Artifacts

**Was**: Dateien (Plots, Reports, Models)

```python
tracker.log_artifact("equity_curve.png", artifact_path="plots/")
tracker.log_artifact("backtest_report.txt", artifact_path="reports/")
```

**Best Practice**: Strukturierte Artifact-Pfade (`plots/`, `reports/`, `models/`).

### Tags

**Was**: Metadata für Filtering/Grouping

```python
tracker.set_tags({
    "env": "dev",
    "version": "1.0",
    "author": "alice",
    "market": "BTC/EUR",
})
```

**Best Practice**: Tags für Umgebung, Version, Autor setzen.

---

## Tracking-Patterns

### Pattern 1: Context Manager (Empfohlen)

```python
from src.core.tracking import MLflowTracker

with MLflowTracker(
    tracking_uri="./mlruns",
    experiment_name="test",
    auto_start_run=True
) as tracker:
    tracker.log_params({"foo": "bar"})
    tracker.log_metrics({"sharpe": 1.8})
    # Run wird automatisch beendet (auch bei Exceptions)
```

**Vorteile**:
- ✅ Automatisches Cleanup
- ✅ Exception-Safe
- ✅ Weniger Boilerplate

### Pattern 2: Manual Start/End

```python
tracker = MLflowTracker(tracking_uri="./mlruns")
tracker.start_run("my_run")

try:
    # ... Backtest ...
    tracker.log_metrics({"sharpe": 1.8})
finally:
    tracker.end_run()  # Immer beenden!
```

**Wann nutzen**: Wenn Run-Lifecycle komplex ist.

### Pattern 3: Auto-Logging via BacktestEngine

```python
from src.core.tracking import build_tracker_from_config

tracker = build_tracker_from_config(config)
tracker.start_run("backtest_001")

engine = BacktestEngine(tracker=tracker)
result = engine.run_realistic(df, strategy_fn, params)
# → Config, Metrics, Artifacts werden automatisch geloggt

tracker.end_run()
```

**Vorteile**:
- ✅ Automatisches Logging (Config, Metrics, Plots)
- ✅ Konsistente Struktur
- ✅ Weniger Code

**Empfohlen für**: Standard-Backtests.

---

## Backend-Optionen

### Local File Store (Default)

```toml
[tracking.mlflow]
tracking_uri = "./mlruns"
```

**Vorteile**:
- ✅ Einfach, kein Setup
- ✅ Schnell
- ✅ Gut für lokale Entwicklung

**Nachteile**:
- ❌ Nicht multi-user
- ❌ Keine Remote-Access

### SQLite Backend

```toml
[tracking.mlflow]
tracking_uri = "sqlite:///mlflow.db"
```

**Vorteile**:
- ✅ Einfach, eine Datei
- ✅ Schneller als File Store

**Nachteile**:
- ❌ Nicht multi-user (Write-Locks)

### PostgreSQL Backend (Production)

```toml
[tracking.mlflow]
tracking_uri = "postgresql://user:pass@localhost/mlflow"
```

**Vorteile**:
- ✅ Multi-User
- ✅ Production-Ready
- ✅ Backup/Restore

**Setup**:
```bash
# PostgreSQL installieren
brew install postgresql  # macOS
sudo apt install postgresql  # Linux

# DB erstellen
createdb mlflow

# MLflow mit PostgreSQL
pip install psycopg2-binary
```

### Remote MLflow Server

```toml
[tracking.mlflow]
tracking_uri = "http://mlflow-server:5000"
```

**Vorteile**:
- ✅ Multi-User
- ✅ Zentralisiert
- ✅ Team-Collaboration

**Setup**:
```bash
# Server starten
mlflow server \
    --backend-store-uri postgresql://user:pass@localhost/mlflow \
    --default-artifact-root s3://my-bucket/mlflow \
    --host 0.0.0.0 \
    --port 5000
```

---

## Best Practices

### 1. Experiment-Naming

**Gut**:
- `ma_crossover_optimization`
- `rsi_strategy_parameter_sweep`
- `portfolio_backtest_2024_q1`

**Schlecht**:
- `test`
- `experiment1`
- `my_experiment`

**Regel**: Beschreibend, eindeutig, datiert (wenn nötig).

### 2. Run-Naming

**Gut**:
- `ma_crossover_fast20_slow50`
- `rsi_strategy_period14_oversold30`
- `backtest_2024_01_15_v1`

**Schlecht**:
- `run1`
- `test`
- `asdf`

**Regel**: Inkludiere Key-Parameter oder Datum.

### 3. Parameter-Logging

**Vollständig loggen**:
```python
tracker.log_params({
    # Strategy-Params
    "strategy": "ma_crossover",
    "fast_window": 20,
    "slow_window": 50,

    # Risk-Params
    "stop_pct": 0.02,
    "risk_per_trade": 0.01,

    # Backtest-Config
    "initial_cash": 10000,
    "fee_bps": 10,

    # Metadata
    "commit_sha": get_git_sha(),
    "data_start": "2023-01-01",
    "data_end": "2024-01-01",
})
```

**Regel**: Alle Werte loggen, die Ergebnis beeinflussen.

### 4. Metrik-Naming

**Konsistent**:
```python
# Gut: Konsistente Namen
tracker.log_metrics({
    "sharpe_ratio": 1.8,
    "total_return": 0.25,
    "max_drawdown": -0.15,
    "win_rate": 0.55,
})

# Schlecht: Inkonsistent
tracker.log_metrics({
    "sharpe": 1.8,
    "return": 0.25,  # Konflikt mit Python-Keyword
    "dd": -0.15,     # Unklar
    "winRate": 0.55, # camelCase statt snake_case
})
```

**Regel**: snake_case, beschreibend, konsistent.

### 5. Artifact-Organisation

**Strukturiert**:
```
artifacts/
├── plots/
│   ├── equity_curve.png
│   ├── drawdown.png
│   └── trades_distribution.png
├── reports/
│   ├── backtest_report.txt
│   ├── trades_summary.json
│   └── risk_metrics.json
├── models/
│   └── strategy_weights.pkl
└── config/
    └── config_snapshot.json
```

**Regel**: Klare Verzeichnis-Struktur.

### 6. Tags für Filtering

```python
tracker.set_tags({
    "env": "dev",           # dev/staging/prod
    "version": "1.0.0",     # Code-Version
    "author": "alice",      # Wer hat Run gemacht
    "market": "BTC/EUR",    # Welches Asset
    "timeframe": "1h",      # Welcher Timeframe
    "regime": "trending",   # Markt-Regime
})
```

**Regel**: Tags für häufige Filter-Kriterien.

### 7. Error Handling

```python
tracker.start_run("my_run")

try:
    # ... Backtest ...
    tracker.log_metrics({"sharpe": 1.8})
    tracker.set_tags({"status": "success"})
except Exception as e:
    tracker.set_tags({"status": "failed", "error": str(e)})
    raise
finally:
    tracker.end_run()
```

**Regel**: Errors als Tags loggen, Run immer beenden.

---

## MLflow UI

### Runs vergleichen

1. UI öffnen: `mlflow ui`
2. Experiment auswählen
3. Runs selektieren (Checkbox)
4. "Compare" Button klicken
5. Parallel Coordinates Plot / Scatter Plot nutzen

### Beste Runs finden

1. Runs nach Metrik sortieren (z.B. "sharpe_ratio")
2. Filter nutzen: `metrics.sharpe_ratio > 1.5`
3. Tags filtern: `tags.market = "BTC/EUR"`

### Artifacts anzeigen

1. Run auswählen
2. "Artifacts" Tab
3. Plots/Reports anklicken → Preview

---

## Troubleshooting

### Problem: "ModuleNotFoundError: No module named 'mlflow'"

**Lösung**:
```bash
pip install mlflow
```

### Problem: "Permission denied: ./mlruns"

**Lösung**:
```bash
chmod -R 755 ./mlruns
# oder: anderen tracking_uri nutzen
```

### Problem: "Port 5000 already in use"

**Lösung**:
```bash
# Anderen Port nutzen
mlflow ui --port 5001
```

### Problem: "Too many parameters (>500)"

**Lösung**:
```python
# MLflow hat 500-Param-Limit
# Lösung: Nested Params flattenen oder als Artifact speichern
tracker.log_artifact("full_config.json")
```

### Problem: "Artifacts nicht sichtbar"

**Lösung**:
```bash
# Check: Artifact-Pfad korrekt?
ls ./mlruns/0/<run_id>/artifacts/

# Check: Datei existiert?
tracker.log_artifact("/path/to/file.png")  # Absoluter Pfad
```

---

## Performance-Tipps

### 1. Batch-Logging

```python
# Gut: Batch
tracker.log_params({
    "param1": 1,
    "param2": 2,
    "param3": 3,
})

# Schlecht: Einzeln (langsam)
tracker.log_params({"param1": 1})
tracker.log_params({"param2": 2})
tracker.log_params({"param3": 3})
```

### 2. Artifacts komprimieren

```python
# Große Dateien komprimieren
import gzip
with gzip.open("trades.json.gz", "wt") as f:
    json.dump(trades, f)

tracker.log_artifact("trades.json.gz")
```

### 3. Selective Logging

```python
# Nicht jede Iteration loggen
if step % 10 == 0:
    tracker.log_metrics({"equity": equity}, step=step)
```

---

## Security

### 1. Credentials

**Niemals** in Config committen:

```toml
# ❌ BAD
[tracking.mlflow]
tracking_uri = "postgresql://user:password@host/db"

# ✅ GOOD
[tracking.mlflow]
tracking_uri = "${MLFLOW_TRACKING_URI}"  # Env-Variable
```

```bash
export MLFLOW_TRACKING_URI="postgresql://user:password@host/db"
```

### 2. Access Control

**MLflow Server mit Auth**:
```bash
mlflow server \
    --backend-store-uri postgresql://... \
    --default-artifact-root s3://... \
    --host 0.0.0.0 \
    --port 5000 \
    --gunicorn-opts "--access-logfile - --error-logfile -"
```

**Nginx Reverse Proxy** mit Basic Auth:
```nginx
location /mlflow {
    auth_basic "MLflow";
    auth_basic_user_file /etc/nginx/.htpasswd;
    proxy_pass http://localhost:5000;
}
```

---

## Integration mit Optuna (Phase 3)

**Preview** (noch nicht implementiert):

```python
import optuna
from src.core.tracking import MLflowTracker

def objective(trial):
    # Optuna schlägt Parameter vor
    fast_window = trial.suggest_int("fast_window", 5, 50)
    slow_window = trial.suggest_int("slow_window", 20, 200)

    # MLflow loggt Trial
    with MLflowTracker(auto_start_run=True) as tracker:
        tracker.log_params({
            "fast_window": fast_window,
            "slow_window": slow_window,
        })

        # Backtest
        result = run_backtest(fast_window, slow_window)

        tracker.log_metrics({"sharpe": result.sharpe})

        return result.sharpe

# Optuna Study
study = optuna.create_study(direction="maximize")
study.optimize(objective, n_trials=100)
```

**Status**: Phase 3 (geplant).

---

## Referenzen

### MLflow Docs
- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)
- [MLflow Tracking](https://mlflow.org/docs/latest/tracking.html)
- [MLflow Python API](https://mlflow.org/docs/latest/python_api/index.html)

### Peak_Trade Docs
- `docs/STRATEGY_LAYER_VNEXT.md` — Roadmap
- `src/core/tracking.py` — Tracking Interface
- `tests/test_tracking_mlflow_integration.py` — Integration-Tests

---

**Maintainer**: Peak_Trade Strategy Team  
**Last Updated**: 2025-12-23  
**Status**: Production-Ready (Phase 2)
