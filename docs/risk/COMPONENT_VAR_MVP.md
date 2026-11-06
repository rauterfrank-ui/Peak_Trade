# Component VaR (MVP) — Parametric Attribution

**Status:** MVP (Parametric only, Euler-validated)  
**Module:** `src.risk.component_var`

## Überblick

Component VaR (auch "Contribution to VaR" oder "CompVaR") zerglegt das Portfolio-VaR in Einzelbeiträge der Assets. Dies ermöglicht:

- **Attribution**: Welches Asset trägt am meisten zum Gesamtrisiko bei?
- **Risk Budgeting**: Wie sollen Limits auf Assets verteilt werden?
- **Portfolio Optimization**: Welche Assets reduzieren das Gesamtrisiko?

### Wichtig: Begrifflichkeiten

- **Component VaR** oder **CompVaR**: Beitrag eines Assets zum Portfolio-VaR
- **CVaR** oder **Conditional VaR**: NICHT Component VaR, sondern Expected Shortfall (ES)

In diesem Dokument verwenden wir "Component VaR" oder "CompVaR", um Verwechslungen mit Conditional VaR zu vermeiden.

---

## Mathematische Grundlagen

### Total Portfolio VaR (Parametric)

Für ein Portfolio mit Gewichten \( w \) und Kovarianzmatrix \( \Sigma \):

$$
\text{VaR}_\alpha = z_\alpha \cdot \sigma_p \cdot \sqrt{H} \cdot V
$$

Wobei:
- \( z_\alpha \): z-Score für Konfidenzniveau \( \alpha \) (z.B. 1.645 für 95%)
- \( \sigma_p = \sqrt{w^T \Sigma w} \): Portfolio-Standardabweichung
- \( H \): Zeithorizont in Tagen
- \( V \): Portfolio-Wert (z.B. 100.000 EUR)

### Marginal VaR

Die **Marginal VaR** für Asset \( i \) ist die partielle Ableitung des VaR nach dem Gewicht:

$$
\text{MVaR}_i = \frac{\partial \text{VaR}}{\partial w_i} = z_\alpha \cdot \frac{(\Sigma w)_i}{\sigma_p} \cdot \sqrt{H} \cdot V
$$

### Component VaR

Die **Component VaR** für Asset \( i \) ist:

$$
\text{CompVaR}_i = w_i \cdot \text{MVaR}_i
$$

### Euler Allocation Property

Die Summe aller Component VaR muss exakt dem Total VaR entsprechen:

$$
\sum_{i=1}^{N} \text{CompVaR}_i = \text{VaR}_\alpha
$$

Dies ist eine mathematische Invariante für parametric VaR aus Covariance. Unser Calculator validiert dies mit `rtol=1e-6` (default).

---

## Installation

Component VaR ist Teil des `src.risk` Moduls. Optional Dependencies:

```bash
# Minimal (nur sample covariance, scipy für z-score)
pip install -e .

# Mit sklearn für Ledoit-Wolf shrinkage
pip install -e '.[risk]'
# oder
pip install scikit-learn
```

---

## Quickstart

### 1. Einfaches Beispiel

```python
import pandas as pd
from src.risk.component_var import ComponentVaRCalculator
from src.risk.covariance import CovarianceEstimator, CovarianceEstimatorConfig
from src.risk.parametric_var import ParametricVaR, ParametricVaRConfig

# Load returns (daily)
returns_df = pd.read_csv("returns.csv")  # Columns: BTC, ETH, SOL

# Configure covariance estimator
cov_config = CovarianceEstimatorConfig(
    method="sample",         # or "diagonal_shrink", "ledoit_wolf"
    min_history=60,
    shrinkage_alpha=0.1,     # nur für diagonal_shrink
)
cov_estimator = CovarianceEstimator(cov_config)

# Configure VaR engine
var_config = ParametricVaRConfig(
    confidence_level=0.95,   # 95% VaR
    horizon_days=1,          # 1-day VaR
)
var_engine = ParametricVaR(var_config)

# Create calculator
calculator = ComponentVaRCalculator(cov_estimator, var_engine)

# Calculate Component VaR
weights = {"BTC": 0.5, "ETH": 0.3, "SOL": 0.2}
portfolio_value = 100_000.0  # EUR

result = calculator.calculate(
    returns_df=returns_df,
    weights=weights,
    portfolio_value=portfolio_value,
    validate_euler=True,   # strict check
)

# Display results
print(result)  # Pretty-printed table

# Or as DataFrame
df = result.to_dataframe()
print(df)
```

**Output:**

```
Component VaR Analysis
======================
Total VaR: 3245.67

  asset  weight  marginal_var  component_var  contribution_pct
0   BTC     0.5       4123.45        2061.73             63.53
1   ETH     0.3       2987.12         896.14             27.61
2   SOL     0.2       1439.02         287.80              8.87

Euler Check: sum(component_var) = 3245.670000 (should equal 3245.670000)
```

### 2. Höchster Contributor identifizieren

```python
df = result.to_dataframe()
highest = df.loc[df["contribution_pct"].idxmax()]
print(f"Highest contributor: {highest['asset']} ({highest['contribution_pct']:.1f}%)")
```

### 3. Config aus PeakConfig (Optional)

Falls ihr Config-Files nutzt:

```toml
# config/risk_component_var.toml
[risk.component_var]
enabled = true
confidence_level = 0.95
horizon_days = 1

[risk.component_var.covariance]
method = "diagonal_shrink"  # works ohne sklearn
min_history = 60
shrinkage_alpha = 0.1
```

