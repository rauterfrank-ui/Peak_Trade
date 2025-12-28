# Peak_Trade Risk Layer – Phasen-Roadmap

**Erstellt:** 28. Dezember 2025  
**Ziel:** Risk Layer von 60% → 100%  
**Geschätzte Dauer:** 4-5 Wochen (20-25 Arbeitstage)  
**Verantwortlich:** Peak_Risk (CRO)

---

## 📋 Übersicht: 5 Phasen

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ROADMAP: RISK LAYER COMPLETION                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Phase 1 ──► Phase 2 ──► Phase 3 ──► Phase 4 ──► Phase 5                   │
│  VaR Core    VaR Test   Attribution  Stress      Emergency                  │
│  (5-6d)      (3-4d)     (3d)         (4-5d)      (4d)                       │
│                                                                             │
│  60% ──────► 75% ──────► 85% ───────► 92% ──────► 100% ✅                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔷 Phase 1: VaR/CVaR Core Implementation

**Dauer:** 5-6 Arbeitstage  
**Fortschritt:** 60% → 75%  
**Start:** Sofort  
**Priorität:** 🔴 KRITISCH

### Ziel
Vollständige Value-at-Risk Berechnung für Portfolio-Risiko-Aussagen.

### Deliverables

| Datei | Beschreibung | Aufwand |
|-------|--------------|---------|
| `src/risk/var/__init__.py` | Modul-Exports | 0.5h |
| `src/risk/var/historical_var.py` | Quantile-basierter VaR | 1d |
| `src/risk/var/parametric_var.py` | Varianz-Kovarianz VaR | 1.5d |
| `src/risk/var/cvar.py` | Expected Shortfall / CVaR | 0.5d |
| `src/risk/var/covariance.py` | Ledoit-Wolf Shrinkage | 0.5d |
| `src/risk/var/config.py` | VaR-Config aus TOML | 0.5d |
| `tests/risk/var/test_historical_var.py` | Unit Tests (10+) | 0.5d |
| `tests/risk/var/test_parametric_var.py` | Unit Tests (10+) | 0.5d |
| `tests/risk/var/test_cvar.py` | Unit Tests (5+) | 0.5d |

### Technische Details

**Historical VaR:**
```python
def calculate_historical_var(
    returns: pd.Series,
    confidence_level: float = 0.95,
    window: int = 252
) -> float:
    """
    Berechnet VaR als Quantile der historischen Returns.

    Args:
        returns: Tägliche Returns
        confidence_level: 0.95 oder 0.99
        window: Rolling Window (252 = 1 Jahr)

    Returns:
        VaR als positiver Wert (Verlustgröße)
    """
```

**Parametric VaR:**
```python
def calculate_parametric_var(
    returns: pd.DataFrame,
    weights: np.ndarray,
    confidence_level: float = 0.95,
    use_ledoit_wolf: bool = True
) -> float:
    """
    Varianz-Kovarianz VaR mit optionalem Shrinkage.
    """
```

**CVaR / Expected Shortfall:**
```python
def calculate_cvar(
    returns: pd.Series,
    confidence_level: float = 0.95
) -> float:
    """
    Durchschnittlicher Verlust jenseits des VaR.
    """
```

### Acceptance Criteria

- [ ] Historical VaR berechnet 95%/99% korrekt
- [ ] Parametric VaR mit Ledoit-Wolf funktioniert
- [ ] CVaR gibt Expected Shortfall aus
- [ ] 25+ Unit Tests alle grün
- [ ] Benchmark: VaR-Berechnung < 100ms für 1000 Tage

### Config (TOML)

```toml
[risk.var]
enabled = true
method = "historical"  # "historical" | "parametric" | "monte_carlo"
confidence_level = 0.95
window_days = 252
use_ledoit_wolf = true

[risk.var.limits]
max_portfolio_var = 0.05     # 5% max daily VaR
max_position_var = 0.02      # 2% max per position
var_breach_action = "alert"  # "alert" | "block" | "reduce"
```

### Go/No-Go Kriterien

| Kriterium | Mindestanforderung |
|-----------|-------------------|
| Unit Test Coverage | ≥ 80% |
| VaR-Berechnung funktioniert | 3 Methoden (hist/param/cvar) |
| Performance | < 100ms für 1000 Tage |
| Documentation | Docstrings vollständig |

