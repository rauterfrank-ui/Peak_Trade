# Phase 75 – Strategy-Library v1.1

**Status:** In Progress
**Version:** 1.1
**Stand:** Dezember 2024

---

## 1. Einleitung

Phase 75 konsolidiert die Peak_Trade Strategy-Library zu einer stabilen v1.1-Version. Ziel ist:

1. **Klare Katalogisierung** aller verfügbaren Strategien mit einheitlicher Dokumentation
2. **Konsistente Config-Struktur** in `config/config.toml` für alle v1.1-Strategien
3. **Vollständige Sweep-Configs** für Parameter-Optimierung
4. **Kuratierte Portfolio-Presets** für Research und Testnet

### Einbettung in die Gesamt-Architektur

```
┌─────────────────────────────────────────────────────────────────┐
│                     Peak_Trade v1.0                              │
├─────────────────────────────────────────────────────────────────┤
│  Data-Layer        │  Strategy-Layer (v1.1)  │  Portfolio-Layer │
│  - OHLCV Loader    │  - BaseStrategy         │  - Presets       │
│  - Cache           │  - Registry             │  - Recipes       │
│  - Indicators      │  - Sweep-Configs        │  - Robustness    │
├─────────────────────────────────────────────────────────────────┤
│  Research-Pipeline │  Backtest-Engine        │  Risk/Safety     │
│  - Experiments     │  - Execution Pipeline   │  - SafetyGuard   │
│  - Monte-Carlo     │  - Walk-Forward         │  - LiveRiskLimits│
│  - Stress-Tests    │  - Reports              │  - PositionSizer │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Strategy-Katalog (v1.1)

### 2.1 Übersicht aller Strategien

| name | file | type | description | default_timeframes | risk_profile | has_sweep_config | portfolio_usage |
|------|------|------|-------------|-------------------|--------------|------------------|-----------------|
| `ma_crossover` | `src/strategies/ma_crossover.py` | trend | Moving Average Crossover (Fast/Slow MA) | `["1h", "4h", "1d"]` | medium | yes | v11_conservative, v11_moderate |
| `rsi_reversion` | `src/strategies/rsi_reversion.py` | mean_reversion | RSI-basierte Mean-Reversion mit optionalem Trendfilter | `["15m", "1h", "4h"]` | medium | yes | v11_conservative, v11_moderate, v11_aggressive |
| `breakout` | `src/strategies/breakout.py` | trend | N-Bar Breakout mit SL/TP/Trailing-Stop und ATR-Filter | `["1h", "4h"]` | medium-high | yes | v11_moderate, v11_aggressive |
| `momentum_1h` | `src/strategies/momentum.py` | momentum | Momentum-basierte Trend-Following-Strategie | `["1h", "4h"]` | medium-high | yes | v11_moderate |
| `bollinger_bands` | `src/strategies/bollinger.py` | mean_reversion | Bollinger Bands Mean-Reversion | `["1h", "4h", "1d"]` | medium | yes | v11_conservative |
| `macd` | `src/strategies/macd.py` | trend | MACD Trend-Following (EMA-Crossover) | `["4h", "1d"]` | medium | yes | v11_moderate |
| `trend_following` | `src/strategies/trend_following.py` | trend | ADX-basierte Trend-Following mit MA-Filter | `["1h", "4h", "1d"]` | medium | yes | v11_conservative, v11_moderate |
| `mean_reversion` | `src/strategies/mean_reversion.py` | mean_reversion | Z-Score Mean-Reversion mit optionalem Vol-Filter | `["1h", "4h"]` | medium | yes | v11_conservative |
| `vol_regime_filter` | `src/strategies/vol_regime_filter.py` | meta/filter | Volatilitäts-Regime-Filter (als Overlay) | `["1h", "4h"]` | - | yes | (filter for all) |
| `composite` | `src/strategies/composite.py` | meta | Multi-Strategy Composite (Aggregation) | - | varies | no | experimental |
| `regime_aware_portfolio` | `src/strategies/regime_aware_portfolio.py` | meta | Regime-Aware Multi-Strategy Portfolio | - | varies | experimental | experimental |

### 2.2 Strategie-Typen

- **trend**: Profitiert von Trending-Märkten, performt schlecht in Range-Märkten
- **mean_reversion**: Profitiert von Range-Märkten, kann in starken Trends verlieren
- **momentum**: Variation von Trend-Following, fokussiert auf Preis-Momentum
- **meta/filter**: Overlay-Strategien zur Filterung oder Kombination anderer Strategien

---

## 3. Curated v1.1 Strategies

Die folgenden **8 Strategien** sind als **v1.1-offiziell** kuratiert:

### 3.1 Trend-Following (3)

| Strategy | Beschreibung | Begründung v1.1 |
|----------|--------------|-----------------|
| `ma_crossover` | Klassiker, robust, klar verständlich | Benchmark-Strategie, gut dokumentiert, stabil |
| `trend_following` | ADX-basiert, filtert schwache Trends | Guter Trendfilter, vermeidet Whipsaws |
| `macd` | EMA-basiert, beliebter Indikator | Bewährter Indikator, gut für 4h/1d |

### 3.2 Mean-Reversion (3)

| Strategy | Beschreibung | Begründung v1.1 |
|----------|--------------|-----------------|
| `rsi_reversion` | RSI mit konfigurierbaren Levels | Flexibel, mit Trendfilter-Option |
| `mean_reversion` | Z-Score basiert | Statistisch fundiert, Vol-Filter möglich |
| `bollinger_bands` | Bollinger Bands Entry/Exit | Klassiker, intuitive Parameter |

### 3.3 Momentum (1)

| Strategy | Beschreibung | Begründung v1.1 |
|----------|--------------|-----------------|
| `momentum_1h` | Einfaches Momentum-Signal | Klar, gut für 1h-Timeframe |

### 3.4 Breakout (1)

| Strategy | Beschreibung | Begründung v1.1 |
|----------|--------------|-----------------|
| `breakout` | N-Bar Breakout mit SL/TP | Vollständiges Risk-Management integriert |

### 3.5 Filter/Meta (1)

| Strategy | Beschreibung | Begründung v1.1 |
|----------|--------------|-----------------|
| `vol_regime_filter` | Volatilitäts-Regime-Filter | Wichtiger Overlay für Portfolio-Konstruktion |

### 3.6 Nicht in v1.1 (experimental)

- `composite`: Noch in Entwicklung, API instabil
- `regime_aware_portfolio`: Komplex, weitere Tests nötig
- `my_strategy`: Template/Beispiel
- Legacy-Varianten (`rsi_strategy`, `breakout_donchian`, etc.): Durch v1.1-Versionen ersetzt

---

## 3a. R&D / Experimental-Layer (separat von v1.1)

Zusätzlich zur produktiven v1.1-Strategy-Library existiert ein **R&D-Layer** mit fortgeschrittenen Forschungsstrategien. Diese sind **klar getrennt** von der v1.1-Bibliothek und **nicht für Live-Trading freigegeben**.

### Produktiver v1.1 Strategy-Core vs. R&D / Experimental-Layer

| Aspekt | v1.1 Strategy-Core | R&D / Experimental |
|--------|-------------------|-------------------|
| **Tier** | `core`, `aux` | `r_and_d` |
| **Live-Freigabe** | nach Validierung möglich | **NEIN** |
| **Verwendung** | Research + Shadow + Testnet + Live | nur Research + Backtests |
| **Beispiele** | ma_crossover, rsi_reversion, breakout | Armstrong, Ehlers, El Karoui |
| **Tests** | vollständig | strukturell + Smoke |

### R&D-Strategie-Welle v1

Mit Commit `7908106` (`feat(research): add R&D strategy modules & tests`) wurde die erste R&D-Welle integriert:

| R&D-Strategie | Kategorie | Modul |
|---------------|-----------|-------|
| Armstrong Cycle Strategy | cycles | `src/strategies/armstrong/` |
| Ehlers Cycle Filter | cycles | `src/strategies/ehlers/` |
| El Karoui Volatility Model | volatility | `src/strategies/el_karoui/` |
| Bouchaud Microstructure Overlay | microstructure | `src/strategies/bouchaud/` |
| Gatheral Cont Vol Overlay | volatility | `src/strategies/gatheral_cont/` |
| Lopez de Prado Meta-Labeling | ml | `src/strategies/lopez_de_prado/` |

### R&D-Strategien – Armstrong & El Karoui (Detail)

Im R&D-Tier existieren zwei experimentelle Strategien, die explizit **nicht** für Live-Trading freigegeben sind:

* **ArmstrongCycleStrategy** (`tier = "r_and_d"`, `IS_LIVE_READY = False`)
  Abstrakte, zyklusbasierte Research-Strategie, die Ideen makroökonomischer
  Zyklen modelliert, ohne proprietäre Modelle zu reproduzieren. Eingesetzt
  ausschließlich in `offline_backtest` und `research`.

* **ElKarouiVolModelStrategy** (`tier = "r_and_d"`, `IS_LIVE_READY = False`)
  Volatilitäts- und Regime-Research-Strategie, die einfache Volatilitätsproxies
  und Regime-Labels nutzt, um Risk-Signale zu untersuchen. Ebenfalls streng auf
  `offline_backtest` und `research` limitiert.

Beide Strategien sind im Strategy-Registry und in `config/strategy_tiering.toml`
hinterlegt und werden von einer umfangreichen Test-Suite (`tests/test_research_strategies.py`)
abgedeckt. Sie dienen als Startpunkt für tiefergehende makroökonomische und
Volatilitäts-Research-Projekte, nicht als produktive Live-Bausteine.

### R&D-Nutzung

R&D-Strategien sind **ausschließlich für folgende Zwecke** gedacht:

1. **Offline-Backtests** – Parameter-Exploration und Sensitivitätsanalysen
2. **Research-Sweeps** – Systematische Evaluation unter verschiedenen Marktbedingungen
3. **Akademische Analysen** – Vergleich mit Referenz-Implementierungen
4. **Strukturierte Experimente** – Prototyping neuer Ansätze

> **Wichtig:** R&D-Strategien werden im Web-Dashboard nur mit `?include_research=true` angezeigt und sind im Strategy-Tiering als `tier = "r_and_d"` mit `allow_live = false` markiert.

### Weiterführende Dokumentation

- [PEAK_TRADE_STATUS_OVERVIEW.md](./PEAK_TRADE_STATUS_OVERVIEW.md) – R&D-Track-Beschreibung im Gesamtkontext
- `config/strategy_tiering.toml` – R&D-Strategie-Einträge mit Labels, Tags und Kategorien
- `tests/test_research_strategies.py` – Tests für R&D-Tiering und Dashboard-Integration

---

## 4. Config-Struktur (v1.1)

### 4.1 Einheitliches Format

Jede v1.1-Strategie hat einen Block in `config/config.toml`:

```toml
[strategies.ma_crossover]
enabled = true
category = "trend"
timeframes = ["1h", "4h", "1d"]
risk_level = "medium"
description = "Moving Average Crossover Strategy"

