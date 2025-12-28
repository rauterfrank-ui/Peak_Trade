# Peak_Trade Risk Layer Roadmap

**Version:** 1.0  
**Datum:** 2025-12-28  
**Status:** 🟡 IN PLANUNG  
**Ziel-Completion:** Risk Layer → 100% (aktuell: 60%)

---

## 📋 Executive Summary

Diese Roadmap beschreibt die vollständige Implementierung der fehlenden Risk-Layer-Komponenten für Peak_Trade. Der Risk Layer ist **Critical Path** für Version 1.0 — ohne vollständigen Risk Layer kein Shadow Trading, kein Testnet, kein Live.

**Fehlende Komponenten (40%):**
1. Portfolio VaR/CVaR Berechnung
2. Component VaR (Risiko-Attribution)
3. Kupiec POF Backtesting (VaR-Validierung)
4. Monte Carlo Simulation
5. Stress Testing (historische Crypto-Szenarien)

**Geschätzter Gesamtaufwand:** 3-4 Wochen (bei Fokus-Arbeit)

---

## 🎯 Übergeordnete Prinzipien

### Safety First
- ✅ Alle Risk-Berechnungen müssen **deterministisch** und **reproduzierbar** sein
- ✅ Keine Approximationen ohne dokumentierte Fehlertoleranz
- ✅ Jede Komponente einzeln testbar (Unit Tests)
- ✅ Integration Tests für Risk-Pipeline

### Architektur-Constraints
- ✅ Modular: Jede Komponente als eigenständiges Modul
- ✅ Config-Driven: Alle Parameter aus `config.toml`
- ✅ Optional Dependencies: scipy/statsmodels nur wenn nötig
- ✅ Fallback-Logik: Graceful degradation bei fehlenden Deps

### Abhängigkeiten
```
Phase 1 (VaR/CVaR) ──────┐
                         ├──► Phase 3 (Kupiec POF)
Phase 2 (Component VaR) ─┘

Phase 4 (Monte Carlo) ───┐
                         ├──► Phase 5 (Integration)
Phase 3 (Kupiec POF) ────┤
                         │
Stress Testing ──────────┘
```

---

## 📊 Phasen-Übersicht

| Phase | Komponente | Aufwand | Abhängigkeiten | Priorität |
|-------|------------|---------|----------------|-----------|
| 1 | Portfolio VaR/CVaR | 4-5 Tage | Data Layer | 🔴 CRITICAL |
| 2 | Component VaR | 3-4 Tage | Phase 1 | 🔴 CRITICAL |
| 3 | Kupiec POF Backtesting | 3-4 Tage | Phase 1, 2 | 🟠 HIGH |
| 4 | Monte Carlo Simulation | 4-5 Tage | Phase 1 | 🟠 HIGH |
| 5 | Stress Testing | 3-4 Tage | Phase 1, 4 | 🟠 HIGH |
| 6 | Integration & Docs | 2-3 Tage | Phase 1-5 | 🟢 MEDIUM |

**Gesamt:** ~20-25 Arbeitstage

---

# Phase 1: Portfolio VaR/CVaR Berechnung

**Dauer:** 4-5 Tage  
**Priorität:** 🔴 CRITICAL  
**Abhängigkeiten:** Data Layer (✅ vorhanden)

## 1.1 Ziele

- Berechnung von Value at Risk (VaR) auf Portfolio-Ebene
- Berechnung von Conditional VaR (CVaR / Expected Shortfall)
- Unterstützung für mehrere VaR-Methoden
- Integration mit bestehender BacktestEngine

## 1.2 VaR-Methoden (zu implementieren)

| Methode | Beschreibung | Komplexität | Priorität |
|---------|--------------|-------------|-----------|
| Historical Simulation | Empirische Verteilung der Returns | Low | P0 |
| Parametric (Variance-Covariance) | Normalverteilungs-Annahme | Medium | P0 |
| Cornish-Fisher | Anpassung für Skewness/Kurtosis | Medium | P1 |
| EWMA (Exponentially Weighted) | Zeit-gewichtete Volatilität | Medium | P1 |

## 1.3 Deliverables

### Dateien
```
src/risk/
├── var.py                     # Haupt-VaR-Modul (VaR + CVaR)
├── covariance.py              # Kovarianz-Schätzer
├── component_var.py           # Component VaR
└── __init__.py                # Exports aktualisieren

tests/risk/
├── test_var.py                # Unit Tests VaR + CVaR
├── test_covariance.py         # Unit Tests Kovarianz
└── test_component_var.py      # Unit Tests Component VaR

config/
└── risk.toml                  # Risk-Parameter (erweitern)
```

### Klassen-Signaturen

```python
# src/risk/var.py

from dataclasses import dataclass
from enum import Enum
from typing import Optional
import numpy as np
import pandas as pd

class VaRMethod(Enum):
    """Unterstützte VaR-Berechnungsmethoden."""
    HISTORICAL = "historical"
    PARAMETRIC = "parametric"
    CORNISH_FISHER = "cornish_fisher"
    EWMA = "ewma"

@dataclass
class VaRResult:
    """Ergebnis einer VaR-Berechnung."""
    var_value: float              # VaR in Währungseinheiten
    var_pct: float                # VaR als Prozentsatz
    confidence_level: float       # z.B. 0.95 oder 0.99
    method: VaRMethod             # Verwendete Methode
    holding_period_days: int      # Haltedauer in Tagen
    timestamp: pd.Timestamp       # Berechnungszeitpunkt
    portfolio_value: float        # Portfolio-Wert zum Zeitpunkt

@dataclass
class CVaRResult:
    """Ergebnis einer CVaR-Berechnung (Expected Shortfall)."""
    cvar_value: float             # CVaR in Währungseinheiten
    cvar_pct: float               # CVaR als Prozentsatz
    var_result: VaRResult         # Zugehöriger VaR
    tail_returns: np.ndarray      # Returns im Tail

class PortfolioVaRCalculator:
    """
    Berechnet Portfolio Value at Risk (VaR).

    Unterstützt mehrere Methoden:
    - Historical Simulation
    - Parametric (Variance-Covariance)
    - Cornish-Fisher Expansion
    - EWMA (Exponentially Weighted Moving Average)
    """

    def __init__(
        self,
        confidence_level: float = 0.95,
        holding_period_days: int = 1,
        method: VaRMethod = VaRMethod.HISTORICAL,
        lookback_days: int = 252,
        ewma_lambda: float = 0.94,  # RiskMetrics Standard
    ):
        """
        Initialisiert den VaR-Calculator.

        Args:
            confidence_level: Konfidenzniveau (0.95 = 95%)
            holding_period_days: Haltedauer für VaR-Skalierung
            method: VaR-Berechnungsmethode
            lookback_days: Historische Daten für Berechnung
            ewma_lambda: Decay-Faktor für EWMA (nur bei EWMA-Methode)
        """
        pass

    def calculate(
        self,
        returns: pd.DataFrame,
        weights: np.ndarray,
        portfolio_value: float,
    ) -> VaRResult:
        """
        Berechnet Portfolio-VaR.

        Args:
            returns: DataFrame mit Asset-Returns (Spalten = Assets)
            weights: Portfolio-Gewichte (summieren zu 1.0)
            portfolio_value: Aktueller Portfolio-Wert in EUR

        Returns:
            VaRResult mit VaR-Wert und Metadaten
        """
        pass

    def calculate_historical(
        self,
        portfolio_returns: pd.Series,
        portfolio_value: float,
    ) -> VaRResult:
        """Historical Simulation VaR."""
        pass

    def calculate_parametric(
        self,
        portfolio_returns: pd.Series,
        portfolio_value: float,
    ) -> VaRResult:
        """Parametric (Variance-Covariance) VaR."""
        pass

    def calculate_cornish_fisher(
        self,
        portfolio_returns: pd.Series,
        portfolio_value: float,
    ) -> VaRResult:
        """Cornish-Fisher VaR mit Skewness/Kurtosis-Anpassung."""
        pass

    def calculate_ewma(
        self,
        portfolio_returns: pd.Series,
        portfolio_value: float,
    ) -> VaRResult:
        """EWMA VaR mit exponentiell gewichteter Volatilität."""
        pass


class PortfolioCVaRCalculator:
    """
    Berechnet Conditional VaR (Expected Shortfall).

    CVaR = E[Loss | Loss > VaR]

    Gibt den erwarteten Verlust an, WENN der VaR überschritten wird.
    Kohärentes Risikomaß (im Gegensatz zu VaR).
    """

    def __init__(
        self,
        var_calculator: PortfolioVaRCalculator,
    ):
        """
        Args:
            var_calculator: VaR-Calculator für Basis-Berechnung
        """
        pass

    def calculate(
        self,
        returns: pd.DataFrame,
        weights: np.ndarray,
        portfolio_value: float,
    ) -> CVaRResult:
        """
        Berechnet Portfolio-CVaR.

        Args:
            returns: DataFrame mit Asset-Returns
            weights: Portfolio-Gewichte
            portfolio_value: Aktueller Portfolio-Wert

        Returns:
            CVaRResult mit CVaR und zugehörigem VaR
        """
        pass
```

