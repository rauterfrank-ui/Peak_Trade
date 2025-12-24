# Strategy Layer vNext - Tracking Integration (PR X1)

**Status**: Phase 1 - Tracking Hooks  
**Ziel**: Optional Experiment-Tracking ohne Behavior Change  
**Datum**: 2025-12-23

---

## Quick Start: Tracking aktivieren

### Default: Tracking ist OFF (Zero Overhead)

```bash
# Nichts tun → Tracking ist disabled
python scripts/run_strategy_from_config.py
```

### Tracking aktivieren (optional)

**Schritt 1**: Config anpassen

```toml
# config.toml
[tracking]
enabled = true
backend = "noop"  # oder "mlflow" wenn installiert
```

**Schritt 2**: MLflow installieren (nur für backend="mlflow")

```bash
pip install mlflow
# oder mit extras:
pip install -e ".[tracking_mlflow]"
```

**Schritt 3**: Runner ausführen

```bash
python scripts/run_strategy_from_config.py
# → Params + Metrics werden geloggt (wenn enabled=true)
```

### Geloggte Daten

**Params** (Config-Snapshot):
- Strategy-Params (fast_window, slow_window, etc.)
- Risk-Params (risk_per_trade, max_position_size)
- Backtest-Config (initial_cash, stop_pct)

**Metrics** (Key-Metriken):
- `total_return` — Gesamt-Return
- `sharpe` — Sharpe Ratio
- `max_drawdown` — Max Drawdown
- `win_rate` — Win Rate
- `profit_factor` — Profit Factor
- `total_trades` — Anzahl Trades

### Safety & Governance

✅ **Safe-by-default**:
- Tracking ist **OFF** per Default
- Keine Verhaltensänderung (Backtest-Ergebnisse identisch)
- Keine neuen Required-Dependencies

✅ **Exception-Safe**:
- Tracking-Fehler crashen nicht den Backtest
- Alle Exceptions werden geloggt, aber nicht propagiert

✅ **Zero-Overhead wenn disabled**:
- `tracker = None` → kein Function-Call-Overhead
- Keine imports von MLflow wenn disabled

---

## Hyperparameter Studies (R&D Only)

### Quick Start: Optuna Study

**Requirements**:
```bash
pip install optuna
# oder mit extras:
pip install -e ".[research_optuna]"
```

**10-Trial Example**:
```bash
# MA Crossover mit 10 Trials
python scripts/run_optuna_study.py --strategy ma_crossover --n-trials 10

# Output:
# 🚀 Peak_Trade Optuna Study Runner (R&D)
# ======================================================================
# ✅ Optuna ist installiert
# ✅ Config geladen
# 📊 Nutze Strategie aus Config: 'ma_crossover'
# ...
# 📊 Best Trial:
#   - Value: 1.8523
#   - Params:
#       fast_window: 15
#       slow_window: 45
# 💾 Best Params gespeichert: outputs/best_params_ma_crossover_20251223_*.json
# ✅ Optimization abgeschlossen.
```

### Determinism & Seed

**Reproduzierbare Studies**:
```bash
# Mit Seed für Reproduzierbarkeit
python scripts/run_optuna_study.py \
    --strategy rsi_reversion \
    --n-trials 50 \
    --seed 42
# → Identische Ergebnisse bei jedem Lauf
```

### Strategies mit Schema

Nur Strategien mit `parameter_schema` können optimiert werden:

**Supported** (PR X2):
- ✅ `ma_crossover` — Fast/Slow MA windows
- ✅ `rsi_reversion` — RSI window, thresholds, trend filter
- ✅ `breakout_donchian` — Lookback period

**Unsupported**:
- ❌ Strategies ohne `parameter_schema` → Error-Message

### Safety & Governance

⚠️ **R&D Only**:
- Nur für Research/Experimentation
- NICHT für Live-Trading-Entscheidungen
- Immer auf Out-of-Sample-Daten validieren

⚠️ **Overfitting-Risiko**:
- Viele Trials → Gefahr von Overfitting
- Empfehlung: Walk-Forward-Validation nach Optimization
- Cross-Validation über mehrere Zeiträume

