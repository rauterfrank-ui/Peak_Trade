# Phase 29 – Experiment-Layer & Parameter-Sweeps

## Übersicht

Phase 29 implementiert einen Experiment-Layer für systematische Parameter-Sweeps über Strategien und Regime-Detection-Konfigurationen.

### Kernkomponenten

| Komponente | Beschreibung |
|-----------|--------------|
| `ParamSweep` | Definiert einen Parameter-Bereich für Sweeps |
| `ExperimentConfig` | Konfiguration für einen Experiment-Durchlauf |
| `SweepResultRow` | Ein einzelnes Ergebnis aus dem Sweep |
| `ExperimentResult` | Gesamtergebnis eines Experiments |
| `ExperimentRunner` | Führt Sweeps aus und sammelt Ergebnisse |

### Helper-Module

| Modul | Beschreibung |
|-------|--------------|
| `strategy_sweeps` | Vordefinierte Sweeps für alle Strategien |
| `regime_sweeps` | Vordefinierte Sweeps für Regime-Detection |

---

## Installation & Abhängigkeiten

Keine zusätzlichen Abhängigkeiten erforderlich. Nutzt:
- `pandas` für DataFrames
- `numpy` für numerische Operationen
- `itertools.product` für kartesische Produkte

---

## Quick Start

### Einfacher Strategy-Sweep

```python
from src.experiments import (
    ExperimentConfig,
    ExperimentRunner,
    ParamSweep,
    get_strategy_sweeps,
)

# Option 1: Mit vordefinierten Sweeps
config = ExperimentConfig(
    name="MA Crossover Optimization",
    strategy_name="ma_crossover",
    param_sweeps=get_strategy_sweeps("ma_crossover", "medium"),
    symbols=["BTC/EUR"],
    timeframe="1h",
    start_date="2024-01-01",
    end_date="2024-06-01",
)

# Option 2: Mit manuellen Sweeps
config = ExperimentConfig(
    name="MA Crossover Manual",
    strategy_name="ma_crossover",
    param_sweeps=[
        ParamSweep("fast_period", [5, 10, 15, 20]),
        ParamSweep("slow_period", [50, 100, 150, 200]),
    ],
)

# Runner erstellen und ausführen
runner = ExperimentRunner()
result = runner.run(config)

# Ergebnisse analysieren
df = result.to_dataframe()
best = result.get_best_by_metric("sharpe_ratio", top_n=5)
```

### CLI-Verwendung

```bash
# Einfacher Sweep
python3 scripts/run_experiment_sweep.py --strategy ma_crossover --granularity medium

# Mit mehreren Symbolen und Zeitraum
python3 scripts/run_experiment_sweep.py \
    --strategy vol_breakout \
    --symbols BTC/EUR ETH/EUR \
    --start 2024-01-01 \
    --end 2024-06-01

# Mit Regime-Detection
python3 scripts/run_experiment_sweep.py \
    --strategy vol_breakout \
    --with-regime \
    --detector volatility_breakout

# Parallel ausführen
python3 scripts/run_experiment_sweep.py \
    --strategy ma_crossover \
    --parallel \
    --workers 4

# Dry-Run (nur Parameter anzeigen)
python3 scripts/run_experiment_sweep.py \
    --strategy ma_crossover \
    --dry-run

# Verfügbare Strategien
python3 scripts/run_experiment_sweep.py --list-strategies
```

---

## API-Referenz

### ParamSweep

```python
@dataclass
class ParamSweep:
    name: str              # Parameter-Name
    values: List[Any]      # Liste möglicher Werte
    description: str       # Optional: Beschreibung

    @classmethod
    def from_range(cls, name, start, stop, step)    # Aus Range

    @classmethod
    def from_logspace(cls, name, start, stop, num)  # Logarithmisch
```

**Beispiele:**

```python
# Explizite Werte
sweep = ParamSweep("fast_period", [5, 10, 15, 20])

# Aus Range
sweep = ParamSweep.from_range("period", 10, 50, 5)
# -> [10, 15, 20, 25, 30, 35, 40, 45, 50]

# Logarithmisch
sweep = ParamSweep.from_logspace("window", 10, 1000, 4)
# -> [10, 46, 215, 1000]
```

### ExperimentConfig

