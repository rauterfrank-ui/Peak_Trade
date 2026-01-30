# Peak_Trade Research Golden Paths

## Übersicht

Dieses Dokument definiert **3 vollständige End-to-End-Workflows** (Golden Paths) für typische Research-Aufgaben in Peak_Trade. Jeder Golden Path führt von Anfang bis Ende durch alle relevanten Schritte mit konkreten Befehlen.

**Stand:** Phase 81 (v1.0)

---

## Golden Path 1: Neue Strategie entwickeln

**Ziel:** Eine neue Strategie von der Idee bis zum profilierten, getierden Eintrag im System.

### Übersicht

```
Idee → Code → Test → Sweep → Profile → Tiering → Portfolio-Preset
```

### Schritt 1: Strategie-Klasse erstellen

Erstelle eine neue Datei unter `src/strategies/`:

```python
# src/strategies/my_new_strategy.py
"""
Meine neue Strategie - Kurze Beschreibung
"""
from src.strategies.base import BaseStrategy
import pandas as pd

class MyNewStrategy(BaseStrategy):
    """
    Meine neue Trading-Strategie.

    Beispiel: RSI + MA Kombination
    """

    def __init__(
        self,
        rsi_period: int = 14,
        ma_period: int = 50,
        rsi_oversold: float = 30.0,
        rsi_overbought: float = 70.0,
    ):
        super().__init__()
        self.rsi_period = rsi_period
        self.ma_period = ma_period
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generiert Trading-Signale."""
        # RSI berechnen
        delta = data['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(self.rsi_period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        # MA berechnen
        ma = data['close'].rolling(self.ma_period).mean()

        # Signale
        signals = pd.Series(0, index=data.index)
        signals[(rsi < self.rsi_oversold) & (data['close'] > ma)] = 1  # Long
        signals[(rsi > self.rsi_overbought) & (data['close'] < ma)] = -1  # Short

        return signals
```

### Schritt 2: In Registry eintragen

```python
# src/strategies/registry.py - Eintrag hinzufügen

from src.strategies.registry import StrategySpec
from src.strategies.my_new_strategy import MyNewStrategy

# In _STRATEGY_REGISTRY hinzufügen
_STRATEGY_REGISTRY["my_new_strategy"] = StrategySpec(
    key="my_new_strategy",
    cls=MyNewStrategy,
    config_section="strategy.my_new_strategy",
    description="Meine neue Strategie",
)
```

### Schritt 3: Basis-Test schreiben

```python
# tests/test_strategy_my_new_strategy.py
import pytest
import pandas as pd
import numpy as np
from src.strategies.my_new_strategy import MyNewStrategy

class TestMyNewStrategy:
    def test_init(self):
        """Strategie kann initialisiert werden."""
        strategy = MyNewStrategy()
        assert strategy.rsi_period == 14

    def test_generate_signals(self):
        """Signale werden korrekt generiert."""
        strategy = MyNewStrategy()

        # Dummy-Daten
        dates = pd.date_range('2024-01-01', periods=100, freq='1h')
        data = pd.DataFrame({
            'open': np.random.randn(100).cumsum() + 100,
            'high': np.random.randn(100).cumsum() + 101,
            'low': np.random.randn(100).cumsum() + 99,
            'close': np.random.randn(100).cumsum() + 100,
            'volume': np.random.randint(1000, 10000, 100),
        }, index=dates)

        signals = strategy.generate_signals(data)

        assert isinstance(signals, pd.Series)
        assert len(signals) == len(data)
        assert set(signals.dropna().unique()).issubset({-1, 0, 1})
```

```bash
# Test ausführen
python3 -m pytest tests/test_strategy_my_new_strategy.py -v
```

### Schritt 4: Sweep-Definition erstellen

```toml
# config/sweeps/my_new_strategy_basic.toml
[sweep]
name = "my_new_strategy_basic"
strategy = "my_new_strategy"
description = "Basis-Sweep für meine neue Strategie"

[sweep.parameters]
rsi_period = [10, 14, 21]
ma_period = [20, 50, 100]
rsi_oversold = [25.0, 30.0, 35.0]
rsi_overbought = [65.0, 70.0, 75.0]

[sweep.symbols]
symbols = ["BTCUSDT", "ETHUSDT"]
timeframe = "1h"

[sweep.backtest]
initial_capital = 10000.0
commission = 0.001
```

