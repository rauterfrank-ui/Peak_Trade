# Phase 82: Research QA & Szenario-Library v1.0

## Übersicht

**Status:** ✅ Implementiert
**Phase:** 82
**Ziel:** Standardisierte Test-Szenarien für Research-QA und Regressions-Erkennung

Phase 82 führt eine **Szenario-Library** ein, die typische Marktbedingungen simuliert und als Basis für E2E-Tests und Regressions-Checks dient.

---

## Motivation

Ohne standardisierte Szenarien ist es schwierig:
- Strategie-Änderungen auf Regressionen zu prüfen
- Verschiedene Strategien fair zu vergleichen
- Erwartetes Verhalten unter bestimmten Marktbedingungen zu dokumentieren

**Lösung:** `config/scenarios/` mit strukturierten TOML-Dateien, die:
- Marktbedingungen definieren
- Erwartete Strategie-Performance spezifizieren
- Automatisierte Regressions-Checks ermöglichen

---

## Szenario-Library

### Verzeichnisstruktur

```
config/scenarios/
├── flash_crash.toml        # Stress: Schneller, harter Drawdown
├── sideways_low_vol.toml   # Regime: Seitwärtsmarkt, niedrige Vol
└── trend_regime.toml       # Regime: Starker Aufwärtstrend
```

### Szenario-Kategorien

| Kategorie | Beschreibung | Beispiele |
|-----------|--------------|-----------|
| **stress** | Extreme Marktbedingungen | Flash Crash, High Volatility Spike |
| **regime** | Typische Marktphasen | Trending, Sideways, Range-bound |
| **edge_case** | Randfall-Szenarien | Gap-Openings, Illiquidität |
| **historical** | Historische Events | 2020 Corona Crash, 2017 Crypto Bubble |

---

## Szenario-Struktur

Jedes Szenario hat folgende Abschnitte:

### `[scenario]` - Basis-Info

```toml
[scenario]
name = "flash_crash"
description = "Schneller, harter Drawdown mit teilweiser Erholung"
category = "stress"
severity = 0.8  # 0.0 (mild) bis 1.0 (extrem)
```

### `[scenario.market_conditions]` - Marktbedingungen

```toml
[scenario.market_conditions]
volatility = "extreme"          # low, medium, high, extreme
trend = "sharp_decline"         # up, down, sideways, sharp_decline, sharp_rise
duration_bars = 50
```

### `[scenario.test_expectations]` - Erwartungen

```toml
[scenario.test_expectations]
baseline_max_portfolio_drawdown = -30.0  # Erwarteter Drawdown
baseline_min_sharpe = -1.0
allow_negative_returns = true
max_acceptable_drawdown = -50.0          # Absolutes Limit

# Optional: Erwartete Gewinner/Verlierer
expected_winners = ["trend_following", "ma_crossover"]
expected_losers = ["rsi_reversion"]
```

### `[scenario.applicable_strategies]` - Relevante Strategien

```toml
[scenario.applicable_strategies]
primary = ["trend_following", "ma_crossover"]
secondary = ["bollinger_bands", "macd"]
not_applicable = []
```

### `[scenario.notes]` - Dokumentation

```toml
[scenario.notes]
description = """
Flash Crash Szenario basiert auf historischen Events...
Testet:
- Stop-Loss-Mechanismen
- Slippage-Auswirkungen
- Erholungsfähigkeit
"""
```

---

## Standard-Szenarien

### 1. Flash Crash (`flash_crash.toml`)

**Kategorie:** stress
**Severity:** 0.8 (hoch)

Simuliert einen schnellen, harten Drawdown:
- Max Drawdown: -25% in 10 Bars
- Volatilität: Extrem
- Erholung: 60% innerhalb von 40 Bars

**Erwartungen:**
- Portfolio-Drawdown: ≤ -30%
- Akzeptabler Drawdown: ≤ -50%
- Negative Returns: Erlaubt

**Relevante Strategien:** Trend-Following, Breakout (primär)

### 2. Sideways Low Vol (`sideways_low_vol.toml`)

**Kategorie:** regime
**Severity:** 0.4 (moderat)

Simuliert einen langen Seitwärtsmarkt:
- Dauer: 200 Bars
- Range: ±2.5%
- Volatilität: Niedrig

**Erwartungen:**
- Portfolio-Drawdown: ≤ -10%
- Akzeptabler Drawdown: ≤ -20%
- Gewinner: Mean-Reversion-Strategien
- Verlierer: Trend-Following-Strategien

**Relevante Strategien:** RSI Reversion, Bollinger Bands (primär)

### 3. Trend Regime (`trend_regime.toml`)

**Kategorie:** regime
**Severity:** 0.3 (niedrig)

Simuliert einen sauberen Aufwärtstrend:
- Gesamtbewegung: +40%
- Dauer: 150 Bars
- Volatilität: Medium
- Pullbacks: 5% Tiefe

**Erwartungen:**
- Portfolio-Drawdown: ≤ -15%
- Akzeptabler Drawdown: ≤ -25%
- Negative Returns: NICHT erlaubt
- Gewinner: Trend-Following-Strategien
- Verlierer: Mean-Reversion (gegen den Trend)

**Relevante Strategien:** Trend Following, MA Crossover, Breakout (primär)

---

## E2E-Tests

### Test-Datei: `tests/test_research_e2e_scenarios.py`