[strategies.ma_crossover.defaults]
fast_window = 20
slow_window = 50
price_col = "close"
```

### 4.2 Kategorie-Übersicht

| category | Strategien |
|----------|-----------|
| `trend` | ma_crossover, trend_following, macd |
| `mean_reversion` | rsi_reversion, mean_reversion, bollinger_bands |
| `momentum` | momentum_1h |
| `breakout` | breakout |
| `meta` | vol_regime_filter, composite |

---

## 5. Sweep-Configs

### 5.1 Verfügbare Sweep-Configs

| Strategy | Sweep-Config | Parameter-Kombis |
|----------|--------------|------------------|
| `ma_crossover` | `config/sweeps/ma_crossover.toml` | ~16 |
| `rsi_reversion` | `config/sweeps/rsi_reversion.toml` | ~36 |
| `breakout` | `config/sweeps/breakout.toml` | ~48 |
| `momentum_1h` | `config/sweeps/momentum.toml` | ~24 |
| `bollinger_bands` | `config/sweeps/bollinger_bands.toml` | ~27 |
| `macd` | `config/sweeps/macd.toml` | ~36 |
| `trend_following` | `config/sweeps/trend_following.toml` | ~108 |
| `mean_reversion` | `config/sweeps/mean_reversion.toml` | ~96 |
| `vol_regime_filter` | `config/sweeps/vol_regime_filter.toml` | ~24 |

### 5.2 Sweep-Ausführung

```bash
# Beispiel: MA-Crossover Sweep
python scripts/run_strategy_sweep.py \
  --strategy ma_crossover \
  --sweep-config config/sweeps/ma_crossover.toml \
  --output-dir reports/sweeps/ma_crossover_v11

