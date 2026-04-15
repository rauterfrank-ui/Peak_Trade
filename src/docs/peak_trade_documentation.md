# Peak_Trade System – Gesamtübersicht & Implementationsdokumentation

## Inhalt
- Option A: Strategy-Fix (State-Signale)
- Option B: Verbesserungen & Validierung
- Option C: Dynamisches Laden der Strategien
- Option D: Filtersystem & Risk-Module
- Option E: Engine-Optimierung + BacktestResult
- Option F: Unit Tests
- Projektstruktur
- Beispielcode & Nutzung

---

## Option A – Strategy-Fix (State-Signale)
Die `ma_crossover.py` wurde vollständig überarbeitet.  
Wichtigster Bestandteil:

- Event-Signale (1/-1) → State-Signale (1/0)
- Crossover über MA-Differenz
- robuster Umgang mit NaN
- Parametervalidierung

**Rückgabeformat:**  
`pd.Series` mit Werten `0` (flat) oder `1` (long).

---

## Option B – Verbesserungen & Validierung
- MA-Perioden validiert (`fast < slow`)
- Datenlänge validiert (`len(df) >= slow`)
- Logging optional möglich
- Nutzen der `min_periods`-Option bei MA-Berechnung

---

## Option C – Dynamisches Laden der Strategien
Es gibt zwei ergänzende Einstiege: **funktions-/modulbasiert** in `src/strategies/__init__.py` (`STRATEGY_REGISTRY`, `load_strategy` → Modulfunktion `generate_signals`, u. a. für Walkforward-Pfade) und **klassen-/konfigurationsbasiert** in `src/strategies/registry.py` (`StrategySpec`, `_STRATEGY_REGISTRY`, z. B. `create_strategy_from_config` für die Config-getriebene Registry).

In `src/strategies/__init__.py`:

```python
# Mapping: Strategie-Name → Modulpfad
# WICHTIG: Namen müssen mit [strategy.*] in config.toml übereinstimmen
STRATEGY_REGISTRY = {
    "ma_crossover": "ma_crossover",
    "momentum_1h": "momentum",  # Strategie-Name != Modul-Name
    "rsi_strategy": "rsi",  # Strategie-Name != Modul-Name
    "bollinger_bands": "bollinger",  # Strategie-Name != Modul-Name
    "macd": "macd",
    "ecm_cycle": "ecm",  # Strategie-Name != Modul-Name
    # Phase 18: Research Playground Baselines
    "trend_following": "trend_following",
    "mean_reversion": "mean_reversion",
    "my_strategy": "my_strategy",
    # Phase 27: Strategy Research Track
    "vol_breakout": "vol_breakout",
    "mean_reversion_channel": "mean_reversion_channel",
    "rsi_reversion": "rsi_reversion",
    # Phase 40: Strategy Library & Portfolio-Track v1
    "breakout": "breakout",
    "vol_regime_filter": "vol_regime_filter",
    "composite": "composite",
    "regime_aware_portfolio": "regime_aware_portfolio",
    # Research-Track: R&D-Only Strategien
    "armstrong_cycle": "armstrong.armstrong_cycle_strategy",
    "el_karoui_vol_model": "el_karoui.el_karoui_vol_model_strategy",
    "ehlers_cycle_filter": "ehlers.ehlers_cycle_filter_strategy",
    "meta_labeling": "lopez_de_prado.meta_labeling_strategy",
    # R&D-Skeleton Strategien (Platzhalter)
    "bouchaud_microstructure": "bouchaud.bouchaud_microstructure_strategy",
    "vol_regime_overlay": "gatheral_cont.vol_regime_overlay_strategy",
}


def load_strategy(strategy_name: str):
    """
    Lädt die Strategie dynamisch.
    Erwartet: Modul hat eine Funktion generate_signals(df, params)
    """
    if strategy_name not in STRATEGY_REGISTRY:
        raise ValueError(
            f"Unbekannte Strategie '{strategy_name}'. Verfügbar: {list(STRATEGY_REGISTRY.keys())}"
        )

    module_name = STRATEGY_REGISTRY[strategy_name]

    # Dynamisch importieren
    module = __import__(f"src.strategies.{module_name}", fromlist=["generate_signals"])

    return module.generate_signals
```

---

## Option D – Filter & Risk-System
### Risk-Module (`position_sizer.py`)
- nutzt `PositionRequest`
- berechnet dynamische Positionsgrößen basierend auf:
  - Equity
  - Entry Price
  - Stop-Loss Price
  - Risk per Trade

### Filter-Beispiel:
`apply_volume_filter(signals, df, threshold)`

---

## Option E – Engine-Optimierung (BacktestEngine)
### BacktestResult hinzugefügt:
- Sharpe Ratio
- Max-Drawdown
- Profit-Factor
- Win-Rate
- Equity-Curve (`pd.Series`)
- Liste der Trades

### Engine-Integration:
- dynamisches Laden der Strategie
- Signale generieren
- Kauf-/Verkaufssimulation
- Equity-Tracking
- Result-Objekt erzeugen

---

## Option F – Unit Tests
### Test für Signals:
- erzeugt korrekte 0/1 State-Signale
- robust gegen Trendwechsel

### Test für Engine:
- führt Backtest mit Testdaten aus
- erwartet mindestens 1 Trade
- testet Equity-Kurve

---

## Projektstruktur

```
Peak_Trade/
├── src/
│   ├── strategies/
│   │   ├── ma_crossover.py
│   │   └── __init__.py
│   ├── backtest/
│   │   ├── engine.py
│   │   ├── results.py
│   │   └── stats.py
│   ├── risk/
│   │   └── position_sizer.py
│   └── data/
├── config.toml
├── tests/
│   ├── test_ma_crossover.py
│   └── test_engine_basic.py
└── README.md
```

---

## Nutzung
Beispiel:

```python
from src.backtest.engine import BacktestEngine

engine = BacktestEngine()
result = engine.run_realistic(df, "ma_crossover", params)

print(result.stats)
print(result.equity_curve.tail())
```

---

## Hinweise
Diese Dokumentation fasst alle Optimierungen zusammen und beschreibt die vollständig funktionierende Systemarchitektur von Peak_Trade.