```python
from src.risk.component_var import build_component_var_calculator_from_config
from src.core.config import load_config

cfg = load_config("config/risk_component_var.toml")
calculator = build_component_var_calculator_from_config(cfg["risk"]["component_var"])

result = calculator.calculate(returns_df, weights, portfolio_value)
```

---

## Covariance Methods

### Sample Covariance (default)

- Standard pandas `cov(ddof=1)`
- Keine zusätzlichen Dependencies
- Best für stabile, liquide Assets mit ausreichend History

```python
CovarianceEstimatorConfig(method="sample", min_history=60)
```

### Diagonal Shrinkage

- Shrinkage: `cov_shrunk = (1-α)*cov_sample + α*diag(cov_sample)`
- Reduziert off-diagonal Elemente (Korrelationen)
- Keine sklearn required
- Robust bei wenig Daten oder hoher Dimensionalität

```python
CovarianceEstimatorConfig(
    method="diagonal_shrink",
    min_history=60,
    shrinkage_alpha=0.2,  # 0=sample, 1=diagonal
)
```

### Ledoit-Wolf (optional, requires sklearn)

- Optimal shrinkage estimator (Ledoit & Wolf, 2004)
- Minimiert Mean Squared Error zur wahren Covariance
- Benötigt `scikit-learn`

```python
CovarianceEstimatorConfig(method="ledoit_wolf", min_history=60)
```

Falls sklearn fehlt:

```
ImportError: Ledoit-Wolf covariance estimation requires scikit-learn.
Install with: pip install -e '.[risk]' or pip install scikit-learn
```

---

## Validation & Error Handling

### Euler Property Check

Der Calculator validiert standardmäßig die Euler-Property:

```python
result = calculator.calculate(..., validate_euler=True, euler_rtol=1e-6)
```

Falls Euler-Check fehlschlägt:

```
ValueError: Euler property violated: sum(component_var) = 3245.123, but total_var = 3245.670
```

Dies sollte **NIE** bei parametric VaR aus Covariance passieren (numerisch stabil). Falls doch:

- Prüfe, ob `total_var` aus derselben `cov` kommt wie `component_var`
- Prüfe auf numerische Instabilität (sehr kleine/große Werte)
- Verwende `euler_rtol=1e-3` für Shrinkage-Methoden (leicht relaxed)

### Positive Definite Check

Covariance Matrix wird automatisch auf Positive Definiteness geprüft (via Cholesky):

```python
cov = estimator.estimate(returns_df, validate=True)  # default
```

Falls Matrix nicht PD:

```
ValueError: Covariance matrix is not positive definite.
This can happen with insufficient data, perfect collinearity, or numerical issues.
Try increasing min_history or using diagonal_shrink method.
```

---

## Interpretation

### Contribution %

- **Positiver Beitrag**: Asset erhöht das Risiko (typisch für long positions)
- **Negativer Beitrag**: Asset reduziert das Risiko (Diversifikation, Hedge)
- **Summe = 100%**: Alle Beiträge addieren sich zum Total VaR

### Marginal vs Component

- **Marginal VaR**: "Wie ändert sich VaR, wenn ich Gewicht um 1% erhöhe?"
- **Component VaR**: "Wie viel trägt dieses Asset aktuell bei?"

Für Risk Budgeting: `Component VaR` ist relevanter.

---

## Limitierungen (MVP)

### Out of Scope in Phase 1

- **Historical Component VaR**: Bootstrap/Monte Carlo Attribution
- **Non-Normal Distributions**: Student-t, GARCH, EVT
- **Dynamic Covariance**: Rolling/EWMA Updates
- **Backtesting Framework**: VaR Breach Analysis
- **Live Integration**: Pre-Trade Risk Checks

Diese Features kommen in späteren Phasen (siehe Roadmap).

### Assumptions

- **Normalität**: Parametric VaR setzt Normal-verteilte Returns voraus
- **Stationarität**: Covariance ist zeitlich konstant
- **Liquidität**: Assets können zu aktuellen Preisen gehandelt werden

Für Crypto/Volatile Assets: Nutze kurze `min_history` (60-120 Tage) und/oder Shrinkage.

---

## Troubleshooting

### "Insufficient data"

```
ValueError: Insufficient data: 50 rows, but min_history=60
```

**Fix:** Erhöhe verfügbare Daten oder reduziere `min_history`.

### "Weights must sum to 1.0"

```
ValueError: Weights must sum to approximately 1.0, but got 0.900000
```

**Fix:** Normalisiere Gewichte oder prüfe, ob alle Assets in `weights` dict enthalten sind.

### "Portfolio sigma is zero"

```
ValueError: Portfolio sigma is zero. Cannot compute Component VaR.
```

**Fix:** Assets haben keine Varianz oder Gewichte sind alle 0. Prüfe Returns.

---

## References

- **Euler Allocation**: Tasche, D. (1999). "Risk Contributions and Performance Measurement"
- **Ledoit-Wolf**: Ledoit, O., & Wolf, M. (2004). "Honey, I Shrunk the Sample Covariance Matrix"
- **Component VaR**: Jorion, P. (2007). "Value at Risk" (3rd ed.), Chapter 7

---

## Next Steps

- **Phase 2**: Historical Component VaR (Bootstrap)
- **Phase 3**: VaR Backtesting Framework
- **Phase 4**: Pre-Trade Risk Checks (live/paper trading)
- **Phase 5**: Advanced Distributions (Student-t, GARCH)

Siehe: `docs/risk/roadmaps/COMPONENT_VAR_ROADMAP_PATCHED.md`