# Beispiel: RSI-Reversion Sweep
python scripts/run_strategy_sweep.py \
  --strategy rsi_reversion \
  --sweep-config config/sweeps/rsi_reversion.toml \
  --output-dir reports/sweeps/rsi_reversion_v11
```

---

## 6. Portfolio-Presets v1.1

### 6.1 Conservative v1.1

**Ziel:** Niedriges Risiko, stabile Returns, geringe Volatilität

```toml
[portfolio_recipes.conservative_v11]
description = "Konservatives v1.1 Portfolio (Low Risk)"
risk_profile = "conservative"
max_drawdown_target = 0.10

strategies = [
  { name = "ma_crossover", weight = 0.30 },
  { name = "mean_reversion", weight = 0.25 },
  { name = "bollinger_bands", weight = 0.25 },
  { name = "trend_following", weight = 0.20 },
]
```

### 6.2 Moderate v1.1

**Ziel:** Ausgewogenes Risiko/Return-Profil

```toml
[portfolio_recipes.moderate_v11]
description = "Moderates v1.1 Portfolio (Balanced)"
risk_profile = "moderate"
max_drawdown_target = 0.15

strategies = [
  { name = "rsi_reversion", weight = 0.25 },
  { name = "breakout", weight = 0.25 },
  { name = "trend_following", weight = 0.25 },
  { name = "macd", weight = 0.25 },
]
```

### 6.3 Aggressive v1.1

**Ziel:** Höheres Risiko für potentiell höhere Returns

```toml
[portfolio_recipes.aggressive_v11]
description = "Aggressives v1.1 Portfolio (High Risk/Return)"
risk_profile = "aggressive"
max_drawdown_target = 0.25