```bash
# Alle Szenario-Tests ausführen
.venv/bin/pytest tests/test_research_e2e_scenarios.py -v

# Nur Struktur-Tests
.venv/bin/pytest tests/test_research_e2e_scenarios.py::TestScenarioConfigStructure -v

# Nur Flash-Crash-Tests
.venv/bin/pytest tests/test_research_e2e_scenarios.py::TestFlashCrashScenario -v
```

### Test-Kategorien

| Testklasse | Fokus |
|------------|-------|
| `TestScenarioDirectory` | Verzeichnis & Datei-Existenz |
| `TestScenarioConfigStructure` | TOML-Struktur & Pflichtfelder |
| `TestFlashCrashScenario` | Flash-Crash-spezifische Checks |
| `TestSidewaysLowVolScenario` | Sideways-spezifische Checks |
| `TestTrendRegimeScenario` | Trend-spezifische Checks |
| `TestScenarioLoader` | Laden & Parsing |
| `TestScenarioE2EWorkflow` | End-to-End-Workflow |
| `TestScenarioRegressionDetection` | Regressions-Checks |
| `TestScenarioIntegration` | Integration mit Strategy-Registry |

---

## Verwendung

### Szenario-Library vs. Stress-Tests (wichtig)

- **Scenario-Library (`config&#47;scenarios&#47;*.toml`)**: dient **Research-QA / E2E-Tests / Regressions-Checks** (Phase 82). Sie beschreibt Marktbedingungen + Erwartungen, wird aber **nicht** 1:1 als CLI-Parameter an die Stress-Test-Runner übergeben.
- **Stress-Tests (Phase 46/47, `src/experiments/stress_tests.py`)**: sind **deterministische Return-Transformationen** und verwenden die Scenario-Typen:
  - `single_crash_bar`, `vol_spike`, `drawdown_extension`, `gap_down_open`

### Stress-Tests in der Research-CLI nutzen (Phase 46)

```bash
# Stress-Tests (deterministische Crash-Szenarien)
python3 scripts/research_cli.py stress \
    --sweep-name my_strategy_sweep \
    --config config/config.toml \
    --scenarios single_crash_bar vol_spike drawdown_extension \
    --severity 0.2
```

### Szenario-Erwartungen in Code abrufen

```python
import tomllib
from pathlib import Path

def load_scenario(name: str) -> dict:
    path = Path("config/scenarios") / f"{name}.toml"
    with open(path, "rb") as fp:
        return tomllib.load(fp)

# Flash Crash laden
scenario = load_scenario("flash_crash")
max_dd = scenario["scenario"]["test_expectations"]["max_acceptable_drawdown"]
print(f"Max acceptable drawdown: {max_dd}%")
```

### Regressions-Check implementieren

```python
def check_regression(strategy_results: dict, scenario: dict) -> bool:
    """Prüft, ob Strategie-Ergebnisse die Szenario-Erwartungen erfüllen."""
    expectations = scenario["scenario"]["test_expectations"]

    actual_dd = strategy_results.get("max_drawdown", 0)
    max_acceptable = expectations["max_acceptable_drawdown"]

    if actual_dd < max_acceptable:
        print(f"❌ REGRESSION: Drawdown {actual_dd}% exceeds limit {max_acceptable}%")
        return False

    print(f"✅ PASSED: Drawdown {actual_dd}% within limit {max_acceptable}%")
    return True
```

---

## Eigene Szenarien erstellen

### Vorlage

```toml
# config/scenarios/my_new_scenario.toml

[scenario]
name = "my_new_scenario"
description = "Beschreibung des Szenarios"
category = "regime"  # stress, regime, edge_case, historical
severity = 0.5       # 0.0 bis 1.0

[scenario.market_conditions]
volatility = "medium"
trend = "up"
duration_bars = 100

[scenario.test_expectations]
baseline_max_portfolio_drawdown = -15.0
baseline_min_sharpe = 0.5
allow_negative_returns = true
max_acceptable_drawdown = -25.0

[scenario.applicable_strategies]
primary = ["strategy1", "strategy2"]
secondary = ["strategy3"]
not_applicable = []

[scenario.notes]
description = """
Ausführliche Beschreibung des Szenarios:
- Was wird simuliert?
- Welche historischen Events sind Vorbild?
- Was wird getestet?
"""
```

---

## Verbindung zu anderen Phasen

| Phase | Verbindung |
|-------|------------|
| **Phase 41B** | Strategy Tiering definiert Strategie-Klassifizierung |
| **Phase 53** | Stress-Tests nutzen Szenarien |
| **Phase 80** | Portfolio-Presets werden gegen Szenarien getestet |
| **Phase 81** | Golden Paths referenzieren Szenarien |
| **Phase 83** | Live-Gates nutzen Szenario-basierte Regressionsprüfung |

---

## Definition of Done

- [x] Mindestens 3 Szenarien definiert (flash_crash, sideways_low_vol, trend_regime)
- [x] E2E-Tests für Szenario-Struktur und -Inhalte
- [x] Szenarien dokumentieren Erwartungen für Regressions-Checks
- [x] Integration mit Strategy-Registry geprüft
- [x] Dokumentation erstellt

---

## Nächste Schritte

→ **Phase 83:** Live-Gates nutzen Szenario-basierte Regressionsprüfung
→ **Future:** Weitere Szenarien (historical, edge_case) hinzufügen