```python
@dataclass
class ExperimentConfig:
    name: str                           # Experiment-Name
    strategy_name: str                  # Strategie aus Registry
    param_sweeps: List[ParamSweep]      # Parameter-Sweeps
    symbols: List[str]                  # Trading-Symbole
    timeframe: str                      # z.B. "1h", "4h", "1d"
    start_date: Optional[str]           # Backtest-Start
    end_date: Optional[str]             # Backtest-Ende
    initial_capital: float = 10000.0    # Startkapital
    regime_config: Optional[Dict]       # Regime-Detection Config
    switching_config: Optional[Dict]    # Strategy-Switching Config
    base_params: Dict[str, Any]         # Feste Parameter
    metrics_to_collect: List[str]       # Gewünschte Metriken
    parallel: bool = False              # Parallele Ausführung
    max_workers: int = 4                # Anzahl Worker
    save_results: bool = True           # Auto-Save
    output_dir: str                     # Output-Verzeichnis
```

**Properties:**

```python
config.num_combinations      # Anzahl aller Kombinationen
config.generate_param_combinations()  # Kartesisches Produkt
config.get_experiment_id()   # Eindeutige ID
```

### ExperimentRunner

```python
class ExperimentRunner:
    def __init__(
        self,
        backtest_fn: Optional[BacktestFunction] = None,
        progress_callback: Optional[Callable] = None,
    ) -> None

    def run(self, config, dry_run=False) -> ExperimentResult
    def run_parallel(self, config) -> ExperimentResult
```

**Custom Backtest-Funktion:**

```python
def my_backtest(
    strategy_name: str,
    params: Dict[str, Any],
    symbol: str,
    timeframe: str,
    start_date: Optional[str],
    end_date: Optional[str],
    initial_capital: float,
) -> Dict[str, float]:
    # Führe Backtest durch...
    return {
        "total_return": 0.15,
        "sharpe_ratio": 1.2,
        "max_drawdown": -0.08,
    }

runner = ExperimentRunner(backtest_fn=my_backtest)
```

### ExperimentResult

```python
@dataclass
class ExperimentResult:
    experiment_id: str
    config: ExperimentConfig
    results: List[SweepResultRow]
    total_runtime_seconds: float

    @property
    def num_runs(self) -> int
    @property
    def num_successful(self) -> int
    @property
    def success_rate(self) -> float

    def to_dataframe(self) -> pd.DataFrame
    def get_best_by_metric(self, metric, ascending=False, top_n=1)
    def get_summary_stats(self) -> Dict
    def save_csv(self, filepath)
    def save_parquet(self, filepath)
```

---

## Vordefinierte Sweeps

### Strategy Sweeps

```python
from src.experiments import get_strategy_sweeps

# Verfügbare Strategien
strategies = [
    "ma_crossover",
    "bollinger",
    "macd",
    "momentum",
    "trend_following",
    "vol_breakout",
    "mean_reversion",
    "mean_reversion_channel",
    "rsi_reversion",
    "breakout_donchian",
]

# Granularitäten
granularities = ["coarse", "medium", "fine"]

# Beispiel
sweeps = get_strategy_sweeps("ma_crossover", "medium")
# -> [ParamSweep("fast_period", [5,10,15,20,30]),
#     ParamSweep("slow_period", [50,75,100,150,200])]
```

### Regime Sweeps

```python
from src.experiments import (
    get_volatility_detector_sweeps,
    get_range_compression_detector_sweeps,
    get_strategy_switching_sweeps,
    get_combined_regime_strategy_sweeps,
)

# Volatility Detector
sweeps = get_volatility_detector_sweeps("medium")
# -> [ParamSweep("regime_vol_window", [...]),
#     ParamSweep("regime_vol_percentile_breakout", [...]),
#     ...]

# Range Compression Detector
sweeps = get_range_compression_detector_sweeps("medium")

# Strategy + Regime kombiniert
sweeps = get_combined_regime_strategy_sweeps(
    "vol_breakout",
    "volatility_breakout",
    "medium",
)
```

---

## Output-Formate

### CSV/Parquet

```
reports/experiments/
├── ma_crossover_abc123_20240601_143052.csv
├── ma_crossover_abc123_20240601_143052.parquet
└── ma_crossover_abc123_20240601_143052_summary.json
```

