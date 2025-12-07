# Phase 80: Tiered Portfolio Presets v1.0

## Übersicht

**Status:** ✅ Implementiert
**Phase:** 80
**Ziel:** Integration des Tiering-Systems (core/aux/legacy) in Portfolio-Presets

Phase 80 verbindet das in Phase 41B eingeführte Strategy-Tiering mit der Portfolio-Konstruktion. Standard-Presets verwenden nun nur `core`-Strategien; `aux`-Strategien werden nur explizit hinzugefügt; `legacy`-Strategien erscheinen nie automatisch in Presets.

---

## Motivation

Das Tiering-System klassifiziert Strategien nach ihrer Robustheit und Eignung:

| Tier | Kriterien | Verwendung |
|------|-----------|------------|
| **core** | Sharpe ≥ 1.5, MaxDD ≥ -15%, robust über Regime | Hauptportfolio, Standard-Presets |
| **aux** | Sharpe ≥ 1.0, MaxDD ≥ -20%, spezifische Stärken | Ergänzend, explizit aktiviert |
| **legacy** | Sharpe < 1.0 oder MaxDD < -20% oder ersetzt | Nur Vergleichszwecke, nie automatisch |

**Problem vor Phase 80:** Portfolio-Presets verwendeten Strategien ohne Tiering-Filterung. Legacy-Strategien konnten versehentlich in Produktions-Portfolios landen.

**Lösung:** Tiering-aware Portfolio-Presets mit automatischer Validierung.

---

## Neue Komponenten

### 1. Modul: `src/experiments/portfolio_presets.py`

Neues Modul für Tiering-aware Portfolio-Konstruktion:

```python
from src.experiments.portfolio_presets import (
    get_strategies_by_tier,
    get_tiering_aware_strategies,
    validate_preset_tiering_compliance,
    load_tiered_preset,
)
```

#### Kernfunktionen

| Funktion | Beschreibung |
|----------|--------------|
| `get_strategies_by_tier(tier)` | Gibt alle Strategien eines Tiers zurück |
| `get_tiering_aware_strategies(include_tiers, exclude_tiers)` | Flexible Tier-Filterung |
| `get_all_tiered_strategies()` | Alle Strategien gruppiert nach Tier |
| `get_strategy_tier(strategy_id)` | Tier einer einzelnen Strategie |
| `validate_preset_tiering_compliance(preset, allowed_tiers)` | Prüft Tiering-Compliance |
| `load_tiered_preset(preset_name)` | Lädt Preset mit Validierung |
| `build_core_only_preset()` | Erstellt Core-Only-Preset programmatisch |
| `build_core_plus_aux_preset()` | Erstellt Core+Aux-Preset programmatisch |

### 2. Portfolio-Presets: `config/portfolio_presets/`

Drei neue tiered Presets:

#### `core_balanced.toml`
- **Strategien:** `rsi_reversion`, `ma_crossover`, `bollinger_bands`
- **Gewichte:** 34% / 33% / 33%
- **Tier-Compliance:** Nur `core`
- **Risikoprofil:** Moderat

```toml
strategies = ["rsi_reversion", "ma_crossover", "bollinger_bands"]
weights = [0.34, 0.33, 0.33]
```

#### `core_trend_meanreversion.toml`
- **Strategien:** Wie `core_balanced`, aber mit Style-Split
- **Gewichte:** 40% Trend (ma_crossover) / 60% Mean-Reversion
- **Tier-Compliance:** Nur `core`
- **Risikoprofil:** Moderat

```toml
# Trend-Following: 40%
# Mean-Reversion: 60%
strategies = ["ma_crossover", "rsi_reversion", "bollinger_bands"]
weights = [0.40, 0.30, 0.30]
```

#### `core_plus_aux_aggro.toml`
- **Strategien:** Core + ausgewählte Aux
- **Gewichte:** 55% Core / 45% Aux
- **Tier-Compliance:** `core` + `aux` (kein `legacy`)
- **Risikoprofil:** Aggressiv

```toml
strategies = [
    "rsi_reversion", "ma_crossover", "bollinger_bands",  # Core
    "breakout", "macd", "momentum_1h",                   # Aux
]
weights = [0.183, 0.184, 0.183, 0.15, 0.15, 0.15]
```

---

## Verwendung

### CLI: Preset laden und validieren

```bash
# Preset laden mit Tiering-Validierung
python -c "
from src.experiments.portfolio_presets import load_tiered_preset
recipe = load_tiered_preset('core_balanced')
print(f'Preset: {recipe.portfolio_name}')
print(f'Strategien: {recipe.strategies}')
"
```

### Tiering-Compliance prüfen

