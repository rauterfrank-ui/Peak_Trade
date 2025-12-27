# Peak_Trade – Risk Layer Roadmap

**Projekt:** Peak_Trade  
**Dokument:** Risk Layer Implementierungs-Roadmap  
**Stand:** 2025-12-25  
**Ziel:** 60% → 100% in 3-4 Wochen

---

## 🎯 Übersicht

| Phase | Beschreibung | Dauer | Tests | Status |
|-------|--------------|-------|-------|--------|
| R1 | Portfolio VaR/CVaR | 5d | 15+ | ⬜ |
| R2 | VaR Backtesting & Validation | 4d | 20+ | ⬜ |
| R3 | Stress Testing | 5d | 15+ | ⬜ |
| R4 | 4-Layer Validation Architecture | 6d | 25+ | ⬜ |
| R5 | Monitoring & Alerting | 4d | 10+ | ⬜ |
| R6 | Integration & Final Validation | 5d | 10+ | ⬜ |
| **TOTAL** | | **~29d** | **95+** | |

---

## Phase R1: Portfolio VaR/CVaR (Woche 1)

**Status:** ⬜ TODO  
**Dauer:** 5 Tage  
**Priorität:** 🔴 P0 (Critical Path)

### Deliverables

```
src/risk/var/
├── __init__.py
├── parametric_var.py      # Varianz-Kovarianz VaR
├── historical_var.py      # Historical Simulation
├── monte_carlo_var.py     # MC mit 10.000+ Iterationen
├── cvar_calculator.py     # Expected Shortfall (CVaR)
└── covariance.py          # Ledoit-Wolf Shrinkage
```

### Tasks

| # | Task | Aufwand | Prio | Status |
|---|------|---------|------|--------|
| 1.1 | Parametric VaR (Normal, t-Distribution) | 1d | P0 | ⬜ |
| 1.2 | Historical VaR (Quantile-basiert) | 0.5d | P0 | ⬜ |
| 1.3 | Monte Carlo VaR (Korrelierte Returns) | 1.5d | P0 | ⬜ |
| 1.4 | CVaR/Expected Shortfall | 0.5d | P0 | ⬜ |
| 1.5 | Ledoit-Wolf Covariance Shrinkage | 0.5d | P0 | ⬜ |
| 1.6 | Component VaR + Marginal Contribution | 1d | P1 | ⬜ |
| 1.7 | Unit Tests (15+ pro Modul) | 1d | P0 | ⬜ |

### Config Template

```toml
[risk.var]
# Confidence Levels für VaR-Berechnung
confidence_levels = [0.95, 0.99]

# Lookback-Periode für historische Daten (Trading Days)
lookback_days = 252

# Monte Carlo Iterationen
mc_iterations = 10000

# Standard-Methode: parametric | historical | monte_carlo
method = "historical"

# Covariance Shrinkage aktivieren
use_ledoit_wolf = true
```

### Interfaces

```python
# src/risk/var/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
import numpy as np
import pandas as pd

@dataclass
class VaRResult:
    """Ergebnis einer VaR-Berechnung."""
    value: float                    # VaR in Portfolio-Währung
    confidence_level: float         # z.B. 0.95
    method: str                     # parametric | historical | monte_carlo
    horizon_days: int               # Zeithorizont
    cvar: float | None = None       # Conditional VaR (Expected Shortfall)
    component_var: dict | None = None  # VaR pro Position

class VaRCalculator(ABC):
    """Abstrakte Basisklasse für VaR-Berechnungen."""

    @abstractmethod
    def calculate(
        self,
        returns: pd.DataFrame,
        weights: np.ndarray,
        confidence_level: float = 0.95,
        horizon_days: int = 1,
    ) -> VaRResult:
        """Berechnet VaR für ein Portfolio."""
        pass
```

```python
# src/risk/var/parametric_var.py
class ParametricVaR(VaRCalculator):
    """Varianz-Kovarianz VaR (Delta-Normal)."""

    def __init__(self, distribution: str = "normal"):
        """
        Args:
            distribution: "normal" oder "t" (Student-t)
        """
        self.distribution = distribution

    def calculate(
        self,
        returns: pd.DataFrame,
        weights: np.ndarray,
        confidence_level: float = 0.95,
        horizon_days: int = 1,
    ) -> VaRResult:
        # Portfolio Returns
        portfolio_returns = returns @ weights

        # Statistiken
        mu = portfolio_returns.mean()
        sigma = portfolio_returns.std()

        # Z-Score basierend auf Verteilung
        if self.distribution == "normal":
            from scipy.stats import norm
            z = norm.ppf(1 - confidence_level)
        else:  # t-distribution
            from scipy.stats import t
            # Degrees of freedom schätzen
            df = max(4, len(portfolio_returns) - 1)
            z = t.ppf(1 - confidence_level, df)

        # VaR (negativ, da Verlust)
        var_1d = -(mu + z * sigma)
        var_nd = var_1d * np.sqrt(horizon_days)

        return VaRResult(
            value=var_nd,
            confidence_level=confidence_level,
            method="parametric",
            horizon_days=horizon_days,
        )
```

### Exit-Kriterien

- [ ] 3 VaR-Methoden implementiert (Parametric, Historical, Monte Carlo)
- [ ] CVaR für alle Methoden verfügbar
- [ ] Covariance Matrix robust (Ledoit-Wolf Shrinkage)
- [ ] Component VaR zeigt Risikobeitrag pro Position
- [ ] 15+ Unit Tests passing
- [ ] Dokumentation in Docstrings

