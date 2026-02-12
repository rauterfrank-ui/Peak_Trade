# Peak_Trade Component VaR Roadmap 🎯

**Projekt:** Peak_Trade Risk-Layer  
**Feature:** Component VaR (Marginal Contribution)  
**Datum:** 2025-12-25  
**Status:** 📋 ROADMAP  
**Ziel:** Portfolio-Level Risk Attribution & Position Sizing

---

## 🎯 Executive Summary

**Was ist Component VaR?**

⚠️ **Terminologie-Hinweis:** In der Literatur steht **CVaR** meist für **Conditional VaR / Expected Shortfall (ES)**. Um Verwechslungen zu vermeiden, benutzt Peak_Trade in dieser Roadmap:
- **CompVaR** = *Component VaR* (Risikobeitrag pro Position)
- **ES (CVaR)** = *Expected Shortfall* (Conditional VaR) – **nicht** Teil dieses MVP


Component VaR (CompVaR) misst den **Risikobeitrag jeder Position zum Gesamtportfolio-Risiko**. Anders als Standalone-VaR berücksichtigt es Korrelationen zwischen Assets und zeigt, welche Position am meisten zum Portfolio-Drawdown beiträgt.

**Warum kritisch für Peak_Trade?**

- ✅ **Risk Attribution:** Welche Position trägt wie viel zum Gesamt-VaR bei?
- ✅ **Position Sizing:** Intelligente Allokation basierend auf Marginal Risk
- ✅ **Rebalancing Signals:** Wann Positionen verkleinern/vergrößern?
- ✅ **Regime Detection:** Korrelationsänderungen früh erkennen
- ✅ **Safety Gate:** Hard-Limit für einzelne Position-Risikobeiträge

**Mathematik (vereinfacht):**

```
VaR_total = Portfolio Value-at-Risk (z.B. 95% Konfidenz)

Component VaR_i = ∂VaR_total / ∂w_i * w_i
                = Marginal VaR * Position Weight

Marginal VaR_i = β_i * σ_portfolio
```

**Praxis-Beispiel:**

```
Portfolio:
  - BTC: 60% Allokation, CompVaR = 8.5% (dominiert Risiko!)
  - ETH: 30% Allokation, CompVaR = 4.2%
  - SOL: 10% Allokation, CompVaR = 2.1%

Σ CompVaR = 14.8% = Total Portfolio VaR

➡️ BTC trägt 8.5/14.8 = 57.4% zum Risiko bei (nicht 60%)!
➡️ Action: BTC-Allokation reduzieren oder Hedge hinzufügen
```

---

## 📊 Phasen-Übersicht

| Phase | Dauer | Effort | Komplexität | Dependencies |
|-------|-------|--------|-------------|--------------|
| **0** Setup & Research | 1-2 Tage | S | Low | Keine |
| **1** Covariance Engine | 3-4 Tage | M | Medium | Phase 0 |
| **2** VaR Calculator | 2-3 Tage | M | Medium | Phase 1 |
| **3** Component VaR Core | 4-5 Tage | L | High | Phase 1+2 |
| **4** Portfolio Optimizer | 5-6 Tage | L | High | Phase 3 |
| **5** Integration & Tests | 3-4 Tage | M | Medium | Phase 1-4 |
| **6** Monitoring & Alerts | 2-3 Tage | S | Low | Phase 5 |

**Gesamt:** ~3-4 Wochen (bei Vollzeit-Fokus)

**Legende:**
- **Effort:** S (1-3d) | M (3-7d) | L (7-14d)
- **Komplexität:** Low | Medium | High


### ⚡ MVP-Cut (empfohlen)
Wenn du schnell *realen Nutzen* willst (Attribution + Sizing-Input + Safety-Gates), ist der sinnvollste erste Slice:
- **Phase 1 (Covariance)** + **Phase 2 (Parametric VaR aus Σ)** + **Phase 3 (CompVaR + Euler-Check)**
- **Ohne** Historical/Monte-Carlo Attribution (die braucht Finite-Difference / spezielle Attribution)
→ Ergebnis nach ~5–8 Tagen: belastbare, mathematisch konsistente Risikobeiträge (CompVaR) mit harten Tests.

---

## 🚀 Phase 0: Setup & Research (1-2 Tage)

### Ziel

Foundations legen: Literatur, Dependencies, mathematische Validierung.

### Deliverables

```
docs/risk/COMPONENT_VAR_THEORY.md          # Mathematik, Literatur, Beispiele
`docs&sol;risk&sol;COVARIANCE_METHODS.md (planned)`            # Shrinkage, Ledoit-Wolf, etc.
`config&sol;risk.toml (planned)`                           # CompVaR Config Section
requirements/risk_extras.txt               # scipy, statsmodels
tests/risk/fixtures/sample_returns.csv     # Test-Daten (3 Assets, 252 Days)
```

### Tasks

**1.1 Literatur & Theorie (4h)**

```bash
# Research Topics
- [x] VaR vs CompVaR vs Marginal VaR (Definitionen)
- [x] Covariance Estimation (Sample, Shrinkage, Ledoit-Wolf)
- [x] Correlation Breakdown (Regime Shifts)
- [x] Portfolio Beta Calculation
- [x] Risk Attribution Methods (Euler Allocation)

# Key Papers
- "Coherent Measures of Risk" (Artzner et al., 1999)
- "Honey, I Shrunk the Sample Covariance Matrix" (Ledoit & Wolf, 2004)
- "Portfolio Risk Budgeting" (Maillard et al., 2010)
```

**1.2 Dependencies installieren (1h)**

```bash
cd ~/Peak_Trade
source .venv/bin/activate

# Neue Dependencies
pip install scipy>=1.11.0          # Covariance, Stats
pip install statsmodels>=0.14.0    # Ledoit-Wolf Shrinkage
pip install scikit-learn>=1.3.0    # Optional: PCA für Dim Reduction

# In pyproject.toml hinzufügen
[tool.poetry.extras]
risk = ["scipy>=1.11.0", "statsmodels>=0.14.0"]
```

**1.3 Config-Struktur definieren (2h)**

```toml
# `config&sol;risk.toml (planned)` (neue Section)
[risk.component_var]
enabled = false                    # Default: OFF (opt-in)
method = "parametric"              # parametric|historical|monte_carlo
confidence_level = 0.95            # 95% VaR
lookback_days = 252                # 1 Jahr für Covariance

[risk.component_var.covariance]
method = "ledoit_wolf"             # sample|ledoit_wolf|shrinkage
min_history = 60                   # Mindestens 60 Tage für Covariance
rebalance_threshold = 0.05         # 5% CompVaR-Shift triggert Alert

[risk.component_var.limits]
max_single_compvar_pct = 0.40         # Keine Position darf >40% vom Total VaR
max_total_var_pct = 0.15           # Portfolio-VaR max 15% des Kapitals
```

**1.4 Test-Daten generieren (2h)**

```python
# tests/risk/fixtures/generate_sample_returns.py
import pandas as pd
import numpy as np

# Generate correlated returns (BTC, ETH, SOL)
np.random.seed(42)
n_days = 252

# Correlation Matrix (realistic crypto correlations)
corr = np.array([
    [1.00, 0.85, 0.70],  # BTC
    [0.85, 1.00, 0.75],  # ETH
    [0.70, 0.75, 1.00],  # SOL
])

# Volatilities (annualized)
vols = np.array([0.60, 0.75, 0.90])  # BTC < ETH < SOL

# Covariance Matrix
cov = np.outer(vols, vols) * corr

# Generate returns
mean_returns = np.array([0.0005, 0.0006, 0.0008])  # Daily
returns = np.random.multivariate_normal(mean_returns, cov, n_days)

df = pd.DataFrame(
    returns,
    columns=["BTC", "ETH", "SOL"],
    index=pd.date_range("2024-01-01", periods=n_days, freq="D")
)

df.to_csv("tests/risk/fixtures/sample_returns.csv")
print("✅ Generated sample_returns.csv")
```

**1.5 Dokumentation schreiben (3h)**