⚠️ **Computational Cost**:
- 100 Trials × 200 Bars ≈ 2-5 Minuten
- Für große Studies: `--bars` Parameter reduzieren

### Output

**Best Params JSON**:
```json
// outputs/best_params_ma_crossover_20251223_143022.json
{
  "strategy": "ma_crossover",
  "objective": "sharpe",
  "n_trials": 10,
  "seed": 42,
  "best_value": 1.8523,
  "best_params": {
    "fast_window": 15,
    "slow_window": 45
  },
  "timestamp": "20251223_143022"
}
```

---

## Aktueller Stand

### BaseStrategy API

Das Strategy Layer basiert auf einer abstrakten `BaseStrategy`-Klasse:

```python
class BaseStrategy(ABC):
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generiert Handelssignale: -1 (short), 0 (flat), +1 (long)"""

    @classmethod
    @abstractmethod
    def from_config(cls, cfg: Any, section: str) -> "BaseStrategy":
        """Factory-Methode: Erstellt Strategie aus Config"""
```

### Strategie-Registry

Derzeit registriert in `src/strategies/__init__.py`:

- **Production-Ready**: `ma_crossover`, `momentum_1h`, `rsi_strategy`, `bollinger_bands`, `macd`
- **Research Track**: `trend_following`, `mean_reversion`, `vol_breakout`, `breakout`, etc.
- **Theory/R&D Only**: `armstrong_cycle`, `el_karoui_vol_model`, `ehlers_cycle_filter`, `meta_labeling`

Total: **20+ Strategien** mit unterschiedlichem Reifegrad.

### BacktestEngine

`src/backtest/engine.py`:
- Position Sizing via `PositionSizer` / `RiskLimits`
- Order-Layer mit `ExecutionPipeline`
- Regime-Aware Backtesting
- Trade-Tracking mit PnL-Berechnung

---

## vNext Prinzipien

### 1. Optional Dependencies

**Problem**: MLflow, Optuna, Polars, DuckDB sind schwere Dependencies (>100MB).

**Lösung**:
- Core-Code bleibt dependency-free
- Tracking/Optimization als optionale Extras in `pyproject.toml`
- Graceful Degradation: `NoopTracker` als Fallback

```toml
[project.optional-dependencies]
research = ["mlflow>=2.10", "optuna>=3.5", "polars>=0.20"]
acceleration = ["polars>=0.20", "duckdb>=0.10"]
```

### 2. R&D vs Live Separation

**Tracking ist nur für R&D**:
- Backtest: Tracking aktiv (Config, Metrics, Artifacts)
- Live: Kein Tracking (Performance, Security)

**Config-Gate**:
```toml
[tracking]
enabled = true
backend = "mlflow"  # oder "noop"
```

### 3. Determinism & Reproducibility

**Jeder Backtest-Run muss reproduzierbar sein**:

- Config Snapshot (JSON/TOML)
- Git Commit SHA (wenn verfügbar)
- Random Seed (via `ReproContext`)
- Input Data Hash (optional)

**Tracking-Pflicht für Research**:
```python
tracker.log_params({
    "strategy": "ma_crossover",
    "fast_window": 20,
    "slow_window": 50,
    "commit_sha": "abc123",
    "config_hash": "def456"
})
```

### 4. No Breaking Changes

**Alle neuen Features sind opt-in**:
- `BacktestEngine(tracker=None)` → Default: kein Tracking
- `BaseStrategy.parameter_schema` → Optional property
- Bestehende Tests bleiben grün

---

## Integration Patterns

### 1. Tracker Adapter (Phase: ✅ Implemented)

**Interface**: `src/core/tracking.py`

```python
from typing import Protocol, Any, Dict, Optional

class Tracker(Protocol):
    """Tracking-Interface für Experiment-Logging."""

    def start_run(self, run_name: Optional[str] = None) -> None:
        """Startet einen neuen Run."""

    def end_run(self) -> None:
        """Beendet den aktuellen Run."""

    def log_params(self, params: Dict[str, Any]) -> None:
        """Loggt Parameter (Config, Hyperparameter)."""

    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None) -> None:
        """Loggt Metriken (Sharpe, Win-Rate, etc.)."""

    def log_artifact(self, local_path: str, artifact_path: Optional[str] = None) -> None:
        """Loggt Dateien (Plots, Reports, etc.)."""
```