---

## Phase R2: VaR Backtesting & Validation (Woche 2)

**Status:** ⬜ TODO  
**Dauer:** 4 Tage  
**Priorität:** 🔴 P0 (Critical Path)

### Deliverables

```
src/risk/validation/
├── __init__.py
├── kupiec_pof.py          # Proportion of Failures Test
├── christoffersen.py      # Independence + Conditional Coverage
├── traffic_light.py       # Basel Traffic Light System
└── var_backtest_runner.py # Backtest Orchestrator
```

### Tasks

| # | Task | Aufwand | Prio | Status |
|---|------|---------|------|--------|
| 2.1 | Kupiec POF Test (Proportion of Failures) | 1d | P0 | ⬜ |
| 2.2 | Christoffersen Independence Test | 0.5d | P1 | ⬜ |
| 2.3 | Basel Traffic Light System | 0.5d | P0 | ⬜ |
| 2.4 | VaR Backtest Runner (Rolling Window) | 1d | P0 | ⬜ |
| 2.5 | Breach Analysis & Reporting | 0.5d | P1 | ⬜ |
| 2.6 | Unit Tests (20+) | 1d | P0 | ⬜ |

### Interfaces

```python
# src/risk/validation/kupiec_pof.py
from dataclasses import dataclass

@dataclass
class KupiecResult:
    """Ergebnis des Kupiec POF Tests."""
    breaches: int               # Anzahl VaR-Verletzungen
    observations: int           # Gesamtzahl Beobachtungen
    expected_breaches: float    # Erwartete Verletzungen
    breach_rate: float          # Tatsächliche Breach-Rate
    lr_statistic: float         # Likelihood Ratio Statistik
    p_value: float              # P-Wert (>0.05 = Modell OK)
    is_valid: bool              # Gesamturteil

def kupiec_pof_test(
    breaches: int,
    observations: int,
    confidence_level: float = 0.95,
    significance: float = 0.05,
) -> KupiecResult:
    """
    Kupiec Proportion of Failures Test.

    Testet, ob die Anzahl der VaR-Verletzungen statistisch
    mit dem erwarteten Niveau übereinstimmt.

    Args:
        breaches: Anzahl der VaR-Verletzungen
        observations: Gesamtzahl der Beobachtungen
        confidence_level: VaR Confidence Level (z.B. 0.95)
        significance: Signifikanzniveau für Test (z.B. 0.05)

    Returns:
        KupiecResult mit Test-Statistiken
    """
    from scipy.stats import chi2
    import numpy as np

    # Erwartete Breach-Rate
    p_expected = 1 - confidence_level
    expected_breaches = observations * p_expected

    # Tatsächliche Breach-Rate
    p_actual = breaches / observations if observations > 0 else 0

    # Likelihood Ratio Statistik
    if breaches == 0:
        lr_stat = -2 * observations * np.log(1 - p_expected)
    elif breaches == observations:
        lr_stat = -2 * observations * np.log(p_expected)
    else:
        lr_stat = -2 * (
            np.log((1 - p_expected) ** (observations - breaches) * p_expected ** breaches) -
            np.log((1 - p_actual) ** (observations - breaches) * p_actual ** breaches)
        )

    # P-Wert (Chi-Quadrat mit 1 Freiheitsgrad)
    p_value = 1 - chi2.cdf(lr_stat, df=1)

    return KupiecResult(
        breaches=breaches,
        observations=observations,
        expected_breaches=expected_breaches,
        breach_rate=p_actual,
        lr_statistic=lr_stat,
        p_value=p_value,
        is_valid=p_value > significance,
    )
```

```python
# src/risk/validation/traffic_light.py
from enum import Enum

class TrafficLight(Enum):
    """Basel Traffic Light für VaR-Modelle."""
    GREEN = "green"    # 0-4 Breaches bei 250 Tagen, 99% VaR
    YELLOW = "yellow"  # 5-9 Breaches
    RED = "red"        # 10+ Breaches

def classify_traffic_light(
    breaches: int,
    observations: int = 250,
    confidence_level: float = 0.99,
) -> TrafficLight:
    """
    Basel Traffic Light Klassifikation.

    Basierend auf 250 Trading Days bei 99% VaR:
    - GREEN:  0-4 Breaches (akzeptabel)
    - YELLOW: 5-9 Breaches (Warnung, erhöhte Kapitalanforderung)
    - RED:    10+ Breaches (inakzeptabel, Modell überarbeiten)

    NOTE: Scaling auf 250 Tage ist heuristisch; Basel Cutoffs sind exakt
    für 250D bei 99% VaR. Bei anderen Perioden/Confidence Levels ist die
    Klassifikation approximativ.
    """
    # Skaliere auf 250 Tage (robust gegen Division durch 0)
    if observations <= 0:
        raise ValueError("observations must be > 0")

    scaled_breaches = breaches * (250.0 / observations)

    if scaled_breaches < 5:
        return TrafficLight.GREEN
    elif scaled_breaches < 10:
        return TrafficLight.YELLOW
    else:
        return TrafficLight.RED
```

### Exit-Kriterien

- [ ] Kupiec Test validiert VaR-Modelle
- [ ] Traffic Light System klassifiziert Modellqualität
- [ ] Automatische Warnungen bei YELLOW/RED
- [ ] Historical Backtests über 1+ Jahr Daten
- [ ] 20+ Unit Tests passing

---

## Phase R3: Stress Testing (Woche 2-3)