## 1.4 Config-Erweiterung

```toml
# config/risk.toml

[risk.var]
# VaR-Konfiguration
enabled = true
confidence_level = 0.95          # 95% Konfidenzniveau
holding_period_days = 1          # 1-Tages-VaR
method = "historical"            # historical | parametric | cornish_fisher | ewma
lookback_days = 252              # ~1 Jahr historische Daten

[risk.var.ewma]
# EWMA-spezifische Parameter
lambda = 0.94                    # RiskMetrics Standard: 0.94
min_observations = 20            # Mindestanzahl Datenpunkte

[risk.cvar]
# CVaR/Expected Shortfall
enabled = true
# Nutzt gleiche Parameter wie VaR

[risk.limits]
# Risiko-Limits (bestehend, erweitern)
max_portfolio_var_pct = 0.05     # Max 5% VaR
max_portfolio_cvar_pct = 0.08    # Max 8% CVaR
var_breach_action = "warn"       # warn | block | reduce
```

## 1.5 Akzeptanzkriterien

### Funktional
- [ ] Historical VaR berechnet korrekt (Vergleich mit Excel/R)
- [ ] Parametric VaR berechnet korrekt (Vergleich mit Formel)
- [ ] CVaR berechnet korrekt (Durchschnitt der Tail-Losses)
- [ ] Multi-Asset Portfolio unterstützt (min. 3 Assets)
- [ ] Holding Period Scaling funktioniert (√t-Regel)

### Tests
- [ ] Unit Tests für alle VaR-Methoden (≥90% Coverage)
- [ ] Edge Cases: Leere Returns, NaN-Werte, zu wenig Daten
- [ ] Benchmark gegen bekannte Werte (z.B. aus Literatur)
- [ ] Performance Test: 10.000 Returns in <1 Sekunde

### Integration
- [ ] Config-Loading aus `risk.toml`
- [ ] Integration mit `RiskManager` Klasse
- [ ] Logging aller VaR-Berechnungen

## 1.6 Beispiel-Nutzung

```python
from src.risk.var_calculator import (
    PortfolioVaRCalculator,
    PortfolioCVaRCalculator,
    VaRMethod
)
import pandas as pd
import numpy as np

# Beispiel: 3-Asset Crypto Portfolio
returns = pd.DataFrame({
    'BTC': np.random.normal(0.001, 0.03, 252),
    'ETH': np.random.normal(0.002, 0.05, 252),
    'LTC': np.random.normal(0.0005, 0.04, 252),
})
weights = np.array([0.5, 0.3, 0.2])  # 50% BTC, 30% ETH, 20% LTC
portfolio_value = 10_000  # EUR

# VaR berechnen
var_calc = PortfolioVaRCalculator(
    confidence_level=0.95,
    method=VaRMethod.HISTORICAL,
)
var_result = var_calc.calculate(returns, weights, portfolio_value)

print(f"95% VaR: {var_result.var_value:.2f} EUR ({var_result.var_pct:.2%})")
# Beispiel-Output: "95% VaR: 487.23 EUR (4.87%)"

# CVaR berechnen
cvar_calc = PortfolioCVaRCalculator(var_calc)
cvar_result = cvar_calc.calculate(returns, weights, portfolio_value)

print(f"95% CVaR: {cvar_result.cvar_value:.2f} EUR ({cvar_result.cvar_pct:.2%})")
# Beispiel-Output: "95% CVaR: 623.45 EUR (6.23%)"
```

---

# Phase 2: Component VaR (Risiko-Attribution)

**Dauer:** 3-4 Tage  
**Priorität:** 🔴 CRITICAL  
**Abhängigkeiten:** Phase 1 (VaR/CVaR)

## 2.1 Ziele

- **Component VaR:** Wie viel trägt jedes Asset zum Gesamt-VaR bei?
- **Marginal VaR:** Wie ändert sich VaR bei kleiner Gewichtsänderung?
- **Incremental VaR:** Wie ändert sich VaR beim Hinzufügen eines neuen Assets?
- Ermöglicht gezielte Risiko-Reduktion

## 2.2 Konzepte

| Konzept | Formel | Nutzen |
|---------|--------|--------|
| **Component VaR** | CVaR_i = w_i × ∂VaR/∂w_i | Risiko-Beitrag pro Asset |
| **Marginal VaR** | MVaR_i = ∂VaR/∂w_i | Sensitivität des VaR |
| **Incremental VaR** | IVaR = VaR(P+A) - VaR(P) | Impact eines neuen Assets |

**Wichtig:** Σ Component VaR = Portfolio VaR (Euler-Zerlegung)

## 2.3 Deliverables

### Dateien
```
src/risk/
├── component_var.py           # Component/Marginal/Incremental VaR
├── risk_attribution.py        # Risk-Attribution-Report
└── risk_decomposition.py      # Diversifikations-Analyse

tests/risk/
├── test_component_var.py      # Unit Tests
└── test_risk_attribution.py   # Integration Tests
```

### Klassen-Signaturen

