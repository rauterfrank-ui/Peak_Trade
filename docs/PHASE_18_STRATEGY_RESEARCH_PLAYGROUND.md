# Phase 18: Strategy Research Playground

## Überblick

Phase 18 führt einen standardisierten **Strategy Research Playground** ein, der es ermöglicht, schnell neue Strategien zu entwickeln, zu testen und zu vergleichen.

### Ziel

- Schnelles Prototyping neuer Strategien
- Standardisierte Backtests mit Registry-Logging
- Reproduzierbare Research-Workflows
- Einfacher Strategie-Vergleich

### Scope

- **Rein intern**: Backtest und Paper-Execution
- **Keine Testnet-/Live-Komponenten**
- **Keine Order-Schnittstellen**

### Nicht-Ziele

- Kein Live-Trading
- Keine Testnet-Orders
- Keine Hyperparameter-Optimierung (kommt in Phase 20)

---

## Architektur

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Strategy Research Playground                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐  │
│  │  Data Layer     │    │  Strategy Layer │    │  Backtest Layer │  │
│  │  (CSV/Parquet)  │───▶│  (OOP Registry) │───▶│  (Engine/Stats) │  │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘  │
│           │                      │                      │            │
│           ▼                      ▼                      ▼            │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐  │
│  │  Position Sizing│    │  Risk Manager   │    │  Experiments    │  │
│  │  (Config-based) │    │  (MaxDD, etc.)  │    │  (Registry CSV) │  │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘  │
│                                                                       │
├─────────────────────────────────────────────────────────────────────┤
│                         Research Scripts                              │
│  ┌─────────────────────────┐  ┌─────────────────────────────────┐   │
│  │ research_run_strategy.py│  │ research_compare_strategies.py  │   │
│  │ (Single Strategy Run)   │  │ (Multi-Strategy Comparison)     │   │
│  └─────────────────────────┘  └─────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Neue Module

### Strategien

| Datei | Beschreibung |
|-------|--------------|
| `src/strategies/trend_following.py` | ADX-basierte Trend-Following-Strategie |
| `src/strategies/mean_reversion.py` | Z-Score Mean-Reversion-Strategie |

### Scripts

| Datei | Beschreibung |
|-------|--------------|
| `scripts/research_run_strategy.py` | Einzelner Research-Run für eine Strategie |
| `scripts/research_compare_strategies.py` | Vergleich mehrerer Strategien |

### Dokumentation

| Datei | Beschreibung |
|-------|--------------|
| `docs/PHASE_18_STRATEGY_RESEARCH_PLAYGROUND.md` | Diese Datei |
| `docs/STRATEGY_RESEARCH_PLAYBOOK.md` | Praktische Anleitung |

---

## Strategy API

Alle Strategien folgen dem OOP-Pattern mit `BaseStrategy`:

```python
from src.strategies.base import BaseStrategy, StrategyMetadata

class MyStrategy(BaseStrategy):
    KEY = "my_strategy"

    def __init__(self, param1=10, param2=20, config=None, metadata=None):
        initial_config = {"param1": param1, "param2": param2}
        if config:
            initial_config.update(config)

        metadata = metadata or StrategyMetadata(
            name="My Strategy",
            description="Description here",
            version="1.0.0",
            regime="trending",  # oder "ranging"
            tags=["trend", "momentum"],
        )

        super().__init__(config=initial_config, metadata=metadata)
        self.param1 = self.config.get("param1", param1)
        self.param2 = self.config.get("param2", param2)
        self.validate()

    def validate(self) -> None:
        if self.param1 <= 0:
            raise ValueError(f"param1 muss > 0 sein")

    @classmethod
    def from_config(cls, cfg, section="strategy.my_strategy"):
        param1 = cfg.get(f"{section}.param1", 10)
        param2 = cfg.get(f"{section}.param2", 20)
        return cls(param1=param1, param2=param2)

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        # Signale generieren
        # Return: Series mit 1 (long), -1 (exit/short), 0 (neutral)
        signals = pd.Series(0, index=data.index, dtype=int)
        # ... Logik ...
        return signals
```