**Status:** ⬜ TODO  
**Dauer:** 5 Tage  
**Priorität:** 🔴 P0

### Deliverables

```
src/risk/stress/
├── __init__.py
├── scenario_generator.py   # Historical + Hypothetical Scenarios
├── historical_scenarios.py # 2008, 2020, 2022 Crashes
├── hypothetical.py         # Custom Shock Scenarios
├── stress_test_runner.py   # Batch Execution
└── stress_report.py        # HTML/PDF Report
```

### Tasks

| # | Task | Aufwand | Prio | Status |
|---|------|---------|------|--------|
| 3.1 | Historical Scenario Library | 1d | P0 | ⬜ |
| 3.2 | Hypothetical Scenario Builder | 1d | P0 | ⬜ |
| 3.3 | Portfolio Impact Calculator | 1d | P0 | ⬜ |
| 3.4 | Stress Test Runner | 0.5d | P0 | ⬜ |
| 3.5 | Stress Report Generator | 0.5d | P1 | ⬜ |
| 3.6 | Unit Tests (15+) | 1d | P0 | ⬜ |

### Scenario Library

```python
# src/risk/stress/historical_scenarios.py
from dataclasses import dataclass
from typing import Dict

@dataclass
class StressScenario:
    """Definition eines Stress-Szenarios."""
    name: str
    description: str
    shocks: Dict[str, float]      # Asset -> Shock (z.B. -0.30 = -30%)
    correlation_shock: float       # Korrelationsanstieg (0.0 - 1.0) - TODO: reserved for future covariance overlay
    duration_days: int            # Dauer des Schocks

# Historische Szenarien (Crypto-spezifisch)
HISTORICAL_SCENARIOS = {
    "2020_covid_march": StressScenario(
        name="COVID-19 Crash (März 2020)",
        description="BTC fiel von $9000 auf $4000 in 2 Tagen",
        shocks={"BTC": -0.50, "ETH": -0.60, "XRP": -0.55},
        correlation_shock=0.95,
        duration_days=2,
    ),
    "2021_may_crash": StressScenario(
        name="Mai 2021 Crash",
        description="China-Verbot, BTC -50% in 2 Wochen",
        shocks={"BTC": -0.50, "ETH": -0.55, "SOL": -0.60},
        correlation_shock=0.90,
        duration_days=14,
    ),
    "2022_luna_collapse": StressScenario(
        name="LUNA/UST Collapse (Mai 2022)",
        description="Stablecoin-Krise, Contagion",
        shocks={"BTC": -0.30, "ETH": -0.40, "SOL": -0.50},
        correlation_shock=0.85,
        duration_days=7,
    ),
    "2022_ftx_collapse": StressScenario(
        name="FTX Collapse (Nov 2022)",
        description="Exchange-Insolvenz, Vertrauenskrise",
        shocks={"BTC": -0.25, "ETH": -0.30, "SOL": -0.60},
        correlation_shock=0.80,
        duration_days=5,
    ),
    "2024_btc_halving_dip": StressScenario(
        name="Halving Korrektur (2024)",
        description="Post-Halving Gewinnmitnahmen",
        shocks={"BTC": -0.20, "ETH": -0.25, "SOL": -0.30},
        correlation_shock=0.70,
        duration_days=14,
    ),
}
```

```python
# src/risk/stress/stress_test_runner.py
from dataclasses import dataclass
from typing import List
import pandas as pd

@dataclass
class StressTestResult:
    """Ergebnis eines Stress-Tests."""
    scenario_name: str
    portfolio_impact: float          # Absoluter Verlust
    portfolio_impact_pct: float      # Prozentualer Verlust
    position_impacts: Dict[str, float]  # Impact pro Position
    survives_limit: bool             # Bleibt unter Stress-Limit?

class StressTestRunner:
    """Führt Stress-Tests auf Portfolio aus."""

    def __init__(self, portfolio_value: float, stress_limit: float = 0.30):
        """
        Args:
            portfolio_value: Aktueller Portfolio-Wert
            stress_limit: Max. erlaubter Verlust im Stress (z.B. 0.30 = 30%)
        """
        self.portfolio_value = portfolio_value
        self.stress_limit = stress_limit

    def run_scenario(
        self,
        scenario: StressScenario,
        positions: Dict[str, float],  # Asset -> Wert in EUR
    ) -> StressTestResult:
        """
        Führt einzelnes Szenario aus.

        NOTE: correlation_shock ist aktuell informational/reserved.
        Zukünftig könnte es für covariance overlay genutzt werden.
        """
        position_impacts = {}
        total_impact = 0.0

        for asset, value in positions.items():
            shock = scenario.shocks.get(asset, 0.0)
            impact = value * shock
            position_impacts[asset] = impact
            total_impact += impact

        # TODO: correlation_shock wird noch nicht angewendet
        # Zukünftig: covariance matrix adjustment basierend auf correlation_shock

        impact_pct = total_impact / self.portfolio_value

        return StressTestResult(
            scenario_name=scenario.name,
            portfolio_impact=total_impact,
            portfolio_impact_pct=impact_pct,
            position_impacts=position_impacts,
            survives_limit=abs(impact_pct) <= self.stress_limit,
        )

    def run_all_scenarios(
        self,
        scenarios: Dict[str, StressScenario],
        positions: Dict[str, float],
    ) -> List[StressTestResult]:
        """Führt alle Szenarien aus."""
        return [
            self.run_scenario(scenario, positions)
            for scenario in scenarios.values()
        ]
```

### Config Template

