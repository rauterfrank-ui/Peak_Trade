# Peak_Trade Risk Layer — Roadmap

**Version:** 1.0  
**Datum:** 2025-12-27  
**Status:** 🔴 IN PROGRESS (60% → 100%)  
**Ziel-Completion:** Q1 2026

---

## 📊 Executive Summary

Der Risk Layer ist das **kritische Fundament** von Peak_Trade. Ohne 100% Completion gibt es **kein Live-Trading** — das ist nicht verhandelbar.

**Aktueller Stand:**
- ✅ Basis-Positionslimits implementiert
- ✅ Stop-Loss/Take-Profit Logik
- ⏳ Portfolio-VaR/CVaR (fehlt)
- ⏳ Component VaR für Attribution (fehlt)
- ⏳ Monte Carlo Simulation (fehlt)
- ⏳ Stress Testing (fehlt)
- ⏳ VaR Backtesting (Kupiec POF) (fehlt)

**Roadmap-Struktur:** 6 Phasen über 4-5 Wochen (Phase 0 = Alignment, dann 5 Implementation-Phasen)

---

## 🔒 Governance & Safety

**⚠️ CRITICAL: Risk Layer MUST remain disabled by default.**

Enabling the Risk Layer (`[risk_layer] enabled = true`) requires:

1. **Governance Approval:** Formal Go/No-Go decision documented
2. **Operator Runbook:** Step-by-step manual procedures for enable/disable
3. **Shadow/Testnet First:** Complete validation in non-live environment
4. **Manual-Only Operation:** No automated enable; requires explicit human action
5. **Rollback Plan:** Pre-defined revert process

**Default State:** `enabled = false` — This is NOT negotiable without governance review.

---

## 🎯 Phasen-Übersicht

| Phase | Name | Dauer | Status | Kritikalität |
|-------|------|-------|--------|--------------|
| **0** | Architecture Alignment | 1-2 Tage | ✅ DONE | 🟢 FOUNDATION |
| **1** | Foundation & VaR Core | 1 Woche | ⬜ TODO | 🔴 KRITISCH |
| **2** | VaR Backtesting & Validation | 1 Woche | ⬜ TODO | 🔴 KRITISCH |
| **3** | Component VaR & Attribution | 1 Woche | ⬜ TODO | 🟡 WICHTIG |
| **4** | Stress Testing & Szenarien | 1 Woche | ⬜ TODO | 🔴 KRITISCH |
| **5** | Defense-in-Depth Integration | 3-5 Tage | ⬜ TODO | 🔴 KRITISCH |

---

## 🏗️ Phase 0: Architecture Alignment

**Dauer:** 1-2 Arbeitstage  
**Status:** ✅ COMPLETED  
**Ziel:** Paketstruktur, gemeinsame Types, Exceptions und Config-Anker etablieren

### 0.1 Architekturentscheidungen

#### ✅ **Entscheidung 1: Package Root**
- **Gewählt:** `src/risk_layer/`
- **Rationale:** Klare Trennung von Legacy `src/risk/` (basic risk logic) und neuem Advanced Risk Layer
- **Struktur:**
  ```
  src/risk_layer/
  ├── __init__.py           # Public API exports
  ├── types.py              # Type stubs für zukünftige Implementation
  ├── exceptions.py         # Custom exceptions (InsufficientDataError, etc.)
  ├── models.py             # Core data models (RiskDecision, Violation)
  ├── risk_gate.py          # Risk gate orchestrator
  ├── kill_switch.py        # Emergency kill switch
  └── *_gate.py             # Specific gates (var, stress, liquidity)
  ```

#### ✅ **Entscheidung 2: Config Strategy**
- **Gewählt:** Dedicated `[risk_layer]` namespace in `config/config.toml`
- **Rationale:** Kompatibel mit PeakConfig-Philosophie, klare Separation von Basic Risk
- **Config-Anker:**
  ```toml
  [risk_layer]
  enabled = false                    # Master-Switch
  var_confidence = 0.95              # Phase R1
  cvar_enabled = false               # Phase R1
  stress_testing_enabled = false     # Phase R3
  validation_frequency_days = 7      # Phase R2
  alert_threshold_utilization = 0.80 # Phase R5
  ```

#### ✅ **Entscheidung 3: Zentrale Types & Exceptions**
- **Types (Stubs für Phasen R1-R5):**
  - `PortfolioVaRResult` — VaR/CVaR Ergebnisse (Phase R1)
  - `ComponentVaRResult` — Component VaR für Attribution (Phase R1)
  - `RiskValidationResult` — Backtesting-Ergebnisse (Phase R2)
  - `StressTestResult` — Stress Test Outcomes (Phase R3)
  - `RiskMetrics` — Aggregierte Risk Metrics (Phase R5)
  - `RiskConfig` — Typed config dataclass
  - `Order` (Protocol) — Minimales Order-Interface
  - `Portfolio` (Protocol) — Minimales Portfolio-Interface

- **Exceptions:**
  ```python
  RiskLayerError(Exception)           # Base exception
  ├── InsufficientDataError(ValueError)  # Zu wenig Daten für Berechnung
  ├── RiskConfigError(ValueError)        # Invalide Konfiguration
  ├── RiskCalculationError               # Numerische Fehler
  └── RiskViolationError                 # Limit-Verletzung
  ```

