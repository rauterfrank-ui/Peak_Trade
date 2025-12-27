# Kupiec POF Backtest – Implementierungs-Roadmap

**Projekt:** Peak_Trade Risk Layer  
**Komponente:** VaR Backtesting / Kupiec Proportion of Failures (POF) Test  
**Erstellt:** 2025-12-27  
**Status:** 📋 ROADMAP READY

---

## 🎯 Ziel

Implementierung des **Kupiec POF Tests** zur statistischen Validierung der VaR-Modelle in Peak_Trade. Der Test prüft, ob die tatsächliche Anzahl von VaR-Überschreitungen (Violations) mit der erwarteten Anzahl bei gegebenem Konfidenzniveau übereinstimmt.

**Warum kritisch:**
- VaR-Modelle müssen validiert werden, bevor sie in Shadow/Live Trading verwendet werden
- Regulatorische Anforderung (Basel III Framework)
- Frühzeitige Erkennung von Model Risk

---

## 📊 Übersicht: Phasen

| Phase | Name | Dauer | Deliverables | Status |
|-------|------|-------|--------------|--------|
| 1 | Foundation | 2-3 Tage | Kernlogik + Unit Tests | ⬜ |
| 2 | Integration | 2-3 Tage | VaR-Engine Anbindung | ⬜ |
| 3 | Reporting | 1-2 Tage | HTML/JSON Reports | ⬜ |
| 4 | CLI & Config | 1 Tag | Operator-Interface | ⬜ |
| 5 | Validation | 2-3 Tage | Edge Cases + Docs | ⬜ |

**Gesamt:** ~8-12 Tage

---

## Phase 1: Foundation (Kernlogik)

### 1.1 Ziel
Implementierung der mathematischen Grundlagen des Kupiec POF Tests als eigenständiges, testbares Modul.

### 1.2 Theorie-Hintergrund

**Kupiec POF Test (1995):**
```
H₀: p = p* (Modell ist korrekt kalibriert)
H₁: p ≠ p* (Modell ist fehlkalibriert)

Likelihood Ratio Statistic:
LR_POF = -2 * ln[(1-p*)^(T-N) * p*^N] + 2 * ln[(1-N/T)^(T-N) * (N/T)^N]

Wobei:
- T = Anzahl Beobachtungen (Backtesting-Fenster)
- N = Anzahl VaR-Überschreitungen (Violations)
- p* = erwartete Violation Rate (1 - Konfidenzniveau, z.B. 0.01 für 99% VaR)

LR_POF ~ χ²(1) unter H₀
```

### 1.3 Deliverables

```
src/risk/var_backtest/
├── __init__.py
├── kupiec_pof.py              # Kernlogik
├── exceptions.py              # Custom Exceptions
└── types.py                   # TypedDicts, Enums

tests/risk/var_backtest/
├── __init__.py
├── test_kupiec_pof.py         # Unit Tests
└── fixtures/
    └── violation_series.py    # Test-Daten
```

### 1.4 Implementierung: `kupiec_pof.py`