### Befehle zum Start

```bash
cd ~/Peak_Trade
git checkout -b feature/risk-layer-phase1-var

# Struktur anlegen
mkdir -p src/risk/var
mkdir -p tests/risk/var

# Dateien erstellen
touch src/risk/var/__init__.py
touch src/risk/var/historical_var.py
touch src/risk/var/parametric_var.py
touch src/risk/var/cvar.py
touch src/risk/var/covariance.py
touch src/risk/var/config.py

# Tests
touch tests/risk/var/__init__.py
touch tests/risk/var/test_historical_var.py
touch tests/risk/var/test_parametric_var.py
touch tests/risk/var/test_cvar.py
```

---

## 🔷 Phase 2: VaR Backtesting & Validation

**Dauer:** 3-4 Arbeitstage  
**Fortschritt:** 75% → 85%  
**Start:** Nach Phase 1  
**Priorität:** 🔴 KRITISCH

### Ziel
Validierung der VaR-Modelle mit statistischen Tests – ohne Validation kein Vertrauen!

### Deliverables

| Datei | Beschreibung | Aufwand |
|-------|--------------|---------|
| `src/risk/validation/__init__.py` | Modul-Exports | 0.5h |
| `src/risk/validation/kupiec_pof.py` | Proportion of Failures Test | 1d |
| `src/risk/validation/traffic_light.py` | Basel Traffic Light System | 0.5d |
| `src/risk/validation/backtest_runner.py` | VaR vs. Actual Vergleich | 1d |
| `src/risk/validation/breach_analysis.py` | Breach-Statistiken | 0.5d |
| `tests/risk/validation/test_kupiec.py` | Unit Tests (10+) | 0.5d |
| `tests/risk/validation/test_traffic_light.py` | Unit Tests (5+) | 0.5d |

### Technische Details

**Kupiec POF Test:**
```python
def kupiec_pof_test(
    var_breaches: int,
    total_observations: int,
    confidence_level: float = 0.95
) -> KupiecResult:
    """
    Proportion of Failures Test für VaR-Validierung.

    H0: VaR-Modell ist korrekt kalibriert
    H1: VaR-Modell ist nicht korrekt

    Returns:
        KupiecResult mit p_value, test_statistic, is_valid
    """
```

**Basel Traffic Light:**
```python
def basel_traffic_light(
    breaches: int,
    observations: int = 250
) -> TrafficLightResult:
    """
    Basel Traffic Light für regulatorische Compliance.

    - GRÜN: 0-4 Breaches (akzeptabel)
    - GELB: 5-9 Breaches (Überprüfung)
    - ROT: 10+ Breaches (Modell versagt)
    """
```

**VaR Backtest Runner:**
```python
def run_var_backtest(
    returns: pd.Series,
    var_series: pd.Series,
    window: int = 250
) -> BacktestResult:
    """
    Vergleicht prognostizierten VaR mit realisierten Verlusten.

    Returns:
        BacktestResult mit breach_count, breach_dates, kupiec_result
    """
```

### Acceptance Criteria

- [ ] Kupiec Test statistisch korrekt (Chi-Square)
- [ ] Traffic Light gibt korrekte Farbe aus
- [ ] Backtest Runner findet alle Breaches
- [ ] 15+ Unit Tests alle grün
- [ ] Report-Output als JSON/Markdown

### Go/No-Go Kriterien

| Kriterium | Mindestanforderung |
|-----------|-------------------|
| Kupiec implementiert | Chi-Square mit p-value |
| Traffic Light funktioniert | Grün/Gelb/Rot korrekt |
| Integration mit Phase 1 | VaR → Validation Pipeline |
| Test Coverage | ≥ 80% |

### Befehle zum Start

```bash
cd ~/Peak_Trade
git checkout -b feature/risk-layer-phase2-validation

mkdir -p src/risk/validation
mkdir -p tests/risk/validation

touch src/risk/validation/__init__.py
touch src/risk/validation/kupiec_pof.py
touch src/risk/validation/traffic_light.py
touch src/risk/validation/backtest_runner.py
touch src/risk/validation/breach_analysis.py

touch tests/risk/validation/__init__.py
touch tests/risk/validation/test_kupiec.py
touch tests/risk/validation/test_traffic_light.py
```

---

## 🔷 Phase 3: Component VaR & Risk Attribution

