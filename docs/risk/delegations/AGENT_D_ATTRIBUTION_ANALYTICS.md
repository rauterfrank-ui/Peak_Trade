# Agent D: Attribution Analytics Implementation

**Agent:** D (Attribution Specialist)  
**Phase:** 3 (Attribution Analytics)  
**Priorität:** 🔴 HOCH  
**Aufwand:** 5-7 Tage  
**Status:** 📋 BEREIT ZU STARTEN

---

## 🎯 Ziel

Implementierung von Attribution Analytics für Risk Layer:
- VaR Decomposition (Marginal, Incremental, Component)
- P&L Attribution
- Factor Analysis (optional scipy)

**Warum wichtig:** Attribution Analytics beantwortet die Frage: "Welche Positionen/Faktoren tragen wie viel zum Gesamtrisiko bei?"

---

## 📚 Hintergrund

### Was ist Attribution?

**VaR Decomposition:**
- **Marginal VaR:** Wie ändert sich Portfolio-VaR wenn Position um 1 Unit erhöht wird?
- **Incremental VaR:** Wie ändert sich Portfolio-VaR wenn Position komplett entfernt wird?
- **Component VaR:** Wie viel trägt jede Position zum Gesamt-VaR bei? (Summe = Portfolio-VaR)

**P&L Attribution:**
- Zerlegung von Gewinnen/Verlusten nach Quellen
- Asset-Level Attribution (welches Asset trug wie viel bei?)
- Factor-Level Attribution (welche Faktoren trieben P&L?)

**Mathematischer Hintergrund:**

```
Portfolio VaR = sqrt(w^T * Σ * w)

Marginal VaR_i = ∂VaR/∂w_i = (Σ * w)_i / VaR

Component VaR_i = w_i * Marginal VaR_i

Incremental VaR_i = VaR(portfolio) - VaR(portfolio \ {i})
```

---

## 📋 Aufgaben

### Task 1: VaR Decomposition Core (2-3 Tage)

**Ziel:** Implementierung von Marginal, Incremental, Component VaR

**Dateien zu erstellen:**
```
src/risk_layer/attribution/
├── __init__.py                    # Public API
├── types.py                       # AttributionResult, ComponentVaR
├── var_decomposition.py           # Hauptimplementierung
└── README.md                      # Modul-Dokumentation
```

#### 1.1 Types definieren

**Datei:** `src/risk_layer/attribution/types.py`

```python
"""Attribution Analytics Types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

import pandas as pd


@dataclass(frozen=True)
class ComponentVaR:
    """Component VaR für eine einzelne Position."""

    asset: str
    weight: float
    marginal_var: float
    component_var: float
    incremental_var: float
    percent_contribution: float  # Component VaR / Portfolio VaR

    @property
    def diversification_benefit(self) -> float:
        """Diversifikations-Vorteil: Incremental - Component."""
        return self.incremental_var - self.component_var


@dataclass(frozen=True)
class VaRDecomposition:
    """Vollständige VaR-Zerlegung für Portfolio."""

    portfolio_var: float
    components: Dict[str, ComponentVaR]
    diversification_ratio: float  # Sum(Standalone VaR) / Portfolio VaR

    def to_dataframe(self) -> pd.DataFrame:
        """Konvertiert zu DataFrame für Reporting."""
        data = []
        for asset, comp in self.components.items():
            data.append({
                "asset": asset,
                "weight": comp.weight,
                "marginal_var": comp.marginal_var,
                "component_var": comp.component_var,
                "incremental_var": comp.incremental_var,
                "percent_contribution": comp.percent_contribution,
                "diversification_benefit": comp.diversification_benefit,
            })
        return pd.DataFrame(data)

    @property
    def top_contributors(self, n: int = 5) -> list[ComponentVaR]:
        """Top N Risiko-Beiträger."""
        sorted_comps = sorted(
            self.components.values(),
            key=lambda c: abs(c.component_var),
            reverse=True,
        )
        return sorted_comps[:n]


@dataclass(frozen=True)
class PnLAttribution:
    """P&L Attribution für Portfolio."""

    total_pnl: float
    asset_contributions: Dict[str, float]
    factor_contributions: Optional[Dict[str, float]] = None

    def to_dataframe(self) -> pd.DataFrame:
        """Konvertiert zu DataFrame."""
        data = [
            {"asset": asset, "pnl_contribution": pnl}
            for asset, pnl in self.asset_contributions.items()
        ]
        return pd.DataFrame(data)
```