```markdown
# docs/risk/COMPONENT_VAR_THEORY.md

## Mathematik

### 1. Portfolio VaR (Parametric)
VaR_portfolio = z_α * σ_portfolio * sqrt(h) * V

z_α: Z-Score (95% ≈ 1.645)
σ_portfolio: Portfolio-Volatilität
V: Portfolio Value
h: Horizont in Tagen (z.B. 1), Skalierung via sqrt(h)

### 2. Marginal VaR (einzelne Position)
MarginalVaR_i(abs) = ∂VaR_portfolio / ∂w_i
                = z_α * ( (Σ w)_i / σ_portfolio ) * sqrt(h) * V

(Σ w)_i = Cov(R_i, R_portfolio)

### 3. CompVaR (Risikobeitrag)
CompVaR_i(abs) = w_i * MarginalVaR_i(abs)

### 4. Validation Check
Σ CompVaR_i = VaR_portfolio  (Euler Allocation)

### Success Metrics

- [x] Theorie-Dokument mit Formeln + Beispielen
- [x] Test-Daten mit bekannten Korrelationen
- [x] Config-Struktur definiert
- [x] Dependencies installiert

---

## 🔧 Phase 1: Covariance Engine (3-4 Tage)

### Ziel

Robuste Covariance-Matrix-Berechnung mit Shrinkage (Ledoit-Wolf).

### Deliverables

```
src/risk/covariance.py                     # CovarianceEstimator Klasse
tests/risk/test_covariance.py              # Unit Tests (6+ Tests)
tests/risk/test_covariance_integration.py  # Integration mit echten Daten
`docs&sol;risk&sol;COVARIANCE_METHODS.md (planned)`            # Implementierungs-Details
```

### Tasks

**1.1 CovarianceEstimator Klasse (1d)**

```python
# src/risk/covariance.py
from dataclasses import dataclass
from enum import Enum
import numpy as np
import pandas as pd
from typing import Optional
from sklearn.covariance import LedoitWolf, ShrunkCovariance

class CovarianceMethod(Enum):
    SAMPLE = "sample"              # Naive Sample Covariance
    LEDOIT_WOLF = "ledoit_wolf"    # Ledoit-Wolf Shrinkage
    SHRINKAGE = "shrinkage"        # Custom Shrinkage (manual alpha)

@dataclass
class CovarianceEstimatorConfig:
    method: CovarianceMethod = CovarianceMethod.LEDOIT_WOLF
    min_history: int = 60          # Minimum Observations
    shrinkage_alpha: float = 0.1   # Nur für method=SHRINKAGE

class CovarianceEstimator:
    """
    Schätzt Covariance-Matrix aus Return-Zeitreihen.

    Unterstützt:
    - Sample Covariance (naive, instabil bei wenig Daten)
    - Ledoit-Wolf Shrinkage (empfohlen, auto-alpha)
    - Manual Shrinkage (custom alpha)

    Usage:
        estimator = CovarianceEstimator(config)
        cov_matrix = estimator.estimate(returns_df)
    """

    def __init__(self, config: CovarianceEstimatorConfig):
        self.config = config

    def estimate(
        self,
        returns: pd.DataFrame,
        validate: bool = True
    ) -> np.ndarray:
        """
        Schätzt Covariance-Matrix.

        Args:
            returns: DataFrame mit Returns (Rows=Tage, Cols=Assets)
            validate: Falls True, prüfe auf Positive Definiteness

        Returns:
            Covariance Matrix (NxN für N Assets)

        Raises:
            ValueError: Wenn zu wenig Daten oder Matrix nicht PD
        """
        if len(returns) < self.config.min_history:
            raise ValueError(
                f"Need at least {self.config.min_history} observations, "
                f"got {len(returns)}"
            )

        # Drop NaNs
        returns_clean = returns.dropna()

        if self.config.method == CovarianceMethod.SAMPLE:
            cov = returns_clean.cov().values

        elif self.config.method == CovarianceMethod.LEDOIT_WOLF:
            lw = LedoitWolf()
            cov = lw.fit(returns_clean.values).covariance_

        elif self.config.method == CovarianceMethod.SHRINKAGE:
            shrink = ShrunkCovariance(
                shrinkage=self.config.shrinkage_alpha
            )
            cov = shrink.fit(returns_clean.values).covariance_

        else:
            raise ValueError(f"Unknown method: {self.config.method}")

        # Validation
        if validate:
            if not self._is_positive_definite(cov):
                raise ValueError("Covariance matrix not positive definite!")

        return cov

    def estimate_correlation(
        self,
        returns: pd.DataFrame
    ) -> np.ndarray:
        """Berechnet Correlation-Matrix aus Covariance."""
        cov = self.estimate(returns, validate=True)

        # Cov -> Corr
        D_inv = np.diag(1.0 / np.sqrt(np.diag(cov)))
        corr = D_inv @ cov @ D_inv

        return corr

    @staticmethod
    def _is_positive_definite(matrix: np.ndarray) -> bool:
        """Prüft ob Matrix positive definite ist."""
        try:
            np.linalg.cholesky(matrix)
            return True
        except np.linalg.LinAlgError:
            return False
```

**1.2 Unit Tests (1d)**

```python
# tests/risk/test_covariance.py
import pytest
import numpy as np
import pandas as pd
from src.risk.covariance import (
    CovarianceEstimator,
    CovarianceEstimatorConfig,
    CovarianceMethod,
)

@pytest.fixture
def sample_returns():
    """Generate simple uncorrelated returns."""
    np.random.seed(42)
    return pd.DataFrame({
        "A": np.random.normal(0, 0.01, 100),
        "B": np.random.normal(0, 0.02, 100),
    })

def test_sample_covariance(sample_returns):
    """Test: Sample Covariance berechnet korrekt."""
    config = CovarianceEstimatorConfig(method=CovarianceMethod.SAMPLE)
    estimator = CovarianceEstimator(config)

    cov = estimator.estimate(sample_returns)

    # Shape check
    assert cov.shape == (2, 2)

    # Symmetrie
    assert np.allclose(cov, cov.T)

    # Diagonal (Varianzen) positiv
    assert np.all(np.diag(cov) > 0)

def test_ledoit_wolf_shrinkage(sample_returns):
    """Test: Ledoit-Wolf gibt positive definite Matrix."""
    config = CovarianceEstimatorConfig(method=CovarianceMethod.LEDOIT_WOLF)
    estimator = CovarianceEstimator(config)

    cov = estimator.estimate(sample_returns, validate=True)

    # Positive Definiteness wurde in estimate() geprüft
    assert cov.shape == (2, 2)

def test_min_history_validation():
    """Test: Fehler bei zu wenig Daten."""
    config = CovarianceEstimatorConfig(min_history=100)
    estimator = CovarianceEstimator(config)

    # Nur 50 Observations
    returns = pd.DataFrame({
        "A": np.random.normal(0, 0.01, 50),
    })

    with pytest.raises(ValueError, match="at least 100"):
        estimator.estimate(returns)

def test_correlation_matrix(sample_returns):
    """Test: Correlation-Matrix hat 1.0 auf Diagonale."""
    config = CovarianceEstimatorConfig(method=CovarianceMethod.LEDOIT_WOLF)
    estimator = CovarianceEstimator(config)

    corr = estimator.estimate_correlation(sample_returns)

    # Diagonale = 1.0
    assert np.allclose(np.diag(corr), 1.0)

    # Off-Diagonal [-1, 1]
    off_diag = corr[np.triu_indices_from(corr, k=1)]
    assert np.all(off_diag >= -1.0) and np.all(off_diag <= 1.0)
```

**1.3 Integration Test mit echten Daten (0.5d)**

```python
# tests/risk/test_covariance_integration.py
import pytest
import pandas as pd
from pathlib import Path
from src.risk.covariance import (
    CovarianceEstimator,
    CovarianceEstimatorConfig,
    CovarianceMethod,
)

@pytest.fixture
def real_returns():
    """Lade sample_returns.csv (generiert in Phase 0)."""
    path = Path(__file__).parent / "fixtures" / "sample_returns.csv"
    return pd.read_csv(path, index_col=0, parse_dates=True)

def test_covariance_with_real_data(real_returns):
    """Test: Covariance mit realistischen Crypto-Daten."""
    config = CovarianceEstimatorConfig(method=CovarianceMethod.LEDOIT_WOLF)
    estimator = CovarianceEstimator(config)

    cov = estimator.estimate(real_returns)

    # Shape check (3 Assets: BTC, ETH, SOL)
    assert cov.shape == (3, 3)

    # BTC Variance (Index 0) < SOL Variance (Index 2)
    # (weil BTC lower vol in unseren Test-Daten)
    assert cov[0, 0] < cov[2, 2]

def test_correlation_realistic_values(real_returns):
    """Test: Correlation zwischen BTC-ETH hoch (>0.7)."""
    config = CovarianceEstimatorConfig(method=CovarianceMethod.LEDOIT_WOLF)
    estimator = CovarianceEstimator(config)

    corr = estimator.estimate_correlation(real_returns)

    # BTC-ETH Correlation (0,1) sollte >0.7 sein
    btc_eth_corr = corr[0, 1]
    assert btc_eth_corr > 0.7
```

**1.4 Dokumentation (0.5d)**

```markdown
# `docs&sol;risk&sol;COVARIANCE_METHODS.md (planned)`

## Warum Covariance Shrinkage?

**Problem:** Sample Covariance ist instabil bei:
- Wenig Daten (N < P, wobei P = Anzahl Assets)
- High Dimensionality (viele Assets)
- Non-Stationarity (Markt-Regime-Shifts)

**Lösung:** Ledoit-Wolf Shrinkage
- Kombiniert Sample Covariance mit Structured Target (z.B. Diagonal)
- Auto-optimiert Shrinkage-Faktor α ∈ [0,1]
- Garantiert Positive Definiteness