#### ✅ **Entscheidung 4: Docs Reference Kompatibilität**
- **Regel:** Nur repo-relative Pfade in Dokumentation
- **Beispiel:** `[Link](../../src/risk_layer/types.py)` ✅
- **Verboten:** Absolute Paths oder externe Links ohne Context ❌
- **Grund:** Docs-Reference-Targets-Gate Kompatibilität

### 0.2 Deliverables (Phase 0)

✅ **Dateien erstellt:**
- `src/risk_layer/types.py` — Type stubs (200+ LOC, voll dokumentiert)
- `src/risk_layer/exceptions.py` — Custom exceptions (70 LOC)
- `src/risk_layer/__init__.py` — Erweiterte Exports inkl. Phase 0 Docs
- `config/config.toml` — `[risk_layer]` Section hinzugefügt
- `docs/risk/roadmaps/RISK_LAYER_ROADMAP.md` — Diese Phase 0 Section

✅ **Tests:**
- `tests/risk_layer/test_imports_smoke.py` — Import-Tests & Type-Instanziierung

✅ **CI/CD:**
- Alle Tests grün ✅
- Linter (ruff) sauber ✅
- Format (ruff format) angewandt ✅

### 0.3 Warum Phase 0?

**Problem ohne Phase 0:**
- Unklare Package-Struktur → Merge-Konflikte in Phase R1-R5
- Fehlende gemeinsame Types → Inkompatible Interfaces zwischen Phasen
- Keine Config-Anker → Jede Phase erfindet eigene Config-Strategie
- Fehlende Exceptions → Unklare Error-Semantik

**Nutzen von Phase 0:**
- ✅ **Alignment:** Alle zukünftigen PRs folgen gleicher Struktur
- ✅ **Contracts:** Types definieren Interfaces für alle Phasen
- ✅ **Testing:** Smoke Tests validieren Struktur ab Tag 1
- ✅ **Velocity:** Phase R1-R5 können parallel entwickelt werden (keine Breaking Changes)

### 0.4 Next Steps → Phase 1

Mit Phase 0 abgeschlossen können wir direkt in Phase 1 starten:
- Types sind definiert → nur noch Implementierung hinzufügen
- Config ist bereit → remains `enabled = false` (requires governance approval to enable)
- Tests laufen → nur Business Logic Tests ergänzen

**Phase 1 startet mit:**
- Implementation von `PortfolioVaRResult` (aktuell Stub)
- VaR Calculator (nutzt bereits definierte Exceptions)
- Config-Loading (aus `[risk_layer]` namespace)

→ Siehe nächste Section für Phase 1 Details.

---

## 📋 Phase 1: Foundation & VaR Core

**Dauer:** 5-7 Arbeitstage  
**Ziel:** Portfolio Value-at-Risk und CVaR als Kernmetriken implementieren

### 1.1 Deliverables

```
src/risk/
├── __init__.py                    # Exports: VaR, CVaR, RiskEngine
├── var_calculator.py              # VaR/CVaR Berechnungen
├── portfolio_risk.py              # Portfolio-Level Aggregation
├── models/
│   ├── __init__.py
│   ├── historical_var.py          # Historical Simulation VaR
│   ├── parametric_var.py          # Varianz-Kovarianz VaR
│   └── monte_carlo_var.py         # Monte Carlo VaR (Stub)
└── config/
    └── risk_limits.toml           # Zentrale Risk-Konfiguration

tests/risk/
├── test_var_calculator.py         # Unit Tests VaR
├── test_portfolio_risk.py         # Integration Tests
└── fixtures/
    └── sample_returns.parquet     # Test-Daten

docs/risk/
└── VAR_METHODOLOGY.md             # Methodik-Dokumentation
```

### 1.2 Funktionen & Signaturen

```python
# src/risk/var_calculator.py

def calculate_var(
    returns: pd.Series | pd.DataFrame,
    confidence_level: float = 0.95,
    method: Literal["historical", "parametric"] = "historical",
    window: int | None = None,
) -> float:
    """
    Berechnet Value-at-Risk für gegebene Returns.

    Args:
        returns: Tägliche Returns (Series) oder Multi-Asset (DataFrame)
        confidence_level: Konfidenzniveau (0.95 = 95%)
        method: Berechnungsmethode
        window: Rolling Window (None = alle Daten)

    Returns:
        VaR als positive Zahl (Verlust bei Konfidenz)

    Raises:
        ValueError: Bei ungültigen Inputs
        InsufficientDataError: Bei zu wenig Datenpunkten
    """

def calculate_cvar(
    returns: pd.Series | pd.DataFrame,
    confidence_level: float = 0.95,
    method: Literal["historical", "parametric"] = "historical",
) -> float:
    """
    Berechnet Conditional VaR (Expected Shortfall).

    CVaR = Erwarteter Verlust, WENN VaR überschritten wird.
    Kohärentes Risikomaß (subadditiv).
    """

def calculate_portfolio_var(
    positions: dict[str, float],  # {symbol: value}
    returns: pd.DataFrame,        # Multi-Asset Returns
    confidence_level: float = 0.95,
    correlation_matrix: pd.DataFrame | None = None,
) -> PortfolioVaRResult:
    """
    Portfolio-VaR unter Berücksichtigung von Korrelationen.

    Returns:
        PortfolioVaRResult mit:
        - var: float
        - cvar: float
        - diversification_benefit: float
        - undiversified_var: float
    """
```

### 1.3 Konfiguration

