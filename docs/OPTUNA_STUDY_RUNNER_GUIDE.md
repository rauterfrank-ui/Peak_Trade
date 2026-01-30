# Optuna Study Runner – User Guide

**Quick Start Guide** für hyperparameter optimization mit Optuna in Peak_Trade.

---

## 🚀 Quick Start

### 1. Installation

```bash
# Minimal (nur Optuna)
pip install optuna

# Mit Visualizations (empfohlen)
pip install optuna[visualization]

# Mit PostgreSQL Storage (optional, für Distributed Optimization)
pip install optuna psycopg2-binary
```

### 2. Erste Optimization

```bash
# Basic: Optimize MA Crossover für Sharpe Ratio
python3 scripts/run_optuna_study.py \
    --strategy ma_crossover \
    --n-trials 100

# Output:
# - Best trial found
# - CSV exported to reports/optuna_studies/
```

### 3. Ergebnisse anschauen

```bash
# CSV
cat reports/optuna_studies/ma_crossover_*.csv

# MLflow UI (falls tracking enabled)
mlflow ui --backend-store-uri ./.mlruns --port 5000
open http://localhost:5000
```

---

## 📖 Usage

### Basic Single-Objective Optimization

**Ziel**: Finde Parameter, die Sharpe Ratio maximieren.

```bash
python3 scripts/run_optuna_study.py \
    --strategy ma_crossover \
    --objectives sharpe \
    --n-trials 100
```

**Output**:
```
Best Trial:
  Trial number: 42
  Objective value: 2.1234
  Parameters:
    fast_window: 15
    slow_window: 45
  All metrics:
    sharpe: 2.1234
    total_return: 0.4567
    max_drawdown: 0.1234
    win_rate: 0.6500
```

---

### Multi-Objective Optimization

**Ziel**: Finde Parameter, die Sharpe **und** Drawdown optimieren (Pareto Front).

```bash
python3 scripts/run_optuna_study.py \
    --strategy ma_crossover \
    --objectives sharpe,max_drawdown \
    --n-trials 200
```

**Output**:
```
Best Trials (Pareto Front):

Trial #42 (Rank 1):
  Objectives: [2.1234, -0.1234]  # High Sharpe, Low Drawdown
  Parameters:
    fast_window: 15
    slow_window: 45

Trial #87 (Rank 2):
  Objectives: [1.9876, -0.1000]  # Lower Sharpe, Even Lower Drawdown
  Parameters:
    fast_window: 20
    slow_window: 50
```

**Interpretation**:
- Trial #42: Höherer Sharpe, aber auch höherer Drawdown
- Trial #87: Niedrigerer Sharpe, aber auch niedrigerer Drawdown
- **Pareto Front**: Kein Trial ist in allen Objectives besser als alle anderen

---

### Persistent Storage (Continue Study)

**Ziel**: Study speichern und später fortsetzen.

```bash
# Initial study (100 trials)
python3 scripts/run_optuna_study.py \
    --strategy ma_crossover \
    --storage sqlite:///optuna_studies.db \
    --study-name ma_crossover_v1 \
    --n-trials 100

# Continue study (50 more trials)
python3 scripts/run_optuna_study.py \
    --strategy ma_crossover \
    --storage sqlite:///optuna_studies.db \
    --study-name ma_crossover_v1 \
    --n-trials 50

# Total: 150 trials
```

**Vorteile**:
- ✅ Study bleibt erhalten (auch nach Neustart)
- ✅ Kann jederzeit fortgesetzt werden
- ✅ Mehrere Studies parallel möglich (unterschiedliche Namen)

---

### Parallel Trials

**Ziel**: Mehrere Trials gleichzeitig laufen lassen (4x schneller).

```bash
python3 scripts/run_optuna_study.py \
    --strategy ma_crossover \
    --storage sqlite:///optuna_studies.db \
    --study-name ma_crossover_parallel \
    --n-trials 100 \
    --jobs 4
```

**Requirements**:
- Storage Backend (SQLite oder PostgreSQL) für Shared State
- Mehrere CPU-Cores

**Performance**:
- 1 job: ~7 seconds (100 trials)
- 4 jobs: ~2 seconds (100 trials)
- **Speedup**: 3.5x

---

### Pruning (schnellere Optimization)

**Ziel**: Schlechte Trials früh abbrechen (mehr Trials in gleicher Zeit).

```bash
python3 scripts/run_optuna_study.py \
    --strategy ma_crossover \
    --pruner median \
    --n-trials 100
```

**Pruner-Typen**:
- `none`: Kein Pruning (alle Trials laufen vollständig)
- `median`: MedianPruner (prunt Trials, die schlechter als Median sind)
- `hyperband`: HyperbandPruner (adaptive resource allocation)

**Effekt**:
- ~30% der Trials werden gepruned (bei median pruner)
- ~20% Zeit gespart
- Gleiche oder bessere Ergebnisse

---

### MLflow Integration

**Ziel**: Alle Trials automatisch zu MLflow loggen.

**Config** (`config.toml`):
```toml
[tracking]
enabled = true
backend = "mlflow"

[tracking.mlflow]
tracking_uri = "file:./.mlruns"
experiment_name = "peak_trade_optuna"
```