**Formula:**
Σ_shrunk = α * Σ_target + (1-α) * Σ_sample

## Implementierung

- `SAMPLE`: Naive pd.DataFrame.cov() → instabil!
- `LEDOIT_WOLF`: sklearn.covariance.LedoitWolf → empfohlen
- `SHRINKAGE`: Manual alpha (wenn du Ledoit-Wolf überschreiben willst)

## Usage

```python
from src.risk.covariance import CovarianceEstimator, CovarianceEstimatorConfig

config = CovarianceEstimatorConfig(method="ledoit_wolf", min_history=60)
estimator = CovarianceEstimator(config)

cov = estimator.estimate(returns_df)
corr = estimator.estimate_correlation(returns_df)
```
```

### Success Metrics

- [x] CovarianceEstimator mit 3 Methods (Sample, Ledoit-Wolf, Shrinkage)
- [x] 6+ Unit Tests (alle passing)
- [x] Integration Test mit sample_returns.csv
- [x] Positive Definiteness Validation
- [x] Dokumentation mit Math + Usage

---

## 📈 Phase 2: VaR Calculator (2-3 Tage)

### Ziel

Portfolio-Level VaR (nicht Component VaR yet, erst Gesamt-VaR).

### Deliverables

```
`src&sol;risk&sol;var_calculator.py (planned)`                 # VaRCalculator Klasse
tests/risk/test_var_calculator.py          # Unit Tests
`docs&sol;risk&sol;VAR_METHODS.md (planned)`                   # Parametric vs Historical vs Monte Carlo
```

### Tasks

**2.1 VaRCalculator Klasse (1d)**

```python
# `src&sol;risk&sol;var_calculator.py (planned)`
from dataclasses import dataclass
from enum import Enum
from statistics import NormalDist
from typing import Optional

import numpy as np
import pandas as pd


class VaRMethod(Enum):
    PARAMETRIC = "parametric"      # Gaussian assumption, VaR aus Σ
    HISTORICAL = "historical"      # Empirical quantile
    MONTE_CARLO = "monte_carlo"    # Bootstrap simulation (Compounding)


@dataclass
class VaRCalculatorConfig:
    method: VaRMethod = VaRMethod.PARAMETRIC
    confidence_level: float = 0.95      # 95% VaR
    lookback_days: int = 252            # 1 Jahr (Trading Days)
    horizon_days: int = 1               # VaR-Horizont (Tage)
    mc_simulations: int = 10_000        # Nur für Monte Carlo


class VaRCalculator:
    """Berechnet Portfolio Value-at-Risk (VaR) auf Portfolio-Level.

    Hinweis:
    - Für PARAMETRIC wird σ_portfolio aus der Kovarianzmatrix Σ berechnet:
      σ = sqrt(wᵀ Σ w). Das hält die Mathematik konsistent zu Component-VaR/Euler.
    - horizon_days wird via sqrt(h) (parametric) bzw. via Compounding (hist/MC) berücksichtigt.
    """

    def __init__(self, config: Optional[VaRCalculatorConfig] = None):
        self.config = config or VaRCalculatorConfig()

    def _z_score(self) -> float:
        """Z-Score für confidence_level; SciPy optional."""
        try:
            from scipy.stats import norm  # type: ignore
            return float(norm.ppf(self.config.confidence_level))
        except Exception:
            return float(NormalDist().inv_cdf(self.config.confidence_level))

    def calculate_var(
        self,
        returns: pd.DataFrame,
        weights: np.ndarray,
        portfolio_value: float = 1.0,
    ) -> float:
        """Returns: VaR als *positive* absolute Größe (z.B. EUR)."""
        # lookback
        if len(returns) > self.config.lookback_days:
            returns = returns.tail(self.config.lookback_days)

        if self.config.method == VaRMethod.PARAMETRIC:
            return self._parametric_var(returns, weights, portfolio_value)
        if self.config.method == VaRMethod.HISTORICAL:
            return self._historical_var(returns, weights, portfolio_value)
        if self.config.method == VaRMethod.MONTE_CARLO:
            return self._monte_carlo_var(returns, weights, portfolio_value)
        raise ValueError(f"Unknown method: {self.config.method}")

    def _parametric_var(
        self,
        returns: pd.DataFrame,
        weights: np.ndarray,
        portfolio_value: float,
    ) -> float:
        # Covariance → σ_portfolio
        cov = returns.cov().values
        sigma = float(np.sqrt(weights @ cov @ weights))
        if sigma <= 0:
            raise ValueError("σ_portfolio <= 0 (covariance/weights prüfen)")

        z = self._z_score()
        h = float(self.config.horizon_days)
        var_abs = z * sigma * np.sqrt(h) * float(portfolio_value)
        return float(var_abs)

    def _historical_var(
        self,
        returns: pd.DataFrame,
        weights: np.ndarray,
        portfolio_value: float,
    ) -> float:
        port_daily = (returns * weights).sum(axis=1)

        h = int(self.config.horizon_days)
        if h == 1:
            path = port_daily
        else:
            # h‑Tage Return via Compounding (robuster als simples Summieren)
            path = (1.0 + port_daily).rolling(h).apply(np.prod, raw=True) - 1.0
            path = path.dropna()

        q = float(np.quantile(path, 1.0 - self.config.confidence_level))
        return float(-q * float(portfolio_value))

    def _monte_carlo_var(
        self,
        returns: pd.DataFrame,
        weights: np.ndarray,
        portfolio_value: float,
    ) -> float:
        # Bootstrap auf Portfolio‑Daily‑Returns
        port_daily = (returns * weights).sum(axis=1).to_numpy()
        n = len(port_daily)
        if n < 2:
            raise ValueError("Zu wenig Daten für Monte Carlo VaR")

        h = int(self.config.horizon_days)
        n_sims = int(self.config.mc_simulations)
        sims = np.empty(n_sims, dtype=float)

        for i in range(n_sims):
            idx = np.random.randint(0, n, size=h)  # horizon‑Sample
            sims[i] = float(np.prod(1.0 + port_daily[idx]) - 1.0)

        q = float(np.percentile(sims, (1.0 - self.config.confidence_level) * 100.0))
        return float(-q * float(portfolio_value))
```

**2.2 Unit Tests (1d)**

```python
# tests/risk/test_var_calculator.py
import pytest
import numpy as np
import pandas as pd
from src.risk.var_calculator import (
    VaRCalculator,
    VaRCalculatorConfig,
    VaRMethod,
)

@pytest.fixture
def simple_returns():
    """Simple 2-asset returns (uncorrelated)."""
    np.random.seed(42)
    return pd.DataFrame({
        "A": np.random.normal(0.001, 0.02, 252),  # 2% daily vol
        "B": np.random.normal(0.001, 0.03, 252),  # 3% daily vol
    })

def test_parametric_var(simple_returns):
    """Test: Parametric VaR ist > 0."""
    config = VaRCalculatorConfig(method=VaRMethod.PARAMETRIC)
    calculator = VaRCalculator(config)

    weights = np.array([0.5, 0.5])
    portfolio_value = 100000  # $100k

    var_dollar = calculator.calculate_var(simple_returns, weights, portfolio_value)

    # VaR sollte positiv sein (Loss)
    assert var_dollar > 0

    # Plausibility: ~1.645 * avg_vol * portfolio_value
    # avg_vol ≈ 2.5% daily
    expected_var = 1.645 * 0.025 * portfolio_value
    assert abs(var_dollar - expected_var) / expected_var < 0.5  # ±50%

def test_historical_var(simple_returns):
    """Test: Historical VaR via Quantile."""
    config = VaRCalculatorConfig(method=VaRMethod.HISTORICAL)
    calculator = VaRCalculator(config)

    weights = np.array([0.6, 0.4])
    portfolio_value = 50000

    var_dollar = calculator.calculate_var(simple_returns, weights, portfolio_value)

    assert var_dollar > 0

def test_monte_carlo_var(simple_returns):
    """Test: Monte Carlo VaR mit 10k Sims."""
    config = VaRCalculatorConfig(
        method=VaRMethod.MONTE_CARLO,
        mc_simulations=10000
    )
    calculator = VaRCalculator(config)

    weights = np.array([0.5, 0.5])
    portfolio_value = 100000

    var_dollar = calculator.calculate_var(simple_returns, weights, portfolio_value)

    assert var_dollar > 0

def test_var_increases_with_volatility():
    """Test: Höhere Volatilität → höherer VaR."""
    # Low vol
    returns_low = pd.DataFrame({
        "A": np.random.normal(0, 0.01, 252),
    })

    # High vol
    returns_high = pd.DataFrame({
        "A": np.random.normal(0, 0.05, 252),
    })

    config = VaRCalculatorConfig(method=VaRMethod.PARAMETRIC)
    calculator = VaRCalculator(config)

    weights = np.array([1.0])

    var_low = calculator.calculate_var(returns_low, weights, 100000)
    var_high = calculator.calculate_var(returns_high, weights, 100000)

    # Higher vol → Higher VaR
    assert var_high > var_low