### DataFrame-Struktur

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| `experiment_id` | str | Experiment-ID |
| `run_id` | str | Eindeutige Run-ID |
| `strategy_name` | str | Strategie |
| `symbol` | str | Trading-Symbol |
| `param_*` | various | Sweep-Parameter |
| `metric_*` | float | Berechnete Metriken |
| `success` | bool | Erfolgreich? |
| `runtime_seconds` | float | Laufzeit |

---

## Best Practices

### 1. Granularität wählen

- **coarse**: Schnelle Exploration, wenige Kombinationen
- **medium**: Guter Kompromiss für Optimierung
- **fine**: Detaillierte Analyse, viele Kombinationen

### 2. Parallelisierung

```python
# Für CPU-intensive Backtests
config = ExperimentConfig(
    ...,
    parallel=True,
    max_workers=4,  # CPU-Kerne - 1
)
result = runner.run_parallel(config)
```

### 3. Schrittweise Optimierung

```python
# Schritt 1: Grobe Suche
config_coarse = ExperimentConfig(
    param_sweeps=get_strategy_sweeps("ma_crossover", "coarse"),
)
result_coarse = runner.run(config_coarse)

# Schritt 2: Best-Bereich identifizieren
best = result_coarse.get_best_by_metric("sharpe_ratio", top_n=3)
best_fast = [r.params["fast_period"] for r in best]

# Schritt 3: Feiner Sweep um beste Werte
refined_sweeps = [
    ParamSweep("fast_period", range(min(best_fast)-5, max(best_fast)+5)),
    ...
]
```

### 4. Regime-Aware Sweeps

```python
# Strategie UND Regime-Detection optimieren
sweeps = get_combined_regime_strategy_sweeps(
    "vol_breakout",
    "volatility_breakout",
    "medium",
)

config = ExperimentConfig(
    strategy_name="vol_breakout",
    param_sweeps=sweeps,
    regime_config={"enabled": True},
)
```

---

## Dateien & Struktur

```
src/experiments/
├── __init__.py           # Public API
├── base.py               # ParamSweep, ExperimentConfig, Runner
├── strategy_sweeps.py    # Strategie-Sweeps
└── regime_sweeps.py      # Regime-Sweeps

scripts/
└── run_experiment_sweep.py  # CLI-Tool

tests/
├── test_experiments_base.py
├── test_experiments_strategy_sweeps.py
├── test_experiments_regime_sweeps.py
└── test_experiments_integration.py
```

---

## Tests

```bash
# Alle Experiment-Tests
python3 -m pytest tests/test_experiments_*.py -v

# Nur Base-Tests
python3 -m pytest tests/test_experiments_base.py -v

# Nur Integration
python3 -m pytest tests/test_experiments_integration.py -v
```

**Test-Abdeckung:** 133 Tests

---

## Erweiterungen

### Neue Strategie hinzufügen

1. In `strategy_sweeps.py`:

```python
def get_my_strategy_sweeps(granularity: Granularity = "medium") -> List[ParamSweep]:
    if granularity == "coarse":
        return [ParamSweep("param1", [1, 2, 3])]
    elif granularity == "medium":
        return [ParamSweep("param1", [1, 2, 3, 4, 5])]
    else:
        return [ParamSweep.from_range("param1", 1, 10, 1)]

# Registry aktualisieren
STRATEGY_SWEEP_REGISTRY["my_strategy"] = lambda g: get_my_strategy_sweeps(g)
```

### Custom Backtest-Integration

```python
from src.backtest.engine import BacktestEngine

def production_backtest(strategy_name, params, symbol, timeframe, start_date, end_date, capital):
    engine = BacktestEngine()
    result = engine.run_realistic(
        strategy=strategy_name,
        symbol=symbol,
        params=params,
        start_date=start_date,
        end_date=end_date,
    )
    return result.stats

runner = ExperimentRunner(backtest_fn=production_backtest)
```

---

## Changelog

**v1.0.0 (Phase 29)**
- Initiale Implementation
- ParamSweep, ExperimentConfig, ExperimentRunner
- Vordefinierte Sweeps für alle Strategien
- Regime-Detection Sweeps
- CLI-Tool `run_experiment_sweep.py`
- 133 Unit-Tests