```python
"""
Kupiec Proportion of Failures (POF) Test
=========================================
Statistischer Backtest für VaR-Modelle.

Referenz:
- Kupiec, P. (1995): "Techniques for Verifying the Accuracy of
  Risk Measurement Models", Journal of Derivatives
"""

from dataclasses import dataclass
from enum import Enum
from typing import Sequence
import math
from scipy import stats


class KupiecResult(Enum):
    """Ergebnis des Kupiec POF Tests."""
    ACCEPT = "accept"      # H₀ nicht abgelehnt → Modell OK
    REJECT = "reject"      # H₀ abgelehnt → Modell fehlkalibriert
    INCONCLUSIVE = "inconclusive"  # Zu wenig Daten


@dataclass(frozen=True)
class KupiecPOFOutput:
    """Strukturiertes Ergebnis des Kupiec POF Tests."""

    # Eingabedaten
    n_observations: int          # T: Anzahl Beobachtungen
    n_violations: int            # N: Anzahl Überschreitungen
    confidence_level: float      # z.B. 0.99 für 99% VaR
    significance_level: float    # z.B. 0.05 für 5% Signifikanz

    # Berechnete Werte
    expected_violation_rate: float   # p* = 1 - confidence_level
    observed_violation_rate: float   # N / T
    lr_statistic: float              # Likelihood Ratio Statistik
    p_value: float                   # p-Wert aus χ²(1)
    critical_value: float            # χ²(1) kritischer Wert

    # Ergebnis
    result: KupiecResult

    @property
    def is_valid(self) -> bool:
        """Modell gilt als valide wenn H₀ nicht abgelehnt."""
        return self.result == KupiecResult.ACCEPT

    @property
    def violation_ratio(self) -> float:
        """Verhältnis beobachtete / erwartete Violations."""
        if self.expected_violation_rate == 0:
            return float('inf')
        return self.observed_violation_rate / self.expected_violation_rate


def kupiec_pof_test(
    violations: Sequence[bool],
    confidence_level: float = 0.99,
    significance_level: float = 0.05,
    min_observations: int = 250,
) -> KupiecPOFOutput:
    """
    Führt den Kupiec POF Test durch.

    Args:
        violations: Sequenz von bool (True = VaR-Überschreitung)
        confidence_level: VaR-Konfidenzniveau (z.B. 0.99 für 99% VaR)
        significance_level: Signifikanzniveau für Hypothesentest
        min_observations: Minimum für validen Test (Basel: 250)

    Returns:
        KupiecPOFOutput mit allen Ergebnissen

    Raises:
        ValueError: Bei ungültigen Eingaben

    Example:
        >>> violations = [False] * 245 + [True] * 5  # 5 Violations in 250 Tagen
        >>> result = kupiec_pof_test(violations, confidence_level=0.99)
        >>> result.is_valid
        True
    """
    # Input Validation
    if not 0 < confidence_level < 1:
        raise ValueError(f"confidence_level muss in (0,1) liegen: {confidence_level}")
    if not 0 < significance_level < 1:
        raise ValueError(f"significance_level muss in (0,1) liegen: {significance_level}")

    T = len(violations)
    N = sum(violations)
    p_star = 1 - confidence_level  # Erwartete Violation Rate

    # Prüfe Mindestanzahl Beobachtungen
    if T < min_observations:
        return KupiecPOFOutput(
            n_observations=T,
            n_violations=N,
            confidence_level=confidence_level,
            significance_level=significance_level,
            expected_violation_rate=p_star,
            observed_violation_rate=N / T if T > 0 else 0.0,
            lr_statistic=float('nan'),
            p_value=float('nan'),
            critical_value=stats.chi2.ppf(1 - significance_level, df=1),
            result=KupiecResult.INCONCLUSIVE,
        )

    # Beobachtete Violation Rate
    p_obs = N / T

    # Likelihood Ratio Statistik berechnen
    lr_stat = _compute_lr_statistic(T, N, p_star)

    # p-Wert aus χ²(1) Verteilung
    p_value = 1 - stats.chi2.cdf(lr_stat, df=1)

    # Kritischer Wert
    critical_value = stats.chi2.ppf(1 - significance_level, df=1)

    # Entscheidung
    if lr_stat > critical_value:
        result = KupiecResult.REJECT
    else:
        result = KupiecResult.ACCEPT

    return KupiecPOFOutput(
        n_observations=T,
        n_violations=N,
        confidence_level=confidence_level,
        significance_level=significance_level,
        expected_violation_rate=p_star,
        observed_violation_rate=p_obs,
        lr_statistic=lr_stat,
        p_value=p_value,
        critical_value=critical_value,
        result=result,
    )


def _compute_lr_statistic(T: int, N: int, p_star: float) -> float:
    """
    Berechnet die Likelihood Ratio Statistik.

    LR = -2 * ln(L₀) + 2 * ln(L₁)

    Wobei:
    - L₀ = (1-p*)^(T-N) * p*^N  (unter H₀)
    - L₁ = (1-p̂)^(T-N) * p̂^N   (unter H₁, mit p̂ = N/T)
    """
    # Edge Cases
    if N == 0:
        # Keine Violations → nur L₀ Term
        return -2 * ((T - N) * math.log(1 - p_star) + N * math.log(p_star) if p_star > 0 else 0)
    if N == T:
        # Alle Violations → Sonderfall
        return -2 * (T * math.log(p_star) - T * math.log(N / T)) if p_star > 0 else float('inf')

    p_obs = N / T

    # Log-Likelihood unter H₀
    log_L0 = (T - N) * math.log(1 - p_star) + N * math.log(p_star)

    # Log-Likelihood unter H₁ (mit beobachteter Rate)
    log_L1 = (T - N) * math.log(1 - p_obs) + N * math.log(p_obs)

    # LR Statistik
    lr = -2 * (log_L0 - log_L1)

    return lr


# Convenience Functions
def quick_kupiec_check(
    n_violations: int,
    n_observations: int,
    confidence_level: float = 0.99,
) -> bool:
    """
    Schneller Check ohne Violations-Sequenz.

    Returns:
        True wenn Modell valide (H₀ nicht abgelehnt)
    """
    violations = [True] * n_violations + [False] * (n_observations - n_violations)
    result = kupiec_pof_test(violations, confidence_level=confidence_level)
    return result.is_valid
```