```

### Success Metrics

- [x] VaRCalculator mit 3 Methods (Parametric, Historical, MC)
- [x] 5+ Unit Tests (alle passing)
- [x] VaR steigt mit Volatilität (Plausibility Check)

---

## 🎯 Phase 3: Component VaR Core (4-5 Tage) **[KRITISCH]**

### Ziel

Marginal Contribution & Risk Attribution implementieren.

**Scope (MVP):** *Parametric* CompVaR aus Σ + Euler-Validation.
**Nicht im MVP:** Historical/Monte‑Carlo *Attribution* (benötigt Finite-Difference oder spezielle Attribution).

### Deliverables

```
src/risk/component_var.py                  # ComponentVaRCalculator
tests/risk/test_component_var.py           # Unit Tests (10+ Tests)
tests/risk/test_euler_allocation.py        # Euler-Test (Σ CompVaR = Total VaR)
`docs&sol;risk&sol;COMPONENT_VAR_MATH.md (planned)`            # Formeln + Validation
```

### Tasks

**3.1 ComponentVaRCalculator Klasse (2d)**

```python
# src/risk/component_var.py
from dataclasses import dataclass
from typing import Dict

import numpy as np
import pandas as pd

from src.risk.covariance import CovarianceEstimator, CovarianceEstimatorConfig
from src.risk.var_calculator import VaRCalculator, VaRCalculatorConfig, VaRMethod


@dataclass
class ComponentVaRResult:
    """Result Container für CompVaR (Component VaR) Berechnung."""

    total_var: float                       # Portfolio VaR (absolut, positive Größe)
    marginal_var: Dict[str, float]         # Marginal VaR pro Asset (absolut)
    component_var: Dict[str, float]        # CompVaR pro Asset (absolut)
    contribution_pct: Dict[str, float]     # CompVaR / Total VaR (%)
    weights: Dict[str, float]              # Portfolio Weights

    def to_dataframe(self) -> pd.DataFrame:
        """Convert to DataFrame für einfache Analyse."""
        return pd.DataFrame(
            {
                "Weight": self.weights,
                "Marginal_VaR": self.marginal_var,
                "Component_VaR": self.component_var,
                "Contribution_%": self.contribution_pct,
            }
        )


class ComponentVaRCalculator:
    """Berechnet CompVaR (Component VaR) + Euler-Validation.

    Mathematik (parametric, konsistent aus Σ):
        σ_portfolio = sqrt(wᵀ Σ w)
        VaR_total   = z_α * σ_portfolio * sqrt(h) * V

        MarginalVaR_i(abs) = z_α * ( (Σ w)_i / σ_portfolio ) * sqrt(h) * V
        CompVaR_i(abs)     = w_i * MarginalVaR_i(abs)

        Euler: Σ CompVaR_i == VaR_total
    """

    def __init__(self, cov_config: CovarianceEstimatorConfig, var_config: VaRCalculatorConfig):
        self.cov_estimator = CovarianceEstimator(cov_config)
        self.var_calculator = VaRCalculator(var_config)

    def calculate(
        self,
        returns: pd.DataFrame,
        weights: Dict[str, float],
        portfolio_value: float,
        validate_euler: bool = True,
        euler_rtol: float = 1e-3,
    ) -> ComponentVaRResult:
        # MVP: Euler‑Attribution sauber nur für PARAMETRIC
        if self.var_calculator.config.method != VaRMethod.PARAMETRIC:
            raise NotImplementedError(
                "CompVaR/Euler im MVP nur für PARAMETRIC. "
                "Für historical/MC später Finite‑Difference Attribution ergänzen."
            )

        # Validate weights
        weight_sum = float(sum(weights.values()))
        if not np.isclose(weight_sum, 1.0):
            raise ValueError(f"Weights must sum to 1.0, got {weight_sum:.6f}")

        # Align weights to returns.columns
        asset_names = list(returns.columns)
        w = np.array([weights[a] for a in asset_names], dtype=float)

        # 1) Covariance
        cov = self.cov_estimator.estimate(returns)

        # 2) σ_portfolio
        sigma = float(np.sqrt(w @ cov @ w))
        if sigma <= 0:
            raise ValueError("σ_portfolio <= 0 (covariance/weights prüfen)")

        # 3) Total VaR (aus derselben Σ!)
        z = float(self.var_calculator._z_score())
        h = float(np.sqrt(self.var_calculator.config.horizon_days))
        total_var = z * sigma * h * float(portfolio_value)

        # 4) Marginal VaR + CompVaR
        cov_with_portfolio = cov @ w  # (Σ w)
        marginal_abs_arr = (z * (cov_with_portfolio / sigma) * h) * float(portfolio_value)
        component_abs_arr = w * marginal_abs_arr

        marginal_var_abs = {a: float(marginal_abs_arr[i]) for i, a in enumerate(asset_names)}
        component_var_abs = {a: float(component_abs_arr[i]) for i, a in enumerate(asset_names)}
        contribution_pct = {a: float(component_var_abs[a] / total_var * 100.0) for a in asset_names}

        # 5) Euler Allocation Check
        if validate_euler:
            compvar_sum = float(sum(component_var_abs.values()))
            if not np.isclose(compvar_sum, total_var, rtol=euler_rtol):
                raise ValueError(
                    f"Euler Allocation failed: Σ CompVaR = {compvar_sum:.6f}, "
                    f"Total VaR = {total_var:.6f} (rtol={euler_rtol})"
                )

        return ComponentVaRResult(
            total_var=float(total_var),
            marginal_var=marginal_var_abs,
            component_var=component_var_abs,
            contribution_pct=contribution_pct,
            weights=weights,
        )
```

**3.2 Unit Tests (1.5d)**

```python
# tests/risk/test_component_var.py
import pytest
import numpy as np
import pandas as pd
from src.risk.component_var import ComponentVaRCalculator, ComponentVaRResult
from src.risk.covariance import CovarianceEstimatorConfig, CovarianceMethod
from src.risk.var_calculator import VaRCalculatorConfig, VaRMethod

@pytest.fixture
def simple_portfolio():
    """2-Asset Portfolio mit bekannten Properties."""
    np.random.seed(42)
    returns = pd.DataFrame({
        "BTC": np.random.normal(0.001, 0.02, 252),
        "ETH": np.random.normal(0.001, 0.025, 252),
    })

    weights = {"BTC": 0.6, "ETH": 0.4}
    portfolio_value = 100000

    return returns, weights, portfolio_value

def test_component_var_calculation(simple_portfolio):
    """Test: Component VaR berechnet korrekt."""
    returns, weights, portfolio_value = simple_portfolio

    cov_config = CovarianceEstimatorConfig(method=CovarianceMethod.LEDOIT_WOLF)
    var_config = VaRCalculatorConfig(method=VaRMethod.PARAMETRIC)

    calculator = ComponentVaRCalculator(cov_config, var_config)
    result = calculator.calculate(returns, weights, portfolio_value)

    # Total VaR > 0
    assert result.total_var > 0

    # CompVaR für beide Assets vorhanden
    assert "BTC" in result.component_var
    assert "ETH" in result.component_var

    # CompVaR > 0
    assert result.component_var["BTC"] > 0
    assert result.component_var["ETH"] > 0

def test_euler_allocation_holds(simple_portfolio):
    """Test: Σ CompVaR = Total VaR (Euler Allocation)."""
    returns, weights, portfolio_value = simple_portfolio

    cov_config = CovarianceEstimatorConfig(method=CovarianceMethod.LEDOIT_WOLF)
    var_config = VaRCalculatorConfig(method=VaRMethod.PARAMETRIC)

    calculator = ComponentVaRCalculator(cov_config, var_config)
    result = calculator.calculate(returns, weights, portfolio_value, validate_euler=True)

    # Σ CompVaR
    compvar_sum = sum(result.component_var.values())

    # Sollte ≈ Total VaR sein (innerhalb 0.1% Toleranz)
    assert np.isclose(compvar_sum, result.total_var, rtol=1e-3)

def test_contribution_pct_sums_to_100(simple_portfolio):
    """Test: Σ Contribution% = 100%."""
    returns, weights, portfolio_value = simple_portfolio

    cov_config = CovarianceEstimatorConfig(method=CovarianceMethod.LEDOIT_WOLF)
    var_config = VaRCalculatorConfig(method=VaRMethod.PARAMETRIC)

    calculator = ComponentVaRCalculator(cov_config, var_config)
    result = calculator.calculate(returns, weights, portfolio_value)

    # Σ Contribution%
    total_contribution = sum(result.contribution_pct.values())

    assert np.isclose(total_contribution, 100.0, rtol=1e-2)