strategies = [
  { name = "breakout", weight = 0.35 },
  { name = "momentum_1h", weight = 0.30 },
  { name = "rsi_reversion", weight = 0.20 },
  { name = "macd", weight = 0.15 },
]
```

---

## 7. Konsistenz-Tests

Die folgenden Tests stellen sicher, dass Config ↔ Strategien ↔ Sweeps konsistent sind:

1. **Strategy ↔ Config**: Jede v1.1-Strategie hat einen `[strategies.<name>]`-Block
2. **Config ↔ Implementation**: Registry kann alle Strategien laden
3. **Config ↔ Sweeps**: Jede enabled Strategie hat eine Sweep-Config
4. **CLI-Smoke**: research_cli.py läuft ohne Exceptions für alle v1.1-Strategien

Testfile: `tests/test_strategy_configs_and_sweeps.py`

---

## 8. Verlinkungen

### Relevante Dokumentation

- [PEAK_TRADE_V1_OVERVIEW_FULL.md](./PEAK_TRADE_V1_OVERVIEW_FULL.md) - Gesamtübersicht
- [DEV_GUIDE_ADD_STRATEGY.md](./DEV_GUIDE_ADD_STRATEGY.md) - Neue Strategie entwickeln
- [DEV_GUIDE_ADD_PORTFOLIO_RECIPE.md](./DEV_GUIDE_ADD_PORTFOLIO_RECIPE.md) - Portfolio-Preset erstellen
- [PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md](./PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md) - Research-Workflow

### Config-Dateien

- `config/config.toml` - Haupt-Konfiguration
- `config/portfolio_recipes.toml` - Portfolio-Presets
- `config/sweeps/*.toml` - Sweep-Parameter-Grids

### Quellcode

- `src/strategies/` - Strategy-Implementierungen
- `src/strategies/registry.py` - Strategy-Registry
- `src/strategies/base.py` - BaseStrategy-Klasse

---

## 9. Summary (nach Abschluss)

**Status:** ABGESCHLOSSEN (2024-12-07)

### v1.1-offizielle Strategien (8 + 1 Filter)

| # | Strategy | Type | Status |
|---|----------|------|--------|
| 1 | `ma_crossover` | Trend (MA Crossover) | enabled |
| 2 | `rsi_reversion` | Mean-Reversion (RSI) | enabled |
| 3 | `breakout` | Breakout (N-Bar) | enabled |
| 4 | `momentum_1h` | Momentum | enabled |
| 5 | `bollinger_bands` | Mean-Reversion (BB) | enabled |
| 6 | `macd` | Trend (MACD) | enabled |
| 7 | `trend_following` | Trend (ADX) | enabled |
| 8 | `mean_reversion` | Mean-Reversion (Z-Score) | enabled |
| 9 | `vol_regime_filter` | Meta/Filter | enabled |

### Portfolio-Presets v1.1 (3)

| Preset | Risk Profile | Strategies | Weights |
|--------|--------------|------------|---------|
| `conservative_v11` | Low Risk | ma_crossover, mean_reversion, bollinger_bands, trend_following | 30/25/25/20 |
| `moderate_v11` | Balanced | rsi_reversion, breakout, trend_following, macd | 25/25/25/25 |
| `aggressive_v11` | High Risk/Return | breakout, momentum_1h, rsi_reversion, macd | 35/30/20/15 |

### Sweep-Configs (9 Dateien)

| Strategy | Sweep-Config | Est. Combos |
|----------|--------------|-------------|
| `ma_crossover` | `config/sweeps/ma_crossover.toml` | ~16 |
| `rsi_reversion` | `config/sweeps/rsi_reversion.toml` | ~36 |
| `breakout` | `config/sweeps/breakout.toml` | ~96 |
| `momentum_1h` | `config/sweeps/momentum.toml` | ~36 |
| `bollinger_bands` | `config/sweeps/bollinger_bands.toml` | ~36 |
| `macd` | `config/sweeps/macd.toml` | ~27 |
| `trend_following` | `config/sweeps/trend_following.toml` | ~108 |
| `mean_reversion` | `config/sweeps/mean_reversion.toml` | ~96 |
| `vol_regime_filter` | `config/sweeps/vol_regime_filter.toml` | ~54 |

### Consistency-Tests

Alle 17 Tests bestanden:

```
tests/test_strategy_configs_and_sweeps.py::test_v11_strategies_have_config_blocks PASSED
tests/test_strategy_configs_and_sweeps.py::test_v11_strategies_are_enabled PASSED
tests/test_strategy_configs_and_sweeps.py::test_v11_strategies_have_category PASSED
tests/test_strategy_configs_and_sweeps.py::test_v11_strategies_have_defaults PASSED
tests/test_strategy_configs_and_sweeps.py::test_registry_can_load_all_v11_strategies PASSED
tests/test_strategy_configs_and_sweeps.py::test_registry_strategies_can_be_instantiated PASSED
tests/test_strategy_configs_and_sweeps.py::test_v11_strategies_have_sweep_configs PASSED
tests/test_strategy_configs_and_sweeps.py::test_sweep_configs_are_parseable PASSED
tests/test_strategy_configs_and_sweeps.py::test_sweep_configs_have_parameters PASSED
tests/test_strategy_configs_and_sweeps.py::test_strategy_smoke_instantiation[trend-ma_crossover] PASSED
tests/test_strategy_configs_and_sweeps.py::test_strategy_smoke_instantiation[mean_reversion-rsi_reversion] PASSED
tests/test_strategy_configs_and_sweeps.py::test_strategy_smoke_instantiation[momentum-momentum_1h] PASSED
tests/test_strategy_configs_and_sweeps.py::test_strategy_registry_list_not_empty PASSED
tests/test_strategy_configs_and_sweeps.py::test_config_registry_loads_without_error PASSED
tests/test_strategy_configs_and_sweeps.py::test_v11_portfolio_presets_exist PASSED
tests/test_strategy_configs_and_sweeps.py::test_v11_portfolio_presets_have_required_fields PASSED
tests/test_strategy_configs_and_sweeps.py::test_v11_portfolio_presets_use_v11_strategies PASSED
```

### Generierte Reports (Pfade)

Nach Ausfuehrung der Sweeps und Backtests:

- `reports/sweeps/<strategy>_v11/` - Sweep-Reports
- `reports/portfolio/<preset>_v11/` - Portfolio-Backtest-Reports

### Aenderungen in dieser Phase

1. **Neue Dokumentation:**
   - `docs/PHASE_75_STRATEGY_LIBRARY_V1_1.md` (diese Datei)

2. **Config-Harmonisierung:**
   - `config/config.toml` - Neue `[strategies.*]`-Bloecke mit einheitlicher Struktur

3. **Neue Sweep-Configs:**
   - `config/sweeps/breakout.toml`
   - `config/sweeps/momentum.toml`
   - `config/sweeps/bollinger_bands.toml`
   - `config/sweeps/macd.toml`
   - `config/sweeps/vol_regime_filter.toml`

4. **Neue Portfolio-Presets:**
   - `config/portfolio_recipes.toml` - 3 neue v1.1-Presets

5. **Neue Tests:**
   - `tests/test_strategy_configs_and_sweeps.py`

---

**WICHTIG:** Live-Trading bleibt BLOCKIERT. Alle Safety-Mechanismen unverändert.