```toml
# config/risk_limits.toml
# NOTE: Example config only. Production requires governance approval.

[var]
confidence_level = 0.95           # 95% VaR
method = "historical"             # historical | parametric
lookback_days = 252               # 1 Jahr
min_observations = 60             # Mindestens 60 Tage

[cvar]
enabled = false  # Example shows true; production requires governance
threshold_percent = 5.0           # Alarm bei >5% CVaR

[portfolio]
max_var_percent = 2.0             # Max 2% Portfolio-VaR
max_cvar_percent = 3.0            # Max 3% Portfolio-CVaR
rebalance_threshold = 0.5         # Rebalance bei 0.5% Abweichung

[alerts]
var_breach_action = "warn"        # warn | block | reduce
cvar_breach_action = "block"      # Strenger bei CVaR
```

### 1.4 Akzeptanzkriterien

- [ ] **AC-1.1:** `calculate_var()` liefert korrekte Werte für bekannte Verteilungen (Normalverteilung: analytisch prüfbar)
- [ ] **AC-1.2:** `calculate_cvar()` ≥ `calculate_var()` für alle Inputs
- [ ] **AC-1.3:** Portfolio-VaR zeigt Diversifikations-Effekt (Portfolio-VaR < Summe Einzel-VaRs)
- [ ] **AC-1.4:** Alle Funktionen werfen `InsufficientDataError` bei < 60 Datenpunkten
- [ ] **AC-1.5:** 100% Test-Coverage für `var_calculator.py`
- [ ] **AC-1.6:** Parametric VaR validiert gegen Historical VaR (Abweichung < 20%)

### 1.5 Risiken & Mitigations

| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|--------|-------------------|--------|------------|
| Fat Tails unterschätzt | Hoch | Hoch | CVaR als primäres Maß, Historical VaR bevorzugen |
| Korrelationsbruch in Krisen | Mittel | Hoch | Stress-Korrelationen in Phase 4 |
| Zu wenig Daten für Krypto | Mittel | Mittel | Min 60 Tage, Warnung bei < 252 |

---

## 📋 Phase 2: VaR Backtesting & Validation

**Dauer:** 5-7 Arbeitstage  
**Ziel:** Sicherstellen, dass VaR-Modelle korrekt kalibriert sind

### 2.1 Deliverables

```
src/risk/
├── backtesting/
│   ├── __init__.py
│   ├── kupiec_test.py             # Proportion of Failures Test
│   ├── christoffersen_test.py     # Independence Test
│   ├── traffic_light.py           # Basel Traffic Light System
│   └── var_backtest_runner.py     # Orchestrierung
└── reports/
    └── var_backtest_report.py     # HTML/JSON Report Generator

tests/risk/backtesting/
├── test_kupiec.py
├── test_christoffersen.py
└── test_traffic_light.py

scripts/risk/
└── run_var_backtest.py            # CLI für VaR Backtesting
```

### 2.2 Funktionen & Signaturen

```python
# src/risk/backtesting/kupiec_test.py

@dataclass
class KupiecTestResult:
    """Ergebnis des Kupiec Proportion of Failures Tests."""
    n_observations: int
    n_exceptions: int
    expected_exceptions: float
    exception_rate: float
    expected_rate: float
    lr_statistic: float           # Likelihood Ratio
    p_value: float
    passed: bool                  # p_value > 0.05
    confidence_level: float

def kupiec_pof_test(
    returns: pd.Series,
    var_series: pd.Series,
    confidence_level: float = 0.95,
) -> KupiecTestResult:
    """
    Kupiec Proportion of Failures Test.

    Nullhypothese: Tatsächliche Überschreitungsrate = Erwartete Rate

    Bei 95% VaR erwarten wir 5% Überschreitungen.
    Test prüft, ob beobachtete Rate signifikant abweicht.

    Args:
        returns: Realisierte Returns
        var_series: Vorhergesagte VaR-Werte (positiv = Verlust)
        confidence_level: VaR Konfidenzniveau

    Returns:
        KupiecTestResult mit Test-Statistiken

    Interpretation:
        - passed=True: Modell nicht verworfen (OK)
        - passed=False: Modell möglicherweise fehlkalibriert
    """

# src/risk/backtesting/traffic_light.py

@dataclass
class TrafficLightResult:
    """Basel Traffic Light System Ergebnis."""
    zone: Literal["green", "yellow", "red"]
    n_exceptions: int
    n_observations: int
    exception_rate: float
    multiplier: float             # Kapitalzuschlag
    recommendation: str

def basel_traffic_light(
    n_exceptions: int,
    n_observations: int = 250,    # Basel: 250 Handelstage
    confidence_level: float = 0.99,
) -> TrafficLightResult:
    """
    Basel Committee Traffic Light System.

    Zones (bei 99% VaR, 250 Tagen):
    - Green:  0-4 Exceptions  → Multiplier 3.0
    - Yellow: 5-9 Exceptions  → Multiplier 3.4-3.85
    - Red:    10+ Exceptions  → Multiplier 4.0, Modell überprüfen!
    """
```

### 2.3 Akzeptanzkriterien

- [ ] **AC-2.1:** Kupiec-Test korrekt implementiert (validiert gegen R/Python statsmodels)
- [ ] **AC-2.2:** Bei synthetischen Daten mit bekannter Verteilung: Test passed
- [ ] **AC-2.3:** Traffic Light System zeigt korrektes Zonenmapping
- [ ] **AC-2.4:** CLI-Script generiert HTML-Report mit Visualisierungen
- [ ] **AC-2.5:** Automatischer Alarm bei "Red Zone"
- [ ] **AC-2.6:** Integration mit MLflow (optional): Backtest-Metriken geloggt