#### 1.2 VaR Decomposition implementieren

**Datei:** `src/risk_layer/attribution/var_decomposition.py`

```python
"""VaR Decomposition Implementation."""

from __future__ import annotations

import logging
from typing import Dict, Optional

import numpy as np
import pandas as pd

from .types import ComponentVaR, VaRDecomposition

logger = logging.getLogger(__name__)


class VaRDecomposer:
    """
    Zerlegt Portfolio-VaR in Komponenten.

    Verwendet Kovarianz-Matrix für analytische Dekomposition.

    Usage:
        >>> decomposer = VaRDecomposer()
        >>> result = decomposer.decompose(
        ...     returns=returns_df,
        ...     weights={"BTC-EUR": 0.6, "ETH-EUR": 0.4},
        ...     confidence_level=0.95,
        ... )
        >>> print(result.to_dataframe())
    """

    def __init__(self, window: int = 252):
        """
        Args:
            window: Rolling window für Kovarianz-Schätzung
        """
        self.window = window

    def decompose(
        self,
        returns: pd.DataFrame,
        weights: Dict[str, float],
        confidence_level: float = 0.95,
        method: str = "parametric",
    ) -> VaRDecomposition:
        """
        Zerlegt Portfolio-VaR in Komponenten.

        Args:
            returns: Returns DataFrame (Assets als Spalten)
            weights: Portfolio-Gewichte {asset: weight}
            confidence_level: VaR-Konfidenzniveau
            method: "parametric" oder "historical"

        Returns:
            VaRDecomposition mit allen Komponenten
        """
        # Validierung
        assets = list(weights.keys())
        if not all(asset in returns.columns for asset in assets):
            raise ValueError("Nicht alle Assets in Returns vorhanden")

        # Returns filtern
        returns_subset = returns[assets].tail(self.window)

        # Portfolio-VaR berechnen
        portfolio_var = self._compute_portfolio_var(
            returns_subset, weights, confidence_level, method
        )

        # Komponenten berechnen
        components = {}

        for asset in assets:
            marginal = self._compute_marginal_var(
                returns_subset, weights, asset, confidence_level, method
            )

            component = weights[asset] * marginal

            incremental = self._compute_incremental_var(
                returns_subset, weights, asset, confidence_level, method
            )

            percent_contrib = component / portfolio_var if portfolio_var > 0 else 0.0

            components[asset] = ComponentVaR(
                asset=asset,
                weight=weights[asset],
                marginal_var=marginal,
                component_var=component,
                incremental_var=incremental,
                percent_contribution=percent_contrib,
            )

        # Diversifikations-Ratio
        standalone_vars = [
            self._compute_standalone_var(returns_subset[[asset]], confidence_level)
            for asset in assets
        ]
        sum_standalone = sum(w * v for w, v in zip(weights.values(), standalone_vars))
        diversification_ratio = sum_standalone / portfolio_var if portfolio_var > 0 else 1.0

        return VaRDecomposition(
            portfolio_var=portfolio_var,
            components=components,
            diversification_ratio=diversification_ratio,
        )

    def _compute_portfolio_var(
        self,
        returns: pd.DataFrame,
        weights: Dict[str, float],
        confidence_level: float,
        method: str,
    ) -> float:
        """Berechnet Portfolio-VaR."""
        if method == "parametric":
            # Parametric VaR
            w = np.array([weights[col] for col in returns.columns])
            cov = returns.cov().values

            portfolio_std = np.sqrt(w @ cov @ w)
            z_score = self._get_z_score(confidence_level)

            return portfolio_std * z_score

        elif method == "historical":
            # Historical VaR
            portfolio_returns = (returns * pd.Series(weights)).sum(axis=1)
            return -np.percentile(portfolio_returns, (1 - confidence_level) * 100)

        else:
            raise ValueError(f"Unknown method: {method}")

    def _compute_marginal_var(
        self,
        returns: pd.DataFrame,
        weights: Dict[str, float],
        asset: str,
        confidence_level: float,
        method: str,
    ) -> float:
        """Berechnet Marginal VaR für ein Asset."""
        if method != "parametric":
            # Für Historical: Numerische Approximation
            epsilon = 0.001
            weights_plus = weights.copy()
            weights_plus[asset] += epsilon

            var_plus = self._compute_portfolio_var(
                returns, weights_plus, confidence_level, method
            )
            var_base = self._compute_portfolio_var(
                returns, weights, confidence_level, method
            )

            return (var_plus - var_base) / epsilon

        # Parametric: Analytische Formel
        w = np.array([weights[col] for col in returns.columns])
        cov = returns.cov().values

        portfolio_var = self._compute_portfolio_var(
            returns, weights, confidence_level, method
        )

        asset_idx = list(returns.columns).index(asset)
        cov_w = cov @ w

        z_score = self._get_z_score(confidence_level)

        return z_score * cov_w[asset_idx] / portfolio_var if portfolio_var > 0 else 0.0

    def _compute_incremental_var(
        self,
        returns: pd.DataFrame,
        weights: Dict[str, float],
        asset: str,
        confidence_level: float,
        method: str,
    ) -> float:
        """Berechnet Incremental VaR (Portfolio ohne Asset)."""
        var_with = self._compute_portfolio_var(
            returns, weights, confidence_level, method
        )

        # Portfolio ohne Asset
        weights_without = {k: v for k, v in weights.items() if k != asset}

        if not weights_without:
            return var_with  # Nur ein Asset im Portfolio

        # Renormalisieren
        total = sum(weights_without.values())
        weights_without = {k: v / total for k, v in weights_without.items()}

        var_without = self._compute_portfolio_var(
            returns[[col for col in returns.columns if col in weights_without]],
            weights_without,
            confidence_level,
            method,
        )

        return var_with - var_without

    def _compute_standalone_var(
        self,
        returns: pd.DataFrame,
        confidence_level: float,
    ) -> float:
        """Berechnet Standalone VaR für ein Asset."""
        std = returns.std().values[0]
        z_score = self._get_z_score(confidence_level)
        return std * z_score

    @staticmethod
    def _get_z_score(confidence_level: float) -> float:
        """Gibt z-score für Konfidenzniveau zurück."""
        from scipy import stats
        return stats.norm.ppf(confidence_level)
```

