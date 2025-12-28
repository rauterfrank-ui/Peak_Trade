# Agent E: Extended Stress Testing Implementation

**Agent:** E (Stress Testing Specialist)  
**Phase:** 4 (Erweiterte Stress Tests)  
**Priorität:** 🟡 MITTEL  
**Aufwand:** 3-4 Tage  
**Status:** 📋 BEREIT ZU STARTEN

---

## 🎯 Ziel

Erweiterung des bestehenden Stress Testing Systems um:
- **Reverse Stress Testing** – "Welche Szenarien würden uns killen?"
- **Forward Stress Scenarios** – Hypothetische Zukunfts-Szenarien
- **Multi-Factor Stress** – Kombinierte Faktor-Shocks

**Kontext:** Basis-Stress-Testing existiert bereits in `src/risk/stress_tester.py`. Diese Task erweitert es um fortgeschrittene Methoden.

---

## 📚 Hintergrund

### Was ist Stress Testing?

**Historical Stress Testing (bereits implementiert):**
- Anwendung historischer Krisen auf aktuelles Portfolio
- Beispiel: "Was wäre bei COVID-Crash 2020 passiert?"

**Reverse Stress Testing (NEU):**
- Findet Szenarien die zu definierten Verlusten führen
- Beispiel: "Welche Marktbewegungen würden -20% Verlust verursachen?"

**Forward Stress Scenarios (NEU):**
- Hypothetische Zukunfts-Szenarien
- Beispiel: "Was wenn BTC um 50% fällt und Volatilität verdoppelt?"

**Multi-Factor Stress (NEU):**
- Kombinierte Shocks über mehrere Faktoren
- Beispiel: "Equity -30%, Vol +100%, Correlation +50%"

---

## 📋 Aufgaben

### Task 1: Reverse Stress Testing (1.5-2 Tage)

**Ziel:** Finde Szenarien die zu definierten Verlusten führen

**Dateien:**
```
src/risk_layer/stress/
├── __init__.py                    # Public API
├── reverse_stress.py              # Hauptimplementierung
└── types.py                       # ReverseStressResult
```

#### 1.1 Types definieren

**Datei:** `src/risk_layer/stress/types.py`

```python
"""Stress Testing Types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import pandas as pd


@dataclass(frozen=True)
class StressScenario:
    """Stress-Test-Szenario."""

    name: str
    description: str
    shocks: Dict[str, float]  # {asset: shock_return}
    metadata: Optional[Dict] = None


@dataclass(frozen=True)
class ReverseStressResult:
    """Ergebnis eines Reverse Stress Tests."""

    target_loss: float
    scenarios: List[StressScenario]
    portfolio_value: float
    current_positions: Dict[str, float]

    def to_dataframe(self) -> pd.DataFrame:
        """Konvertiert Szenarien zu DataFrame."""
        data = []
        for scenario in self.scenarios:
            for asset, shock in scenario.shocks.items():
                data.append({
                    "scenario": scenario.name,
                    "asset": asset,
                    "shock_return": shock,
                    "description": scenario.description,
                })
        return pd.DataFrame(data)


@dataclass(frozen=True)
class ForwardStressResult:
    """Ergebnis eines Forward Stress Tests."""

    scenario: StressScenario
    portfolio_loss: float
    portfolio_loss_pct: float
    asset_contributions: Dict[str, float]
    var_breach: bool

    def to_dict(self) -> Dict:
        """Konvertiert zu Dict für Reporting."""
        return {
            "scenario": self.scenario.name,
            "description": self.scenario.description,
            "portfolio_loss": self.portfolio_loss,
            "portfolio_loss_pct": self.portfolio_loss_pct,
            "var_breach": self.var_breach,
            "asset_contributions": self.asset_contributions,
        }
```

#### 1.2 Reverse Stress Testing implementieren

**Datei:** `src/risk_layer/stress/reverse_stress.py`