### 2.4 Beispiel-Workflow

```bash
# VaR Backtesting für BTC/EUR
python scripts/risk/run_var_backtest.py \
  --symbol BTC/EUR \
  --start 2024-01-01 \
  --end 2024-12-31 \
  --confidence 0.95 \
  --output reports/var_backtest_btc_2024.html

# Erwartete Ausgabe:
# ══════════════════════════════════════════════════════════════
# VaR Backtest Report: BTC/EUR (2024)
# ══════════════════════════════════════════════════════════════
# Observations:     252 days
# VaR Confidence:   95%
# Method:           Historical
#
# RESULTS:
# ────────────────────────────────────────────────────────────────
# Exceptions:       14 (5.6%)
# Expected:         12.6 (5.0%)
#
# Kupiec POF Test:
#   LR Statistic:   0.42
#   P-Value:        0.52
#   Result:         ✅ PASSED (Modell nicht verworfen)
#
# Basel Traffic Light:
#   Zone:           🟢 GREEN
#   Multiplier:     3.0x
# ══════════════════════════════════════════════════════════════
```

---

## 📋 Phase 3: Component VaR & Attribution

**Dauer:** 5-7 Arbeitstage  
**Ziel:** Verstehen, WELCHE Positionen zum Portfolio-Risiko beitragen

### 3.1 Deliverables

```
src/risk/
├── attribution/
│   ├── __init__.py
│   ├── component_var.py           # Component VaR Berechnung
│   ├── marginal_var.py            # Marginal VaR
│   ├── incremental_var.py         # Incremental VaR
│   └── risk_decomposition.py      # Aggregierte Attribution
└── visualization/
    └── risk_attribution_chart.py  # Sunburst/Treemap Charts

tests/risk/attribution/
├── test_component_var.py
├── test_marginal_var.py
└── test_risk_decomposition.py

scripts/risk/
└── analyze_risk_attribution.py    # CLI für Risk Attribution
```

### 3.2 Konzepte

```
┌─────────────────────────────────────────────────────────────────┐
│                    RISK ATTRIBUTION KONZEPTE                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  MARGINAL VaR (MVaR)                                            │
│  ──────────────────                                             │
│  Wie ändert sich Portfolio-VaR bei 1€ mehr in Asset i?          │
│  MVaR_i = ∂VaR / ∂w_i                                           │
│  → Zeigt Sensitivität, nicht absoluten Beitrag                  │
│                                                                  │
│  COMPONENT VaR (CVaR)                                           │
│  ─────────────────────                                          │
│  Absoluter Beitrag von Asset i zum Portfolio-VaR                │
│  CVaR_i = w_i × MVaR_i                                          │
│  → Summe aller CVaR_i = Portfolio-VaR                           │
│  → Perfekt für Attribution!                                     │
│                                                                  │
│  INCREMENTAL VaR (IVaR)                                         │
│  ──────────────────────                                         │
│  Um wieviel sinkt VaR, wenn Asset i komplett entfernt wird?     │
│  IVaR_i = VaR_portfolio - VaR_portfolio_ohne_i                  │
│  → Zeigt Diversifikationseffekt von Asset i                     │
│                                                                  │
│  BEISPIEL:                                                       │
│  Portfolio: 60% BTC, 30% ETH, 10% LTC                           │
│  Portfolio-VaR: 5.2%                                            │
│                                                                  │
│  Component VaR:                                                  │
│  ┌─────────┬──────────┬────────────┐                            │
│  │ Asset   │ CVaR     │ % of Total │                            │
│  ├─────────┼──────────┼────────────┤                            │
│  │ BTC     │ 3.1%     │ 60%        │                            │
│  │ ETH     │ 1.8%     │ 35%        │                            │
│  │ LTC     │ 0.3%     │ 5%         │                            │
│  └─────────┴──────────┴────────────┘                            │
│  → BTC ist der Hauptrisikotreiber                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.3 Funktionen & Signaturen

```python
# src/risk/attribution/component_var.py

@dataclass
class ComponentVaRResult:
    """Component VaR Ergebnis pro Asset."""
    symbol: str
    weight: float
    marginal_var: float
    component_var: float
    percent_contribution: float

@dataclass
class RiskAttributionResult:
    """Komplette Risk Attribution."""
    portfolio_var: float
    portfolio_cvar: float
    components: list[ComponentVaRResult]
    diversification_ratio: float
    concentration_index: float  # Herfindahl-Index

def calculate_component_var(
    positions: dict[str, float],
    returns: pd.DataFrame,
    confidence_level: float = 0.95,
) -> RiskAttributionResult:
    """
    Berechnet Component VaR für alle Positionen.

    Args:
        positions: {symbol: market_value}
        returns: DataFrame mit Returns pro Asset
        confidence_level: VaR Konfidenzniveau

    Returns:
        RiskAttributionResult mit vollständiger Attribution

    Invariante:
        sum(component.component_var) == portfolio_var
    """