```python
# src/risk/component_var.py

from dataclasses import dataclass
from typing import Dict, List
import numpy as np
import pandas as pd

@dataclass
class ComponentVaRResult:
    """Ergebnis der Component VaR Berechnung."""
    portfolio_var: float                    # Gesamt-Portfolio-VaR
    component_var: Dict[str, float]         # VaR pro Asset
    component_var_pct: Dict[str, float]     # VaR-Anteil pro Asset (%)
    marginal_var: Dict[str, float]          # Marginaler VaR
    diversification_benefit: float          # Diversifikations-Effekt

    def to_dataframe(self) -> pd.DataFrame:
        """Konvertiert Ergebnis zu DataFrame für Reporting."""
        pass

@dataclass
class IncrementalVaRResult:
    """Ergebnis der Incremental VaR Berechnung."""
    base_var: float                         # VaR ohne neues Asset
    new_var: float                          # VaR mit neuem Asset
    incremental_var: float                  # Differenz
    incremental_var_pct: float              # Prozentuale Änderung
    new_asset: str                          # Name des neuen Assets
    new_weight: float                       # Gewicht des neuen Assets


class ComponentVaRCalculator:
    """
    Berechnet Component VaR für Risiko-Attribution.

    Component VaR zeigt, wie viel jedes Asset zum Gesamt-VaR beiträgt.
    Nutzt Euler-Zerlegung für konsistente Attribution.
    """

    def __init__(
        self,
        var_calculator: "PortfolioVaRCalculator",
        delta_weight: float = 0.0001,  # Für numerische Ableitung
    ):
        """
        Args:
            var_calculator: Basis-VaR-Calculator
            delta_weight: Schrittweite für Marginal VaR
        """
        pass

    def calculate(
        self,
        returns: pd.DataFrame,
        weights: np.ndarray,
        portfolio_value: float,
        asset_names: List[str],
    ) -> ComponentVaRResult:
        """
        Berechnet Component VaR für alle Assets.

        Args:
            returns: Asset-Returns
            weights: Portfolio-Gewichte
            portfolio_value: Aktueller Portfolio-Wert
            asset_names: Namen der Assets (für Report)

        Returns:
            ComponentVaRResult mit VaR-Zerlegung
        """
        pass

    def calculate_marginal_var(
        self,
        returns: pd.DataFrame,
        weights: np.ndarray,
        portfolio_value: float,
        asset_index: int,
    ) -> float:
        """
        Berechnet Marginal VaR für ein Asset.

        Marginal VaR = ∂VaR/∂w_i
        """
        pass

    def calculate_incremental_var(
        self,
        returns: pd.DataFrame,
        current_weights: np.ndarray,
        portfolio_value: float,
        new_asset_returns: pd.Series,
        new_weight: float,
        new_asset_name: str,
    ) -> IncrementalVaRResult:
        """
        Berechnet Incremental VaR beim Hinzufügen eines neuen Assets.

        Args:
            returns: Bestehende Asset-Returns
            current_weights: Aktuelle Gewichte (werden re-scaled)
            portfolio_value: Portfolio-Wert
            new_asset_returns: Returns des neuen Assets
            new_weight: Zielgewicht für neues Asset
            new_asset_name: Name des neuen Assets

        Returns:
            IncrementalVaRResult mit VaR-Änderung
        """
        pass

    def calculate_diversification_benefit(
        self,
        returns: pd.DataFrame,
        weights: np.ndarray,
        portfolio_value: float,
    ) -> float:
        """
        Berechnet Diversifikations-Benefit.

        Benefit = Σ(Individual VaR) - Portfolio VaR

        Positiver Wert = Diversifikation reduziert Risiko.
        """
        pass
```

## 2.4 Config-Erweiterung

```toml
# config/risk.toml (erweitern)

[risk.component_var]
enabled = true
delta_weight = 0.0001            # Schrittweite für Marginal VaR
min_component_var_pct = 0.01     # Minimum für Report (1%)
report_top_n = 5                 # Top N Risiko-Beiträge

[risk.attribution]
# Risk Attribution Reporting
generate_report = true
report_format = "html"           # html | json | csv
include_charts = true
```

## 2.5 Akzeptanzkriterien

### Funktional
- [ ] Component VaR summiert zu Portfolio VaR (Euler-Zerlegung)
- [ ] Marginal VaR korrekt berechnet (numerisch oder analytisch)
- [ ] Incremental VaR zeigt Impact neuer Assets
- [ ] Diversifikations-Benefit korrekt berechnet

### Tests
- [ ] Unit Tests für alle Methoden
- [ ] Validierung: Σ Component VaR = Portfolio VaR (Toleranz <0.01%)
- [ ] Edge Cases: 1-Asset Portfolio, 100% Korrelation

### Reporting
- [ ] DataFrame-Export für alle Ergebnisse
- [ ] HTML-Report mit Risk Attribution Chart (optional)

## 2.6 Beispiel-Nutzung

```python
from src.risk.component_var import ComponentVaRCalculator
from src.risk.var_calculator import PortfolioVaRCalculator

# Setup
var_calc = PortfolioVaRCalculator(confidence_level=0.95)
comp_var_calc = ComponentVaRCalculator(var_calc)

# Berechnung
result = comp_var_calc.calculate(
    returns=returns,
    weights=np.array([0.5, 0.3, 0.2]),
    portfolio_value=10_000,
    asset_names=['BTC', 'ETH', 'LTC'],
)

print(f"Portfolio VaR: {result.portfolio_var:.2f} EUR")
print(f"\nComponent VaR:")
for asset, cvar in result.component_var.items():
    pct = result.component_var_pct[asset]
    print(f"  {asset}: {cvar:.2f} EUR ({pct:.1%})")
print(f"\nDiversification Benefit: {result.diversification_benefit:.2f} EUR")

# Output:
# Portfolio VaR: 487.23 EUR
#
# Component VaR:
#   BTC: 312.45 EUR (64.1%)
#   ETH: 156.78 EUR (32.2%)
#   LTC: 18.00 EUR (3.7%)
#
# Diversification Benefit: 89.34 EUR
```

---

# Phase 3: Kupiec POF Backtesting

**Dauer:** 3-4 Tage  
**Priorität:** 🟠 HIGH  
**Abhängigkeiten:** Phase 1 (VaR), Phase 2 (Component VaR)

## 3.1 Ziele

- **VaR-Modell-Validierung** mittels statistischer Tests
- **Kupiec POF Test** (Proportion of Failures)
- **Christoffersen Test** (Unabhängigkeit der Verletzungen)
- **Traffic Light Approach** (Basel-konform)

## 3.2 Konzepte

### Kupiec POF Test
```
H0: Beobachtete Verletzungsrate = Erwartete Verletzungsrate
H1: Verletzungsraten unterscheiden sich

Test-Statistik:
LR_POF = -2 * ln[(1-p)^(T-N) * p^N / (1-N/T)^(T-N) * (N/T)^N]

Wobei:
- p = 1 - Konfidenzniveau (z.B. 0.05 bei 95% VaR)
- N = Anzahl VaR-Verletzungen
- T = Anzahl Beobachtungen

LR_POF ~ χ²(1) unter H0
```

### Traffic Light Zones (Basel III)
| Zone | Verletzungen (250 Tage, 99% VaR) | Multiplikator |
|------|-----------------------------------|---------------|
| 🟢 Green | 0-4 | 3.0 |
| 🟡 Yellow | 5-9 | 3.4-3.85 |
| 🔴 Red | ≥10 | 4.0 |

## 3.3 Deliverables

### Dateien
```
src/risk/
├── var_backtester.py          # VaR Backtesting
├── kupiec_test.py             # Kupiec POF Test
├── christoffersen_test.py     # Independence Test
└── traffic_light.py           # Basel Traffic Light

tests/risk/
├── test_var_backtester.py     # Unit Tests
├── test_kupiec.py             # Kupiec Test Tests
└── test_traffic_light.py      # Traffic Light Tests
```