### 1.5 Unit Tests: `test_kupiec_pof.py`

```python
"""Unit Tests für Kupiec POF Test."""

import pytest
import math
from src.risk.var_backtest.kupiec_pof import (
    kupiec_pof_test,
    quick_kupiec_check,
    KupiecResult,
    KupiecPOFOutput,
)


class TestKupiecPOFBasic:
    """Grundlegende Funktionalitätstests."""

    def test_perfect_calibration_99_var(self):
        """99% VaR mit exakt 1% Violations → sollte ACCEPT sein."""
        T = 1000
        N = 10  # Exakt 1% Violations
        violations = [True] * N + [False] * (T - N)

        result = kupiec_pof_test(violations, confidence_level=0.99)

        assert result.result == KupiecResult.ACCEPT
        assert result.n_observations == T
        assert result.n_violations == N
        assert abs(result.observed_violation_rate - 0.01) < 1e-10

    def test_too_many_violations_rejected(self):
        """Deutlich zu viele Violations → sollte REJECT sein."""
        T = 250
        N = 15  # 6% statt erwarteter 1% → klar zu viel
        violations = [True] * N + [False] * (T - N)

        result = kupiec_pof_test(violations, confidence_level=0.99)

        assert result.result == KupiecResult.REJECT
        assert result.violation_ratio > 5  # 6x mehr als erwartet

    def test_too_few_violations_rejected(self):
        """Null Violations bei 1000 Beobachtungen → verdächtig."""
        T = 1000
        N = 0  # 0% statt erwarteter 1%
        violations = [False] * T

        result = kupiec_pof_test(violations, confidence_level=0.99)

        # Null Violations kann auch auf Überkonservativität hindeuten
        # Bei großem T wird dies abgelehnt
        assert result.observed_violation_rate == 0.0

    def test_insufficient_data_inconclusive(self):
        """Weniger als min_observations → INCONCLUSIVE."""
        violations = [False] * 100 + [True] * 1

        result = kupiec_pof_test(violations, min_observations=250)

        assert result.result == KupiecResult.INCONCLUSIVE
        assert math.isnan(result.lr_statistic)


class TestKupiecPOFEdgeCases:
    """Edge Cases und Grenzwerte."""

    def test_all_violations(self):
        """100% Violations → definitiv REJECT."""
        violations = [True] * 250

        result = kupiec_pof_test(violations, confidence_level=0.99)

        assert result.result == KupiecResult.REJECT
        assert result.observed_violation_rate == 1.0

    def test_no_violations_large_sample(self):
        """0 Violations bei großem Sample."""
        violations = [False] * 500

        result = kupiec_pof_test(violations, confidence_level=0.99)

        assert result.n_violations == 0
        assert result.observed_violation_rate == 0.0

    def test_confidence_95_var(self):
        """95% VaR (5% erwartete Violations)."""
        T = 500
        N = 25  # Exakt 5%
        violations = [True] * N + [False] * (T - N)

        result = kupiec_pof_test(violations, confidence_level=0.95)

        assert result.expected_violation_rate == 0.05
        assert result.result == KupiecResult.ACCEPT


class TestKupiecPOFValidation:
    """Input Validation Tests."""

    def test_invalid_confidence_level_high(self):
        """confidence_level >= 1 → ValueError."""
        with pytest.raises(ValueError, match="confidence_level"):
            kupiec_pof_test([False] * 250, confidence_level=1.0)

    def test_invalid_confidence_level_low(self):
        """confidence_level <= 0 → ValueError."""
        with pytest.raises(ValueError, match="confidence_level"):
            kupiec_pof_test([False] * 250, confidence_level=0.0)

    def test_invalid_significance_level(self):
        """significance_level außerhalb (0,1) → ValueError."""
        with pytest.raises(ValueError, match="significance_level"):
            kupiec_pof_test([False] * 250, significance_level=1.5)


class TestQuickKupiecCheck:
    """Tests für Convenience-Funktion."""

    def test_quick_check_valid(self):
        """Schneller Check mit validen Werten."""
        assert quick_kupiec_check(n_violations=3, n_observations=250) is True

    def test_quick_check_invalid(self):
        """Schneller Check mit zu vielen Violations."""
        assert quick_kupiec_check(n_violations=20, n_observations=250) is False


class TestKupiecPOFOutput:
    """Tests für Output-Struktur."""

    def test_output_immutable(self):
        """Output sollte frozen dataclass sein."""
        violations = [False] * 250 + [True] * 3
        result = kupiec_pof_test(violations)

        with pytest.raises(AttributeError):
            result.n_violations = 999  # type: ignore

    def test_violation_ratio_calculation(self):
        """violation_ratio korrekt berechnet."""
        T = 500
        N = 10  # 2% statt erwarteter 1%
        violations = [True] * N + [False] * (T - N)

        result = kupiec_pof_test(violations, confidence_level=0.99)

        assert abs(result.violation_ratio - 2.0) < 0.01  # ~2x mehr
```