```python
"""Reverse Stress Testing Implementation."""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from .types import ReverseStressResult, StressScenario

logger = logging.getLogger(__name__)


class ReverseStressTester:
    """
    Findet Szenarien die zu definierten Verlusten führen.

    Verwendet Optimierung um "minimale" Shocks zu finden die
    target_loss erreichen.

    Usage:
        >>> tester = ReverseStressTester()
        >>> result = tester.find_stress_scenarios(
        ...     positions={"BTC-EUR": 1000, "ETH-EUR": 500},
        ...     target_loss=0.20,  # -20% Verlust
        ...     n_scenarios=5,
        ... )
        >>> print(result.to_dataframe())
    """

    def __init__(
        self,
        max_shock: float = 0.50,  # Max 50% Shock pro Asset
        min_shock: float = -0.50,  # Min -50% Shock
    ):
        """
        Args:
            max_shock: Maximaler positiver Shock
            min_shock: Maximaler negativer Shock
        """
        self.max_shock = max_shock
        self.min_shock = min_shock

    def find_stress_scenarios(
        self,
        positions: Dict[str, float],
        target_loss: float,
        n_scenarios: int = 5,
        method: str = "minimal_shock",
    ) -> ReverseStressResult:
        """
        Findet Szenarien die zu target_loss führen.

        Args:
            positions: Position-Werte {asset: value}
            target_loss: Ziel-Verlust (z.B. 0.20 für -20%)
            n_scenarios: Anzahl zu findender Szenarien
            method: "minimal_shock" oder "diversified_shock"

        Returns:
            ReverseStressResult mit gefundenen Szenarien
        """
        portfolio_value = sum(positions.values())
        target_loss_abs = portfolio_value * target_loss

        scenarios = []

        if method == "minimal_shock":
            # Finde Szenarien mit minimalen Shocks
            for i in range(n_scenarios):
                scenario = self._find_minimal_shock_scenario(
                    positions, target_loss_abs, seed=i
                )
                if scenario:
                    scenarios.append(scenario)

        elif method == "diversified_shock":
            # Finde Szenarien mit diversifizierten Shocks
            for i in range(n_scenarios):
                scenario = self._find_diversified_shock_scenario(
                    positions, target_loss_abs, seed=i
                )
                if scenario:
                    scenarios.append(scenario)

        else:
            raise ValueError(f"Unknown method: {method}")

        return ReverseStressResult(
            target_loss=target_loss,
            scenarios=scenarios,
            portfolio_value=portfolio_value,
            current_positions=positions,
        )

    def _find_minimal_shock_scenario(
        self,
        positions: Dict[str, float],
        target_loss_abs: float,
        seed: int = 0,
    ) -> Optional[StressScenario]:
        """
        Findet Szenario mit minimalen Shocks (L2-Norm).

        Optimierungsproblem:
            minimize: sum(shock_i^2)
            subject to: sum(position_i * shock_i) = target_loss_abs
                       min_shock <= shock_i <= max_shock
        """
        assets = list(positions.keys())
        n_assets = len(assets)

        # Objective: Minimize L2-Norm der Shocks
        def objective(shocks):
            return np.sum(shocks ** 2)

        # Constraint: Portfolio-Verlust = target_loss_abs
        def constraint_loss(shocks):
            portfolio_loss = sum(
                positions[asset] * shocks[i]
                for i, asset in enumerate(assets)
            )
            return portfolio_loss + target_loss_abs  # = 0

        # Bounds
        bounds = [(self.min_shock, self.max_shock) for _ in range(n_assets)]

        # Initial guess (mit seed für Variation)
        np.random.seed(seed)
        x0 = np.random.uniform(self.min_shock, self.max_shock, n_assets)

        # Optimierung
        result = minimize(
            objective,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints={"type": "eq", "fun": constraint_loss},
        )

        if not result.success:
            logger.warning(f"Optimization failed for seed={seed}: {result.message}")
            return None

        # Scenario erstellen
        shocks = {asset: float(result.x[i]) for i, asset in enumerate(assets)}

        # Beschreibung generieren
        main_shock_asset = max(shocks.items(), key=lambda x: abs(x[1]))
        description = f"Hauptsächlich {main_shock_asset[0]} Shock ({main_shock_asset[1]:.1%})"

        return StressScenario(
            name=f"Reverse Stress {seed+1}",
            description=description,
            shocks=shocks,
            metadata={"method": "minimal_shock", "seed": seed},
        )

    def _find_diversified_shock_scenario(
        self,
        positions: Dict[str, float],
        target_loss_abs: float,
        seed: int = 0,
    ) -> Optional[StressScenario]:
        """
        Findet Szenario mit diversifizierten Shocks (L1-Norm).

        Fördert gleichmäßige Verteilung der Shocks über Assets.
        """
        assets = list(positions.keys())
        n_assets = len(assets)

        # Objective: Minimize L1-Norm (fördert Sparsity)
        def objective(shocks):
            return np.sum(np.abs(shocks))

        # Constraint: Portfolio-Verlust = target_loss_abs
        def constraint_loss(shocks):
            portfolio_loss = sum(
                positions[asset] * shocks[i]
                for i, asset in enumerate(assets)
            )
            return portfolio_loss + target_loss_abs

        # Bounds
        bounds = [(self.min_shock, self.max_shock) for _ in range(n_assets)]

        # Initial guess
        np.random.seed(seed + 100)  # Anderer Seed als minimal_shock
        x0 = np.random.uniform(self.min_shock, self.max_shock, n_assets)

        # Optimierung
        result = minimize(
            objective,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints={"type": "eq", "fun": constraint_loss},
        )

        if not result.success:
            return None

        shocks = {asset: float(result.x[i]) for i, asset in enumerate(assets)}

        return StressScenario(
            name=f"Diversified Stress {seed+1}",
            description="Diversifizierte Shocks über alle Assets",
            shocks=shocks,
            metadata={"method": "diversified_shock", "seed": seed},
        )
```