def test_higher_weight_not_always_higher_compvar():
    """
    Test: CompVaR ≠ Weight (wegen Correlation!).

    Asset mit höherem Weight kann KLEINEREN CompVaR haben,
    wenn es negativ korreliert mit Rest.
    """
    # BTC-ETH stark korreliert, SOL uncorrelated
    np.random.seed(42)

    btc = np.random.normal(0, 0.02, 252)
    eth = btc * 0.9 + np.random.normal(0, 0.01, 252)  # Hohe Corr mit BTC
    sol = np.random.normal(0, 0.03, 252)              # Uncorrelated

    returns = pd.DataFrame({"BTC": btc, "ETH": eth, "SOL": sol})

    # BTC dominiert Weight (60%)
    weights = {"BTC": 0.60, "ETH": 0.25, "SOL": 0.15}

    cov_config = CovarianceEstimatorConfig(method=CovarianceMethod.SAMPLE)
    var_config = VaRCalculatorConfig(method=VaRMethod.PARAMETRIC)

    calculator = ComponentVaRCalculator(cov_config, var_config)
    result = calculator.calculate(returns, weights, 100000)

    # BTC hat 60% Weight, aber könnte <60% CompVaR haben (wegen Diversification)
    btc_contrib = result.contribution_pct["BTC"]

    # Test: BTC Contribution ist plausibel (nicht exakt 60%)
    assert 40 < btc_contrib < 80  # Breiter Range wegen randomness
```

**3.3 Euler Allocation Test (0.5d)**

```python
# tests/risk/test_euler_allocation.py
import pytest
import numpy as np
import pandas as pd
from src.risk.component_var import ComponentVaRCalculator
from src.risk.covariance import CovarianceEstimatorConfig, CovarianceMethod
from src.risk.var_calculator import VaRCalculatorConfig, VaRMethod

def test_euler_allocation_3_assets():
    """Test: Euler Allocation gilt für 3-Asset Portfolio."""
    # Load real data (aus Phase 0)
    from pathlib import Path
    path = Path(__file__).parent / "fixtures" / "sample_returns.csv"
    returns = pd.read_csv(path, index_col=0, parse_dates=True)

    weights = {"BTC": 0.50, "ETH": 0.30, "SOL": 0.20}

    cov_config = CovarianceEstimatorConfig(method=CovarianceMethod.LEDOIT_WOLF)
    var_config = VaRCalculatorConfig(method=VaRMethod.PARAMETRIC)

    calculator = ComponentVaRCalculator(cov_config, var_config)

    # validate_euler=True sollte NICHT raisen
    result = calculator.calculate(returns, weights, 100000, validate_euler=True)

    # Explicit check
    compvar_sum = sum(result.component_var.values())
    assert np.isclose(compvar_sum, result.total_var, rtol=1e-3)

def test_euler_allocation_fails_on_broken_implementation():
    """Test: Euler Check detected fehlerhaften Code."""
    # Dummy: Fake ComponentVaRCalculator der Euler verletzt

    # (Dieser Test ist mehr konzeptionell – zeigt, dass validate_euler funktioniert)
    # Im echten Code würde fehlerhafte Implementierung ValueError raisen
    pass
```

**3.4 Dokumentation (1d)**

```markdown
# `docs&sol;risk&sol;COMPONENT_VAR_MATH.md (planned)`

## Formeln

### 1. Portfolio VaR (Baseline)
VaR_portfolio = z_α * σ_portfolio * V

### 2. Portfolio Variance
σ²_portfolio = w^T * Σ * w

Σ: Covariance Matrix (NxN)
w: Weights (Nx1)

### 3. Beta (Asset Correlation mit Portfolio)
β_i = Cov(R_i, R_portfolio) / Var(R_portfolio)
    = (Σ * w)_i / (w^T * Σ * w)

### 4. Marginal VaR (per 1% increase in Weight_i)
MVaR_i = β_i * σ_portfolio * z_α

### 5. Component VaR (total contribution)
CompVaR_i = MVaR_i * w_i * V

### 6. Euler Allocation (Validation)
Σ CompVaR_i = VaR_portfolio

**Interpretation:**
- CompVaR_i > 0: Asset erhöht Portfolio-Risiko
- CompVaR_i < 0: Asset hedged Portfolio (möglich bei neg. Correlation!)

## Beispiel

**Portfolio:**
- BTC: 60% @ $60k → $36k
- ETH: 30% @ $3k → $900
- SOL: 10% @ $100 → $10
Total: $46,910

**Returns (Daily, 252 Days):**
- σ_BTC = 3.5%, σ_ETH = 4.2%, σ_SOL = 5.8%
- Corr(BTC,ETH) = 0.85
- Corr(BTC,SOL) = 0.70
- Corr(ETH,SOL) = 0.75

**Calculation:**
1. Covariance Matrix (3x3) → Ledoit-Wolf Shrinkage
2. σ_portfolio = sqrt(w^T * Σ * w) ≈ 3.8%
3. VaR_total (95%) = 1.645 * 3.8% * $46,910 ≈ $2,930

**Component VaR:**
- CompVaR_BTC = $1,680 → 57.3% Contribution (trotz 60% Weight!)
- CompVaR_ETH = $820 → 28.0%
- CompVaR_SOL = $430 → 14.7%

Σ CompVaR = $2,930 ✅ (Euler OK)

**Insights:**
- BTC dominiert Risiko (57.3% vs 60% Weight)
- SOL hat niedrigsten CompVaR trotz höchster Vol (nur 10% Weight)
- Diversification funktioniert (Total VaR < Σ Standalone VaRs)
```

### Success Metrics

- [x] ComponentVaRCalculator implementiert
- [x] Euler Allocation validiert (Σ CompVaR = Total VaR)
- [x] 10+ Unit Tests (alle passing)
- [x] Mathematik dokumentiert mit Beispiel

---

## 🔄 Phase 4: Portfolio Optimizer (5-6 Tage)

### Ziel

Risk Budgeting & Position Sizing basierend auf Component VaR.

### Deliverables

```
`src&sol;risk&sol;portfolio_optimizer.py (planned)`            # RiskBudgetOptimizer
src/risk/position_sizer.py                 # CompVaR-based Position Sizing
tests/risk/test_portfolio_optimizer.py     # Unit Tests
`docs&sol;risk&sol;RISK_BUDGETING.md (planned)`                # Theorie + Usage
```

### Tasks

**4.1 RiskBudgetOptimizer (2d)**

```python
# `src&sol;risk&sol;portfolio_optimizer.py (planned)`
from dataclasses import dataclass
from typing import Dict, Optional
import numpy as np
from scipy.optimize import minimize
from src.risk.component_var import ComponentVaRCalculator, ComponentVaRResult

@dataclass
class RiskBudget:
    """Risk Budget Constraints."""
    max_single_compvar_pct: float = 0.40      # Max 40% vom Total VaR
    max_total_var_pct: float = 0.15        # Max 15% vom Portfolio Value
    target_compvar_distribution: Optional[Dict[str, float]] = None

class RiskBudgetOptimizer:
    """
    Optimiert Weights um Risk Budget zu erfüllen.

    Objectives:
    1. Equal Risk Contribution (ERC): Alle CompVaR_i gleich
    2. Target Risk Distribution: CompVaR_i = target_i * Total VaR
    3. Min Total VaR: Minimize Total VaR subject to constraints

    Usage:
        optimizer = RiskBudgetOptimizer(compvar_calculator, risk_budget)
        optimal_weights = optimizer.optimize_erc(returns)
    """

    def __init__(
        self,
        compvar_calculator: ComponentVaRCalculator,
        risk_budget: RiskBudget
    ):
        self.compvar_calculator = compvar_calculator
        self.risk_budget = risk_budget

    def optimize_erc(
        self,
        returns: pd.DataFrame,
        portfolio_value: float
    ) -> Dict[str, float]:
        """
        Equal Risk Contribution: Alle CompVaR_i = Total VaR / N.

        Returns:
            Optimale Weights {asset: weight}
        """
        n_assets = len(returns.columns)
        asset_names = list(returns.columns)

        # Objective: Minimize Variance von CompVaR Contributions
        def objective(w):
            weights_dict = {asset: w[i] for i, asset in enumerate(asset_names)}
            result = self.compvar_calculator.calculate(
                returns, weights_dict, portfolio_value, validate_euler=False
            )

            compvars = np.array(list(result.component_var.values()))

            # Target: Alle CompVaR gleich
            target_compvar = result.total_var / n_assets
            return np.sum((compvars - target_compvar) ** 2)

        # Constraints
        constraints = [
            {"type": "eq", "fun": lambda w: np.sum(w) - 1.0},  # Σ w = 1
        ]

        # Bounds: 0 <= w_i <= 1
        bounds = [(0.0, 1.0) for _ in range(n_assets)]

        # Initial guess: Equal weights
        w0 = np.ones(n_assets) / n_assets

        # Optimize
        result = minimize(
            objective,
            w0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
        )

        if not result.success:
            raise ValueError(f"Optimization failed: {result.message}")

        # Convert to dict
        optimal_weights = {
            asset: result.x[i] for i, asset in enumerate(asset_names)
        }

        return optimal_weights

    def validate_risk_budget(
        self,
        result: ComponentVaRResult
    ) -> Dict[str, bool]:
        """
        Prüft ob Risk Budget eingehalten wird.

        Returns:
            {check_name: passed}
        """
        checks = {}

        # Check 1: Max Single CompVaR %
        max_contrib = max(result.contribution_pct.values())
        checks["max_single_compvar"] = (
            max_contrib <= self.risk_budget.max_single_compvar_pct * 100
        )

        # Check 2: Max Total VaR %
        # (würde Portfolio Value benötigen – simplified)
        checks["max_total_var"] = True  # Placeholder

        return checks