### Klassen-Signaturen

```python
# src/risk/var_backtester.py

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple
import numpy as np
import pandas as pd

class TrafficLightZone(Enum):
    """Basel Traffic Light Zones."""
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"

@dataclass
class VaRViolation:
    """Eine einzelne VaR-Verletzung."""
    date: pd.Timestamp
    var_estimate: float
    actual_loss: float
    excess_loss: float  # actual_loss - var_estimate

@dataclass
class KupiecTestResult:
    """Ergebnis des Kupiec POF Tests."""
    test_statistic: float         # LR_POF
    p_value: float                # p-Wert
    reject_h0: bool               # H0 ablehnen bei α=0.05?
    observed_violations: int      # Anzahl Verletzungen
    expected_violations: float    # Erwartete Verletzungen
    violation_rate: float         # Beobachtete Rate
    expected_rate: float          # Erwartete Rate (1-CL)

@dataclass
class ChristoffersenTestResult:
    """Ergebnis des Christoffersen Independence Tests."""
    test_statistic: float         # LR_ind
    p_value: float
    reject_h0: bool               # Verletzungen unabhängig?
    n00: int                      # No violation → No violation
    n01: int                      # No violation → Violation
    n10: int                      # Violation → No violation
    n11: int                      # Violation → Violation

@dataclass
class VaRBacktestResult:
    """Gesamtergebnis des VaR Backtests."""
    # Basis-Statistiken
    total_observations: int
    total_violations: int
    violation_rate: float
    expected_rate: float

    # Test-Ergebnisse
    kupiec_result: KupiecTestResult
    christoffersen_result: Optional[ChristoffersenTestResult]

    # Traffic Light
    traffic_light_zone: TrafficLightZone
    basel_multiplier: float

    # Details
    violations: List[VaRViolation]
    var_estimates: pd.Series
    actual_returns: pd.Series


class VaRBacktester:
    """
    Backtestet VaR-Modelle mit statistischen Tests.

    Implementiert:
    - Kupiec POF Test (Proportion of Failures)
    - Christoffersen Test (Independence)
    - Basel Traffic Light System
    """

    def __init__(
        self,
        var_calculator: "PortfolioVaRCalculator",
        significance_level: float = 0.05,
    ):
        """
        Args:
            var_calculator: VaR-Calculator für Out-of-Sample Estimates
            significance_level: Signifikanzniveau für Tests (default: 5%)
        """
        pass

    def run_backtest(
        self,
        returns: pd.DataFrame,
        weights: np.ndarray,
        portfolio_value: float,
        estimation_window: int = 252,
        test_window: Optional[int] = None,
    ) -> VaRBacktestResult:
        """
        Führt Rolling-Window VaR Backtest durch.

        Args:
            returns: Asset-Returns für gesamten Zeitraum
            weights: Portfolio-Gewichte
            portfolio_value: Portfolio-Wert
            estimation_window: Tage für VaR-Schätzung
            test_window: Tage für Test (None = Rest der Daten)

        Returns:
            VaRBacktestResult mit allen Test-Ergebnissen
        """
        pass

    def kupiec_pof_test(
        self,
        violations: int,
        observations: int,
        confidence_level: float,
    ) -> KupiecTestResult:
        """
        Führt Kupiec POF Test durch.

        Tests ob beobachtete Verletzungsrate der erwarteten entspricht.
        """
        pass

    def christoffersen_test(
        self,
        violation_series: pd.Series,
    ) -> ChristoffersenTestResult:
        """
        Führt Christoffersen Independence Test durch.

        Tests ob VaR-Verletzungen unabhängig voneinander sind.
        """
        pass

    def get_traffic_light_zone(
        self,
        violations: int,
        observations: int = 250,
        confidence_level: float = 0.99,
    ) -> Tuple[TrafficLightZone, float]:
        """
        Bestimmt Basel Traffic Light Zone.

        Returns:
            Tuple von (Zone, Multiplikator)
        """
        pass
```

## 3.4 Config-Erweiterung

```toml
# config/risk.toml (erweitern)

[risk.var_backtest]
enabled = true
estimation_window = 252          # ~1 Jahr für VaR-Schätzung
test_significance = 0.05         # 5% Signifikanzniveau
run_christoffersen = true        # Independence Test

[risk.traffic_light]
# Basel Traffic Light Konfiguration
reference_days = 250             # Tage für Traffic Light
green_max_violations = 4         # Max für Green Zone (99% VaR)
yellow_max_violations = 9        # Max für Yellow Zone
```

## 3.5 Akzeptanzkriterien

### Funktional
- [ ] Kupiec POF Test berechnet korrekt (Vergleich mit R/Python Referenz)
- [ ] Christoffersen Test implementiert (Markov-Kette)
- [ ] Traffic Light Zones korrekt zugeordnet
- [ ] Rolling-Window Backtest funktioniert

### Tests
- [ ] Unit Tests für alle statistischen Tests
- [ ] Validierung gegen bekannte Ergebnisse
- [ ] Edge Cases: Keine Verletzungen, nur Verletzungen

### Reporting
- [ ] Backtest-Report mit allen Metriken
- [ ] Violations-Timeline (Datum, VaR, Actual Loss)

## 3.6 Beispiel-Nutzung

```python
from src.risk.var_backtester import VaRBacktester
from src.risk.var_calculator import PortfolioVaRCalculator, VaRMethod

# Setup
var_calc = PortfolioVaRCalculator(
    confidence_level=0.99,  # 99% für Basel-konform
    method=VaRMethod.HISTORICAL,
)
backtester = VaRBacktester(var_calc)

# Backtest durchführen (mind. 500 Tage Daten empfohlen)
result = backtester.run_backtest(
    returns=returns,
    weights=weights,
    portfolio_value=10_000,
    estimation_window=252,
)

print(f"=== VaR Backtest Results ===")
print(f"Observations: {result.total_observations}")
print(f"Violations: {result.total_violations}")
print(f"Violation Rate: {result.violation_rate:.2%} (expected: {result.expected_rate:.2%})")
print(f"\nKupiec POF Test:")
print(f"  Test Statistic: {result.kupiec_result.test_statistic:.3f}")
print(f"  p-Value: {result.kupiec_result.p_value:.4f}")
print(f"  Reject H0: {result.kupiec_result.reject_h0}")
print(f"\nTraffic Light: {result.traffic_light_zone.value.upper()}")
print(f"Basel Multiplier: {result.basel_multiplier:.2f}")

# Output:
# === VaR Backtest Results ===
# Observations: 248
# Violations: 3
# Violation Rate: 1.21% (expected: 1.00%)
#
# Kupiec POF Test:
#   Test Statistic: 0.187
#   p-Value: 0.6654
#   Reject H0: False
#
# Traffic Light: GREEN
# Basel Multiplier: 3.00
```

---

# Phase 4: Monte Carlo Simulation

**Dauer:** 4-5 Tage  
**Priorität:** 🟠 HIGH  
**Abhängigkeiten:** Phase 1 (VaR/CVaR)

## 4.1 Ziele

- **Monte Carlo VaR:** VaR-Berechnung via Simulation
- **Portfolio Path Simulation:** Simuliere Equity-Kurven
- **Tail Risk Analysis:** Extreme Szenarien analysieren
- **Korrelations-Stress:** Impact von Korrelationsänderungen