def calculate_marginal_var(
    positions: dict[str, float],
    returns: pd.DataFrame,
    confidence_level: float = 0.95,
    delta: float = 0.01,  # 1% Positionsänderung
) -> dict[str, float]:
    """
    Berechnet Marginal VaR per Finite-Differenzen.

    MVaR_i ≈ (VaR(w_i + δ) - VaR(w_i)) / δ
    """
```

### 3.4 Akzeptanzkriterien

- [ ] **AC-3.1:** `sum(component_var) == portfolio_var` (Invariante)
- [ ] **AC-3.2:** Marginal VaR korreliert mit Asset-Volatilität
- [ ] **AC-3.3:** Bei gleich gewichteten, unkorrelierten Assets: Component VaR proportional zu Gewichten
- [ ] **AC-3.4:** Visualisierung: Sunburst-Chart zeigt Risikobeiträge
- [ ] **AC-3.5:** Report identifiziert Top-3 Risikotreiber

---

## 📋 Phase 4: Stress Testing & Szenarien

**Dauer:** 5-7 Arbeitstage  
**Ziel:** Portfolioverhalten unter Extrembedingungen verstehen

### 4.1 Deliverables

```
src/risk/
├── stress/
│   ├── __init__.py
│   ├── scenario_engine.py         # Szenario-Simulation
│   ├── historical_scenarios.py    # Historische Krisen
│   ├── hypothetical_scenarios.py  # Was-wäre-wenn
│   └── reverse_stress_test.py     # Welches Szenario killt uns?
├── monte_carlo/
│   ├── __init__.py
│   ├── simulation.py              # MC Simulation Engine
│   ├── copulas.py                 # Abhängigkeitsmodellierung
│   └── fat_tails.py               # t-Verteilung, GEV
└── scenarios/
    ├── crypto_crash_2022.yaml     # Terra/Luna, FTX
    ├── covid_march_2020.yaml      # Corona-Crash
    ├── btc_halving_2024.yaml      # Halving-Volatilität
    └── custom_template.yaml       # User-definierte Szenarien

tests/risk/stress/
├── test_scenario_engine.py
├── test_historical_scenarios.py
└── test_monte_carlo.py

scripts/risk/
├── run_stress_test.py             # CLI Stress Testing
└── run_monte_carlo.py             # CLI Monte Carlo
```

### 4.2 Historische Szenarien (Krypto-fokussiert)

```yaml
# src/risk/scenarios/crypto_crash_2022.yaml

name: "Crypto Winter 2022 (Terra/Luna + FTX)"
description: |
  Kombination aus Terra/Luna Collapse (Mai 2022) und FTX Bankruptcy (Nov 2022).
  Einer der schlimmsten Bärenmärkte in Krypto-Geschichte.

period:
  start: "2022-04-01"
  end: "2022-12-31"

shocks:
  BTC/EUR:
    drawdown: -0.65      # -65% Drawdown
    volatility_mult: 3.0 # 3x normale Volatilität
  ETH/EUR:
    drawdown: -0.68
    volatility_mult: 3.5
  correlation_shock: 0.95  # Korrelationen → 1 in Krisen

liquidity:
  spread_multiplier: 5.0   # 5x normale Spreads
  slippage_multiplier: 3.0

triggers:
  - "Stablecoin de-peg (UST → 0)"
  - "Exchange bankruptcy (FTX)"
  - "Contagion (Genesis, BlockFi)"

expected_portfolio_impact:
  max_drawdown: -0.60      # Erwarte ~60% Drawdown
  recovery_days: 365       # ~1 Jahr Recovery

---
# src/risk/scenarios/flash_crash.yaml

name: "Flash Crash Scenario"
description: "Kurzfristiger Liquiditätskollaps (Minuten bis Stunden)"

shocks:
  all_assets:
    instant_drop: -0.30    # -30% in Minuten
    recovery_time: "4h"    # Erholung in 4 Stunden
    bid_ask_spread: 0.10   # 10% Spread während Crash

liquidity:
  order_book_depth: 0.1    # 90% Liquidität weg
  market_orders_fail: true # Market Orders scheitern
```

### 4.3 Monte Carlo Simulation

```python
# src/risk/monte_carlo/simulation.py

@dataclass
class MonteCarloConfig:
    """Konfiguration für Monte Carlo Simulation."""
    n_simulations: int = 10_000
    time_horizon_days: int = 252
    confidence_levels: list[float] = field(default_factory=lambda: [0.95, 0.99])
    distribution: Literal["normal", "t", "historical"] = "t"
    t_degrees_of_freedom: int = 5  # Fat Tails
    correlation_method: Literal["sample", "shrinkage", "dcc"] = "shrinkage"
    seed: int | None = 42  # Reproduzierbarkeit!

@dataclass
class MonteCarloResult:
    """Ergebnis der Monte Carlo Simulation."""
    simulated_returns: np.ndarray  # (n_sims, horizon)
    var_estimates: dict[float, float]  # {0.95: 0.05, 0.99: 0.12}
    cvar_estimates: dict[float, float]
    percentiles: dict[int, float]  # {1: -0.45, 5: -0.28, ...}
    max_drawdown_distribution: np.ndarray
    expected_shortfall: float
    probability_of_ruin: float  # P(total loss > X%)

def run_monte_carlo(
    positions: dict[str, float],
    returns: pd.DataFrame,
    config: MonteCarloConfig,
) -> MonteCarloResult:
    """
    Führt Monte Carlo Simulation durch.

    Schritte:
    1. Fit Verteilung an historische Returns
    2. Schätze Korrelationsmatrix (mit Shrinkage)
    3. Generiere n_simulations Pfade
    4. Berechne VaR/CVaR aus simulierter Verteilung
    5. Analysiere Tail-Risiken

    Wichtig: Seed setzen für Reproduzierbarkeit!
    """