**Dauer:** 3 Arbeitstage  
**Fortschritt:** 85% → 92%  
**Start:** Nach Phase 2  
**Priorität:** 🟡 WICHTIG

### Ziel
Verstehen, welche Position wie viel zum Gesamtrisiko beiträgt → Optimierungsgrundlage.

### Deliverables

| Datei | Beschreibung | Aufwand |
|-------|--------------|---------|
| `src/risk/attribution/__init__.py` | Modul-Exports | 0.5h |
| `src/risk/attribution/marginal_var.py` | Marginaler VaR | 1d |
| `src/risk/attribution/component_var.py` | Component VaR | 1d |
| `src/risk/attribution/contribution.py` | Prozentuale Beiträge | 0.5d |
| `tests/risk/attribution/test_marginal_var.py` | Unit Tests (5+) | 0.25d |
| `tests/risk/attribution/test_component_var.py` | Unit Tests (5+) | 0.25d |

### Technische Details

**Marginal VaR:**
```python
def calculate_marginal_var(
    portfolio_var: float,
    weights: np.ndarray,
    covariance_matrix: np.ndarray
) -> np.ndarray:
    """
    Marginaler VaR = ∂VaR/∂w_i

    Wie viel ändert sich Portfolio-VaR bei kleiner Gewichtsänderung?
    """
```

**Component VaR:**
```python
def calculate_component_var(
    marginal_var: np.ndarray,
    weights: np.ndarray
) -> np.ndarray:
    """
    Component VaR = w_i × Marginal VaR_i

    Summe aller Component VaR = Portfolio VaR
    """
```

**Contribution Report:**
```python
def generate_risk_contribution_report(
    positions: list[Position],
    portfolio_var: float
) -> RiskContributionReport:
    """
    Report mit:
    - Position Name
    - Gewicht
    - Component VaR
    - % Contribution zum Gesamtrisiko
    """
```

### Acceptance Criteria

- [ ] Marginal VaR mathematisch korrekt
- [ ] Component VaR summiert zu Portfolio VaR
- [ ] Contribution % summiert zu 100%
- [ ] 10+ Unit Tests alle grün
- [ ] Report als JSON/Markdown/CLI

### Go/No-Go Kriterien

| Kriterium | Mindestanforderung |
|-----------|-------------------|
| Math korrekt | ΣComponentVaR = PortfolioVaR |
| Integration | Nutzt VaR aus Phase 1 |
| Test Coverage | ≥ 80% |

---

## 🔷 Phase 4: Stress Testing & Monte Carlo

**Dauer:** 4-5 Arbeitstage  
**Fortschritt:** 92% → 97%  
**Start:** Nach Phase 3  
**Priorität:** 🔴 KRITISCH

### Ziel
Krypto-spezifische Extremszenarien simulieren – "Was passiert bei einem FTX-Kollaps?"

### Deliverables

| Datei | Beschreibung | Aufwand |
|-------|--------------|---------|
| `src/risk/stress/__init__.py` | Modul-Exports | 0.5h |
| `src/risk/stress/monte_carlo.py` | MC Simulation Engine | 2d |
| `src/risk/stress/scenarios.py` | 5+ Historische Szenarien | 1.5d |
| `src/risk/stress/scenario_runner.py` | Szenario-Ausführung | 0.5d |
| `src/risk/stress/report.py` | Stress Test Report | 0.5d |
| `tests/risk/stress/test_monte_carlo.py` | Unit Tests (10+) | 0.5d |
| `tests/risk/stress/test_scenarios.py` | Unit Tests (5+) | 0.5d |

### Technische Details

**Monte Carlo Engine:**
```python
def run_monte_carlo_simulation(
    returns: pd.DataFrame,
    weights: np.ndarray,
    n_simulations: int = 10_000,
    time_horizon: int = 10
) -> MonteCarloResult:
    """
    Korrelierte Return-Simulation mit Cholesky-Decomposition.

    Returns:
        - Simulated portfolio values
        - VaR at various confidence levels
        - CVaR / Expected Shortfall
        - Worst-case scenarios
    """
```