---

## Technischer Ablauf

### `research_run_strategy.py`

```
1. CLI-Args parsen
2. Config laden (config.toml)
3. Strategie aus Registry laden
4. OHLCV-Daten laden (CSV oder Dummy)
5. Position-Sizer + Risk-Manager erstellen
6. BacktestEngine.run_realistic() ausführen
7. Stats berechnen
8. CLI-Summary ausgeben
9. Run in Experiment-Registry loggen
```

### `research_compare_strategies.py`

```
1. CLI-Args parsen (Strategieliste)
2. Config laden
3. OHLCV-Daten laden (einmal für alle)
4. Für jede Strategie:
   - Backtest ausführen
   - Ergebnis speichern
5. Vergleichstabelle ausgeben
6. Alle Runs mit gemeinsamer Group-ID loggen
7. Optional: CSV-Export
```

---

## Config-Sektionen

Phase 18 fügt folgende Sektionen zu `config.toml` hinzu:

```toml
[strategy.trend_following]
adx_period = 14
adx_threshold = 25.0
exit_threshold = 20.0
ma_period = 50
use_ma_filter = true
stop_pct = 0.025

[strategy.mean_reversion]
lookback = 20
entry_threshold = -2.0
exit_threshold = 0.0
use_vol_filter = false
vol_window = 20
max_vol_percentile = 70
stop_pct = 0.02
```

---

## Registry-Integration

Alle Research-Runs werden automatisch in der Experiment-Registry geloggt:

- **Run-Type**: `backtest`
- **Metadata**:
  - `runner`: Name des Scripts
  - `phase`: `18_research_playground`
  - `tag`: User-definierter Tag
  - `data_source`: `csv` oder `dummy`
  - `custom_params`: Überschriebene Parameter
  - `group_id`: Bei Vergleichen - gemeinsame ID

---

## Safety-Hinweise

1. **Kein Live-Trading**: Alle Komponenten arbeiten nur mit Backtest-Daten
2. **Keine Order-Schnittstellen**: Es werden keine Orders gesendet
3. **Keine Testnet-Verbindungen**: Rein lokale Verarbeitung
4. **SafetyGuard bleibt aktiv**: Bestehende Sicherheitsmechanismen unverändert

---

## Abhängigkeiten

- **Von Phase 18 genutzt**:
  - Data-Layer (Phase 1-5)
  - Backtest-Engine (Phase 6-8)
  - Risk-Layer (Phase 9-11)
  - Experiments/Registry (Phase 12+)
  - Environment/Safety (Phase 17)

- **Phase 18 bereitet vor**:
  - Phase 19: Regime-Aware Strategien
  - Phase 20: Hyperparameter-Sweeps

---

## Dateien-Übersicht

### Neu erstellt

```
src/strategies/trend_following.py     # TrendFollowingStrategy
src/strategies/mean_reversion.py      # MeanReversionStrategy
scripts/research_run_strategy.py      # Single-Strategy Runner
scripts/research_compare_strategies.py # Multi-Strategy Comparison
docs/PHASE_18_STRATEGY_RESEARCH_PLAYGROUND.md
docs/STRATEGY_RESEARCH_PLAYBOOK.md
tests/test_strategies_research_playground.py
```

### Modifiziert

```
src/strategies/registry.py            # Neue Strategien registriert
src/strategies/__init__.py            # Legacy-Mapping erweitert
config.toml                           # Neue Strategie-Sektionen
```

---

## Nächste Schritte

Nach Phase 18 können folgende Phasen aufbauen:

1. **Phase 19**: Regime-Erkennung und Portfolio-Konstruktion
2. **Phase 20**: Hyperparameter-Sweeps und Experiment-Orchestrierung
3. **Phase 21**: Reporting v2 mit HTML-Dashboards