def run_monte_carlo_with_stress(
    positions: dict[str, float],
    returns: pd.DataFrame,
    config: MonteCarloConfig,
    stress_scenarios: list[StressScenario],
    stress_probability: float = 0.05,  # 5% Wahrscheinlichkeit für Stress
) -> MonteCarloResult:
    """
    Monte Carlo mit eingestreuten Stress-Szenarien.

    In 5% der Simulationen: Wende Stress-Szenario an.
    → Bessere Tail-Modellierung als reine Normalverteilung.
    """
```

### 4.4 Akzeptanzkriterien

- [ ] **AC-4.1:** Mindestens 3 historische Krypto-Szenarien implementiert
- [ ] **AC-4.2:** Monte Carlo mit 10.000 Simulationen läuft in < 30 Sekunden
- [ ] **AC-4.3:** Fat-Tail-Verteilung (t-dist) zeigt höhere VaR als Normalverteilung
- [ ] **AC-4.4:** Stress-Test Report zeigt Portfolio-Impact pro Szenario
- [ ] **AC-4.5:** Reverse Stress Test identifiziert "Break-Point" Szenarien
- [ ] **AC-4.6:** Seed-basierte Reproduzierbarkeit: Gleicher Seed → Gleiches Ergebnis

---

## 📋 Phase 5: Defense-in-Depth Integration

**Dauer:** 3-5 Arbeitstage  
**Ziel:** 4-Layer-Architektur vollständig integriert und getestet

### 5.1 Defense-in-Depth Architektur

```
┌─────────────────────────────────────────────────────────────────┐
│                     DEFENSE-IN-DEPTH (4 LAYER)                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ LAYER 4: KILL SWITCH (Emergency)                          │  │
│  │ ─────────────────────────────────────────────────────────│  │
│  │ • Manuelle Notabschaltung                                 │  │
│  │ • Auto-Trigger bei extremen Verlusten                     │  │
│  │ • Alle Orders canceln, alle Positionen schließen          │  │
│  │ • Alarm an Operator (SMS/Push/Email)                      │  │
│  │ • KEINE Trades mehr bis manueller Reset                   │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              ▲                                   │
│                              │ Escalation                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ LAYER 3: PORTFOLIO RISK (Aggregate)                       │  │
│  │ ─────────────────────────────────────────────────────────│  │
│  │ • Portfolio-VaR < 2% (config-driven)                      │  │
│  │ • Portfolio-CVaR < 3%                                     │  │
│  │ • Max Drawdown < 15%                                      │  │
│  │ • Daily Loss Limit < 1%                                   │  │
│  │ • Concentration Limit (kein Asset > 40%)                  │  │
│  │ → Breach = Neue Trades blockiert, bestehende OK           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              ▲                                   │
│                              │ Escalation                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ LAYER 2: POSITION RISK (Per-Trade)                        │  │
│  │ ─────────────────────────────────────────────────────────│  │
│  │ • Max Position Size (% Portfolio)                         │  │
│  │ • Stop-Loss mandatory (max 5% vom Entry)                  │  │
│  │ • Take-Profit optional aber empfohlen                     │  │
│  │ • Position-Level VaR Check                                │  │
│  │ → Breach = Order rejected, Log + Alarm                    │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              ▲                                   │
│                              │ Escalation                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ LAYER 1: PRE-TRADE VALIDATION (Entry Gate)                │  │
│  │ ─────────────────────────────────────────────────────────│  │
│  │ • Order-Syntax prüfen (Symbol, Size, Side)                │  │
│  │ • Balance-Check (genug Cash?)                             │  │
│  │ • Min Order Size (Kraken: 0.0001 BTC)                     │  │
│  │ • Whitelist-Check (nur erlaubte Pairs)                    │  │
│  │ • Rate Limit Check                                        │  │
│  │ → Breach = Order rejected, Log                            │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ═══════════════════════════════════════════════════════════════│
│                     JEDER LAYER KANN UNABHÄNGIG BLOCKEN          │
│  ═══════════════════════════════════════════════════════════════│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Deliverables

```
src/risk/
├── layers/
│   ├── __init__.py
│   ├── pre_trade_validator.py     # Layer 1
│   ├── position_risk_guard.py     # Layer 2
│   ├── portfolio_risk_guard.py    # Layer 3
│   └── kill_switch.py             # Layer 4
├── engine/
│   ├── __init__.py
│   └── risk_engine.py             # Orchestriert alle Layer
└── alerts/
    ├── __init__.py
    ├── alert_manager.py           # Zentrale Alert-Logik
    └── channels/
        ├── log_channel.py         # Logging (immer aktiv)
        ├── console_channel.py     # Terminal-Ausgabe
        └── webhook_channel.py     # Für später: Slack/Discord

config/
└── defense_in_depth.toml          # Zentrale Defense Config

tests/risk/layers/
├── test_pre_trade_validator.py
├── test_position_risk_guard.py
├── test_portfolio_risk_guard.py
├── test_kill_switch.py
└── test_risk_engine_integration.py
```

### 5.3 Risk Engine API