```toml
[risk.stress]
# Maximaler erlaubter Verlust im Stress-Szenario
max_stress_loss = 0.30  # 30%

# Welche Szenarien standardmäßig ausführen
default_scenarios = [
    "2020_covid_march",
    "2022_luna_collapse",
    "2022_ftx_collapse",
]

# Hypothetische Szenarien aktivieren
enable_hypothetical = true

# Report-Format
report_format = "html"  # html | pdf | json
```

### Exit-Kriterien

- [ ] 5+ Historical Scenarios implementiert
- [ ] Custom Scenario Builder funktional
- [ ] Portfolio-Impact in EUR berechnet
- [ ] Stress-Limits in Config definierbar
- [ ] 15+ Unit Tests passing

---

## Phase R4: 4-Layer Validation Architecture (Woche 3)

**Status:** 🟡 Partial  
**Dauer:** 6 Tage  
**Priorität:** 🔴 P0 (Critical Path)

### Defense-in-Depth Architektur

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 4: KILL SWITCH (Emergency)                           │
│  ├─ Daily Loss Limit erreicht      → HALT ALL TRADING      │
│  ├─ Max Drawdown erreicht          → HALT ALL TRADING      │
│  ├─ Stress Test Failed             → HALT ALL TRADING      │
│  └─ Manual Override                → HALT ALL TRADING      │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: PORTFOLIO RISK (Aggregated)                       │
│  ├─ Portfolio VaR Limit            → REJECT if exceeded    │
│  ├─ Concentration Limit            → REJECT if >30%/asset  │
│  ├─ Correlation Risk               → WARN if too high      │
│  └─ Sector Exposure                → REJECT if exceeded    │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: POSITION RISK (Per-Trade)                         │
│  ├─ Max Position Size              → REJECT if exceeded    │
│  ├─ Stop-Loss Required             → REJECT if missing     │
│  ├─ Position VaR Limit             → REJECT if exceeded    │
│  └─ Risk/Reward Ratio              → WARN if < 1:2         │
├─────────────────────────────────────────────────────────────┤
│  Layer 1: PRE-TRADE VALIDATION (Sanity Checks)              │
│  ├─ Order Size >= Min Trade Size   → REJECT if too small   │
│  ├─ Sufficient Balance             → REJECT if insufficient│
│  ├─ Market Open / Tradable         → REJECT if closed      │
│  └─ Valid Price Range              → REJECT if suspicious  │
└─────────────────────────────────────────────────────────────┘
```

### Deliverables

```
src/risk/layers/
├── __init__.py
├── base.py                # Abstrakte Basisklasse
├── pre_trade.py           # Layer 1: Sanity Checks
├── position_risk.py       # Layer 2: Per-Trade Limits
├── portfolio_risk.py      # Layer 3: Aggregated Limits
├── kill_switch.py         # Layer 4: Emergency Controls
├── risk_gate.py           # Orchestrator (alle Layer)
└── audit_log.py           # Audit Logging für alle Decisions
```

### Tasks

| # | Task | Aufwand | Prio | Status |
|---|------|---------|------|--------|
| 4.1 | Layer 1: Pre-Trade Validation | 0.5d | P0 | ⬜ |
| 4.2 | Layer 2: Position Risk (erweitern) | 1d | P0 | ⬜ |
| 4.3 | Layer 3: Portfolio Risk Integration | 1.5d | P0 | ⬜ |
| 4.4 | Layer 4: Kill Switch (erweitern) | 1d | P0 | ⬜ |
| 4.5 | RiskGate Orchestrator | 1d | P0 | ⬜ |
| 4.6 | Audit Logging (alle Decisions) | 0.5d | P0 | ⬜ |
| 4.7 | Unit Tests (25+) | 1.5d | P0 | ⬜ |

### Interfaces

```python
# src/risk/layers/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional

class RiskAction(Enum):
    """Mögliche Aktionen einer Risk-Entscheidung."""
    APPROVE = "approve"
    REJECT = "reject"
    WARN = "warn"
    HALT = "halt"  # Nur für Kill Switch

@dataclass
class RiskDecision:
    """Entscheidung eines Risk-Layers."""
    layer: str                      # z.B. "pre_trade", "position_risk"
    action: RiskAction              # APPROVE | REJECT | WARN | HALT
    reason: str                     # Begründung
    details: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

@dataclass
class Order:
    """Order für Risk-Validierung."""
    symbol: str                     # z.B. "BTC/EUR"
    side: str                       # "buy" | "sell"
    amount: float                   # Menge
    price: Optional[float] = None   # Limit-Preis (None = Market)
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

class RiskLayer(ABC):
    """Abstrakte Basisklasse für Risk-Layer."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name des Layers."""
        pass

    @abstractmethod
    def validate(self, order: Order, context: dict) -> RiskDecision:
        """Validiert eine Order."""
        pass
```

```python
# src/risk/layers/risk_gate.py
from typing import List
from .base import RiskLayer, RiskDecision, RiskAction, Order
from .pre_trade import PreTradeLayer
from .position_risk import PositionRiskLayer
from .portfolio_risk import PortfolioRiskLayer
from .kill_switch import KillSwitchLayer
from .audit_log import AuditLog

@dataclass
class GateResult:
    """Gesamtergebnis des Risk Gates."""
    approved: bool
    decisions: List[RiskDecision]
    blocking_decision: Optional[RiskDecision] = None