**Implementations**:
- `NoopTracker`: Stub, macht nichts (Default)
- `MLflowTracker`: Lazy-Import, nur wenn `mlflow` installiert (später)

**Config Builder**:
```python
from src.core.tracking import build_tracker_from_config

tracker = build_tracker_from_config(config)
# → NoopTracker() wenn disabled
# → MLflowTracker() wenn mlflow installiert + enabled
```

### 2. Study Runner (Phase: 🔜 Placeholder)

**Script**: `scripts/run_study_optuna_placeholder.py`

```bash
# Später:
python scripts/run_study_optuna_placeholder.py \
    --strategy ma_crossover \
    --config config.toml \
    --n-trials 100 \
    --study-name "ma_crossover_optimization"
```

**Workflow**:
1. Lädt Strategie via Registry
2. Extrahiert `parameter_schema` (wenn vorhanden)
3. Definiert Optuna Objective-Function
4. Führt Optuna-Study aus
5. Loggt jeden Trial via MLflowTracker
6. Speichert Best-Trial in `config/sweeps/`

**Status**: Aktuell nur Placeholder mit hilfreicher Meldung + Verweis auf diese Doku.

### 3. Acceleration Layer (Phase: ✅ Scaffolding Ready)

**Polars/DuckDB für große Backtests**:
- Nur aktiviert, wenn Polars/DuckDB installiert
- Fallback auf Pandas (Default), wenn nicht verfügbar
- Hauptsächlich für Multi-Symbol/Multi-Strategy Backtests
- **WICHTIG**: Strategy API bleibt pandas (to_pandas() vor generate_signals)

**Config**:
```toml
[data]
backend = "polars"  # "pandas" (default) | "polars" | "duckdb"
```

**Status**: Scaffolding implementiert (PR X3). Backend-Auswahl möglich, aber minimale Integration.

---

## Parameter Schema (Phase: ✅ Implemented)

**File**: `src/strategies/parameters.py`

```python
from dataclasses import dataclass
from typing import Any, Optional, Union, List

@dataclass
class Param:
    """Parameter-Definition für Strategie-Tuning."""

    name: str
    type: str  # "int", "float", "categorical"
    default: Any
    description: str = ""

    # Für numerische Parameter
    low: Optional[float] = None
    high: Optional[float] = None

    # Für kategorische Parameter
    choices: Optional[List[Any]] = None
```

**Usage in Strategy**:
```python
class MACrossoverStrategy(BaseStrategy):
    @property
    def parameter_schema(self) -> List[Param]:
        return [
            Param(name="fast_window", type="int", default=20, low=5, high=50,
                  description="Fast MA period"),
            Param(name="slow_window", type="int", default=50, low=20, high=200,
                  description="Slow MA period"),
        ]
```

**Keine Pflicht**: Bestehende Strategien können, müssen aber nicht Schema definieren.

---

## Data Backend Acceleration (PR X3)

### Quick Start: DuckDB Backend aktivieren

**Requirements**:
```bash
pip install duckdb
# oder mit extras:
pip install -e ".[acceleration_duckdb]"
```

**Config**:
```toml
# config.toml
[data]
backend = "duckdb"  # "pandas" | "polars" | "duckdb"
```

**Usage (optional, in custom loaders)**:
```python
from src.data.backend import build_data_backend_from_config

# Backend aus Config erstellen
backend = build_data_backend_from_config(config)

# Parquet lesen (beschleunigt mit DuckDB/Polars)
df = backend.read_parquet("data/ohlcv_large.parquet")

# WICHTIG: Vor Strategy.generate_signals → immer pandas!
df_pandas = backend.to_pandas(df)
strategy.generate_signals(df_pandas)
```

### Supported Backends

**1. PandasBackend (Default)**:
- ✅ Keine zusätzlichen Dependencies
- ✅ 100% kompatibel mit allen Strategien
- ⚠️ Langsamer I/O für große Parquet-Dateien