**Historische Szenarien:**
```python
CRYPTO_STRESS_SCENARIOS = {
    "covid_crash_2020": {
        "name": "COVID Crash März 2020",
        "btc_return": -0.50,  # -50%
        "eth_return": -0.60,  # -60%
        "duration_days": 2,
        "description": "Globaler Markt-Crash wegen COVID-19"
    },
    "china_ban_2021": {
        "name": "China Mining Ban Mai 2021",
        "btc_return": -0.55,
        "eth_return": -0.60,
        "duration_days": 30,
        "description": "China verbietet Krypto-Mining"
    },
    "luna_collapse_2022": {
        "name": "Terra/Luna Collapse Mai 2022",
        "btc_return": -0.30,
        "eth_return": -0.40,
        "duration_days": 7,
        "description": "Algorithmischer Stablecoin kollabiert"
    },
    "ftx_collapse_2022": {
        "name": "FTX Collapse November 2022",
        "btc_return": -0.25,
        "eth_return": -0.30,
        "duration_days": 2,
        "description": "Zweitgrößte Exchange geht bankrott"
    },
    "flash_crash_generic": {
        "name": "Flash Crash (generisch)",
        "btc_return": -0.30,
        "eth_return": -0.35,
        "duration_days": 0.04,  # ~1 Stunde
        "description": "Schneller Markt-Crash mit Recovery"
    }
}
```

**Szenario Runner:**
```python
def run_stress_test(
    portfolio: Portfolio,
    scenario: StressScenario
) -> StressTestResult:
    """
    Wendet Szenario auf Portfolio an und berechnet:
    - Portfolio-Verlust in €
    - % Drawdown
    - Margin Call Risk
    - Liquidation Risk
    """
```

### Acceptance Criteria

- [ ] Monte Carlo mit 10.000 Iterationen < 5s
- [ ] 5 historische Szenarien implementiert
- [ ] Cholesky Decomposition für Korrelation
- [ ] Stress Test Report als HTML/JSON
- [ ] 15+ Unit Tests alle grün

### Go/No-Go Kriterien

| Kriterium | Mindestanforderung |
|-----------|-------------------|
| Monte Carlo funktioniert | 10k Iterationen |
| Szenarien | 5+ historisch validiert |
| Performance | < 5s für 10k Simulationen |
| Report | Visuell verständlich |

---

## 🔷 Phase 5: Emergency Controls & Kill Switch

**Dauer:** 4 Arbeitstage  
**Fortschritt:** 97% → 100%  
**Start:** Nach Phase 4  
**Priorität:** 🔴 KRITISCH

### Ziel
Letzte Verteidigungslinie – automatischer und manueller Notfall-Stop.

### Deliverables

| Datei | Beschreibung | Aufwand |
|-------|--------------|---------|
| `src/risk/emergency/__init__.py` | Modul-Exports | 0.5h |
| `src/risk/emergency/kill_switch.py` | Auto/Manual Kill Switch | 1d |
| `src/risk/emergency/circuit_breaker.py` | Flash Crash Protection | 1d |
| `src/risk/emergency/notifications.py` | Alert System | 0.5d |
| `src/risk/emergency/audit_trail.py` | Vollständiges Audit Log | 0.5d |
| `src/risk/emergency/health_monitor.py` | System Health Check | 0.5d |
| `tests/risk/emergency/test_kill_switch.py` | Unit Tests (10+) | 0.5d |

### Technische Details

**Kill Switch:**
```python
class KillSwitch:
    """
    Zentrale Notfall-Steuerung.

    States:
        - ACTIVE: Trading erlaubt
        - TRIGGERED: Automatisch ausgelöst (Limit erreicht)
        - MANUAL_STOP: Manuell vom Operator gestoppt
        - COOLDOWN: Nach Trigger, wartet auf Reset
    """

    def trigger_auto(self, reason: str) -> None:
        """Automatischer Trigger bei Limit-Verletzung."""

    def trigger_manual(self, operator: str, reason: str) -> None:
        """Manueller Trigger durch Operator."""

    def reset(self, operator: str, confirmation_code: str) -> None:
        """Reset nur mit Bestätigungscode."""

    def is_trading_allowed(self) -> bool:
        """Prüft ob Trading erlaubt ist."""
```

**Circuit Breaker:**
```python
class CircuitBreaker:
    """
    Flash Crash Protection.

    Trigger:
        - Preis fällt > X% in Y Minuten
        - Volatilität > Z% annualisiert
        - Spread > W% (Liquiditätskrise)

    Aktion:
        - Pausiert alle neuen Orders
        - Prüft bestehende Positionen
        - Sendet Alert
        - Wartet auf manuelle Freigabe oder Timeout
    """
```