**Run Study**:
```bash
python3 scripts/run_optuna_study.py \
    --strategy ma_crossover \
    --n-trials 100
```

**View Results**:
```bash
mlflow ui --backend-store-uri ./.mlruns --port 5000
open http://localhost:5000
```

**Was wird geloggt**:
- ✅ Trial-Parameter (fast_window, slow_window, ...)
- ✅ Trial-Metrics (sharpe, total_return, max_drawdown, ...)
- ✅ Trial-State (COMPLETE, PRUNED, FAIL)

---

## 🎯 Supported Objectives

**Single-Objective** (maximize oder minimize):
- `sharpe` (maximize) – Sharpe Ratio
- `total_return` (maximize) – Total Return
- `max_drawdown` (minimize) – Maximum Drawdown
- `win_rate` (maximize) – Win Rate
- `profit_factor` (maximize) – Profit Factor

**Multi-Objective** (comma-separated):
```bash
--objectives sharpe,max_drawdown
--objectives sharpe,max_drawdown,win_rate
```

---

## 🔧 CLI Options

### Required

- `--strategy <name>`: Strategy name (e.g., `ma_crossover`, `rsi_reversion`)

### Optional

- `--config <path>`: Path to config.toml (default: `config.toml`)
- `--n-trials <int>`: Number of trials (default: `100`)
- `--study-name <name>`: Study name (default: auto-generated)
- `--objectives <list>`: Comma-separated objectives (default: `sharpe`)
- `--storage <uri>`: Storage URI (default: in-memory)
  - In-Memory: (omit `--storage`)
  - SQLite: `sqlite:&#47;&#47;&#47;optuna_studies.db`
  - PostgreSQL: `postgresql:&#47;&#47;user:pass@localhost&#47;optuna`
- `--pruner <type>`: Pruner type (default: `median`)
  - Choices: `none`, `median`, `hyperband`
- `--sampler <type>`: Sampler type (default: `tpe`)
  - Choices: `tpe`, `random`, `grid`
- `--timeout <seconds>`: Timeout in seconds (default: no timeout)
- `--jobs <int>`: Number of parallel jobs (default: `1`)
- `--direction <dir>`: Optimization direction (default: auto)
  - Choices: `maximize`, `minimize`
- `--no-load-if-exists`: Don't load existing study, create new one

---

## 📊 Output

### Console Output

```
[INFO] Loading strategy: ma_crossover
[INFO] Parameter schema: 2 parameters
[INFO]   - fast_window (int): 5 - 50
[INFO]   - slow_window (int): 20 - 200
[INFO] Study name: ma_crossover_20251223_120000
[INFO] Single-objective optimization: sharpe

[Progress Bar] 100/100 trials complete

================================================================================
Best Trial:
================================================================================
  Trial number: 42
  Objective value: 2.1234
  Parameters:
    fast_window: 15
    slow_window: 45
  All metrics:
    sharpe: 2.1234
    total_return: 0.4567
    max_drawdown: 0.1234
    win_rate: 0.6500

================================================================================
Study Statistics:
================================================================================
  Total trials: 100
  Completed: 95
  Pruned: 5
  Failed: 0

✅ Results exported to: reports/optuna_studies/ma_crossover_20251223_120000.csv
```

---

### CSV Export

**Location**: `reports&#47;optuna_studies&#47;<study_name>.csv`

**Columns**:
- `number`: Trial number
- `value`: Objective value (single-objective)
- `values_0`, `values_1`, ... (multi-objective)
- `params_fast_window`, `params_slow_window`, ... (parameters)
- `user_attrs_sharpe`, `user_attrs_total_return`, ... (all metrics)
- `state`: COMPLETE, PRUNED, FAIL
- `duration`: Trial duration (seconds)

**Usage**:
```bash
# View CSV
cat reports/optuna_studies/ma_crossover_*.csv

# Import in Python
import pandas as pd
df = pd.read_csv("reports/optuna_studies/ma_crossover_20251223_120000.csv")
print(df.head())
```

---

### HTML Visualizations (optional)

**Requires**: `pip install optuna[visualization]`

**Location**: `reports&#47;optuna_studies&#47;<study_name>_viz&#47;`

**Files**:
- `history.html`: Optimization history (objective value over trials)
- `param_importances.html`: Parameter importances (which params matter most)

**Usage**:
```bash
# Open in browser
open reports/optuna_studies/ma_crossover_20251223_120000_viz/history.html
open reports/optuna_studies/ma_crossover_20251223_120000_viz/param_importances.html
```

---

## 🧪 Adding Parameter Schema to Your Strategy

**Requirement**: Strategy muss `parameter_schema` property haben.

**Example** (`src/strategies/my_strategy.py`):