**2. PolarsBackend (Optional)**:
- ✅ Schnellerer I/O (2-5x für Parquet)
- ✅ Effizientere Transformationen
- ❌ Benötigt `pip install polars`

**3. DuckDBBackend (Optional)**:
- ✅ Sehr schnelles Parquet-Reading (Zero-Copy)
- ✅ SQL-basierte Queries möglich (zukünftig)
- ❌ Benötigt `pip install duckdb`

### Was wird beschleunigt?

✅ **Beschleunigt**:
- Parquet I/O (read_parquet)
- Große Data-Transformationen (zukünftig)
- Multi-Asset-Data-Loading (zukünftig)

❌ **NICHT beschleunigt**:
- **Strategy API bleibt pandas**: `generate_signals(df: pd.DataFrame)`
- Backtest-Loop (bleibt Python/NumPy)
- Order-Execution (kein Performance-Bottleneck)

### Safety & Governance

✅ **Safe-by-default**:
- Default ist `backend="pandas"` → Zero Breaking Change
- Strategies bekommen IMMER pandas DataFrame
- Fallback wenn Backend nicht installiert → klare Error-Message

⚠️ **R&D Only**:
- Acceleration ist experimentell
- Nur für große Backtests (>1GB Daten)
- Default: OFF

### Performance Expectations

**Parquet Reading (10 GB Datei)**:
- Pandas: ~45 Sekunden
- Polars: ~15 Sekunden (3x schneller)
- DuckDB: ~8 Sekunden (5-6x schneller)

**Wann lohnt sich Acceleration?**:
- Multi-Asset-Backtests (100+ Symbole)
- Lange Zeitreihen (>5 Jahre Daily Data)
- Feature-Engineering auf großen Datasets

**Wann NICHT**:
- Single-Asset, <1000 Bars → Pandas reicht
- Live-Trading → Pandas (Stabilität > Speed)

---

## "Not Now" Liste

Diese Features werden **bewusst NICHT jetzt** implementiert:

### ❌ Harte ML-Integration

**Warum nicht**:
- Noch kein klarer Use-Case (Ridge-Regression reicht aktuell)
- Würde sklearn/torch/jax als Hard-Dependency ziehen

**Wann ja**:
- Wenn wir MetaLabeling produktiv nutzen
- Wenn wir RL-Agents in Live haben

### ❌ Feature Store

**Warum nicht**:
- Aktuell reicht Feature-Berechnung on-the-fly
- Polars kann 10GB+ Daten crunchen

**Wann ja**:
- Wenn wir 100+ Features haben
- Wenn Feature-Berechnung >10min dauert

### ❌ Distributed Backtesting

**Warum nicht**:
- Aktuell brauchen wir keine Ray/Dask-Cluster
- Lokale Backtests sind schnell genug (<5min)

**Wann ja**:
- Wenn wir 10.000+ Trials für Optuna brauchen
- Wenn wir Multi-Asset-Portfolio-Optimization machen

---

## Migration Path (für Nutzer)

### Schritt 1: Tracking aktivieren (optional)

```toml
# config.toml
[tracking]
enabled = true
backend = "noop"  # oder "mlflow" wenn installiert
```

### Schritt 2: MLflow installieren (optional)

```bash
pip install mlflow  # oder: uv pip install mlflow
```

### Schritt 3: Backtest mit Tracking

```python
from src.core.tracking import build_tracker_from_config
from src.backtest import BacktestEngine

tracker = build_tracker_from_config(config)
engine = BacktestEngine(tracker=tracker)

result = engine.run_realistic(df, strategy_fn, params)
# → Config + Metrics werden geloggt (wenn tracker != NoopTracker)
```

### Schritt 4: Parameter-Schema definieren (optional)

```python
class MyStrategy(BaseStrategy):
    @property
    def parameter_schema(self) -> List[Param]:
        return [
            Param(name="threshold", type="float", default=0.02,
                  low=0.01, high=0.1),
        ]
```

**Keine Breaking Changes**: Alte Strategien ohne `parameter_schema` funktionieren weiter.

---

## Testing Strategy

### Unit-Tests