### 1.6 Akzeptanzkriterien Phase 1

- [ ] `kupiec_pof_test()` implementiert mit vollständiger Signatur
- [ ] `KupiecPOFOutput` dataclass mit allen Feldern
- [ ] Edge Cases behandelt (N=0, N=T, T < min)
- [ ] Unit Tests: ≥95% Coverage für `kupiec_pof.py`
- [ ] Type Hints vollständig
- [ ] Docstrings (Deutsch) für alle public Functions
- [ ] `pytest tests/risk/var_backtest/` grün

---

## Phase 2: Integration (VaR-Engine Anbindung)

### 2.1 Ziel
Anbindung des Kupiec POF Tests an die bestehende VaR-Berechnung und Portfolio-Daten.

### 2.2 Deliverables

```
src/risk/var_backtest/
├── var_backtest_runner.py     # Orchestrierung
├── violation_detector.py      # VaR-Überschreitungen erkennen
└── backtest_config.py         # TOML-basierte Konfiguration

config/
└── var_backtest.toml          # Konfigurations-Template
```

### 2.3 Implementierung: `violation_detector.py`

```python
"""
VaR Violation Detector
======================
Erkennt VaR-Überschreitungen in historischen Portfoliodaten.
"""

from dataclasses import dataclass
from typing import Sequence
import pandas as pd


@dataclass
class ViolationSeries:
    """Container für Violation-Daten."""
    dates: pd.DatetimeIndex
    returns: pd.Series           # Tägliche Portfolio-Returns
    var_estimates: pd.Series     # VaR-Schätzungen (negativ!)
    violations: pd.Series        # bool: Return < VaR?

    @property
    def violation_dates(self) -> pd.DatetimeIndex:
        """Daten mit VaR-Überschreitung."""
        return self.dates[self.violations]

    @property
    def n_violations(self) -> int:
        return self.violations.sum()

    @property
    def n_observations(self) -> int:
        return len(self.violations)


def detect_violations(
    returns: pd.Series,
    var_estimates: pd.Series,
) -> ViolationSeries:
    """
    Erkennt VaR-Überschreitungen.

    Args:
        returns: Tägliche Portfolio-Returns (z.B. -0.02 für -2%)
        var_estimates: VaR-Schätzungen (negativ, z.B. -0.015 für -1.5% VaR)

    Returns:
        ViolationSeries mit allen Daten

    Note:
        Violation = Return < VaR (beide negativ!)
        Beispiel: Return = -3%, VaR = -2% → Violation (Verlust größer als VaR)
    """
    # Alignment
    aligned = pd.DataFrame({
        'returns': returns,
        'var': var_estimates,
    }).dropna()

    # Violation: Return unterschreitet VaR
    violations = aligned['returns'] < aligned['var']

    return ViolationSeries(
        dates=aligned.index,
        returns=aligned['returns'],
        var_estimates=aligned['var'],
        violations=violations,
    )
```