**Notification System:**
```python
def send_alert(
    alert_type: AlertType,
    message: str,
    severity: Severity,
    data: dict
) -> None:
    """
    Multi-Channel Alerting.

    Channels:
        - Console (immer)
        - Log File (immer)
        - Webhook (optional)
        - Email (optional, später)
    """
```

**Audit Trail:**
```python
def log_risk_decision(
    decision_type: str,
    decision_outcome: str,
    risk_metrics: dict,
    context: dict
) -> None:
    """
    Vollständiges Audit Log im JSONL Format.

    Pflichtfelder:
        - timestamp (ISO 8601)
        - decision_id (UUID)
        - decision_type
        - decision_outcome
        - risk_metrics (VaR, CVaR, etc.)
        - context (Position, Order, etc.)
    """
```

### Config (TOML)

```toml
[risk.emergency]
enabled = true

[risk.emergency.kill_switch]
# Automatische Trigger
daily_loss_limit = 0.05           # 5% Tagesverlust → Kill Switch
weekly_loss_limit = 0.10          # 10% Wochenverlust → Kill Switch
max_drawdown_trigger = 0.15       # 15% Drawdown → Kill Switch
var_breach_count_trigger = 3      # 3 VaR-Breaches → Kill Switch

# Cooldown
cooldown_hours = 24               # Wartezeit nach Trigger
require_manual_reset = true       # Manueller Reset erforderlich

[risk.emergency.circuit_breaker]
enabled = true
price_drop_threshold = 0.10       # 10% Drop in ...
price_drop_window_minutes = 15    # ... 15 Minuten
volatility_threshold = 2.0        # 200% annualisierte Vola
spread_threshold = 0.05           # 5% Spread

[risk.emergency.notifications]
console = true
log_file = true
webhook_url = ""                  # Optional
webhook_on_severity = ["HIGH", "CRITICAL"]
```

### Acceptance Criteria

- [ ] Kill Switch trigert bei Limit-Verletzung
- [ ] Manual Override funktioniert
- [ ] Circuit Breaker erkennt Flash Crash
- [ ] Notifications werden gesendet
- [ ] Audit Trail vollständig (JSONL)
- [ ] 10+ Unit Tests alle grün

### Go/No-Go Kriterien

| Kriterium | Mindestanforderung |
|-----------|-------------------|
| Kill Switch | Auto + Manual |
| Circuit Breaker | Preis + Vola Trigger |
| Latenz | < 100ms für Kill Switch |
| Audit Trail | JSONL, vollständig |
| Test Coverage | ≥ 80% |

---

## 📊 Gesamt-Timeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  WOCHE 1                    │  WOCHE 2                                      │
│  ───────────────────────────│───────────────────────────────────────────    │
│  Phase 1: VaR/CVaR Core     │  Phase 2: VaR Backtesting                     │
│  • Historical VaR           │  • Kupiec POF Test                            │
│  • Parametric VaR           │  • Basel Traffic Light                        │
│  • CVaR (ES)                │  • Backtest Runner                            │
│  • Ledoit-Wolf Covariance   │  • Breach Analysis                            │
│  • Unit Tests (25+)         │  • Unit Tests (15+)                           │
│                             │                                               │
│  ▸ 60% → 75%                │  ▸ 75% → 85%                                  │
├─────────────────────────────┼───────────────────────────────────────────────┤
│  WOCHE 3                    │  WOCHE 4                                      │
│  ───────────────────────────│───────────────────────────────────────────    │
│  Phase 3: Attribution       │  Phase 4: Stress Testing                      │
│  • Marginal VaR             │  • Monte Carlo Engine (10k)                   │
│  • Component VaR            │  • 5 Historische Szenarien                    │
│  • Contribution %           │  • Szenario Runner                            │
│  • Unit Tests (10+)         │  • Stress Test Report                         │
│                             │  • Unit Tests (15+)                           │
│  ▸ 85% → 92%                │  ▸ 92% → 97%                                  │
├─────────────────────────────┴───────────────────────────────────────────────┤
│  WOCHE 5                                                                    │
│  ───────────────────────────────────────────────────────────────────────    │
│  Phase 5: Emergency Controls                                                │
│  • Kill Switch (Auto/Manual)                                                │
│  • Circuit Breaker                                                          │
│  • Notification System                                                      │
│  • Audit Trail (JSONL)                                                      │
│  • Health Monitor                                                           │
│  • Integration Tests                                                        │
│                                                                             │
│  ▸ 97% → 100% ✅                                                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## ✅ Checkliste pro Phase