class RiskGate:
    """
    Orchestriert alle 4 Risk-Layer.

    Jeder Layer kann unabhängig REJECT. Alle müssen APPROVE
    für eine erfolgreiche Validierung.
    """

    def __init__(self, cfg: PeakConfig):
        """
        Args:
            cfg: PeakConfig instance
        """
        from src.core.config import PeakConfig

        self.cfg = cfg

        # Layer initialisieren
        self.layers: List[RiskLayer] = [
            PreTradeLayer(cfg),
            PositionRiskLayer(cfg),
            PortfolioRiskLayer(cfg),
            KillSwitchLayer(cfg),
        ]

        # Audit Log
        self.audit_log = AuditLog(cfg.get("risk.audit_log.path", "./logs/risk_audit.jsonl"))

    def validate_order(self, order: Order, context: dict) -> GateResult:
        """
        Validiert Order durch alle Layer.

        Args:
            order: Die zu validierende Order
            context: Zusätzlicher Kontext (Portfolio, Marktdaten, etc.)

        Returns:
            GateResult mit allen Entscheidungen
        """
        decisions: List[RiskDecision] = []
        blocking_decision: Optional[RiskDecision] = None

        for layer in self.layers:
            decision = layer.validate(order, context)
            decisions.append(decision)

            # REJECT oder HALT blockiert sofort
            if decision.action in (RiskAction.REJECT, RiskAction.HALT):
                blocking_decision = decision
                break

        # Audit Log (IMMER, auch bei APPROVE)
        self.audit_log.log(order, decisions)

        return GateResult(
            approved=blocking_decision is None,
            decisions=decisions,
            blocking_decision=blocking_decision,
        )
```

```python
# src/risk/layers/kill_switch.py
from dataclasses import dataclass
from datetime import datetime
from .base import RiskLayer, RiskDecision, RiskAction, Order

@dataclass
class KillSwitchState:
    """Zustand des Kill Switch."""
    is_active: bool = False
    triggered_at: Optional[datetime] = None
    reason: Optional[str] = None
    triggered_by: Optional[str] = None  # "daily_loss" | "max_dd" | "manual" | "stress_test"

class KillSwitchLayer(RiskLayer):
    """
    Layer 4: Emergency Kill Switch.

    Stoppt ALLEN Handel bei kritischen Ereignissen.
    """

    def __init__(self, cfg: PeakConfig):
        """
        Args:
            cfg: PeakConfig instance
        """
        from src.core.config import PeakConfig

        self.cfg = cfg
        self.state = KillSwitchState()

        # Limits aus Config
        self.daily_loss_limit = cfg.get("risk.kill_switch.daily_loss_limit", 0.05)  # 5%
        self.max_drawdown_limit = cfg.get("risk.kill_switch.max_drawdown", 0.10)    # 10%

    @property
    def name(self) -> str:
        return "kill_switch"

    def validate(self, order: Order, context: dict) -> RiskDecision:
        """Prüft, ob Kill Switch aktiv ist."""

        # Manual Override aktiv?
        if self.state.is_active:
            return RiskDecision(
                layer=self.name,
                action=RiskAction.HALT,
                reason=f"Kill Switch aktiv: {self.state.reason}",
                details={"triggered_at": self.state.triggered_at.isoformat()},
            )

        # Daily Loss prüfen
        daily_pnl = context.get("daily_pnl", 0.0)
        portfolio_value = context.get("portfolio_value", 1.0)
        daily_loss_pct = abs(min(0, daily_pnl)) / portfolio_value

        if daily_loss_pct >= self.daily_loss_limit:
            self._activate("daily_loss", f"Daily Loss {daily_loss_pct:.1%} >= {self.daily_loss_limit:.1%}")
            return RiskDecision(
                layer=self.name,
                action=RiskAction.HALT,
                reason=f"Daily Loss Limit erreicht: {daily_loss_pct:.1%}",
                details={"daily_loss_pct": daily_loss_pct, "limit": self.daily_loss_limit},
            )

        # Max Drawdown prüfen
        current_drawdown = context.get("current_drawdown", 0.0)

        if current_drawdown >= self.max_drawdown_limit:
            self._activate("max_dd", f"Drawdown {current_drawdown:.1%} >= {self.max_drawdown_limit:.1%}")
            return RiskDecision(
                layer=self.name,
                action=RiskAction.HALT,
                reason=f"Max Drawdown erreicht: {current_drawdown:.1%}",
                details={"drawdown": current_drawdown, "limit": self.max_drawdown_limit},
            )

        return RiskDecision(
            layer=self.name,
            action=RiskAction.APPROVE,
            reason="Kill Switch nicht aktiv",
        )

    def _activate(self, triggered_by: str, reason: str):
        """Aktiviert den Kill Switch."""
        self.state = KillSwitchState(
            is_active=True,
            triggered_at=datetime.utcnow(),
            reason=reason,
            triggered_by=triggered_by,
        )

    def reset(self, manual_confirmation: bool = False):
        """
        Setzt den Kill Switch zurück.

        ACHTUNG: Erfordert explizite Bestätigung!
        """
        if not manual_confirmation:
            raise ValueError("Kill Switch Reset erfordert explizite Bestätigung!")

        self.state = KillSwitchState()
```

### Config Template

```toml
[risk.layers]
# Alle Layer aktivieren
enabled = true

[risk.layers.pre_trade]
min_order_size_eur = 10.0
max_price_deviation = 0.05  # 5% vom Marktpreis

[risk.layers.position]
max_position_size_pct = 0.10    # Max 10% pro Position
require_stop_loss = true
min_risk_reward = 2.0           # Min 1:2 Risk/Reward