**Acceptance Criteria:**
- [ ] `VaRDecomposer` implementiert
- [ ] Marginal VaR berechnet (analytisch für parametric)
- [ ] Component VaR berechnet
- [ ] Incremental VaR berechnet (numerisch)
- [ ] Diversifikations-Ratio berechnet
- [ ] Funktioniert mit und ohne scipy

---

### Task 2: P&L Attribution (2 Tage)

**Ziel:** P&L-Zerlegung nach Assets und Faktoren

**Datei:** `src/risk_layer/attribution/pnl_attribution.py`

```python
"""P&L Attribution Implementation."""

from __future__ import annotations

import logging
from typing import Dict, Optional

import pandas as pd

from .types import PnLAttribution

logger = logging.getLogger(__name__)


class PnLAttributor:
    """
    Zerlegt P&L nach Assets und Faktoren.

    Usage:
        >>> attributor = PnLAttributor()
        >>> result = attributor.attribute_pnl(
        ...     positions={"BTC-EUR": 1000, "ETH-EUR": 500},
        ...     returns={"BTC-EUR": 0.05, "ETH-EUR": -0.02},
        ... )
        >>> print(result.to_dataframe())
    """

    def attribute_pnl(
        self,
        positions: Dict[str, float],
        returns: Dict[str, float],
        factor_exposures: Optional[Dict[str, Dict[str, float]]] = None,
    ) -> PnLAttribution:
        """
        Zerlegt P&L nach Assets.

        Args:
            positions: Position-Werte {asset: value}
            returns: Returns {asset: return}
            factor_exposures: Optional Factor-Exposures {asset: {factor: exposure}}

        Returns:
            PnLAttribution
        """
        # Asset-Level Attribution
        asset_contributions = {}
        total_pnl = 0.0

        for asset, position_value in positions.items():
            if asset in returns:
                pnl = position_value * returns[asset]
                asset_contributions[asset] = pnl
                total_pnl += pnl

        # Factor-Level Attribution (optional)
        factor_contributions = None
        if factor_exposures:
            factor_contributions = self._attribute_to_factors(
                asset_contributions, factor_exposures
            )

        return PnLAttribution(
            total_pnl=total_pnl,
            asset_contributions=asset_contributions,
            factor_contributions=factor_contributions,
        )

    def _attribute_to_factors(
        self,
        asset_contributions: Dict[str, float],
        factor_exposures: Dict[str, Dict[str, float]],
    ) -> Dict[str, float]:
        """Zerlegt Asset-P&L nach Faktoren."""
        factor_pnl = {}

        for asset, pnl in asset_contributions.items():
            if asset in factor_exposures:
                for factor, exposure in factor_exposures[asset].items():
                    if factor not in factor_pnl:
                        factor_pnl[factor] = 0.0
                    factor_pnl[factor] += pnl * exposure

        return factor_pnl
```