```python
# src/risk/engine/risk_engine.py

class RiskEngine:
    """
    Zentrale Risk-Engine: Orchestriert alle 4 Defense Layer.

    Jede Order muss ALLE Layer passieren.
    Ein Veto von IRGENDEINEM Layer = Order rejected.
    """

    def __init__(self, config: RiskConfig):
        self.config = config
        self.layer1 = PreTradeValidator(config)
        self.layer2 = PositionRiskGuard(config)
        self.layer3 = PortfolioRiskGuard(config)
        self.layer4 = KillSwitch(config)
        self.alert_manager = AlertManager(config)

        self._kill_switch_active = False

    def validate_order(
        self,
        order: Order,
        portfolio: Portfolio,
    ) -> RiskValidationResult:
        """
        Validiert Order gegen alle 4 Layer.

        Returns:
            RiskValidationResult:
                - approved: bool
                - rejected_by: Optional[str]  # Layer-Name
                - reason: Optional[str]
                - warnings: list[str]
                - risk_metrics: RiskMetrics
        """
        # Layer 4 Check (Kill Switch) - VOR allem anderen!
        if self._kill_switch_active:
            return RiskValidationResult(
                approved=False,
                rejected_by="kill_switch",
                reason="Kill Switch aktiv - alle Trades gestoppt",
            )

        # Layer 1: Pre-Trade
        l1_result = self.layer1.validate(order)
        if not l1_result.passed:
            return self._reject(order, "pre_trade", l1_result.reason)

        # Layer 2: Position Risk
        l2_result = self.layer2.validate(order, portfolio)
        if not l2_result.passed:
            return self._reject(order, "position_risk", l2_result.reason)

        # Layer 3: Portfolio Risk
        l3_result = self.layer3.validate(order, portfolio)
        if not l3_result.passed:
            return self._reject(order, "portfolio_risk", l3_result.reason)

        # Alle Layer bestanden
        return RiskValidationResult(
            approved=True,
            risk_metrics=l3_result.metrics,
            warnings=l1_result.warnings + l2_result.warnings + l3_result.warnings,
        )

    def trigger_kill_switch(
        self,
        reason: str,
        triggered_by: Literal["manual", "auto"] = "manual",
    ) -> None:
        """
        Aktiviert Kill Switch.

        Effekte:
        1. Alle neuen Orders blockiert
        2. Alert an alle Channels
        3. (Optional) Offene Positionen schließen

        Reset NUR über: reset_kill_switch() mit Passwort/2FA
        """
        self._kill_switch_active = True
        self.alert_manager.send_critical(
            f"🚨 KILL SWITCH AKTIVIERT\n"
            f"Grund: {reason}\n"
            f"Trigger: {triggered_by}\n"
            f"Zeit: {datetime.utcnow().isoformat()}"
        )

    def reset_kill_switch(self, confirmation_code: str) -> bool:
        """Reset Kill Switch - erfordert Bestätigung."""
        if confirmation_code == self.config.kill_switch_reset_code:
            self._kill_switch_active = False
            self.alert_manager.send_info("Kill Switch deaktiviert")
            return True
        return False
```

### 5.4 Konfiguration

```toml
# config/defense_in_depth.toml
# NOTE: Example config only. All layers require governance approval for production.

[layer1_pre_trade]
enabled = false  # Example; requires governance
allowed_pairs = ["BTC/EUR", "ETH/EUR", "LTC/EUR"]
min_order_value_eur = 10.0
max_order_value_eur = 10000.0
rate_limit_orders_per_minute = 10

[layer2_position]
enabled = false  # Example; requires governance
max_position_pct = 25.0           # Max 25% in einer Position
stop_loss_mandatory = true
max_stop_loss_pct = 5.0           # Stop max 5% vom Entry
position_var_limit_pct = 3.0      # Max 3% Position-VaR

[layer3_portfolio]
enabled = false  # Example; requires governance
max_portfolio_var_pct = 2.0
max_portfolio_cvar_pct = 3.0
max_drawdown_pct = 15.0
daily_loss_limit_pct = 1.0
max_concentration_pct = 40.0      # Kein Asset > 40%

[layer4_kill_switch]
enabled = false  # Example; requires governance
auto_trigger_drawdown_pct = 20.0  # Auto-Kill bei -20%
auto_trigger_daily_loss_pct = 3.0 # Auto-Kill bei -3% am Tag
reset_code = "PEAK_RESET_2025"    # Für Reset erforderlich
close_positions_on_trigger = false # true = Notliquidation

[alerts]
log_all = true
console_warnings = true
critical_webhook_url = ""         # Optional: Slack/Discord
```

### 5.5 Akzeptanzkriterien

- [ ] **AC-5.1:** Jeder Layer kann unabhängig Orders blocken
- [ ] **AC-5.2:** Kill Switch blockiert ALLE Orders sofort
- [ ] **AC-5.3:** Kill Switch erfordert Confirmation Code für Reset
- [ ] **AC-5.4:** Auto-Kill triggert bei Überschreitung der Limits
- [ ] **AC-5.5:** Alle Rejections werden geloggt mit Grund
- [ ] **AC-5.6:** Integration Test: Order durchläuft alle 4 Layer
- [ ] **AC-5.7:** Performance: validate_order() < 10ms

---

## 📊 Gesamt-Akzeptanzkriterien (Risk Layer Complete)

### Funktional