### 2.4 Implementierung: `var_backtest_runner.py`

```python
"""
VaR Backtest Runner
===================
Orchestriert den gesamten VaR-Backtest-Prozess.
"""

from dataclasses import dataclass
from typing import Optional
import pandas as pd

from .kupiec_pof import kupiec_pof_test, KupiecPOFOutput
from .violation_detector import detect_violations, ViolationSeries


@dataclass
class VaRBacktestResult:
    """Vollständiges Backtest-Ergebnis."""

    # Metadaten
    symbol: str
    start_date: pd.Timestamp
    end_date: pd.Timestamp
    var_confidence: float
    var_method: str              # "historical", "parametric", "monte_carlo"

    # Violation-Daten
    violations: ViolationSeries

    # Kupiec Test
    kupiec: KupiecPOFOutput

    @property
    def is_valid(self) -> bool:
        """VaR-Modell gilt als valide."""
        return self.kupiec.is_valid

    def summary(self) -> dict:
        """Kompakte Zusammenfassung."""
        return {
            "symbol": self.symbol,
            "period": f"{self.start_date.date()} - {self.end_date.date()}",
            "n_observations": self.kupiec.n_observations,
            "n_violations": self.kupiec.n_violations,
            "expected_rate": f"{self.kupiec.expected_violation_rate:.2%}",
            "observed_rate": f"{self.kupiec.observed_violation_rate:.2%}",
            "violation_ratio": f"{self.kupiec.violation_ratio:.2f}x",
            "kupiec_lr": f"{self.kupiec.lr_statistic:.4f}",
            "p_value": f"{self.kupiec.p_value:.4f}",
            "result": self.kupiec.result.value.upper(),
            "is_valid": self.is_valid,
        }


class VaRBacktestRunner:
    """
    Führt VaR-Backtests mit Kupiec POF Test durch.

    Example:
        >>> runner = VaRBacktestRunner(confidence_level=0.99)
        >>> result = runner.run(
        ...     returns=portfolio_returns,
        ...     var_estimates=var_series,
        ...     symbol="BTC/EUR",
        ... )
        >>> print(result.summary())
    """

    def __init__(
        self,
        confidence_level: float = 0.99,
        significance_level: float = 0.05,
        min_observations: int = 250,
        var_method: str = "historical",
    ):
        self.confidence_level = confidence_level
        self.significance_level = significance_level
        self.min_observations = min_observations
        self.var_method = var_method

    def run(
        self,
        returns: pd.Series,
        var_estimates: pd.Series,
        symbol: str = "PORTFOLIO",
    ) -> VaRBacktestResult:
        """
        Führt vollständigen VaR-Backtest durch.

        Args:
            returns: Tägliche Portfolio-Returns
            var_estimates: VaR-Schätzungen (negativ)
            symbol: Asset/Portfolio-Bezeichnung

        Returns:
            VaRBacktestResult mit allen Ergebnissen
        """
        # 1. Violations erkennen
        violations = detect_violations(returns, var_estimates)

        # 2. Kupiec POF Test
        kupiec_result = kupiec_pof_test(
            violations=violations.violations.tolist(),
            confidence_level=self.confidence_level,
            significance_level=self.significance_level,
            min_observations=self.min_observations,
        )

        # 3. Ergebnis zusammenstellen
        return VaRBacktestResult(
            symbol=symbol,
            start_date=violations.dates.min(),
            end_date=violations.dates.max(),
            var_confidence=self.confidence_level,
            var_method=self.var_method,
            violations=violations,
            kupiec=kupiec_result,
        )
```

### 2.5 Config: `config/var_backtest.toml`

```toml
# Peak_Trade VaR Backtest Konfiguration
# =====================================

[var_backtest]
# Allgemeine Einstellungen
enabled = true
confidence_level = 0.99          # VaR-Konfidenzniveau (99%)
significance_level = 0.05        # Signifikanzniveau für Tests (5%)
min_observations = 250           # Minimum für validen Test (Basel: 250 Tage)

[var_backtest.kupiec]
# Kupiec POF Test Einstellungen
enabled = true
warning_threshold = 1.5          # Warnung wenn violation_ratio > 1.5x
critical_threshold = 2.0         # Kritisch wenn violation_ratio > 2.0x

[var_backtest.output]
# Report-Einstellungen
format = "html"                  # "html", "json", "console"
output_dir = "reports/var_backtest"
include_charts = true
include_violation_details = true
```