**Acceptance Criteria:**
- [ ] Asset-Level Attribution implementiert
- [ ] Factor-Level Attribution implementiert (optional)
- [ ] Summe der Komponenten = Total P&L (Validierung)

---

### Task 3: Integration & Testing (1-2 Tage)

**Tests:** `tests/risk_layer/attribution/`

```python
# test_var_decomposition.py

import pytest
import numpy as np
import pandas as pd

from src.risk_layer.attribution import VaRDecomposer


@pytest.fixture
def sample_returns():
    """Sample Returns für Tests."""
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=500, freq="D")

    # Korrelierte Returns
    cov = np.array([[0.04, 0.02], [0.02, 0.09]])
    returns = np.random.multivariate_normal([0.001, 0.001], cov, 500)

    return pd.DataFrame(
        returns,
        columns=["BTC-EUR", "ETH-EUR"],
        index=dates,
    )


def test_var_decomposition_basic(sample_returns):
    """Test basic VaR decomposition."""
    decomposer = VaRDecomposer(window=252)

    weights = {"BTC-EUR": 0.6, "ETH-EUR": 0.4}

    result = decomposer.decompose(
        returns=sample_returns,
        weights=weights,
        confidence_level=0.95,
        method="parametric",
    )

    # Portfolio VaR sollte positiv sein
    assert result.portfolio_var > 0

    # Summe der Component VaRs sollte Portfolio VaR sein
    sum_components = sum(c.component_var for c in result.components.values())
    assert abs(sum_components - result.portfolio_var) < 1e-6

    # Diversifikations-Ratio sollte > 1 sein (Diversifikations-Vorteil)
    assert result.diversification_ratio > 1.0


def test_marginal_var_positive(sample_returns):
    """Test dass Marginal VaR positiv ist."""
    decomposer = VaRDecomposer()

    result = decomposer.decompose(
        returns=sample_returns,
        weights={"BTC-EUR": 0.6, "ETH-EUR": 0.4},
        confidence_level=0.95,
    )

    for comp in result.components.values():
        assert comp.marginal_var > 0


def test_incremental_var_removal(sample_returns):
    """Test Incremental VaR bei Asset-Entfernung."""
    decomposer = VaRDecomposer()

    result = decomposer.decompose(
        returns=sample_returns,
        weights={"BTC-EUR": 0.6, "ETH-EUR": 0.4},
        confidence_level=0.95,
    )

    # Incremental VaR sollte kleiner sein als Portfolio VaR
    for comp in result.components.values():
        assert comp.incremental_var < result.portfolio_var


def test_top_contributors(sample_returns):
    """Test Top Contributors."""
    decomposer = VaRDecomposer()

    result = decomposer.decompose(
        returns=sample_returns,
        weights={"BTC-EUR": 0.6, "ETH-EUR": 0.4},
        confidence_level=0.95,
    )

    top = result.top_contributors(n=1)
    assert len(top) == 1
    assert top[0].asset in ["BTC-EUR", "ETH-EUR"]
```