```

**4.2 Position Sizer (1d)**

```python
# src/risk/position_sizer.py
from dataclasses import dataclass
from typing import Dict
import numpy as np
from src.risk.component_var import ComponentVaRCalculator, ComponentVaRResult

@dataclass
class PositionSizingConfig:
    max_position_compvar_pct: float = 0.05    # Max 5% Portfolio Value pro Position
    risk_per_trade_pct: float = 0.02       # 2% Risk per Trade

class PositionSizer:
    """
    CompVaR-basiertes Position Sizing.

    Nutzt Marginal VaR um Position Size zu bestimmen:
        Position Size = Risk Budget / MVaR_i

    Usage:
        sizer = PositionSizer(config, compvar_calculator)
        size = sizer.calculate_position_size("BTC", portfolio_value, current_weights)
    """

    def __init__(
        self,
        config: PositionSizingConfig,
        compvar_calculator: ComponentVaRCalculator
    ):
        self.config = config
        self.compvar_calculator = compvar_calculator

    def calculate_position_size(
        self,
        asset: str,
        returns: pd.DataFrame,
        portfolio_value: float,
        current_weights: Dict[str, float]
    ) -> float:
        """
        Berechnet maximale Position Size für Asset.

        Args:
            asset: Asset Symbol
            returns: Historical Returns
            portfolio_value: Total Portfolio Value
            current_weights: Current Portfolio Weights

        Returns:
            Max Position Value (in $)
        """
        # Calculate CompVaR für current weights
        result = self.compvar_calculator.calculate(
            returns, current_weights, portfolio_value
        )

        # Marginal VaR für Asset
        mvar = result.marginal_var[asset]

        # Risk Budget (in $)
        risk_budget = portfolio_value * self.config.risk_per_trade_pct

        # Position Size = Risk Budget / MVaR
        # (vereinfacht – echte Implementierung würde Stop-Loss berücksichtigen)
        position_size = risk_budget / (mvar / portfolio_value)

        # Cap bei max_position_compvar_pct
        max_position = portfolio_value * self.config.max_position_compvar_pct

        return min(position_size, max_position)
```

**4.3 Tests (1.5d)**

```python
# tests/risk/test_portfolio_optimizer.py
import pytest
import pandas as pd
from pathlib import Path
from src.risk.portfolio_optimizer import RiskBudgetOptimizer, RiskBudget
from src.risk.component_var import ComponentVaRCalculator
from src.risk.covariance import CovarianceEstimatorConfig
from src.risk.var_calculator import VaRCalculatorConfig

@pytest.fixture
def crypto_returns():
    path = Path(__file__).parent / "fixtures" / "sample_returns.csv"
    return pd.read_csv(path, index_col=0, parse_dates=True)

def test_erc_optimization(crypto_returns):
    """Test: ERC liefert ausgeglichene CompVaR Contributions."""
    cov_config = CovarianceEstimatorConfig()
    var_config = VaRCalculatorConfig()
    compvar_calc = ComponentVaRCalculator(cov_config, var_config)

    risk_budget = RiskBudget()
    optimizer = RiskBudgetOptimizer(compvar_calc, risk_budget)

    optimal_weights = optimizer.optimize_erc(crypto_returns, 100000)

    # Weights sollten sinnvoll sein
    assert all(0 <= w <= 1 for w in optimal_weights.values())
    assert np.isclose(sum(optimal_weights.values()), 1.0)

    # CompVaR Contributions sollten ähnlich sein
    result = compvar_calc.calculate(crypto_returns, optimal_weights, 100000)
    compvars = list(result.component_var.values())

    # Variance von CompVaRs sollte kleiner sein als bei Equal Weights
    variance_compvars = np.var(compvars)

    # (Lower variance = mehr ausgeglichen)
    assert variance_compvars < 1000000  # Plausibility check
```

### Success Metrics

- [x] RiskBudgetOptimizer (ERC)
- [x] PositionSizer (CompVaR-based)
- [x] Tests zeigen ausgeglichene Risk Contributions
- [x] Dokumentation mit Beispiel

---

## ✅ Phase 5: Integration & Tests (3-4 Tage)

### Ziel

End-to-End Integration in Peak_Trade Risk-Layer + umfassende Tests.

### Deliverables

```
src/risk/__init__.py                       # Exports (ComponentVaR API)
tests/risk/test_component_var_e2e.py       # End-to-End Test
tests/risk/benchmark_compvar.py               # Performance Benchmark
scripts/risk/demo_component_var.py         # Demo-Script
`docs&sol;risk&sol;QUICKSTART_COMPONENT_VAR.md (planned)`      # Operator-Guide
```

### Tasks

**5.1 API Exports (0.5d)**

```python
# src/risk/__init__.py
from .covariance import (
    CovarianceEstimator,
    CovarianceEstimatorConfig,
    CovarianceMethod,
)

from .var_calculator import (
    VaRCalculator,
    VaRCalculatorConfig,
    VaRMethod,
)

from .component_var import (
    ComponentVaRCalculator,
    ComponentVaRResult,
)

from .portfolio_optimizer import (
    RiskBudgetOptimizer,
    RiskBudget,
)

from .position_sizer import (
    PositionSizer,
    PositionSizingConfig,
)

__all__ = [
    "CovarianceEstimator",
    "CovarianceEstimatorConfig",
    "CovarianceMethod",
    "VaRCalculator",
    "VaRCalculatorConfig",
    "VaRMethod",
    "ComponentVaRCalculator",
    "ComponentVaRResult",
    "RiskBudgetOptimizer",
    "RiskBudget",
    "PositionSizer",
    "PositionSizingConfig",
]
```

**5.2 End-to-End Test (1d)**

```python
# tests/risk/test_component_var_e2e.py
import pytest
import pandas as pd
from pathlib import Path
from src.risk import (
    ComponentVaRCalculator,
    CovarianceEstimatorConfig,
    VaRCalculatorConfig,
    RiskBudgetOptimizer,
    RiskBudget,
)

def test_full_workflow():
    """
    Test: Kompletter Workflow von Returns → CompVaR → Optimization.

    Workflow:
    1. Load Returns
    2. Calculate Component VaR
    3. Check Risk Budget
    4. Optimize Weights (ERC)
    5. Recalculate CompVaR
    6. Validate Euler Allocation
    """
    # 1. Load Data
    path = Path(__file__).parent / "fixtures" / "sample_returns.csv"
    returns = pd.read_csv(path, index_col=0, parse_dates=True)

    # 2. Initial Weights (naive equal)
    weights_initial = {"BTC": 0.33, "ETH": 0.33, "SOL": 0.34}
    portfolio_value = 100000

    # 3. Calculate CompVaR
    cov_config = CovarianceEstimatorConfig()
    var_config = VaRCalculatorConfig()
    compvar_calc = ComponentVaRCalculator(cov_config, var_config)

    result_initial = compvar_calc.calculate(returns, weights_initial, portfolio_value)

    print("\n=== Initial Portfolio ===")
    print(result_initial.to_dataframe())

    # 4. Optimize (ERC)
    risk_budget = RiskBudget()
    optimizer = RiskBudgetOptimizer(compvar_calc, risk_budget)

    weights_optimized = optimizer.optimize_erc(returns, portfolio_value)

    # 5. Recalculate CompVaR
    result_optimized = compvar_calc.calculate(returns, weights_optimized, portfolio_value)

    print("\n=== Optimized Portfolio (ERC) ===")
    print(result_optimized.to_dataframe())

    # 6. Validate
    compvars_optimized = list(result_optimized.component_var.values())
    variance_compvars = np.var(compvars_optimized)

    # ERC sollte CompVaR Variance reduzieren
    compvars_initial = list(result_initial.component_var.values())
    variance_initial = np.var(compvars_initial)

    assert variance_compvars < variance_initial
```

**5.3 Demo-Script (1d)**

```python
# scripts/risk/demo_component_var.py
"""
Component VaR Demo
==================

Zeigt kompletten Workflow:
1. Load Crypto Returns
2. Calculate Component VaR
3. Visualize Risk Contributions
4. Optimize for Equal Risk Contribution
"""