### Schritt 5: Sweep ausführen

```bash
# Sweep starten
python3 scripts/research_cli.py sweep \
    --sweep-name my_new_strategy_basic \
    --config config/config.toml

# Erwartete Ausgabe:
# Starting sweep: my_new_strategy_basic
# Running 81 parameter combinations...
# Progress: [========================================] 100%
# Sweep completed. Results saved to reports/experiments/
```

### Schritt 6: Sweep-Report generieren

```bash
# Report erstellen
python3 scripts/research_cli.py report \
    --sweep-name my_new_strategy_basic \
    --format both \
    --with-plots

# Ausgabe:
# Generating report for sweep: my_new_strategy_basic
# - Markdown report: reports/sweeps/my_new_strategy_basic_report_<timestamp>.md
# - HTML report: reports/sweeps/my_new_strategy_basic_report_<timestamp>.html
```

### Schritt 7: Top-N auswählen und Robustness testen

```bash
# Walk-Forward Testing
python3 scripts/research_cli.py walkforward \
    --sweep-name my_new_strategy_basic \
    --top-n 5 \
    --train-window 90d \
    --test-window 30d

# Monte-Carlo Analyse
python3 scripts/research_cli.py montecarlo \
    --sweep-name my_new_strategy_basic \
    --config config/config.toml \
    --top-n 3 \
    --num-runs 500

# Stress-Tests
python3 scripts/research_cli.py stress \
    --sweep-name my_new_strategy_basic \
    --config config/config.toml \
    --top-n 3 \
    --scenarios single_crash_bar vol_spike \
    --severity 0.2
```

### Schritt 8: StrategyProfile generieren

```bash
# Profil erstellen
python3 scripts/research_cli.py strategy-profile \
    --strategy-id my_new_strategy \
    --output-format both \
    --with-regime \
    --with-montecarlo \
    --mc-num-runs 100 \
    --with-stress \
    --stress-scenarios single_crash_bar vol_spike

# Ausgabe:
# Strategy Profile: my_new_strategy
# - Sharpe: 1.45
# - Max Drawdown: -12.3%
# - Total Return: 87.5%
# Profile saved to: reports/strategy_profiles/my_new_strategy_profile_v1.json
```

### Schritt 9: Tiering zuweisen

Basierend auf den Profil-Metriken, füge einen Eintrag in `config/strategy_tiering.toml` hinzu:

```toml
# config/strategy_tiering.toml - Neuer Eintrag

[strategy.my_new_strategy]
tier = "aux"  # oder "core" bei Sharpe >= 1.5, MaxDD >= -15%
recommended_config_id = "my_new_strategy_v1"
allow_live = false
notes = "RSI+MA Kombination, gute Performance in Trending-Märkten. Sharpe 1.45, MaxDD -12.3%"
```

**Tiering-Entscheidung:**
- `tier = "core"` wenn Sharpe ≥ 1.5 UND MaxDD ≥ -15%
- `tier = "aux"` wenn Sharpe ≥ 1.0 UND MaxDD ≥ -20%
- `tier = "legacy"` sonst

### Schritt 10: In Portfolio-Preset aufnehmen (optional)

Wenn die Strategie als `aux` oder `core` klassifiziert wurde:

```bash
# Validieren dass Tiering korrekt ist
python3 -c "
from src.experiments.portfolio_presets import get_strategy_tier
print(f'Tier: {get_strategy_tier(\"my_new_strategy\")}')
"
```

---

## Golden Path 2: Strategie-Parameter optimieren

**Ziel:** Bestehende Strategie tunen und Robustheit validieren.

### Übersicht

```
Strategie auswählen → Sweep anpassen → Top-N → Robustness → Update Profile
```

### Schritt 1: Bestehende Strategie auswählen