**Acceptance Criteria:**
- [ ] Reverse Stress Testing implementiert
- [ ] Findet Szenarien mit minimalen Shocks (L2-Norm)
- [ ] Findet Szenarien mit diversifizierten Shocks (L1-Norm)
- [ ] Constraints werden respektiert (min/max shock)
- [ ] Funktioniert mit scipy.optimize

---

### Task 2: Forward Stress Scenarios (1-1.5 Tage)

**Ziel:** Hypothetische Zukunfts-Szenarien definieren und testen

**Datei:** `src/risk_layer/stress/forward_scenarios.py`

```python
"""Forward Stress Scenarios Implementation."""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

import pandas as pd

from .types import ForwardStressResult, StressScenario

logger = logging.getLogger(__name__)


class ForwardStressTester:
    """
    Testet hypothetische Zukunfts-Szenarien.

    Usage:
        >>> tester = ForwardStressTester()
        >>> scenario = StressScenario(
        ...     name="BTC Crash",
        ...     description="BTC -50%, ETH -30%",
        ...     shocks={"BTC-EUR": -0.50, "ETH-EUR": -0.30},
        ... )
        >>> result = tester.test_scenario(
        ...     scenario=scenario,
        ...     positions={"BTC-EUR": 1000, "ETH-EUR": 500},
        ...     var_limit=0.10,
        ... )
    """

    def test_scenario(
        self,
        scenario: StressScenario,
        positions: Dict[str, float],
        var_limit: Optional[float] = None,
    ) -> ForwardStressResult:
        """
        Testet ein Forward-Szenario.

        Args:
            scenario: Stress-Szenario
            positions: Position-Werte {asset: value}
            var_limit: Optional VaR-Limit für Breach-Check

        Returns:
            ForwardStressResult
        """
        portfolio_value = sum(positions.values())

        # Asset-Contributions berechnen
        asset_contributions = {}
        total_loss = 0.0

        for asset, position_value in positions.items():
            if asset in scenario.shocks:
                shock = scenario.shocks[asset]
                loss = position_value * shock
                asset_contributions[asset] = loss
                total_loss += loss

        # VaR Breach prüfen
        var_breach = False
        if var_limit is not None:
            var_breach = abs(total_loss / portfolio_value) > var_limit

        return ForwardStressResult(
            scenario=scenario,
            portfolio_loss=total_loss,
            portfolio_loss_pct=total_loss / portfolio_value if portfolio_value > 0 else 0.0,
            asset_contributions=asset_contributions,
            var_breach=var_breach,
        )

    def test_multiple_scenarios(
        self,
        scenarios: List[StressScenario],
        positions: Dict[str, float],
        var_limit: Optional[float] = None,
    ) -> List[ForwardStressResult]:
        """Testet mehrere Szenarien."""
        results = []
        for scenario in scenarios:
            result = self.test_scenario(scenario, positions, var_limit)
            results.append(result)
        return results

    @staticmethod
    def create_predefined_scenarios() -> List[StressScenario]:
        """Erstellt vordefinierte Standard-Szenarien."""
        scenarios = [
            StressScenario(
                name="Crypto Crash",
                description="BTC -50%, ETH -40%, Altcoins -60%",
                shocks={
                    "BTC-EUR": -0.50,
                    "ETH-EUR": -0.40,
                    "BTC-USDT": -0.50,
                    "ETH-USDT": -0.40,
                },
            ),
            StressScenario(
                name="Flash Crash",
                description="Alle Assets -30% (Liquiditäts-Krise)",
                shocks={
                    "BTC-EUR": -0.30,
                    "ETH-EUR": -0.30,
                    "BTC-USDT": -0.30,
                    "ETH-USDT": -0.30,
                },
            ),
            StressScenario(
                name="BTC Dominance",
                description="BTC +20%, Altcoins -20%",
                shocks={
                    "BTC-EUR": 0.20,
                    "ETH-EUR": -0.20,
                    "BTC-USDT": 0.20,
                    "ETH-USDT": -0.20,
                },
            ),
            StressScenario(
                name="Regulatory Shock",
                description="Alle Crypto -25% (Regulierungs-Angst)",
                shocks={
                    "BTC-EUR": -0.25,
                    "ETH-EUR": -0.25,
                    "BTC-USDT": -0.25,
                    "ETH-USDT": -0.25,
                },
            ),
        ]
        return scenarios
```