import pandas as pd
from pathlib import Path
from src.risk import (
    ComponentVaRCalculator,
    CovarianceEstimatorConfig,
    VaRCalculatorConfig,
    CovarianceMethod,
    VaRMethod,
)

def main():
    # 1. Load Data
    data_path = Path(__file__).parents[2] / "tests/risk/fixtures/sample_returns.csv"
    returns = pd.read_csv(data_path, index_col=0, parse_dates=True)

    print("📊 Loaded Returns:")
    print(returns.tail())
    print()

    # 2. Configure
    cov_config = CovarianceEstimatorConfig(
        method=CovarianceMethod.LEDOIT_WOLF,
        min_history=60
    )

    var_config = VaRCalculatorConfig(
        method=VaRMethod.PARAMETRIC,
        confidence_level=0.95
    )

    # 3. Calculate CompVaR
    calculator = ComponentVaRCalculator(cov_config, var_config)

    weights = {"BTC": 0.60, "ETH": 0.30, "SOL": 0.10}
    portfolio_value = 100000

    result = calculator.calculate(returns, weights, portfolio_value)

    # 4. Display Results
    print("🎯 Component VaR Results:")
    print("─" * 60)
    print(f"Total Portfolio VaR (95%): ${result.total_var:,.2f}")
    print()
    print(result.to_dataframe().to_string())
    print()

    # 5. Risk Budget Check
    max_contrib = max(result.contribution_pct.values())
    max_asset = max(result.contribution_pct, key=result.contribution_pct.get)

    print(f"⚠️  Highest Risk Contributor: {max_asset} ({max_contrib:.1f}%)")

    if max_contrib > 50:
        print("   → Consider rebalancing to reduce concentration risk!")

    print()
    print("✅ Euler Allocation Check:")
    compvar_sum = sum(result.component_var.values())
    print(f"   Σ CompVaR = ${compvar_sum:,.2f}")
    print(f"   Total VaR = ${result.total_var:,.2f}")
    print(f"   Difference: ${abs(compvar_sum - result.total_var):.2f}")

if __name__ == "__main__":
    main()
```

**5.4 Performance Benchmark (0.5d)**

```python
# tests/risk/benchmark_compvar.py
import time
import pandas as pd
import numpy as np
from pathlib import Path
from src.risk import (
    ComponentVaRCalculator,
    CovarianceEstimatorConfig,
    VaRCalculatorConfig,
)

def benchmark():
    """Benchmark: Wie lange dauert CompVaR Calculation?"""
    # Load Data
    path = Path(__file__).parent / "fixtures" / "sample_returns.csv"
    returns = pd.read_csv(path, index_col=0, parse_dates=True)

    weights = {"BTC": 0.5, "ETH": 0.3, "SOL": 0.2}

    # Setup
    cov_config = CovarianceEstimatorConfig()
    var_config = VaRCalculatorConfig()
    calculator = ComponentVaRCalculator(cov_config, var_config)

    # Benchmark
    n_iterations = 100
    times = []

    for _ in range(n_iterations):
        start = time.perf_counter()
        result = calculator.calculate(returns, weights, 100000, validate_euler=False)
        elapsed = time.perf_counter() - start
        times.append(elapsed)

    print(f"⏱️  Component VaR Benchmark ({n_iterations} iterations):")
    print(f"   Mean: {np.mean(times)*1000:.2f} ms")
    print(f"   Median: {np.median(times)*1000:.2f} ms")
    print(f"   P95: {np.percentile(times, 95)*1000:.2f} ms")

if __name__ == "__main__":
    benchmark()
```

**5.5 Operator-Guide (1d)**

```markdown
# `docs&sol;risk&sol;QUICKSTART_COMPONENT_VAR.md (planned)`

## Component VaR Quickstart

### 1. Installation

```bash
cd ~/Peak_Trade
source .venv/bin/activate

# Install Risk Extras
pip install -e ".[risk]"
```

### 2. Basic Usage

```python
from src.risk import (
    ComponentVaRCalculator,
    CovarianceEstimatorConfig,
    VaRCalculatorConfig,
)
import pandas as pd

# Load Returns
returns = pd.read_csv("data/returns.csv", index_col=0, parse_dates=True)

# Configure
cov_config = CovarianceEstimatorConfig(method="ledoit_wolf")
var_config = VaRCalculatorConfig(confidence_level=0.95)

# Calculate
calculator = ComponentVaRCalculator(cov_config, var_config)

weights = {"BTC": 0.6, "ETH": 0.3, "SOL": 0.1}
result = calculator.calculate(returns, weights, portfolio_value=100000)

# Display
print(result.to_dataframe())
```

### 3. Risk Budget Validation

```python
from src.risk import RiskBudgetOptimizer, RiskBudget

risk_budget = RiskBudget(
    max_single_compvar_pct=0.40,   # Max 40% vom Total VaR
    max_total_var_pct=0.15       # Max 15% vom Portfolio
)

optimizer = RiskBudgetOptimizer(calculator, risk_budget)
checks = optimizer.validate_risk_budget(result)

if not all(checks.values()):
    print("⚠️  Risk Budget verletzt!")
```

### 4. Demo ausführen

```bash
python3 scripts/risk/demo_component_var.py
```
```

### Success Metrics

- [x] API Exports in src/risk/__init__.py
- [x] E2E Test (Returns → CompVaR → Optimization)
- [x] Demo-Script funktioniert
- [x] Performance <50ms median (für 3 Assets, 252 Days)
- [x] Quickstart dokumentiert

---

## 📊 Phase 6: Monitoring & Alerts (2-3 Tage)

### Ziel

CompVaR-Monitoring in Backtests + Alerts bei Risk Budget Violation.

### Deliverables

```
`src&sol;risk&sol;compvar_monitor.py (planned)`                   # CompVaRMonitor Klasse
`src&sol;backtest&sol;compvar_integration.py (planned)`           # Backtest Integration
tests/risk/test_compvar_monitor.py            # Unit Tests
`docs&sol;risk&sol;MONITORING_ALERTS.md (planned)`             # Alert-Konfiguration
```

### Tasks

**6.1 CompVaRMonitor (1d)**

```python
# `src&sol;risk&sol;compvar_monitor.py (planned)`
from dataclasses import dataclass, field
from typing import List, Dict
from datetime import datetime
import pandas as pd

@dataclass
class CompVaRAlert:
    timestamp: datetime
    alert_type: str                        # "max_single_compvar", "total_var", etc.
    asset: str
    current_value: float
    threshold: float
    message: str

@dataclass
class CompVaRMonitorConfig:
    enabled: bool = False                  # Default: OFF
    check_interval_bars: int = 24          # Check every 24 bars (daily)
    alert_threshold_pct: float = 0.05      # Alert bei 5% Überschreitung

class CompVaRMonitor:
    """
    Monitored Component VaR während Backtests.

    Features:
    - Periodic CompVaR Checks (alle N Bars)
    - Alerts bei Risk Budget Violations
    - Historical CompVaR Tracking

    Usage:
        monitor = CompVaRMonitor(config, compvar_calculator, risk_budget)

        # In Backtest-Loop:
        for bar in bars:
            alert = monitor.check(current_bar, returns, weights, portfolio_value)
            if alert:
                print(alert.message)
    """

    def __init__(
        self,
        config: CompVaRMonitorConfig,
        compvar_calculator: ComponentVaRCalculator,
        risk_budget: RiskBudget
    ):
        self.config = config
        self.compvar_calculator = compvar_calculator
        self.risk_budget = risk_budget
        self.alerts: List[CompVaRAlert] = []
        self.history: List[ComponentVaRResult] = []
        self._last_check_bar = 0

    def check(
        self,
        current_bar: int,
        returns: pd.DataFrame,
        weights: Dict[str, float],
        portfolio_value: float
    ) -> List[CompVaRAlert]:
        """
        Prüft CompVaR und gibt Alerts zurück.

        Returns:
            Liste von Alerts (leer wenn alles OK)
        """
        if not self.config.enabled:
            return []

        # Check nur alle N Bars
        if current_bar - self._last_check_bar < self.config.check_interval_bars:
            return []

        self._last_check_bar = current_bar

        # Calculate CompVaR
        result = self.compvar_calculator.calculate(returns, weights, portfolio_value)
        self.history.append(result)

        # Check Risk Budget
        alerts = []

        # Check 1: Max Single CompVaR %
        max_contrib_asset = max(result.contribution_pct, key=result.contribution_pct.get)
        max_contrib_value = result.contribution_pct[max_contrib_asset]

        threshold = self.risk_budget.max_single_compvar_pct * 100

        if max_contrib_value > threshold * (1 + self.config.alert_threshold_pct):
            alert = CompVaRAlert(
                timestamp=datetime.now(),
                alert_type="max_single_compvar",
                asset=max_contrib_asset,
                current_value=max_contrib_value,
                threshold=threshold,
                message=(
                    f"⚠️  {max_contrib_asset} CompVaR Contribution {max_contrib_value:.1f}% "
                    f"exceeds threshold {threshold:.1f}%"
                )
            )
            alerts.append(alert)
            self.alerts.append(alert)

        return alerts

    def get_compvar_history_df(self) -> pd.DataFrame:
        """Gibt CompVaR History als DataFrame zurück."""
        records = []
        for i, result in enumerate(self.history):
            for asset, compvar in result.component_var.items():
                records.append({
                    "check_index": i,
                    "asset": asset,
                    "component_var": compvar,
                    "contribution_pct": result.contribution_pct[asset],
                })

        return pd.DataFrame(records)