## 4.2 Methodik

### Monte Carlo VaR
1. Schätze Parameter der Return-Verteilung (μ, Σ)
2. Generiere N simulierte Return-Pfade
3. Berechne Portfolio-Returns für jeden Pfad
4. VaR = Quantil der simulierten Verluste

### Optionen für Return-Generierung
| Methode | Beschreibung | Crypto-Eignung |
|---------|--------------|----------------|
| Multivariate Normal | Standard, schnell | ⚠️ Unterschätzt Tails |
| Student-t | Fat Tails | ✅ Besser für Crypto |
| Bootstrap | Nicht-parametrisch | ✅ Erhält echte Verteilung |
| GARCH | Zeitvariante Volatilität | ✅ Volatility Clustering |

## 4.3 Deliverables

### Dateien
```
src/risk/
├── monte_carlo.py             # Monte Carlo Engine
├── path_simulator.py          # Portfolio Path Simulation
├── correlation_stress.py      # Korrelations-Stress-Tests
└── distribution_models.py     # Verteilungsmodelle

tests/risk/
├── test_monte_carlo.py        # Unit Tests
├── test_path_simulator.py     # Simulation Tests
└── test_correlation_stress.py # Stress Test Tests
```

### Klassen-Signaturen

```python
# src/risk/monte_carlo.py

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple
import numpy as np
import pandas as pd

class DistributionModel(Enum):
    """Verteilungsmodelle für Simulation."""
    NORMAL = "normal"
    STUDENT_T = "student_t"
    BOOTSTRAP = "bootstrap"

@dataclass
class MonteCarloConfig:
    """Konfiguration für Monte Carlo Simulation."""
    n_simulations: int = 10_000
    distribution: DistributionModel = DistributionModel.STUDENT_T
    random_seed: Optional[int] = 42  # Reproduzierbarkeit!
    student_t_df: float = 5.0        # Degrees of freedom für t-Verteilung
    horizon_days: int = 1            # Simulations-Horizont

@dataclass
class MonteCarloVaRResult:
    """Ergebnis der Monte Carlo VaR-Berechnung."""
    var_value: float                  # VaR in EUR
    var_pct: float                    # VaR als Prozent
    cvar_value: float                 # CVaR in EUR
    cvar_pct: float                   # CVaR als Prozent
    confidence_level: float
    n_simulations: int
    simulated_returns: np.ndarray     # Alle simulierten Returns
    percentiles: dict                 # {1%, 5%, 10%, 50%, 90%, 95%, 99%}

@dataclass
class EquityPathResult:
    """Ergebnis der Equity Path Simulation."""
    paths: np.ndarray                 # Shape: (n_simulations, horizon_days+1)
    final_values: np.ndarray          # Endwerte aller Pfade
    mean_path: np.ndarray             # Durchschnittlicher Pfad
    percentile_paths: dict            # {5%: [...], 50%: [...], 95%: [...]}
    max_drawdowns: np.ndarray         # Max DD pro Pfad

    def plot(self, n_sample: int = 100) -> None:
        """Plottet Sample-Pfade mit Konfidenz-Band."""
        pass


class MonteCarloVaRCalculator:
    """
    Berechnet VaR mittels Monte Carlo Simulation.

    Vorteile gegenüber analytischen Methoden:
    - Keine Verteilungsannahmen (bei Bootstrap)
    - Erfasst non-lineare Risiken
    - Flexible Horizonte
    """

    def __init__(
        self,
        config: MonteCarloConfig,
    ):
        """
        Args:
            config: Monte Carlo Konfiguration
        """
        pass

    def calculate(
        self,
        returns: pd.DataFrame,
        weights: np.ndarray,
        portfolio_value: float,
        confidence_level: float = 0.95,
    ) -> MonteCarloVaRResult:
        """
        Berechnet Monte Carlo VaR.

        Args:
            returns: Historische Asset-Returns
            weights: Portfolio-Gewichte
            portfolio_value: Aktueller Portfolio-Wert
            confidence_level: VaR-Konfidenzniveau

        Returns:
            MonteCarloVaRResult mit VaR und CVaR
        """
        pass

    def simulate_returns(
        self,
        returns: pd.DataFrame,
        n_simulations: int,
    ) -> np.ndarray:
        """
        Simuliert multivariate Returns.

        Returns:
            Array mit Shape (n_simulations, n_assets)
        """
        pass

    def simulate_equity_paths(
        self,
        returns: pd.DataFrame,
        weights: np.ndarray,
        initial_value: float,
        horizon_days: int,
        n_simulations: int,
    ) -> EquityPathResult:
        """
        Simuliert Equity-Kurven über mehrere Tage.

        Returns:
            EquityPathResult mit allen Pfaden und Statistiken
        """
        pass


class CorrelationStressTester:
    """
    Testet Portfolio-Risiko unter veränderten Korrelationen.

    Crypto-Märkte zeigen oft:
    - Korrelations-Breakdown in Krisen (alles fällt)
    - Regime-Wechsel (Bull vs Bear Market)
    """

    def __init__(
        self,
        mc_calculator: MonteCarloVaRCalculator,
    ):
        pass

    def stress_correlation(
        self,
        returns: pd.DataFrame,
        weights: np.ndarray,
        portfolio_value: float,
        correlation_multiplier: float,  # z.B. 1.5 = 50% höhere Korrelationen
    ) -> MonteCarloVaRResult:
        """
        Berechnet VaR unter Stress-Korrelationen.

        Args:
            correlation_multiplier: Faktor für Korrelations-Erhöhung
                - 1.0 = keine Änderung
                - 1.5 = 50% höhere Korrelationen
                - 2.0 = Korrelationen verdoppelt (capped bei 1.0)
        """
        pass

    def run_correlation_scenarios(
        self,
        returns: pd.DataFrame,
        weights: np.ndarray,
        portfolio_value: float,
        multipliers: list = [1.0, 1.25, 1.5, 1.75, 2.0],
    ) -> pd.DataFrame:
        """
        Führt mehrere Korrelations-Szenarien durch.

        Returns:
            DataFrame mit VaR pro Szenario
        """
        pass
```

## 4.4 Config-Erweiterung

```toml
# config/risk.toml (erweitern)

[risk.monte_carlo]
enabled = true
n_simulations = 10000            # Anzahl Simulationen
distribution = "student_t"       # normal | student_t | bootstrap
random_seed = 42                 # Für Reproduzierbarkeit
student_t_df = 5.0               # Degrees of Freedom für t-Verteilung

[risk.monte_carlo.equity_paths]
horizon_days = 30                # Simulations-Horizont
report_percentiles = [5, 25, 50, 75, 95]

[risk.correlation_stress]
enabled = true
multipliers = [1.0, 1.25, 1.5, 2.0]
crisis_correlation = 0.8         # Korrelation in Krisenszenario
```

## 4.5 Akzeptanzkriterien

### Funktional
- [ ] MC VaR konvergiert zu analytischem VaR (bei Normalverteilung)
- [ ] Bootstrap erhält historische Verteilung
- [ ] Student-t produziert dickere Tails als Normal
- [ ] Equity Paths reproduzierbar (bei fixem Seed)

### Performance
- [ ] 10.000 Simulationen in <5 Sekunden
- [ ] 100.000 Simulationen in <30 Sekunden