```bash
# Verfügbare Strategien anzeigen
python3 -c "
from src.strategies.registry import get_available_strategy_keys
for name in sorted(get_available_strategy_keys()):
    print(f'  - {name}')
"

# Tiering prüfen
python3 -c "
from src.experiments.portfolio_presets import get_all_tiered_strategies
for tier, strategies in get_all_tiered_strategies().items():
    print(f'{tier}: {strategies}')
"
```

### Schritt 2: Sweep-Definition anpassen

Bearbeite oder erstelle eine Sweep-Definition:

```bash
# Bestehende Sweeps anzeigen
ls config/sweeps/

# Beispiel: rsi_reversion_basic.toml anpassen
cat config/sweeps/rsi_reversion_basic.toml
```

```toml
# config/sweeps/rsi_reversion_tuning_v2.toml
[sweep]
name = "rsi_reversion_tuning_v2"
strategy = "rsi_reversion"
description = "Erweiterter Parameter-Sweep für RSI Reversion"

[sweep.parameters]
# Erweiterte Parameter-Bereiche
rsi_period = [7, 10, 14, 21, 28]
oversold_threshold = [20, 25, 30, 35]
overbought_threshold = [65, 70, 75, 80]
lookback = [10, 20, 30, 50]

[sweep.symbols]
symbols = ["BTCUSDT", "ETHUSDT"]
timeframe = "1h"

[sweep.backtest]
initial_capital = 10000.0
commission = 0.001
```

### Schritt 3: Vollständige Pipeline ausführen

```bash
# End-to-End Pipeline mit allen Robustness-Tests
python3 scripts/research_cli.py pipeline \
    --sweep-name rsi_reversion_tuning_v2 \
    --config config/config.toml \
    --format both \
    --with-plots \
    --top-n 5 \
    --run-walkforward \
    --walkforward-train-window 90d \
    --walkforward-test-window 30d \
    --run-montecarlo \
    --mc-num-runs 500 \
    --run-stress-tests \
    --stress-scenarios single_crash_bar vol_spike drawdown_extension

# Erwartete Ausgabe:
# === RESEARCH PIPELINE ===
# Step 1/5: Running sweep...
# Step 2/5: Generating report...
# Step 3/5: Walk-forward testing (top 5)...
# Step 4/5: Monte-Carlo analysis (top 5)...
# Step 5/5: Stress tests (top 5)...
#
# Pipeline completed!
# Results: reports/sweeps/rsi_reversion_tuning_v2/
```

### Schritt 4: Ergebnisse analysieren

```bash
# Report öffnen
open reports/sweeps/rsi_reversion_tuning_v2/report.html

# Oder Markdown anzeigen
cat reports/sweeps/rsi_reversion_tuning_v2/report.md
```

**Wichtige Metriken prüfen:**
- Sharpe Ratio (Ziel: ≥ 1.5 für core)
- Max Drawdown (Ziel: ≥ -15% für core)
- Walk-Forward Stability (OOS vs IS Performance)
- Monte-Carlo p5 Percentile (sollte positiv sein)
- Stress-Test Min Return (akzeptables Worst-Case)

### Schritt 5: Profil aktualisieren

```bash
# Neues Profil generieren
python3 scripts/research_cli.py strategy-profile \
    --strategy-id rsi_reversion \
    --output-format both \
    --with-regime \
    --with-montecarlo

# Vergleich mit altem Profil
diff reports/strategy_profiles/rsi_reversion_profile_v1.json \
     reports/strategy_profiles/rsi_reversion_profile_v2.json
```

### Schritt 6: Tiering ggf. anpassen

Wenn die Metriken sich signifikant verbessert haben:

```toml
# config/strategy_tiering.toml - Update
[strategy.rsi_reversion]
tier = "core"  # Bleibt core oder Upgrade von aux
recommended_config_id = "rsi_reversion_v2_core"  # Neue empfohlene Config
allow_live = false
notes = "V2 Tuning: Sharpe 1.72 (+0.2), MaxDD -11.5% (+3.5pp). Robust über Regime."
```

---

## Golden Path 3: Portfolio mit Tiering bauen

**Ziel:** Ein robustes Portfolio aus getierden Strategien konstruieren.

### Übersicht

```
Tier-Filter → Strategien auswählen → Gewichte definieren → Preset erstellen → Robustness → Shadow-Ready
```