**Acceptance Criteria:**
- [ ] Unit Tests für VaR Decomposition (>90% Coverage)
- [ ] Unit Tests für P&L Attribution
- [ ] Integration Test mit echten Daten
- [ ] Edge Cases getestet (Single Asset, Equal Weights, etc.)

---

## 📁 Dateistruktur

```
src/risk_layer/attribution/
├── __init__.py                    # Public API Exports
├── types.py                       # AttributionResult, ComponentVaR, PnLAttribution
├── var_decomposition.py           # VaRDecomposer
├── pnl_attribution.py             # PnLAttributor
└── README.md                      # Modul-Dokumentation

tests/risk_layer/attribution/
├── __init__.py
├── conftest.py                    # Shared Fixtures
├── test_var_decomposition.py      # VaR Decomposition Tests
├── test_pnl_attribution.py        # P&L Attribution Tests
└── test_integration.py            # Integration Tests

docs/risk/
└── ATTRIBUTION_GUIDE.md           # User Guide
```

---

## 📊 Acceptance Criteria (Gesamt)

- [ ] VaR Decomposition implementiert (Marginal, Component, Incremental)
- [ ] P&L Attribution implementiert (Asset-Level)
- [ ] Factor Attribution implementiert (optional)
- [ ] Alle Tests passing (>90% Coverage)
- [ ] Dokumentation vollständig
- [ ] Integration mit bestehenden Risk-Modulen getestet
- [ ] Performance: <100ms für typisches Portfolio (10 Assets)

---

## 🚀 Deliverables

### Code
- `src/risk_layer/attribution/` Package (vollständig)

### Tests
- `tests/risk_layer/attribution/` (vollständig)

### Dokumentation
- `docs/risk/ATTRIBUTION_GUIDE.md`

---

## 📝 PR-Serie

**PR1:** `feat(risk): add var decomposition and attribution core`
- Types + VaRDecomposer
- Basic Tests

**PR2:** `feat(risk): add pnl attribution analytics`
- PnLAttributor
- Integration Tests

**PR3 (optional):** `feat(risk): add factor analysis (optional scipy)`
- Factor-Level Attribution
- Advanced Analytics

---

## ⏱️ Timeline

| Task | Aufwand |
|------|---------|
| VaR Decomposition Core | 2-3 Tage |
| P&L Attribution | 2 Tage |
| Integration & Testing | 1-2 Tage |
| **GESAMT** | **5-7 Tage** |

---

## 📞 Support

**Bei Fragen:**
- Alignment Doc: `docs/risk/RISK_LAYER_ROADMAP_ALIGNMENT.md`
- Bestehende VaR Implementation: `src/risk/var.py`, `src/risk/component_var.py`

**Agent A (Lead):** Verfügbar für Architektur-Fragen

---

**Erstellt von:** Agent A (Lead Orchestrator)  
**Delegiert an:** Agent D (Attribution Specialist)  
**Status:** 📋 BEREIT ZU STARTEN

**Viel Erfolg! 🚀**