### Tests
- [ ] Konvergenz-Test: MC VaR → Analytischer VaR bei n→∞
- [ ] Seed-Test: Gleicher Seed → Gleiche Ergebnisse
- [ ] Korrelations-Stress produziert höhere VaR

## 4.6 Beispiel-Nutzung

```python
from src.risk.monte_carlo import (
    MonteCarloVaRCalculator,
    MonteCarloConfig,
    DistributionModel,
    CorrelationStressTester,
)

# Setup mit Student-t für Fat Tails
config = MonteCarloConfig(
    n_simulations=10_000,
    distribution=DistributionModel.STUDENT_T,
    random_seed=42,
    student_t_df=5.0,
)
mc_calc = MonteCarloVaRCalculator(config)

# Monte Carlo VaR
result = mc_calc.calculate(
    returns=returns,
    weights=weights,
    portfolio_value=10_000,
    confidence_level=0.95,
)

print(f"=== Monte Carlo VaR (n={result.n_simulations:,}) ===")
print(f"95% VaR: {result.var_value:.2f} EUR ({result.var_pct:.2%})")
print(f"95% CVaR: {result.cvar_value:.2f} EUR ({result.cvar_pct:.2%})")
print(f"\nPercentiles:")
for p, val in result.percentiles.items():
    print(f"  {p}: {val:.2%}")

# Equity Path Simulation
paths = mc_calc.simulate_equity_paths(
    returns=returns,
    weights=weights,
    initial_value=10_000,
    horizon_days=30,
    n_simulations=1_000,
)
print(f"\n=== 30-Day Equity Simulation ===")
print(f"Median Final Value: {np.median(paths.final_values):.2f} EUR")
print(f"5th Percentile: {np.percentile(paths.final_values, 5):.2f} EUR")
print(f"95th Percentile: {np.percentile(paths.final_values, 95):.2f} EUR")
print(f"Median Max Drawdown: {np.median(paths.max_drawdowns):.2%}")

# Korrelations-Stress
stress_tester = CorrelationStressTester(mc_calc)
scenarios = stress_tester.run_correlation_scenarios(
    returns=returns,
    weights=weights,
    portfolio_value=10_000,
)
print(f"\n=== Correlation Stress Scenarios ===")
print(scenarios.to_string())
```

---

# Phase 5: Stress Testing

**Dauer:** 3-4 Tage  
**Priorität:** 🟠 HIGH  
**Abhängigkeiten:** Phase 1, Phase 4

## 5.1 Ziele

- **Historische Stress-Szenarien:** Crypto-spezifische Krisen simulieren
- **Hypothetische Szenarien:** What-If Analysen
- **Reverse Stress Testing:** Welches Szenario führt zu X% Verlust?
- **Stress-Report:** Übersichtliche Darstellung der Risiken

## 5.2 Historische Crypto-Szenarien

| Szenario | Zeitraum | BTC Drawdown | Charakteristik |
|----------|----------|--------------|----------------|
| **COVID Crash** | März 2020 | -50% in 2 Tagen | Liquiditätskrise, hohe Korrelation |
| **China Ban 2021** | Mai 2021 | -55% in 2 Wochen | Regulatorischer Schock |
| **Luna/UST Collapse** | Mai 2022 | -40% in 1 Woche | Stablecoin-Krise, Contagion |
| **FTX Collapse** | Nov 2022 | -25% in 1 Woche | Exchange-Risiko, Trust-Krise |
| **2018 Bear Market** | Jan-Dec 2018 | -84% über Jahr | Prolonged Bear, keine Recovery |

## 5.3 Deliverables

### Dateien
```
src/risk/
├── stress_testing.py          # Stress Test Engine
├── historical_scenarios.py    # Crypto-Szenarien
├── reverse_stress.py          # Reverse Stress Testing
└── stress_report.py           # Report-Generierung

data/scenarios/
├── covid_crash_2020.json      # Szenario-Daten
├── china_ban_2021.json
├── luna_collapse_2022.json
├── ftx_collapse_2022.json
└── bear_market_2018.json

tests/risk/
├── test_stress_testing.py     # Unit Tests
└── test_reverse_stress.py     # Reverse Stress Tests
```

### Klassen-Signaturen

```python
# src/risk/stress_testing.py

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional
import numpy as np
import pandas as pd

class ScenarioType(Enum):
    """Typen von Stress-Szenarien."""
    HISTORICAL = "historical"
    HYPOTHETICAL = "hypothetical"
    CUSTOM = "custom"

@dataclass
class StressScenario:
    """Definition eines Stress-Szenarios."""
    name: str
    scenario_type: ScenarioType
    description: str

    # Asset-spezifische Shocks (prozentual)
    asset_shocks: Dict[str, float]  # z.B. {"BTC": -0.50, "ETH": -0.60}

    # Korrelations-Override (optional)
    correlation_override: Optional[float] = None

    # Zeitraum (für historische)
    start_date: Optional[str] = None
    end_date: Optional[str] = None

    # Metadata
    severity: str = "extreme"  # mild | moderate | severe | extreme
    probability_estimate: Optional[float] = None

@dataclass
class StressTestResult:
    """Ergebnis eines Stress-Tests."""
    scenario: StressScenario

    # Portfolio-Impact
    portfolio_loss_pct: float        # Prozentualer Verlust
    portfolio_loss_abs: float        # Absoluter Verlust in EUR
    stressed_portfolio_value: float  # Wert nach Stress

    # Asset-Level
    asset_losses: Dict[str, float]   # Verlust pro Asset
    largest_contributor: str         # Asset mit größtem Verlust-Beitrag

    # Risiko-Metriken nach Stress
    post_stress_var: Optional[float] = None
    max_drawdown_estimate: Optional[float] = None

    # Recovery-Analyse
    days_to_recover: Optional[int] = None  # Bei historischen Szenarien

@dataclass
class ReverseStressResult:
    """Ergebnis eines Reverse Stress Tests."""
    target_loss_pct: float           # Ziel-Verlust (z.B. -30%)
    required_btc_shock: float        # Benötigter BTC-Schock
    required_uniform_shock: float    # Benötigter uniformer Schock
    scenario_probability: str        # "rare" | "plausible" | "likely"
    comparison_to_historical: str    # "worse than COVID" etc.


class StressTester:
    """
    Führt Stress Tests für das Portfolio durch.

    Unterstützt:
    - Historische Crypto-Szenarien
    - Hypothetische Szenarien
    - Custom Szenarien
    - Reverse Stress Testing
    """

    def __init__(
        self,
        scenarios_dir: str = "data/scenarios/",
    ):
        """
        Args:
            scenarios_dir: Verzeichnis mit Szenario-Definitionen
        """
        pass

    def load_historical_scenarios(self) -> List[StressScenario]:
        """Lädt alle vordefinierten historischen Szenarien."""
        pass

    def run_stress_test(
        self,
        scenario: StressScenario,
        weights: np.ndarray,
        portfolio_value: float,
        asset_names: List[str],
    ) -> StressTestResult:
        """
        Führt einen Stress-Test durch.

        Args:
            scenario: Stress-Szenario
            weights: Portfolio-Gewichte
            portfolio_value: Aktueller Portfolio-Wert
            asset_names: Asset-Namen (müssen zu weights passen)

        Returns:
            StressTestResult mit Impact-Analyse
        """
        pass

    def run_all_scenarios(
        self,
        weights: np.ndarray,
        portfolio_value: float,
        asset_names: List[str],
        scenario_types: List[ScenarioType] = None,
    ) -> List[StressTestResult]:
        """
        Führt alle konfigurierten Szenarien durch.

        Returns:
            Liste aller StressTestResults, sortiert nach Severity
        """
        pass

    def reverse_stress_test(
        self,
        weights: np.ndarray,
        portfolio_value: float,
        asset_names: List[str],
        target_loss_pct: float,  # z.B. -0.30 für 30% Verlust
    ) -> ReverseStressResult:
        """
        Findet Szenario, das zu gegebenem Verlust führt.

        Args:
            target_loss_pct: Ziel-Verlust (negativ, z.B. -0.30)

        Returns:
            ReverseStressResult mit benötigten Shocks
        """
        pass

    def create_custom_scenario(
        self,
        name: str,
        asset_shocks: Dict[str, float],
        description: str = "",
        correlation_override: Optional[float] = None,
    ) -> StressScenario:
        """
        Erstellt ein benutzerdefiniertes Szenario.

        Args:
            name: Szenario-Name
            asset_shocks: Shocks pro Asset (z.B. {"BTC": -0.40})
            description: Beschreibung
            correlation_override: Korrelation für alle Assets (optional)

        Returns:
            Neues StressScenario
        """
        pass


class StressReportGenerator:
    """Generiert Stress-Test Reports."""

    def generate_report(
        self,
        results: List[StressTestResult],
        portfolio_value: float,
        output_format: str = "html",  # html | json | markdown
    ) -> str:
        """
        Generiert Stress-Test Report.

        Returns:
            Report als String (HTML, JSON oder Markdown)
        """
        pass
```