### Schritt 1: Verfügbare Core/Aux-Strategien identifizieren

```bash
# Tiering-Status anzeigen
python3 -c "
from src.experiments.portfolio_presets import (
    get_all_tiered_strategies,
    get_strategies_by_tier,
)

all_tiered = get_all_tiered_strategies()

print('=== CORE (für Hauptportfolio) ===')
for s in all_tiered['core']:
    print(f'  - {s}')

print()
print('=== AUX (als Ergänzung) ===')
for s in all_tiered['aux']:
    print(f'  - {s}')

print()
print('=== LEGACY (nicht verwenden) ===')
for s in all_tiered['legacy']:
    print(f'  - {s}')
"

# Erwartete Ausgabe:
# === CORE (für Hauptportfolio) ===
#   - rsi_reversion
#   - ma_crossover
#   - bollinger_bands
#
# === AUX (als Ergänzung) ===
#   - breakout
#   - macd
#   - momentum_1h
#   - ...
#
# === LEGACY (nicht verwenden) ===
#   - breakout_donchian
#   - my_strategy
#   - vol_breakout
```

### Schritt 2: Portfolio-Strategie definieren

Wähle Strategien basierend auf:
- **Diversifikation:** Mix aus Trend + Mean-Reversion
- **Korrelation:** Niedrige Korrelation zwischen Komponenten
- **Tiering:** Nur core (konservativ) oder core+aux (aggressiv)

**Beispiel: Core-Only Portfolio (Konservativ)**

```python
# Strategien und Gewichte
strategies = ["rsi_reversion", "ma_crossover", "bollinger_bands"]
weights = [0.40, 0.35, 0.25]  # Summe = 1.0
```

**Beispiel: Core+Aux Portfolio (Aggressiv)**

```python
# Strategien und Gewichte
strategies = [
    "rsi_reversion",   # Core - Mean Reversion
    "ma_crossover",    # Core - Trend
    "bollinger_bands", # Core - Vol-based MR
    "breakout",        # Aux - Trend Breakout
    "macd",            # Aux - Momentum
]
weights = [0.25, 0.20, 0.15, 0.20, 0.20]  # Summe = 1.0
```

### Schritt 3: Portfolio-Preset erstellen

```toml
# config/portfolio_presets/my_custom_portfolio.toml
[portfolio_recipes.my_custom_portfolio]
id = "my_custom_portfolio"
portfolio_name = "Mein Custom Portfolio"
description = "Core-basiertes Portfolio mit Style-Diversifikation"

# Nur Core-Strategien
strategies = [
    "rsi_reversion",
    "ma_crossover",
    "bollinger_bands",
]

# Gewichtung
weights = [0.40, 0.35, 0.25]

# Robustness-Tests
run_montecarlo = true
mc_num_runs = 200

run_stress_tests = true
stress_scenarios = ["single_crash_bar", "vol_spike", "drawdown_extension"]
stress_severity = 0.5

format = "both"
risk_profile = "moderate"
tags = ["core", "custom", "tiered"]
```

### Schritt 4: Tiering-Compliance validieren

```bash
# Validierung
python3 -c "
from src.experiments.portfolio_presets import validate_preset_tiering_compliance
from src.experiments.portfolio_recipes import load_portfolio_recipes
from pathlib import Path

recipes = load_portfolio_recipes(Path('config/portfolio_presets/my_custom_portfolio.toml'))
result = validate_preset_tiering_compliance(
    'my_custom_portfolio',
    allowed_tiers=['core'],  # Nur Core erlaubt
    recipe=recipes['my_custom_portfolio'],
)
print(result)
"

# Erwartete Ausgabe:
# Tiering Compliance: my_custom_portfolio
# Status: ✅ COMPLIANT
# Allowed Tiers: core
# Strategies Checked: 3
```

### Schritt 5: Portfolio-Robustness testen