```bash
python -c "
from src.experiments.portfolio_presets import validate_preset_tiering_compliance
from src.experiments.portfolio_recipes import load_portfolio_recipes
from pathlib import Path

recipes = load_portfolio_recipes(Path('config/portfolio_presets/core_balanced.toml'))
result = validate_preset_tiering_compliance(
    'core_balanced',
    allowed_tiers=['core'],
    recipe=recipes['core_balanced'],
)
print(result)
"
```

### Alle Strategien nach Tier auflisten

```bash
python -c "
from src.experiments.portfolio_presets import get_all_tiered_strategies
for tier, strategies in get_all_tiered_strategies().items():
    print(f'{tier}: {strategies}')
"
```

### Programmatisch Core-Preset bauen

```python
from src.experiments.portfolio_presets import build_core_only_preset

recipe = build_core_only_preset(
    name="my_core_portfolio",
    description="Mein Core-Portfolio",
    weights=[0.5, 0.3, 0.2],  # Optional: Custom weights
)

print(recipe.strategies)  # ['rsi_reversion', 'ma_crossover', 'bollinger_bands']
```

---

## Tests

```bash
# Alle Phase-80-Tests ausführen
pytest tests/test_portfolio_presets_tiering.py -v

# Spezifische Testklasse
pytest tests/test_portfolio_presets_tiering.py::TestCorePresetsNoLegacy -v
```

### Testabdeckung

| Testklasse | Fokus |
|------------|-------|
| `TestGetStrategiesByTier` | Tier-Filterung |
| `TestGetTieringAwareStrategies` | Flexible Filterung |
| `TestValidatePresetTieringCompliance` | Compliance-Validierung |
| `TestCorePresetsNoLegacy` | **Kritisch:** Kein Legacy in Core-Presets |
| `TestBuildCoreOnlyPreset` | Programmatische Preset-Erstellung |
| `TestTieringIntegration` | End-to-End-Workflow |

---

## Tiering-Klassifizierung (Stand Phase 80)

### Core-Strategien
| Strategy | Sharpe | MaxDD | Notes |
|----------|--------|-------|-------|
| `rsi_reversion` | ≥1.5 | ≥-15% | Mean-Reversion, robust |
| `ma_crossover` | ≥1.5 | ≥-15% | Trend-Following, stabil |
| `bollinger_bands` | ≥1.5 | ≥-15% | Vol-basierte MR |

### Aux-Strategien
| Strategy | Sharpe | MaxDD | Notes |
|----------|--------|-------|-------|
| `breakout` | ≥1.0 | ≥-20% | Trend, höhere Tail-Risiken |
| `macd` | ≥1.0 | ≥-20% | Momentum, gut in Trends |
| `momentum_1h` | ≥1.0 | ≥-20% | Kurzfristiges Momentum |
| `trend_following` | ≥1.0 | ≥-20% | ADX-basiert |
| `mean_reversion` | ≥1.0 | ≥-20% | Z-Score-basiert |
| `vol_regime_filter` | ≥1.0 | ≥-20% | Volatilitäts-Overlay |
| `composite` | ≥1.0 | ≥-20% | Multi-Strategy |
| `regime_aware_portfolio` | ≥1.0 | ≥-20% | Adaptive Allokation |

### Legacy-Strategien (nie automatisch in Presets)
| Strategy | Grund |
|----------|-------|
| `breakout_donchian` | Ersetzt durch `breakout` |
| `my_strategy` | Demo, nicht für Produktion |
| `vol_breakout` | Ersetzt durch `vol_regime_filter + breakout` |

---

## Verbindung zu anderen Phasen

| Phase | Verbindung |
|-------|------------|
| **Phase 41B** | StrategyProfile & Tiering-System definiert |
| **Phase 53** | Portfolio-Recipes eingeführt |
| **Phase 81** | Golden Paths nutzen Tiered Presets |
| **Phase 83** | Live-Gates nutzen Tiering für Eligibility |
| **Phase 84** | Operator-Dashboard zeigt Tiering-Status |

---

## Definition of Done

- [x] Mind. 3 Presets konfiguriert (`core_balanced`, `core_trend_meanreversion`, `core_plus_aux_aggro`)
- [x] Tests für Tiering-Filterung im Portfolio-Kontext
- [x] Doku erklärt core/aux/legacy im Portfolio-Kontext
- [x] Helper-Funktionen für Tiering-aware Portfolio-Bau
- [x] Validierungsfunktionen für Tiering-Compliance

---

## Nächste Schritte

→ **Phase 81:** Research Golden Paths mit Tiered Presets dokumentieren
→ **Phase 83:** Live-Gates nutzen Tiering für Eligibility-Checks