[risk.layers.portfolio]
max_portfolio_var_pct = 0.02    # Max 2% VaR
max_concentration_pct = 0.30    # Max 30% pro Asset
max_correlation = 0.80          # Warnung bei hoher Korrelation

[risk.kill_switch]
daily_loss_limit = 0.05         # 5% Daily Loss → HALT
max_drawdown = 0.10             # 10% Drawdown → HALT
enable_manual_override = true

[risk.audit_log]
path = "./logs/risk_audit.jsonl"
retention_days = 365
```

### Exit-Kriterien

- [ ] Alle 4 Layer implementiert & integriert
- [ ] Jeder Layer kann unabhängig rejecten
- [ ] Audit Log für ALLE Entscheidungen
- [ ] Config-driven Limits (keine Hardcodes)
- [ ] Kill Switch mit Reset-Sicherung
- [ ] 25+ Unit Tests passing

---

## Phase R5: Monitoring & Alerting (Woche 3-4)

**Status:** ⬜ TODO  
**Dauer:** 4 Tage  
**Priorität:** 🔴 P0

### Deliverables

```
src/risk/monitoring/
├── __init__.py
├── risk_monitor.py        # Real-time Risk Metrics
├── alert_manager.py       # Threshold-based Alerts
├── risk_dashboard.py      # CLI Dashboard (Rich)
└── risk_reporter.py       # Daily Risk Report
```

### Tasks

| # | Task | Aufwand | Prio | Status |
|---|------|---------|------|--------|
| 5.1 | Risk Monitor (VaR, DD, Exposure) | 1d | P0 | ⬜ |
| 5.2 | Alert Manager (Thresholds) | 1d | P0 | ⬜ |
| 5.3 | CLI Dashboard (Rich) | 0.5d | P1 | ⬜ |
| 5.4 | Daily Risk Report (HTML) | 0.5d | P1 | ⬜ |
| 5.5 | Integration mit Kill Switch | 0.5d | P0 | ⬜ |
| 5.6 | Unit Tests (10+) | 0.5d | P0 | ⬜ |

### Interfaces

```python
# src/risk/monitoring/risk_monitor.py
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List

@dataclass
class RiskMetrics:
    """Aktuelle Risk-Metriken."""
    timestamp: datetime
    portfolio_value: float

    # VaR Metrics
    var_95: float
    var_99: float
    cvar_95: float
    var_utilization: float  # Aktuelles VaR / VaR Limit

    # Drawdown Metrics
    current_drawdown: float
    max_drawdown: float
    drawdown_duration_days: int

    # Exposure Metrics
    gross_exposure: float
    net_exposure: float
    concentration: Dict[str, float]  # Asset -> Anteil

    # PnL Metrics
    daily_pnl: float
    daily_pnl_pct: float
    mtd_pnl: float
    ytd_pnl: float

class RiskMonitor:
    """Real-time Risk Monitoring."""

    def __init__(self, cfg: PeakConfig):
        """
        Args:
            cfg: PeakConfig instance
        """
        from src.core.config import PeakConfig

        self.cfg = cfg
        self.alert_manager = AlertManager(cfg)

    def calculate_metrics(
        self,
        portfolio: "Portfolio",
        returns: pd.DataFrame,
    ) -> RiskMetrics:
        """Berechnet aktuelle Risk-Metriken."""
        # ... Implementation
        pass

    def check_alerts(self, metrics: RiskMetrics) -> List["Alert"]:
        """Prüft Metriken gegen Alert-Thresholds."""
        return self.alert_manager.check(metrics)
```

```python
# src/risk/monitoring/alert_manager.py
from dataclasses import dataclass
from enum import Enum
from typing import List, Callable

class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

@dataclass
class Alert:
    level: AlertLevel
    metric: str
    current_value: float
    threshold: float
    message: str

class AlertManager:
    """Threshold-basiertes Alert-System."""

    def __init__(self, cfg: PeakConfig):
        """
        Args:
            cfg: PeakConfig instance
        """
        from src.core.config import PeakConfig

        self.thresholds = {
            "var_utilization": {
                "warning": cfg.get("risk.alerts.var_warning", 0.80),
                "critical": cfg.get("risk.alerts.var_critical", 0.95),
                "comparator": ">=",  # value >= threshold
            },
            "current_drawdown": {
                "warning": cfg.get("risk.alerts.dd_warning", 0.05),
                "critical": cfg.get("risk.alerts.dd_critical", 0.10),
                "comparator": ">=",  # value >= threshold
            },
            "daily_pnl_pct": {
                "warning": cfg.get("risk.alerts.daily_loss_warning", -0.03),
                "critical": cfg.get("risk.alerts.daily_loss_critical", -0.05),
                "comparator": "<=",  # value <= threshold (negative losses)
            },
        }

    def check(self, metrics: RiskMetrics) -> List[Alert]:
        """Prüft alle Metriken gegen Thresholds."""
        alerts = []

        for metric_name, thresholds in self.thresholds.items():
            value = getattr(metrics, metric_name)
            comparator = thresholds["comparator"]

            # Comparator-basierte Prüfung
            if comparator == ">=":
                critical_triggered = value >= thresholds["critical"]
                warning_triggered = value >= thresholds["warning"]
            else:  # "<="
                critical_triggered = value <= thresholds["critical"]
                warning_triggered = value <= thresholds["warning"]

            if critical_triggered:
                alerts.append(Alert(
                    level=AlertLevel.CRITICAL,
                    metric=metric_name,
                    current_value=value,
                    threshold=thresholds["critical"],
                    message=f"CRITICAL: {metric_name} = {value:.2%} (Limit: {thresholds['critical']:.2%})",
                ))
            elif warning_triggered:
                alerts.append(Alert(
                    level=AlertLevel.WARNING,
                    metric=metric_name,
                    current_value=value,
                    threshold=thresholds["warning"],
                    message=f"WARNING: {metric_name} = {value:.2%} (Limit: {thresholds['warning']:.2%})",
                ))

        return alerts