```bash
# Portfolio-Level Robustness
python3 scripts/research_cli.py portfolio \
    --config config/config.toml \
    --portfolio-preset my_custom_portfolio \
    --format both \
    --use-dummy-data

# Erwartete Ausgabe:
# === PORTFOLIO ROBUSTNESS ===
# Portfolio: Mein Custom Portfolio
# Components: 3 strategies
#
# Running Monte-Carlo (200 runs)...
# Running Stress Tests (3 scenarios)...
#
# Results:
# - Sharpe: 1.65 (baseline)
# - MC p5/p50/p95: 0.82 / 1.58 / 2.45
# - Stress Min/Avg: -8.2% / -4.1%
#
# Report: reports/portfolio_robustness/my_custom_portfolio/portfolio_robustness_report.html
```

### Schritt 6: Go/No-Go Entscheidung

**Kriterien für "Go":**
- [ ] Baseline Sharpe ≥ 1.2
- [ ] MC p5 Percentile > 0 (oder akzeptabler negativer Wert)
- [ ] Stress-Test Min Return > -20%
- [ ] Walk-Forward OOS/IS Ratio > 0.7
- [ ] Keine einzelne Strategie dominiert (max 50% Gewicht)

**Bei "Go":** Portfolio ist bereit für Shadow/Testnet

```bash
# Portfolio-Snapshot + Risk-Check (Phase 48, PaperBroker-Fallback)
python3 scripts/preview_live_portfolio.py \
    --config config/config.toml \
    --no-risk

# Ausgabe:
# === Live Portfolio Snapshot (...) UTC ===
# Positions: ...
# Totals: ...
```

---

## Schnellreferenz: CLI-Befehle

### Sweep & Report

```bash
# Sweep starten
python3 scripts/research_cli.py sweep --sweep-name NAME --config config/config.toml

# Report generieren
python3 scripts/research_cli.py report --sweep-name NAME --format both --with-plots

# Top-N promoten
python3 scripts/research_cli.py promote --sweep-name NAME --top-n 5
```

### Robustness-Tests

```bash
# Walk-Forward
python3 scripts/research_cli.py walkforward --sweep-name NAME --top-n 3 --train-window 90d --test-window 30d

# Monte-Carlo
python3 scripts/research_cli.py montecarlo --sweep-name NAME --config config/config.toml --top-n 3 --num-runs 500

# Stress-Tests
python3 scripts/research_cli.py stress --sweep-name NAME --config config/config.toml --top-n 3 --scenarios single_crash_bar vol_spike --severity 0.2
```

### Portfolio

```bash
# Portfolio-Robustness
python3 scripts/research_cli.py portfolio --config config/config.toml --portfolio-preset NAME --format both --use-dummy-data

# Portfolio-Snapshot (Phase 48)
python3 scripts/preview_live_portfolio.py --config config/config.toml --no-risk
```

### Profiling & Tiering

```bash
# Strategy-Profile generieren
python3 scripts/research_cli.py strategy-profile --strategy-id NAME --output-format both --with-regime --with-montecarlo --with-stress

# Tiering-Status anzeigen
python3 -c "from src.experiments.portfolio_presets import get_all_tiered_strategies; print(get_all_tiered_strategies())"

# Tiering-Compliance prüfen
python3 -c "from src.experiments.portfolio_presets import validate_preset_tiering_compliance; ..."
```

### Full Pipeline

```bash
# End-to-End Pipeline
python3 scripts/research_cli.py pipeline \
    --sweep-name NAME \
    --config config/config.toml \
    --format both \
    --with-plots \
    --top-n 5 \
    --run-walkforward \
    --walkforward-train-window 90d \
    --walkforward-test-window 30d \
    --run-montecarlo \
    --mc-num-runs 500 \
    --run-stress-tests \
    --stress-scenarios single_crash_bar vol_spike
```

---

## Weiterführende Dokumentation

- [Phase 80: Tiered Portfolio Presets](PHASE_80_TIERED_PORTFOLIO_PRESETS.md)
- [Playbook: Research → Live](PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md)
- [Portfolio Recipes & Presets](PORTFOLIO_RECIPES_AND_PRESETS.md)
- [Strategy Research Playbook](STRATEGY_RESEARCH_PLAYBOOK.md)
- [Phase 41B: Strategy Robustness & Tiering](PHASE_41B_STRATEGY_ROBUSTNESS_AND_TIERING.md)

---

**Phase 81 - Peak_Trade Research Golden Paths v1.0**