### 2.6 Akzeptanzkriterien Phase 2

- [ ] `VaRBacktestRunner` integriert mit bestehender VaR-Engine
- [ ] `ViolationSeries` korrekt berechnet
- [ ] TOML-Config geladen und angewendet
- [ ] Integration Tests mit echten Backtest-Daten
- [ ] Dokumentation der Schnittstellen

---

## Phase 3: Reporting (HTML/JSON)

### 3.1 Ziel
Professionelle Reports für Kupiec POF Backtests mit Visualisierungen.

### 3.2 Deliverables

```
src/risk/var_backtest/
├── report_generator.py        # Report-Erstellung
└── templates/
    └── kupiec_report.html     # Jinja2 Template

tests/risk/var_backtest/
└── test_report_generator.py
```

### 3.3 Report-Inhalte

**HTML Report:**
1. Executive Summary (Traffic Light: 🟢/🟡/🔴)
2. Test-Statistiken (Tabelle)
3. Violation Timeline (Chart)
4. Violation Rate über Zeit (Rolling Window)
5. VaR vs. Actual Returns (Scatter)
6. Detaillierte Violation-Liste

**JSON Report:**
```json
{
  "meta": {
    "generated_at": "2025-12-27T10:30:00Z",
    "peak_trade_version": "0.9.0",
    "test_type": "kupiec_pof"
  },
  "summary": {
    "symbol": "BTC/EUR",
    "result": "ACCEPT",
    "is_valid": true,
    "traffic_light": "green"
  },
  "statistics": {
    "n_observations": 365,
    "n_violations": 4,
    "expected_rate": 0.01,
    "observed_rate": 0.011,
    "violation_ratio": 1.10,
    "lr_statistic": 0.1234,
    "p_value": 0.7253,
    "critical_value": 3.8415
  },
  "violations": [
    {"date": "2024-03-15", "return": -0.045, "var": -0.032},
    {"date": "2024-06-22", "return": -0.038, "var": -0.029}
  ]
}
```

### 3.4 Akzeptanzkriterien Phase 3

- [ ] HTML Report mit allen Visualisierungen
- [ ] JSON Report maschinenlesbar
- [ ] Traffic Light System (🟢 ACCEPT, 🟡 WARNING, 🔴 REJECT)
- [ ] Charts: Violation Timeline, VaR vs Returns
- [ ] Export nach `reports/var_backtest/`

---

## Phase 4: CLI & Config (Operator-Interface)

### 4.1 Ziel
Kommandozeilen-Interface für einfache Ausführung und CI-Integration.

### 4.2 Deliverables

```
scripts/risk/
└── run_var_backtest.py        # CLI Entry Point

scripts/ops/
└── var_backtest_check.sh      # CI-freundliches Wrapper-Script
```

### 4.3 CLI Usage

```bash
# Einzelner Backtest
python scripts/risk/run_var_backtest.py \
  --symbol BTC/EUR \
  --start 2024-01-01 \
  --end 2024-12-31 \
  --confidence 0.99 \
  --output reports/var_backtest/btc_eur_2024.html

# Portfolio Backtest
python scripts/risk/run_var_backtest.py \
  --portfolio config/portfolio.toml \
  --output reports/var_backtest/portfolio_2024.html

# CI Mode (Exit Code basiert auf Ergebnis)
python scripts/risk/run_var_backtest.py \
  --symbol BTC/EUR \
  --ci-mode \
  --fail-on-reject
```

### 4.4 Exit Codes

| Code | Bedeutung |
|------|-----------|
| 0 | ACCEPT (Modell valide) |
| 1 | REJECT (Modell fehlkalibriert) |
| 2 | INCONCLUSIVE (zu wenig Daten) |
| 3 | ERROR (Ausführungsfehler) |

### 4.5 Akzeptanzkriterien Phase 4

- [ ] CLI mit `--help` Dokumentation
- [ ] TOML-Config Unterstützung
- [ ] CI-freundliche Exit Codes
- [ ] `--dry-run` Option
- [ ] `--verbose` / `--quiet` Flags

---

## Phase 5: Validation (Edge Cases & Docs)