```

### Config Template

```toml
[risk.alerts]
# VaR Utilization Thresholds
var_warning = 0.80    # 80% of VaR limit → WARNING
var_critical = 0.95   # 95% of VaR limit → CRITICAL

# Drawdown Thresholds
dd_warning = 0.05     # 5% drawdown → WARNING
dd_critical = 0.10    # 10% drawdown → CRITICAL → KILL SWITCH

# Daily Loss Thresholds
daily_loss_warning = -0.03   # -3% daily → WARNING
daily_loss_critical = -0.05  # -5% daily → CRITICAL → KILL SWITCH

# Notification Channels (später)
# email = "alerts@example.com"
# slack_webhook = "https://..."
```

### Exit-Kriterien

- [ ] Real-time Risk Metrics verfügbar
- [ ] Alert Thresholds konfigurierbar
- [ ] CRITICAL Alerts triggern Kill Switch
- [ ] Daily Report automatisierbar
- [ ] CLI Dashboard funktional
- [ ] 10+ Unit Tests passing

---

## Phase R6: Integration & Final Validation (Woche 4)

**Status:** ⬜ TODO  
**Dauer:** 5 Tage  
**Priorität:** 🔴 P0

### Tasks

| # | Task | Aufwand | Prio | Status |
|---|------|---------|------|--------|
| 6.1 | Integration Tests (End-to-End) | 1.5d | P0 | ⬜ |
| 6.2 | Backtest Engine Integration | 1d | P0 | ⬜ |
| 6.3 | Config Template finalisieren | 0.5d | P0 | ⬜ |
| 6.4 | Documentation (RISK_LAYER.md) | 1d | P0 | ⬜ |
| 6.5 | Code Review & Cleanup | 0.5d | P1 | ⬜ |
| 6.6 | Performance Benchmark | 0.5d | P1 | ⬜ |

### Integration Tests

```python
# tests/integration/test_risk_layer_integration.py
import pytest
from src.risk.layers import RiskGate
from src.risk.var import ParametricVaR, HistoricalVaR
from src.risk.stress import StressTestRunner
from src.backtest import BacktestEngine

class TestRiskLayerIntegration:
    """End-to-End Tests für Risk Layer."""

    def test_full_validation_pipeline(self):
        """Test: Order durchläuft alle 4 Layer."""
        # Setup
        config = load_config("config/risk.toml")
        gate = RiskGate(config)

        # Valid Order
        order = Order(symbol="BTC/EUR", side="buy", amount=0.1, stop_loss=40000)
        context = {"portfolio_value": 10000, "daily_pnl": 0, "current_drawdown": 0}

        result = gate.validate_order(order, context)

        assert result.approved
        assert len(result.decisions) == 4  # Alle Layer durchlaufen

    def test_kill_switch_blocks_all(self):
        """Test: Kill Switch blockiert alle Orders."""
        config = load_config("config/risk.toml")
        gate = RiskGate(config)

        # Trigger Kill Switch
        context = {
            "portfolio_value": 10000,
            "daily_pnl": -600,  # 6% Verlust
            "current_drawdown": 0.06,
        }

        order = Order(symbol="BTC/EUR", side="buy", amount=0.1)
        result = gate.validate_order(order, context)

        assert not result.approved
        assert result.blocking_decision.layer == "kill_switch"

    def test_var_integration_with_backtest(self):
        """Test: VaR-Berechnung mit Backtest-Daten."""
        # Load historical data
        data = pd.read_parquet("tests/fixtures/btc_eur_1h.parquet")

        # Run VaR
        var_calc = HistoricalVaR()
        result = var_calc.calculate(
            returns=data["close"].pct_change().dropna(),
            weights=np.array([1.0]),
            confidence_level=0.95,
        )

        assert result.value > 0
        assert result.method == "historical"
```

### Final Config Template

```toml
# config/risk.toml
# Peak_Trade Risk Layer Configuration

[risk]
enabled = true

[risk.audit_log]
path = "./logs/risk_audit.jsonl"

# ============================================================================
# VaR Configuration
# ============================================================================
[risk.var]
confidence_levels = [0.95, 0.99]
lookback_days = 252
mc_iterations = 10000
method = "historical"
use_ledoit_wolf = true

[risk.var.limits]
portfolio_var_95_max = 0.02   # Max 2% VaR (95%)
portfolio_var_99_max = 0.03   # Max 3% VaR (99%)
position_var_max = 0.01       # Max 1% VaR pro Position

# ============================================================================
# Stress Testing
# ============================================================================
[risk.stress]
max_stress_loss = 0.30
default_scenarios = ["2020_covid_march", "2022_luna_collapse", "2022_ftx_collapse"]
enable_hypothetical = true
report_format = "html"

# ============================================================================
# 4-Layer Validation
# ============================================================================
[risk.layers]
enabled = true

[risk.layers.pre_trade]
min_order_size_eur = 10.0
max_price_deviation = 0.05