```python
from src.strategies.base import BaseStrategy
from src.strategies.parameters import Param

class MyStrategy(BaseStrategy):
    KEY = "my_strategy"

    def __init__(self, window: int = 20, threshold: float = 0.02):
        self.window = window
        self.threshold = threshold
        super().__init__()

    @property
    def parameter_schema(self) -> list:
        """Parameter schema for optimization."""
        return [
            Param(
                name="window",
                kind="int",
                default=20,
                low=5,
                high=50,
                description="Lookback window",
            ),
            Param(
                name="threshold",
                kind="float",
                default=0.02,
                low=0.01,
                high=0.1,
                description="Signal threshold",
            ),
        ]

    def generate_signals(self, data):
        # ... strategy logic ...
        pass
```

**Supported Param Types**:
- `kind="int"`: Integer parameter (requires `low`, `high`)
- `kind="float"`: Float parameter (requires `low`, `high`)
- `kind="choice"`: Categorical parameter (requires `choices`)
- `kind="bool"`: Boolean parameter

**Run Optimization**:
```bash
python3 scripts/run_optuna_study.py \
    --strategy my_strategy \
    --n-trials 100
```

---

## 🐛 Troubleshooting

### Error: "Optuna is not installed"

**Solution**:
```bash
pip install optuna
```

---

### Error: "Strategy has no parameter_schema"

**Cause**: Strategy hat keine `parameter_schema` property.

**Solution**: Füge `parameter_schema` property zu Strategy hinzu (siehe oben).

---

### Error: "No trials completed"

**Cause**: Alle Trials sind failed (z.B. ungültige Parameter).

**Solution**:
- Check Parameter-Ranges (low/high)
- Check Strategy-Validierung (z.B. `fast_window < slow_window`)
- Run mit `--n-trials 10` für Quick-Test

---

### Performance: Trials sind langsam

**Solutions**:
- **Parallel Trials**: `--jobs 4` (requires storage backend)
- **Pruning**: `--pruner median` (abort bad trials early)
- **Reduce Data**: Kürze Backtest-Zeitraum in `config.toml`
- **Reduce Trials**: Start mit `--n-trials 50` statt 100

---

### Storage: SQLite locked

**Cause**: Mehrere Prozesse greifen gleichzeitig auf SQLite zu.

**Solution**:
- Use PostgreSQL statt SQLite für Parallel Trials
- Oder: Run Sequential (`--jobs 1`)

---

## 📚 Further Reading

### Internal Docs
- **Phase 3 Report**: `STRATEGY_LAYER_VNEXT_PHASE3_REPORT.md`
- **Parameter Schema**: `src/strategies/parameters.py` (Docstrings)
- **Tests**: `tests/test_optuna_integration.py` (Examples)

### External Docs
- **Optuna Tutorial**: https://optuna.readthedocs.io/en/stable/tutorial/index.html
- **Optuna API**: https://optuna.readthedocs.io/en/stable/reference/index.html
- **MLflow Docs**: https://mlflow.org/docs/latest/index.html

---

## ✅ Best Practices

### 1. Start Small

```bash
# First run: 10-20 trials für Quick-Test
python3 scripts/run_optuna_study.py \
    --strategy ma_crossover \
    --n-trials 10

# If successful: 100-200 trials für Production
python3 scripts/run_optuna_study.py \
    --strategy ma_crossover \
    --n-trials 100
```

---

### 2. Use Persistent Storage

```bash
# Always use storage for studies > 50 trials
python3 scripts/run_optuna_study.py \
    --strategy ma_crossover \
    --storage sqlite:///optuna_studies.db \
    --study-name ma_crossover_v1 \
    --n-trials 100
```

**Vorteile**:
- ✅ Study bleibt erhalten (auch nach Crash)
- ✅ Kann fortgesetzt werden
- ✅ Mehrere Studies parallel

---

### 3. Enable MLflow Tracking

```toml
# config.toml
[tracking]
enabled = true
backend = "mlflow"
```

**Vorteile**:
- ✅ Alle Trials in MLflow UI sichtbar
- ✅ Comparison-View
- ✅ Export (CSV, JSON)

---

### 4. Use Pruning

```bash
# Always use pruning für studies > 50 trials
python3 scripts/run_optuna_study.py \
    --strategy ma_crossover \
    --pruner median \
    --n-trials 100
```

**Vorteile**:
- ✅ ~20% schneller
- ✅ Mehr Trials in gleicher Zeit
- ✅ Bessere Exploration

---

### 5. Multi-Objective für Robustheit

```bash
# Optimize for Sharpe AND Drawdown (not just Sharpe)
python3 scripts/run_optuna_study.py \
    --strategy ma_crossover \
    --objectives sharpe,max_drawdown \
    --n-trials 200
```

**Vorteile**:
- ✅ Robustere Parameter (nicht nur Sharpe-optimiert)
- ✅ Pareto Front zeigt Tradeoffs
- ✅ Mehrere gute Lösungen (nicht nur eine)

---

## 🎉 Happy Optimizing!

**Questions?** Check:
- `STRATEGY_LAYER_VNEXT_PHASE3_REPORT.md` (Implementation Details)
- `tests/test_optuna_integration.py` (Code Examples)
- Optuna Docs: https://optuna.readthedocs.io/

---

**Version**: 1.0.0  
**Maintainer**: Peak_Trade Strategy Team  
**Last Updated**: 2025-12-23