## 5.4 Szenario-Definitionen

```json
// data/scenarios/covid_crash_2020.json
{
  "name": "COVID Crash März 2020",
  "scenario_type": "historical",
  "description": "Globaler Liquiditätsschock, alle Risk-Assets fallen synchron",
  "asset_shocks": {
    "BTC": -0.50,
    "ETH": -0.60,
    "LTC": -0.55,
    "XRP": -0.50,
    "default": -0.50
  },
  "correlation_override": 0.95,
  "start_date": "2020-03-10",
  "end_date": "2020-03-13",
  "severity": "extreme",
  "probability_estimate": 0.01,
  "recovery_days": 55
}
```

## 5.5 Config-Erweiterung

```toml
# config/risk.toml (erweitern)

[risk.stress_testing]
enabled = true
scenarios_dir = "data/scenarios/"
run_on_startup = false           # Stress Tests bei jedem Start?

[risk.stress_testing.thresholds]
# Warn-Schwellen für Stress-Test-Ergebnisse
warn_loss_pct = 0.20             # Warnung bei >20% Verlust
critical_loss_pct = 0.40         # Kritisch bei >40% Verlust
max_acceptable_loss_pct = 0.50   # Max akzeptabler Verlust

[risk.stress_testing.reverse]
enabled = true
target_loss_levels = [0.20, 0.30, 0.50]  # Analyse für 20%, 30%, 50% Verlust

[risk.stress_testing.report]
generate_html = true
include_charts = true
output_dir = "reports/stress/"
```

## 5.6 Akzeptanzkriterien

### Funktional
- [ ] Alle 5 historischen Szenarien laden korrekt
- [ ] Stress-Test berechnet Portfolio-Verlust korrekt
- [ ] Custom Szenarien funktionieren
- [ ] Reverse Stress Test findet korrekten Shock

### Scenarios
- [ ] COVID Crash: -50% BTC → korrekter Portfolio-Impact
- [ ] Luna Collapse: Contagion-Effekt modelliert
- [ ] Default-Shock für unbekannte Assets

### Reporting
- [ ] HTML-Report generiert
- [ ] Severity-Ranking korrekt
- [ ] Vergleich mit Risiko-Limits

## 5.7 Beispiel-Nutzung

```python
from src.risk.stress_testing import StressTester, StressReportGenerator

# Setup
tester = StressTester(scenarios_dir="data/scenarios/")

# Alle historischen Szenarien laden
scenarios = tester.load_historical_scenarios()
print(f"Loaded {len(scenarios)} scenarios")

# Alle Szenarien durchführen
results = tester.run_all_scenarios(
    weights=np.array([0.5, 0.3, 0.2]),
    portfolio_value=10_000,
    asset_names=['BTC', 'ETH', 'LTC'],
)

print("=== Stress Test Results ===")
for r in results:
    print(f"\n{r.scenario.name}:")
    print(f"  Portfolio Loss: {r.portfolio_loss_pct:.1%} ({r.portfolio_loss_abs:.2f} EUR)")
    print(f"  Largest Contributor: {r.largest_contributor}")
    print(f"  Post-Stress Value: {r.stressed_portfolio_value:.2f} EUR")

# Reverse Stress Test
reverse = tester.reverse_stress_test(
    weights=np.array([0.5, 0.3, 0.2]),
    portfolio_value=10_000,
    asset_names=['BTC', 'ETH', 'LTC'],
    target_loss_pct=-0.30,  # Was braucht es für 30% Verlust?
)

print(f"\n=== Reverse Stress Test (Target: -30%) ===")
print(f"Required BTC Shock: {reverse.required_btc_shock:.1%}")
print(f"Required Uniform Shock: {reverse.required_uniform_shock:.1%}")
print(f"Scenario Probability: {reverse.scenario_probability}")
print(f"Comparison: {reverse.comparison_to_historical}")

# Report generieren
reporter = StressReportGenerator()
html_report = reporter.generate_report(
    results=results,
    portfolio_value=10_000,
    output_format="html",
)
with open("reports/stress/stress_report.html", "w") as f:
    f.write(html_report)
print("\nReport saved to reports/stress/stress_report.html")
```

---

# Phase 6: Integration & Dokumentation

**Dauer:** 2-3 Tage  
**Priorität:** 🟢 MEDIUM  
**Abhängigkeiten:** Phase 1-5

## 6.1 Ziele

- Integration aller Risk-Komponenten in `RiskManager`
- Defense-in-Depth Architektur vollständig
- Dokumentation für Entwickler und Operator
- Final Testing und Sign-Off

## 6.2 Deliverables

### Integration
```python
# src/risk/risk_manager.py (erweitern)

class RiskManager:
    """
    Zentraler Risk Manager mit allen Komponenten.

    Defense-in-Depth Layers:
    1. Pre-Trade Validation (Position Limits)
    2. VaR/CVaR Checks (Portfolio Risk)
    3. Stress Testing (Extreme Scenarios)
    4. Kill Switch (Emergency Stop)
    """

    def __init__(self, config: dict):
        # Bestehende Komponenten
        self.position_validator = PositionValidator(config)
        self.kill_switch = KillSwitch(config)

        # NEUE Komponenten
        self.var_calculator = PortfolioVaRCalculator(config)
        self.cvar_calculator = PortfolioCVaRCalculator(self.var_calculator)
        self.component_var = ComponentVaRCalculator(self.var_calculator)
        self.monte_carlo = MonteCarloVaRCalculator(config)
        self.stress_tester = StressTester(config)
        self.var_backtester = VaRBacktester(self.var_calculator)

    def full_risk_assessment(
        self,
        portfolio: Portfolio,
        returns: pd.DataFrame,
    ) -> RiskAssessmentResult:
        """
        Führt vollständige Risiko-Bewertung durch.

        Kombiniert:
        - VaR/CVaR Berechnung
        - Component VaR Attribution
        - Stress Test Results
        - Risk Limit Checks
        """
        pass

    def validate_new_trade(
        self,
        trade: Trade,
        portfolio: Portfolio,
        returns: pd.DataFrame,
    ) -> TradeValidationResult:
        """
        Validiert neuen Trade gegen alle Risk Layers.

        Returns:
            TradeValidationResult mit APPROVED/REJECTED und Begründung
        """
        pass
```