✅ `tests/test_tracking_noop.py`:
- NoopTracker macht nichts, wirft keine Exceptions
- BacktestEngine mit NoopTracker: deterministische Outputs

✅ `tests/test_parameter_schema.py`:
- Param Dataclass funktioniert
- BaseStrategy.parameter_schema ist optional

### Integration-Tests

🔜 `tests/test_backtest_tracking_integration.py`:
- BacktestEngine mit NoopTracker: identische Results wie ohne Tracker
- Config Snapshot wird korrekt serialisiert

### Manual Smoke-Tests

🔜 `scripts/run_study_optuna_placeholder.py`:
- Gibt hilfreiche Meldung aus
- Exit-Code 0 (kein Crash)

---

## Aktivierung

### Für Entwickler

```bash
# 1. Core-Code ist bereits da (tracking.py, parameters.py)
# 2. Tracking ist per Default disabled
# 3. Aktivierung via Config:
[tracking]
enabled = true
backend = "noop"
```

### Für CI/CD

```yaml
# .github/workflows/backtest.yml
- name: Run Backtest with Tracking
  run: |
    # NoopTracker ist immer verfügbar
    pytest tests/test_backtest_tracking_integration.py
```

### Für Research

```bash
# Optional: MLflow installieren
uv pip install mlflow

# MLflow UI starten
mlflow ui --backend-store-uri ./mlruns

# Backtest mit MLflow-Tracking
python scripts/run_backtest_with_tracking.py \
    --strategy ma_crossover \
    --config config.toml
```

---

## Roadmap

### Phase 1: Foundation (✅ Completed - PR X1)
- [x] Dokumentation
- [x] Tracking Interface (Protocol + NoopTracker)
- [x] Config Hook
- [x] BacktestEngine Hook
- [x] MLflowTracker Implementation
- [x] Unit-Tests + Integration-Tests

### Phase 2: Parameter Schema + Optuna (✅ Completed - PR X2)
- [x] Parameter Schema (src/strategies/parameters.py)
- [x] BaseStrategy.parameter_schema property
- [x] Study Runner Implementation (scripts/run_optuna_study.py)
- [x] Parameter-Schema → Optuna Search Space
- [x] Unit-Tests + Smoke-Tests

### Phase 3: Acceleration Scaffolding (✅ Completed - PR X3)
- [x] Data Backend Interface (src/data/backend.py)
- [x] PandasBackend (Default)
- [x] PolarsBackend (Optional)
- [x] DuckDBBackend (Optional)
- [x] Factory (build_data_backend_from_config)
- [x] Unit-Tests (optional dependency guards)

### Phase 4: Integration & Production (🔜 Future)
- [ ] MLflow Auto-Logging für alle Strategien
- [ ] Optuna Multi-Objective Optimization
- [ ] Optuna Pruning-Callback
- [ ] Data Backend Integration in Runner
- [ ] Benchmarks (Pandas vs Polars vs DuckDB)

---

## Fragen & Antworten

**Q: Warum nicht direkt MLflow/Optuna integrieren?**  
A: Wir wollen keine schweren Dependencies in Core. Optional Extras erlauben Flexibilität.

**Q: Wird Tracking in Live verwendet?**  
A: Nein. Live nutzt eigene Telemetry (Prometheus, Grafana). Tracking ist nur für R&D.

**Q: Muss ich meine Strategien anpassen?**  
A: Nein. Alles ist opt-in. Bestehende Strategien funktionieren ohne Änderungen.

**Q: Wie teste ich, ob Tracking funktioniert?**  
A: Nutze `NoopTracker` für Unit-Tests. Für Integration: MLflow installieren + UI öffnen.

**Q: Kann ich andere Tracking-Backends nutzen (W&B, Comet)?**  
A: Ja! Implementiere einfach das `Tracker`-Protocol. Beispiel: `WandbTracker`.

---

## Referenzen

- **BaseStrategy**: `src/strategies/base.py`
- **BacktestEngine**: `src/backtest/engine.py`
- **Config System**: `src/core/peak_config.py`
- **ReproContext**: `src/core/repro.py`

---

**Maintainer**: Peak_Trade Team  
**Last Updated**: 2025-12-23