**Acceptance Criteria:**
- [ ] Forward Stress Testing implementiert
- [ ] Vordefinierte Szenarien erstellt
- [ ] Asset-Contributions berechnet
- [ ] VaR Breach Detection
- [ ] Batch-Testing für mehrere Szenarien

---

### Task 3: Integration & Testing (0.5-1 Tag)

**Tests:** `tests/risk_layer/stress/`

```python
# test_reverse_stress.py

import pytest
from src.risk_layer.stress import ReverseStressTester


def test_reverse_stress_basic():
    """Test basic reverse stress testing."""
    tester = ReverseStressTester()

    positions = {"BTC-EUR": 1000, "ETH-EUR": 500}
    target_loss = 0.20  # -20%

    result = tester.find_stress_scenarios(
        positions=positions,
        target_loss=target_loss,
        n_scenarios=3,
        method="minimal_shock",
    )

    # Sollte 3 Szenarien finden
    assert len(result.scenarios) == 3

    # Jedes Szenario sollte target_loss erreichen
    for scenario in result.scenarios:
        portfolio_loss = sum(
            positions[asset] * scenario.shocks[asset]
            for asset in positions.keys()
        )
        expected_loss = result.portfolio_value * target_loss

        # Toleranz für Optimierungs-Fehler
        assert abs(portfolio_loss + expected_loss) < 1.0


def test_reverse_stress_constraints():
    """Test dass Shocks Constraints respektieren."""
    tester = ReverseStressTester(max_shock=0.30, min_shock=-0.30)

    result = tester.find_stress_scenarios(
        positions={"BTC-EUR": 1000},
        target_loss=0.10,
        n_scenarios=1,
    )

    for scenario in result.scenarios:
        for shock in scenario.shocks.values():
            assert -0.30 <= shock <= 0.30


# test_forward_scenarios.py

from src.risk_layer.stress import ForwardStressTester, StressScenario


def test_forward_stress_basic():
    """Test basic forward stress testing."""
    tester = ForwardStressTester()

    scenario = StressScenario(
        name="Test Crash",
        description="BTC -50%",
        shocks={"BTC-EUR": -0.50},
    )

    result = tester.test_scenario(
        scenario=scenario,
        positions={"BTC-EUR": 1000},
    )

    assert result.portfolio_loss == -500.0
    assert result.portfolio_loss_pct == -0.50


def test_forward_stress_var_breach():
    """Test VaR breach detection."""
    tester = ForwardStressTester()

    scenario = StressScenario(
        name="Large Crash",
        description="BTC -20%",
        shocks={"BTC-EUR": -0.20},
    )

    result = tester.test_scenario(
        scenario=scenario,
        positions={"BTC-EUR": 1000},
        var_limit=0.10,  # 10% VaR Limit
    )

    # -20% Verlust sollte VaR Breach sein
    assert result.var_breach is True


def test_predefined_scenarios():
    """Test vordefinierte Szenarien."""
    scenarios = ForwardStressTester.create_predefined_scenarios()

    assert len(scenarios) >= 4
    assert any(s.name == "Crypto Crash" for s in scenarios)
```