- [ ] **F-1:** VaR/CVaR berechnet für Einzel-Assets und Portfolio
- [ ] **F-2:** VaR-Modell validiert durch Kupiec-Test
- [ ] **F-3:** Component VaR identifiziert Risikotreiber
- [ ] **F-4:** Stress Tests zeigen Portfolio-Impact
- [ ] **F-5:** Monte Carlo mit Fat Tails implementiert
- [ ] **F-6:** Defense-in-Depth mit 4 Layern aktiv

### Qualität

- [ ] **Q-1:** 100% Test-Coverage für kritische Pfade
- [ ] **Q-2:** Alle Funktionen mit Typannotationen
- [ ] **Q-3:** Docstrings für alle öffentlichen APIs
- [ ] **Q-4:** Methodik-Dokumentation vorhanden

### Sicherheit

- [ ] **S-1:** Kein Live-Trading ohne Risk Layer aktiv
- [ ] **S-2:** Kill Switch funktioniert zuverlässig
- [ ] **S-3:** Alle Limits config-driven, nicht hardcoded
- [ ] **S-4:** Audit-Log für alle Risk-Entscheidungen

### Performance

- [ ] **P-1:** VaR-Berechnung < 100ms für 10 Assets
- [ ] **P-2:** Monte Carlo (10k sims) < 30s
- [ ] **P-3:** validate_order() < 10ms

---

## 🚀 Meilensteine & Timeline

```
┌──────────────────────────────────────────────────────────────────┐
│                       RISK LAYER TIMELINE                        │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Woche 1        Woche 2        Woche 3        Woche 4    Woche 5 │
│  ┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐   ┌──────┐ │
│  │Phase 1 │    │Phase 2 │    │Phase 3 │    │Phase 4 │   │ P5   │ │
│  │VaR Core│───▶│Backtest│───▶│Comp VaR│───▶│Stress  │──▶│D-i-D │ │
│  └────────┘    └────────┘    └────────┘    └────────┘   └──────┘ │
│                                                                   │
│  Deliverables:                                                    │
│  ────────────────────────────────────────────────────────────────│
│  W1: var_calculator.py, portfolio_risk.py, Tests                 │
│  W2: kupiec_test.py, traffic_light.py, var_backtest_runner.py    │
│  W3: component_var.py, marginal_var.py, attribution charts       │
│  W4: scenario_engine.py, monte_carlo.py, 3 Krypto-Szenarien      │
│  W5: risk_engine.py, alle 4 Layer, Integration Tests             │
│                                                                   │
│  Milestone: 🏁 RISK LAYER 100% COMPLETE                          │
│  ═══════════════════════════════════════════════════════════════ │
│                                                                   │
│  Danach: Shadow Trading Prep (16 Wochen)                         │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## ⚠️ Risiken & Abhängigkeiten

### Risiken

| Risiko | Wahrsch. | Impact | Mitigation |
|--------|----------|--------|------------|
| Zu wenig historische Krypto-Daten | Mittel | Hoch | Mehr Asset-Pairs, Bootstrap-Methoden |
| Korrelationen brechen in Krisen | Hoch | Hoch | Stress-Korrelationen, Copulas |
| Monte Carlo zu langsam | Niedrig | Mittel | Numba/Vectorization, Cloud-Compute |
| Kill Switch False Positives | Mittel | Mittel | Konservative Thresholds, Hysterese |

### Abhängigkeiten

| Phase | Abhängigkeit | Kritikalität |
|-------|--------------|--------------|
| Phase 1 | Data Layer (OHLCV Returns) | 🔴 Blocker |
| Phase 2 | Phase 1 (VaR-Werte für Backtest) | 🔴 Blocker |
| Phase 3 | Phase 1 (Portfolio-VaR) | 🟡 Soft |
| Phase 4 | Historische Krypto-Daten (min. 3 Jahre) | 🟡 Soft |
| Phase 5 | Alle vorherigen Phasen | 🔴 Blocker |

---

## 📚 Referenzen

**Value-at-Risk:**
- Jorion, P. (2006). *Value at Risk: The New Benchmark*
- Hull, J. (2018). *Risk Management and Financial Institutions*

**Backtesting:**
- Kupiec, P. (1995). *Techniques for Verifying the Accuracy of Risk Measurement Models*
- Basel Committee (2019). *Minimum capital requirements for market risk*

**Monte Carlo:**
- Glasserman, P. (2003). *Monte Carlo Methods in Financial Engineering*

**Krypto-spezifisch:**
- Bouri, E. et al. (2017). *On the hedge and safe haven properties of Bitcoin*

---

## ✅ Nächste Schritte

1. **Heute:** Phase 1 Feature Branch erstellen
   ```bash
   git checkout -b feature/risk-layer-phase1
   ```

2. **Diese Woche:** Phase 1 VaR Core implementieren
   - var_calculator.py
   - portfolio_risk.py
   - Tests schreiben
   - Docs schreiben

3. **Review Gate:** Nach jeder Phase PR + Code Review

4. **Final Gate:** Risk Layer 100% → Shadow Trading freigeben

---

**Status:** ⬜ TODO → 🔴 IN PROGRESS → 🟡 IN REVIEW → ✅ COMPLETE

**Verantwortlich:** Peak_Risk (CRO)  
**Reviewed by:** Lead Engineer (Boss der Bosse)

---

*Dieses Dokument ist die verbindliche Roadmap für den Risk Layer. Änderungen erfordern Review durch Lead Engineer.*