### Dokumentation
```
docs/risk/
├── RISK_LAYER_OVERVIEW.md         # Architektur-Übersicht
├── VAR_CALCULATION.md             # VaR/CVaR Methoden
├── COMPONENT_VAR.md               # Risk Attribution
├── VAR_BACKTESTING.md             # Kupiec POF, Christoffersen
├── MONTE_CARLO.md                 # MC Simulation
├── STRESS_TESTING.md              # Szenarien, Reverse Stress
├── OPERATOR_GUIDE.md              # Wie nutze ich den Risk Layer?
└── TROUBLESHOOTING.md             # Häufige Probleme
```

### Final Tests
```
tests/integration/
├── test_risk_layer_e2e.py         # End-to-End Tests
├── test_defense_in_depth.py       # Layer-Tests
└── test_risk_reporting.py         # Report-Tests
```

## 6.3 Akzeptanzkriterien

### Integration
- [ ] Alle Komponenten im RiskManager verfügbar
- [ ] Config-Loading für alle Parameter
- [ ] Graceful Degradation bei fehlenden Deps

### Tests
- [ ] Integration Tests für Risk Pipeline
- [ ] E2E Test: Backtest → Risk Assessment → Report
- [ ] Performance: Full Assessment in <10 Sekunden

### Dokumentation
- [ ] Alle Docs geschrieben
- [ ] Code-Beispiele in Docs funktionieren
- [ ] Operator Guide vollständig

## 6.4 Sign-Off Checklist

```markdown
## Risk Layer v1.0 Sign-Off

### Komponenten
- [ ] Portfolio VaR/CVaR: Unit Tests ✅, Integration ✅
- [ ] Component VaR: Unit Tests ✅, Integration ✅
- [ ] Kupiec POF Backtesting: Unit Tests ✅, Integration ✅
- [ ] Monte Carlo Simulation: Unit Tests ✅, Integration ✅
- [ ] Stress Testing: Unit Tests ✅, Integration ✅

### Qualität
- [ ] Test Coverage: ≥85%
- [ ] Code Review: Completed
- [ ] Documentation: Complete
- [ ] Performance: Benchmarks passed

### Abhängigkeiten
- [ ] Keine Breaking Changes in Data Layer
- [ ] Keine Breaking Changes in Backtest Engine
- [ ] Config Migration Guide (falls nötig)

### Sign-Off
- [ ] **Peak_Risk** (Risk Officer): ___________
- [ ] **Peak_Backtest** (QA): ___________
- [ ] **Franky** (Project Owner): ___________
```

---

# 📅 Timeline & Milestones

## Übersicht

```
Woche 1: Phase 1 + Phase 2
├── Tag 1-2: Portfolio VaR (Historical + Parametric)
├── Tag 3-4: CVaR + EWMA + Cornish-Fisher
├── Tag 5: Component VaR Start
└── Tag 6-7: Component VaR Complete + Tests

Woche 2: Phase 3 + Phase 4
├── Tag 8-9: Kupiec POF + Christoffersen
├── Tag 10: Traffic Light + Backtest Report
├── Tag 11-12: Monte Carlo VaR
└── Tag 13-14: Equity Paths + Correlation Stress

Woche 3: Phase 5 + Phase 6
├── Tag 15-16: Stress Testing + Historical Scenarios
├── Tag 17-18: Reverse Stress + Custom Scenarios
├── Tag 19-20: Integration + Final Tests
└── Tag 21: Documentation + Sign-Off
```

## Milestones

| Milestone | Ziel-Datum | Deliverable |
|-----------|------------|-------------|
| **M1: VaR MVP** | Ende Woche 1 | VaR/CVaR + Component VaR funktional |
| **M2: Validation** | Mitte Woche 2 | Kupiec Backtesting + Traffic Light |
| **M3: Simulation** | Ende Woche 2 | Monte Carlo + Correlation Stress |
| **M4: Stress Testing** | Mitte Woche 3 | Alle historischen Szenarien |
| **M5: Release Ready** | Ende Woche 3 | Integration + Docs + Sign-Off |

---

# 🔧 Dependencies & Tools

## Python Packages

```toml
# pyproject.toml - Risk Layer Dependencies

[project.optional-dependencies]
risk = [
    "scipy>=1.11.0",           # Statistische Funktionen (Chi², t-Verteilung)
    "statsmodels>=0.14.0",     # EWMA, GARCH (optional)
]

# Minimal (ohne optional deps)
risk-minimal = []
```

## Fallback-Strategie

```python
# src/risk/_compat.py

try:
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

def chi2_cdf(x: float, df: int) -> float:
    """Chi²-Verteilung CDF mit Fallback."""
    if SCIPY_AVAILABLE:
        return stats.chi2.cdf(x, df)
    else:
        # Approximation für df=1 (Kupiec Test)
        raise NotImplementedError(
            "Chi² Approximation ohne scipy nicht implementiert. "
            "Bitte scipy installieren: pip install scipy"
        )
```

---

# ⚠️ Risiken & Mitigations

| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|--------|-------------------|--------|------------|
| scipy nicht verfügbar | Low | Medium | Fallback-Implementierung für kritische Funktionen |
| Monte Carlo zu langsam | Medium | Medium | Numba JIT oder Cython für Hot Paths |
| Historische Daten fehlen | Low | High | Synthetische Szenarien als Fallback |
| VaR-Modell ungenau | Medium | High | Multiple Methoden + Backtesting-Validierung |
| Korrelations-Breakdown | High (in Krisen) | High | Stress Testing mit erhöhten Korrelationen |

---

# 📚 Referenzen

## Bücher
- Jorion, P. (2007). *Value at Risk* (3rd ed.)
- McNeil, Frey, Embrechts (2015). *Quantitative Risk Management*

## Papers
- Kupiec (1995). *Techniques for Verifying the Accuracy of Risk Measurement Models*
- Christoffersen (1998). *Evaluating Interval Forecasts*

## Online
- RiskMetrics Technical Document (1996): EWMA Methodology
- Basel III Framework: VaR Backtesting Requirements

---

# ✅ Next Actions

## Sofort (heute)
1. ✅ Roadmap reviewed
2. ✅ Feature Branch erstellt: `feat/risk-layer-v1-complete`
3. ✅ Phase 1 abgeschlossen: `src/risk/var.py` implementiert

## Diese Woche
- ❑ Phase 1 abschließen (VaR/CVaR)
- ❑ Phase 2 abschließen (Component VaR)
- ❑ Unit Tests für beide Phasen

## Nächste Woche
- ❑ Phase 3 + 4 (Kupiec + Monte Carlo)
- ❑ Integration Tests beginnen

---

**Erstellt von:** Peak_Risk (Chief Risk Officer)  
**Review durch:** Franky (Project Owner)  
**Status:** 🟡 BEREIT ZUR UMSETZUNG