**Acceptance Criteria:**
- [ ] Unit Tests für Reverse Stress (>90% Coverage)
- [ ] Unit Tests für Forward Stress
- [ ] Integration Test mit echten Positionen
- [ ] Edge Cases getestet

---

## 📁 Dateistruktur

```
src/risk_layer/stress/
├── __init__.py                    # Public API Exports
├── types.py                       # StressScenario, Results
├── reverse_stress.py              # ReverseStressTester
├── forward_scenarios.py           # ForwardStressTester
└── README.md                      # Modul-Dokumentation

tests/risk_layer/stress/
├── __init__.py
├── conftest.py                    # Shared Fixtures
├── test_reverse_stress.py         # Reverse Stress Tests
├── test_forward_scenarios.py      # Forward Stress Tests
└── test_integration.py            # Integration Tests

docs/risk/
└── STRESS_TESTING_GUIDE.md        # User Guide

config/scenarios/
├── crypto_crash.toml              # Vordefinierte Szenarien
├── flash_crash.toml
└── regulatory_shock.toml
```

---

## 📊 Acceptance Criteria (Gesamt)

- [ ] Reverse Stress Testing implementiert
- [ ] Forward Stress Scenarios implementiert
- [ ] Vordefinierte Szenarien erstellt
- [ ] Alle Tests passing (>90% Coverage)
- [ ] Dokumentation vollständig
- [ ] Integration mit bestehenden Stress-Modulen
- [ ] Performance: <1s für Reverse Stress (5 Szenarien)

---

## 🚀 Deliverables

### Code
- `src/risk_layer/stress/` Package (neu)

### Tests
- `tests/risk_layer/stress/` (vollständig)

### Dokumentation
- `docs/risk/STRESS_TESTING_GUIDE.md`

### Config
- `config/scenarios/*.toml` (vordefinierte Szenarien)

---

## 📝 PR

**Titel:** `feat(risk): extend stress testing with reverse and forward scenarios`

**Beschreibung:**
```markdown
## 🎯 Ziel

Erweiterung des Stress Testing Systems um Reverse und Forward Stress Tests.

## ✨ Änderungen

### 1. Reverse Stress Testing
- Findet Szenarien die zu definierten Verlusten führen
- Minimal Shock Method (L2-Norm)
- Diversified Shock Method (L1-Norm)

### 2. Forward Stress Scenarios
- Hypothetische Zukunfts-Szenarien
- Vordefinierte Standard-Szenarien
- VaR Breach Detection

### 3. Integration
- Integration mit bestehendem Stress-System
- Config-driven Scenarios

## 🧪 Tests

- ✅ Reverse Stress Tests (>90% Coverage)
- ✅ Forward Stress Tests
- ✅ Integration Tests

## 📚 Dokumentation

- ✅ Stress Testing Guide aktualisiert
```

---

## ⏱️ Timeline

| Task | Aufwand |
|------|---------|
| Reverse Stress Testing | 1.5-2 Tage |
| Forward Stress Scenarios | 1-1.5 Tage |
| Integration & Testing | 0.5-1 Tag |
| **GESAMT** | **3-4 Tage** |

---

## 📞 Support

**Bei Fragen:**
- Alignment Doc: `docs/risk/RISK_LAYER_ROADMAP_ALIGNMENT.md`
- Bestehende Stress Implementation: `src/risk/stress_tester.py`

**Agent A (Lead):** Verfügbar für Architektur-Fragen

---

**Erstellt von:** Agent A (Lead Orchestrator)  
**Delegiert an:** Agent E (Stress Testing Specialist)  
**Status:** 📋 BEREIT ZU STARTEN

**Viel Erfolg! 🚀**