### 5.1 Ziel
Umfassende Validierung und Dokumentation für Production-Readiness.

### 5.2 Deliverables

```
tests/risk/var_backtest/
├── test_edge_cases.py         # Grenzfälle
├── test_integration.py        # End-to-End Tests
└── test_performance.py        # Performance Benchmarks

docs/risk/
├── VAR_BACKTEST_GUIDE.md      # Operator Guide
├── KUPIEC_POF_THEORY.md       # Theoretischer Hintergrund
└── INTERPRETATION_GUIDE.md    # Ergebnisinterpretation
```

### 5.3 Edge Cases zu testen

| Szenario | Erwartetes Verhalten |
|----------|---------------------|
| Leere Datenserie | Graceful Error mit Hinweis |
| Alle Returns = 0 | Keine Violations, ACCEPT |
| Extreme Volatilität | Korrekte Violation-Detection |
| Lücken in Zeitreihe | Warnung + Fortsetzen |
| NaN in VaR-Schätzungen | Graceful Handling |
| Verschiedene Zeitzonen | UTC-Normalisierung |

### 5.4 Performance Benchmarks

| Datensatz | Ziel-Laufzeit |
|-----------|---------------|
| 250 Tage | < 100ms |
| 1.000 Tage | < 200ms |
| 10.000 Tage | < 1s |
| 100.000 Tage | < 5s |

### 5.5 Akzeptanzkriterien Phase 5

- [ ] Edge Case Tests: 100% der identifizierten Fälle
- [ ] Integration Test mit echten Kraken-Daten
- [ ] Performance Benchmarks dokumentiert
- [ ] Operator Guide vollständig
- [ ] Theorie-Dokumentation (für Audits)
- [ ] Interpretation Guide (für Nicht-Quants)

---

## 📋 Gesamtcheckliste

### Phase 1: Foundation ⬜
- [ ] `kupiec_pof.py` implementiert
- [ ] `KupiecPOFOutput` dataclass
- [ ] Unit Tests ≥95% Coverage
- [ ] Type Hints + Docstrings

### Phase 2: Integration ⬜
- [ ] `VaRBacktestRunner` implementiert
- [ ] `ViolationDetector` implementiert
- [ ] TOML-Config Integration
- [ ] Integration Tests

### Phase 3: Reporting ⬜
- [ ] HTML Report Generator
- [ ] JSON Report Generator
- [ ] Visualisierungen (Charts)
- [ ] Traffic Light System

### Phase 4: CLI & Config ⬜
- [ ] CLI Entry Point
- [ ] CI-freundliche Exit Codes
- [ ] `--help` Dokumentation
- [ ] Wrapper Script für CI

### Phase 5: Validation ⬜
- [ ] Edge Case Tests
- [ ] Performance Benchmarks
- [ ] Operator Guide
- [ ] Theorie-Dokumentation

---

## 🔗 Referenzen

**Paper:**
- Kupiec, P. (1995): "Techniques for Verifying the Accuracy of Risk Measurement Models", Journal of Derivatives, Vol. 3, No. 2

**Basel Framework:**
- Basel Committee: "Supervisory Framework for the Use of Backtesting" (1996)
- Mindestbeobachtungen: 250 Handelstage (~1 Jahr)

**Python Packages:**
- `scipy.stats.chi2` für χ²-Verteilung
- `pandas` für Zeitreihen-Handling
- `jinja2` für HTML-Reports
- `plotly` oder `matplotlib` für Charts

---

## 📝 Notizen

**Warum Kupiec POF:**
- Einfachster VaR-Backtest (nur Violation Count)
- Regulatorisch anerkannt (Basel)
- Guter erster Schritt vor komplexeren Tests (Christoffersen, Traffic Light)

**Limitationen:**
- Testet nur Frequenz, nicht Clustering (dafür: Christoffersen Independence Test)
- Geringe Power bei kleinen Samples
- Unterscheidet nicht zwischen leichten und schweren Violations

**Nächste Schritte nach Kupiec:**
1. Christoffersen Independence Test (Violation Clustering)
2. Traffic Light Test (kombiniert mehrere Kriterien)
3. Expected Shortfall Backtest (ES statt VaR)

---

**Status:** 📋 READY FOR IMPLEMENTATION  
**Nächster Schritt:** Phase 1 starten mit `kupiec_pof.py`