[risk.layers.position]
max_position_size_pct = 0.10
require_stop_loss = true
min_risk_reward = 2.0

[risk.layers.portfolio]
max_portfolio_var_pct = 0.02
max_concentration_pct = 0.30
max_correlation = 0.80

[risk.kill_switch]
daily_loss_limit = 0.05
max_drawdown = 0.10
enable_manual_override = true

# ============================================================================
# Alerts
# ============================================================================
[risk.alerts]
var_warning = 0.80
var_critical = 0.95
dd_warning = 0.05
dd_critical = 0.10
daily_loss_warning = -0.03
daily_loss_critical = -0.05

# ============================================================================
# Monitoring
# ============================================================================
[risk.monitoring]
update_interval_seconds = 60
dashboard_enabled = true
daily_report_enabled = true
daily_report_time = "18:00"
```

### Exit-Kriterien

- [ ] Alle Integration Tests passing
- [ ] Backtest Engine nutzt Risk Layer
- [ ] Config Template vollständig & dokumentiert
- [ ] RISK_LAYER.md Dokumentation komplett
- [ ] Performance: <100ms pro Order-Validation
- [ ] 95+ Unit Tests insgesamt passing

---

## 📝 Implementation Notes

### Config Access Pattern
- **Alle Risk-Layer nutzen `PeakConfig`**: `from src.core.config import PeakConfig`
- **Config-Zugriff**: `cfg.get("a.b.c", default_value)` statt `config["a"]["b"]["c"]`
- **Vorteil**: Type-safe, dot-notation, defaults, validation

### Audit Log Configuration
- **TOML Path**: `[risk.audit_log]` → `path = "./logs/risk_audit.jsonl"`
- **Code Access**: `cfg.get("risk.audit_log.path", "./logs/risk_audit.jsonl")`
- **Konsistenz**: Alle Layer nutzen denselben Pfad

### Alert Comparator Logic
- **VaR Utilization**: `value >= threshold` (höher = schlechter)
- **Drawdown**: `value >= threshold` (höher = schlechter)
- **Daily PnL**: `value <= threshold` (negativer = schlechter, z.B. -6% < -5%)
- **Wichtig**: Thresholds für Verluste sind negativ (-0.03, -0.05)

### Basel Traffic Light System
- **Exakt für**: 250 Trading Days, 99% VaR
- **Scaling**: Heuristisch bei anderen Perioden/Confidence Levels
- **Cutoffs**: GREEN (0-4), YELLOW (5-9), RED (10+)
- **Robustheit**: Division-by-zero protected

### Stress Testing
- **`correlation_shock`**: Aktuell reserved/informational
- **Zukünftig**: Covariance matrix overlay für erhöhte Korrelationen
- **Aktuell**: Nur direkte Asset-Shocks werden angewendet

---

## 📊 Zusammenfassung

### Gesamtaufwand

| Phase | Dauer | Tests | Prio |
|-------|-------|-------|------|
| R1: Portfolio VaR/CVaR | 5d | 15+ | P0 |
| R2: VaR Backtesting | 4d | 20+ | P0 |
| R3: Stress Testing | 5d | 15+ | P0 |
| R4: 4-Layer Architecture | 6d | 25+ | P0 |
| R5: Monitoring/Alerting | 4d | 10+ | P0 |
| R6: Integration | 5d | 10+ | P0 |
| **TOTAL** | **~29 Tage** | **95+** | |

### Gantt-Übersicht

```
Woche 1  │████████████████│ R1: VaR/CVaR
Woche 2  │████████│        │ R2: VaR Backtesting
         │        │████████│ R3: Stress Testing (Start)
Woche 3  │████████│        │ R3: Stress Testing (Ende)
         │        │████████│ R4: 4-Layer Architecture
Woche 4  │████████│        │ R5: Monitoring
         │        │████████│ R6: Integration
```

### Dependencies

```
R1 (VaR) ──┬──→ R2 (Backtesting)
           │
           └──→ R3 (Stress) ──→ R4 (4-Layer) ──→ R5 (Monitoring) ──→ R6 (Integration)
```

**Critical Path:** R1 → R4 → R6

---

## ✅ Checkliste vor v1.0

### Minimum Viable Risk Layer
- [ ] VaR/CVaR (3 Methoden)
- [ ] Kupiec POF Test
- [ ] 5+ Stress Scenarios
- [ ] 4-Layer Validation komplett
- [ ] Kill Switch mit Daily Loss + Max DD
- [ ] Audit Logging

### Nice-to-Have (v1.1)
- [ ] Christoffersen Independence Test
- [ ] CLI Dashboard
- [ ] Automated Daily Reports
- [ ] Notification Channels (Email/Slack)

### Blocker für Live Trading
- [ ] 12+ Monate Shadow Trading
- [ ] VaR Backtest: GREEN Traffic Light
- [ ] Stress Tests: Alle bestanden
- [ ] Kill Switch: Getestet & funktional
- [ ] Audit Trail: Vollständig

---

## 🚀 Nächster Schritt

**Starte mit Phase R1: Portfolio VaR/CVaR**

```bash
cd ~/Peak_Trade

# Branch erstellen
git checkout -b feature/risk-layer-var

# Verzeichnis anlegen
mkdir -p src/risk/var
touch src/risk/var/__init__.py

# Erste Datei erstellen
code src/risk/var/parametric_var.py
```

---

**Erstellt:** 2025-12-25  
**Autor:** Peak_Trade Development Team  
**Status:** READY FOR IMPLEMENTATION