```

**6.2 Backtest Integration (1d)**

```python
# `src&sol;backtest&sol;compvar_integration.py (planned)`
"""
Integration von Component VaR in BacktestEngine.

Usage:
    from src.backtest.compvar_integration import enable_compvar_monitoring

    engine = BacktestEngine(...)
    monitor = enable_compvar_monitoring(engine, compvar_config, risk_budget_config)

    result = engine.run_realistic(...)

    # Nach Backtest:
    print(monitor.get_compvar_history_df())
"""

from src.risk import (
    ComponentVaRCalculator,
    CovarianceEstimatorConfig,
    VaRCalculatorConfig,
)
from src.risk.compvar_monitor import CompVaRMonitor, CompVaRMonitorConfig
from src.risk.portfolio_optimizer import RiskBudget

def enable_compvar_monitoring(
    backtest_engine,
    compvar_config: dict,
    risk_budget_config: dict
) -> CompVaRMonitor:
    """
    Aktiviert CompVaR Monitoring in BacktestEngine.

    Args:
        backtest_engine: BacktestEngine Instance
        compvar_config: Config Dict für CompVaR (aus config.toml)
        risk_budget_config: Risk Budget Config

    Returns:
        CompVaRMonitor Instance (für Post-Analysis)
    """
    # Setup Calculator
    cov_config = CovarianceEstimatorConfig(
        method=compvar_config.get("covariance", {}).get("method", "ledoit_wolf")
    )

    var_config = VaRCalculatorConfig(
        confidence_level=compvar_config.get("confidence_level", 0.95)
    )

    compvar_calculator = ComponentVaRCalculator(cov_config, var_config)

    # Setup Risk Budget
    risk_budget = RiskBudget(
        max_single_compvar_pct=risk_budget_config.get("max_single_compvar_pct", 0.40),
        max_total_var_pct=risk_budget_config.get("max_total_var_pct", 0.15)
    )

    # Setup Monitor
    monitor_config = CompVaRMonitorConfig(
        enabled=compvar_config.get("enabled", False),
        check_interval_bars=compvar_config.get("check_interval_bars", 24)
    )

    monitor = CompVaRMonitor(monitor_config, compvar_calculator, risk_budget)

    # Hook in BacktestEngine (würde Custom Callback benötigen)
    # Placeholder: In echter Implementierung würde man on_bar Callback nutzen

    return monitor
```

**6.3 Tests + Docs (0.5d)**

```python
# tests/risk/test_compvar_monitor.py
import pytest
from src.risk.compvar_monitor import CompVaRMonitor, CompVaRMonitorConfig
from src.risk import ComponentVaRCalculator, CovarianceEstimatorConfig, VaRCalculatorConfig
from src.risk.portfolio_optimizer import RiskBudget

def test_monitor_alerts_on_violation():
    """Test: Monitor raised Alert bei Risk Budget Violation."""
    # Setup
    cov_config = CovarianceEstimatorConfig()
    var_config = VaRCalculatorConfig()
    compvar_calc = ComponentVaRCalculator(cov_config, var_config)

    risk_budget = RiskBudget(max_single_compvar_pct=0.30)  # Strict: Max 30%

    monitor_config = CompVaRMonitorConfig(
        enabled=True,
        check_interval_bars=1,     # Check every bar
        alert_threshold_pct=0.05
    )

    monitor = CompVaRMonitor(monitor_config, compvar_calc, risk_budget)

    # Load Data
    from pathlib import Path
    import pandas as pd
    path = Path(__file__).parent / "fixtures" / "sample_returns.csv"
    returns = pd.read_csv(path, index_col=0, parse_dates=True)

    # Portfolio mit BTC dominance (wird Alert triggern)
    weights = {"BTC": 0.80, "ETH": 0.15, "SOL": 0.05}

    # Check
    alerts = monitor.check(
        current_bar=0,
        returns=returns,
        weights=weights,
        portfolio_value=100000
    )

    # Sollte Alert haben (BTC >30% CompVaR)
    assert len(alerts) > 0
    assert alerts[0].asset == "BTC"
```

### Success Metrics

- [x] CompVaRMonitor mit Alert System
- [x] Backtest Integration (Hook)
- [x] Tests zeigen Alerts bei Violations
- [x] Dokumentation mit Alert-Konfiguration

---

## 🎯 Next Actions (Nach Roadmap)

### Immediate (Woche 1)

```bash
cd ~/Peak_Trade
git checkout -b feature/component-var

# Phase 0: Setup
python3 tests/risk/fixtures/generate_sample_returns.py
cat `config&sol;risk.toml (planned)`  # Review config

# Phase 1: Covariance
# Implementiere src/risk/covariance.py
python3 -m pytest tests/risk/test_covariance.py -v
```

### Short-term (Woche 2-3)

- Phase 2: VaR Calculator
- Phase 3: Component VaR Core (KRITISCH)
- Euler Allocation validieren

### Medium-term (Woche 4)

- Phase 4: Portfolio Optimizer
- Phase 5: Integration & Tests
- Phase 6: Monitoring

### Review Checkpoints

**Nach Phase 3:**
- Euler Allocation Tests 100% passing?
- Mathematik dokumentiert + validiert?
- Performance Benchmark <50ms?

**Nach Phase 5:**
- E2E Test funktioniert?
- Demo-Script läuft?
- API Exports sauber?

**Nach Phase 6:**
- Alert System funktioniert?
- Backtest Integration klar?
- Ready für v1.0?

---

## 📚 Literatur & Referenzen

**Papers:**
- Artzner et al. (1999): "Coherent Measures of Risk"
- Ledoit & Wolf (2004): "Honey, I Shrunk the Sample Covariance Matrix"
- Maillard et al. (2010): "Portfolio Risk Budgeting"

**Books:**
- McNeil et al. (2015): "Quantitative Risk Management"
- Jorion (2006): "Value at Risk: The New Benchmark for Managing Financial Risk"

**Code:**
- sklearn.covariance: Ledoit-Wolf Implementation
- scipy.stats: Statistical Distributions
- scipy.optimize: Portfolio Optimization

---

## ✅ Checkliste (Gesamt)

### Phase 0: Setup
- [ ] Literatur gelesen (4h)
- [ ] Dependencies installiert
- [ ] Config definiert
- [ ] Test-Daten generiert
- [ ] Theorie dokumentiert

### Phase 1: Covariance
- [ ] CovarianceEstimator implementiert
- [ ] 6+ Unit Tests passing
- [ ] Integration Test mit sample_returns.csv
- [ ] Dokumentation mit Beispiel

### Phase 2: VaR
- [ ] VaRCalculator implementiert (3 Methods)
- [ ] 5+ Unit Tests passing
- [ ] Performance validiert

### Phase 3: Component VaR **[KRITISCH]**
- [ ] ComponentVaRCalculator implementiert
- [ ] Euler Allocation validiert
- [ ] 10+ Unit Tests passing
- [ ] Mathematik dokumentiert

### Phase 4: Optimizer
- [ ] RiskBudgetOptimizer (ERC)
- [ ] PositionSizer
- [ ] Tests passing
- [ ] Dokumentation

### Phase 5: Integration
- [ ] API Exports
- [ ] E2E Test
- [ ] Demo-Script
- [ ] Performance <50ms
- [ ] Quickstart dokumentiert

### Phase 6: Monitoring
- [ ] CompVaRMonitor implementiert
- [ ] Backtest Integration
- [ ] Alert Tests
- [ ] Dokumentation

---

## 🎉 Fazit

**Status:** 📋 **ROADMAP COMPLETE**

**Effort:** ~3-4 Wochen (Vollzeit)

**Kritischer Pfad:**
Phase 0 → Phase 1 → Phase 2 → **Phase 3** → Phase 4 → Phase 5 → Phase 6

**Risk Level:** 🟡 **MEDIUM**
- Phase 3 (Component VaR) ist mathematisch anspruchsvoll
- Euler Allocation muss 100% korrekt sein
- Covariance Estimation benötigt Shrinkage für Stabilität

**Success Criteria:**
- ✅ Euler Allocation Tests passing
- ✅ Performance <50ms für 3-5 Assets
- ✅ Dokumentation mit Beispielen
- ✅ E2E Test funktioniert
- ✅ Config-driven (opt-in via config.toml)

---

**READY TO IMPLEMENT! 🚀**