### Phase 1: VaR/CVaR Core
- [ ] `historical_var.py` implementiert
- [ ] `parametric_var.py` implementiert
- [ ] `cvar.py` implementiert
- [ ] `covariance.py` (Ledoit-Wolf)
- [ ] Config in TOML integriert
- [ ] 25+ Unit Tests grün
- [ ] Code Review
- [ ] Merge to main

### Phase 2: VaR Backtesting
- [ ] `kupiec_pof.py` implementiert
- [ ] `traffic_light.py` implementiert
- [ ] `backtest_runner.py` implementiert
- [ ] `breach_analysis.py` implementiert
- [ ] 15+ Unit Tests grün
- [ ] Code Review
- [ ] Merge to main

### Phase 3: Component VaR
- [ ] `marginal_var.py` implementiert
- [ ] `component_var.py` implementiert
- [ ] `contribution.py` implementiert
- [ ] 10+ Unit Tests grün
- [ ] Code Review
- [ ] Merge to main

### Phase 4: Stress Testing
- [ ] `monte_carlo.py` implementiert
- [ ] `scenarios.py` (5+ Szenarien)
- [ ] `scenario_runner.py` implementiert
- [ ] `report.py` implementiert
- [ ] 15+ Unit Tests grün
- [ ] Performance Benchmark (< 5s)
- [ ] Code Review
- [ ] Merge to main

### Phase 5: Emergency Controls
- [ ] `kill_switch.py` implementiert
- [ ] `circuit_breaker.py` implementiert
- [ ] `notifications.py` implementiert
- [ ] `audit_trail.py` implementiert
- [ ] `health_monitor.py` implementiert
- [ ] 10+ Unit Tests grün
- [ ] Integration Tests
- [ ] Code Review
- [ ] Merge to main
- [ ] **RISK LAYER 100% ✅**

---

## 🎯 Meilensteine & Gates

| Meilenstein | Datum (Ziel) | Gate-Kriterien |
|-------------|--------------|----------------|
| M1: VaR Core Done | Woche 1 Ende | VaR berechnet, Tests grün |
| M2: VaR Validated | Woche 2 Ende | Kupiec + Traffic Light OK |
| M3: Attribution Done | Woche 3 Ende | Component VaR summiert korrekt |
| M4: Stress Tests Done | Woche 4 Ende | 5 Szenarien, MC < 5s |
| M5: Emergency Ready | Woche 5 Ende | Kill Switch getestet |
| **RISK LAYER v1.0** | Woche 5 Ende | **100%, alle Tests grün** |

---

## ⚠️ Risiken & Mitigationen

| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|--------|-------------------|--------|------------|
| scipy fehlt | Niedrig | Hoch | numpy-only Fallback |
| Covariance singulär | Mittel | Mittel | Ledoit-Wolf mandatory |
| MC zu langsam | Mittel | Mittel | Vectorization, numba |
| Kill Switch Bugs | Mittel | KRITISCH | Extensive Testing |
| Integration Konflikte | Niedrig | Mittel | Feature Branches |

---

## 📚 Referenzen

- **VaR Methoden:** Hull, J.C. (2018). Risk Management and Financial Institutions
- **Kupiec Test:** Kupiec, P. (1995). Techniques for Verifying the Accuracy of Risk Management Models
- **Ledoit-Wolf:** Ledoit, O. & Wolf, M. (2004). A Well-Conditioned Estimator for Large-Dimensional Covariance Matrices
- **Basel Traffic Light:** Basel Committee on Banking Supervision (1996)

---

## 🚀 Nächster Schritt

**Jetzt Phase 1 starten:**

```bash
cd ~/Peak_Trade
git checkout -b feature/risk-layer-phase1-var
mkdir -p src/risk/var tests/risk/var
```

---

**Erstellt:** 28. Dezember 2025  
**Version:** 1.0  
**Status:** READY FOR IMPLEMENTATION
