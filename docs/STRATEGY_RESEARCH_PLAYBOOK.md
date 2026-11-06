# Strategy Research Playbook

Praktische Anleitung für den Strategy Research Playground (Phase 18).

---

## Schnellstart

### Eine Strategie testen

```bash
# Mit Default-Strategie und Dummy-Daten
python3 scripts/research_run_strategy.py

# Mit spezifischer Strategie
python3 scripts/research_run_strategy.py --strategy trend_following

# Mit echten Daten
python3 scripts/research_run_strategy.py --strategy mean_reversion \
    --data-file data/btc_eur_1h.csv
```

### Strategien vergleichen

```bash
# Alle Strategien vergleichen
python3 scripts/research_compare_strategies.py --all

# Nur bestimmte Strategien
python3 scripts/research_compare_strategies.py \
    --strategies ma_crossover,trend_following,mean_reversion

# Mit Daten und CSV-Export
python3 scripts/research_compare_strategies.py --all \
    --data-file data/btc_eur_1h.csv \
    --export results/comparison.csv
```

### Verfügbare Strategien anzeigen

```bash
python3 scripts/research_run_strategy.py --list-strategies
```

---

## Strategien im Detail

### Trend-Following (trend_following)

**Konzept**: ADX-basierte Trend-Following-Strategie

- Entry: ADX > Threshold UND +DI > -DI (starker Aufwärtstrend)
- Exit: ADX < Exit-Threshold ODER Trendwechsel
- Optimal für: Trending Märkte

**Parameter**:

| Parameter | Default | Beschreibung |
|-----------|---------|--------------|
| `adx_period` | 14 | Periode für ADX-Berechnung |
| `adx_threshold` | 25.0 | Mindest-ADX für Entry |
| `exit_threshold` | 20.0 | ADX unter diesem Wert = Exit |
| `ma_period` | 50 | Periode für MA-Trendfilter |
| `use_ma_filter` | true | Zusätzlicher MA-Filter |

```bash
python3 scripts/research_run_strategy.py --strategy trend_following \
    --param adx_threshold=30 --param ma_period=100
```

### Mean Reversion (mean_reversion)

**Konzept**: Z-Score-basierte Mean-Reversion

- Entry: Z-Score < Entry-Threshold (überverkauft)
- Exit: Z-Score > Exit-Threshold (zurück zum Mittel)
- Optimal für: Seitwärtsmärkte (Ranging)

**Parameter**:

| Parameter | Default | Beschreibung |
|-----------|---------|--------------|
| `lookback` | 20 | Periode für MA und Std |
| `entry_threshold` | -2.0 | Z-Score für Entry |
| `exit_threshold` | 0.0 | Z-Score für Exit |
| `use_vol_filter` | false | Volatilitätsfilter |

```bash
python3 scripts/research_run_strategy.py --strategy mean_reversion \
    --param entry_threshold=-2.5 --param use_vol_filter=true
```

### Weitere Strategien

| Key | Typ | Beschreibung |
|-----|-----|--------------|
| `ma_crossover` | Trend | Moving Average Crossover |
| `momentum_1h` | Trend | Momentum-basiert |
| `rsi_reversion` | Mean-Rev | RSI Oversold/Overbought |
| `bollinger_bands` | Mean-Rev | Bollinger Bands |
| `macd` | Trend | MACD Crossover |
| `breakout_donchian` | Trend | Donchian Channel Breakout |

---

## Eine neue Strategie hinzufügen

### Schritt 1: Strategie-Datei erstellen

Erstelle `src/strategies/my_strategy.py`:

```python
from __future__ import annotations
from typing import Any, Dict, Optional
import pandas as pd
from .base import BaseStrategy, StrategyMetadata

class MyStrategy(BaseStrategy):
    """Meine neue Strategie."""

    KEY = "my_strategy"

    def __init__(
        self,
        param1: int = 10,
        param2: float = 0.5,
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[StrategyMetadata] = None,
    ) -> None:
        initial_config = {
            "param1": param1,
            "param2": param2,
        }
        if config:
            initial_config.update(config)

        if metadata is None:
            metadata = StrategyMetadata(
                name="My Strategy",
                description="Beschreibung meiner Strategie",
                version="1.0.0",
                author="Peak_Trade",
                regime="trending",  # oder "ranging"
                tags=["custom", "research"],
            )

        super().__init__(config=initial_config, metadata=metadata)

        self.param1 = int(self.config.get("param1", param1))
        self.param2 = float(self.config.get("param2", param2))
        self.validate()

    def validate(self) -> None:
        if self.param1 <= 0:
            raise ValueError(f"param1 ({self.param1}) muss > 0 sein")

    @classmethod
    def from_config(cls, cfg: Any, section: str = "strategy.my_strategy"):
        param1 = cfg.get(f"{section}.param1", 10)
        param2 = cfg.get(f"{section}.param2", 0.5)
        return cls(param1=param1, param2=param2)

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generiert Handelssignale.

        Returns:
            Series mit:
            - 1: Long Entry
            - -1: Exit
            - 0: Neutral
        """
        if "close" not in data.columns:
            raise ValueError("'close' Spalte erforderlich")

        signals = pd.Series(0, index=data.index, dtype=int)

        # Deine Signal-Logik hier
        # ...

        return signals
```

### Schritt 2: In Registry eintragen

Bearbeite `src/strategies/registry.py`:

```python
# Import hinzufügen
from .my_strategy import MyStrategy

# In _STRATEGY_REGISTRY hinzufügen
_STRATEGY_REGISTRY: Dict[str, StrategySpec] = {
    # ... andere Strategien ...
    "my_strategy": StrategySpec(
        key="my_strategy",
        cls=MyStrategy,
        config_section="strategy.my_strategy",
        description="Meine neue Strategie",
    ),
}
```

### Schritt 3: Config hinzufügen

Füge zu `config.toml` hinzu:

```toml
[strategy.my_strategy]
param1 = 10
param2 = 0.5
stop_pct = 0.02
```

### Schritt 4: Testen

```bash
# Strategie testen
python3 scripts/research_run_strategy.py --strategy my_strategy

# Mit anderen vergleichen
python3 scripts/research_compare_strategies.py \
    --strategies ma_crossover,my_strategy
```

---

## Best Practices

### Overfitting vermeiden

1. **Train/Test-Split**: Trenne Daten in In-Sample (Training) und Out-of-Sample (Test)
2. **Robustheit prüfen**: Teste mit verschiedenen Parametern
3. **Mehrere Märkte**: Validiere auf verschiedenen Symbolen

```bash
# In-Sample (Training)
python3 scripts/research_run_strategy.py --strategy trend_following \
    --data-file data/btc_1h.csv --start 2022-01-01 --end 2023-06-30

# Out-of-Sample (Test)
python3 scripts/research_run_strategy.py --strategy trend_following \
    --data-file data/btc_1h.csv --start 2023-07-01 --end 2024-01-01
```

### Parameter-Sensitivität

Teste verschiedene Parameter-Varianten:

```bash
# Konservativ
python3 scripts/research_run_strategy.py --strategy trend_following \
    --param adx_threshold=30 --tag conservative

# Aggressiv
python3 scripts/research_run_strategy.py --strategy trend_following \
    --param adx_threshold=20 --tag aggressive
```

### Strategie-Kategorisierung

Nutze das `regime`-Feld in StrategyMetadata:

- `trending`: Für Trend-Following-Strategien
- `ranging`: Für Mean-Reversion-Strategien
- `adaptive`: Für regime-adaptive Strategien

---

## Registry-Nutzung

### Runs taggen

```bash
# Mit Tag für spätere Filterung
python3 scripts/research_run_strategy.py --strategy ma_crossover \
    --tag experiment_v1

# Runs ohne Registry-Logging
python3 scripts/research_run_strategy.py --strategy ma_crossover \
    --no-registry
```

### Experiments analysieren

```bash
# Alle Experiments anzeigen
python3 scripts/list_experiments.py

# Nach Tag filtern
python3 scripts/list_experiments.py --tag experiment_v1

# Details anzeigen
python3 scripts/show_experiment.py --run-id <RUN_ID>
```

---

## CLI-Referenz

### research_run_strategy.py

```
--strategy KEY       Strategie-Key (default: aus Config)
--data-file PATH     CSV-Datei mit OHLCV-Daten
--symbol SYMBOL      Trading-Symbol (default: BTC/EUR)
--timeframe TF       Timeframe (default: 1h)
--start YYYY-MM-DD   Startdatum
--end YYYY-MM-DD     Enddatum
--bars N             Anzahl Dummy-Bars (default: 500)
--param KEY=VALUE    Custom-Parameter (mehrfach verwendbar)
--tag TAG            Tag für Registry
--config PATH        Config-Datei (default: config.toml)
--no-registry        Kein Registry-Logging
--verbose            Ausführliche Ausgabe
--list-strategies    Alle Strategien anzeigen
```

### research_compare_strategies.py

```
--strategies LIST    Komma-getrennte Strategie-Keys
--all                Alle Strategien vergleichen
--data-file PATH     CSV-Datei mit OHLCV-Daten
--symbol SYMBOL      Trading-Symbol (default: BTC/EUR)
--sort-by METRIC     Sortiermetrik (default: total_return)
--sort-asc           Aufsteigend sortieren
--export PATH        CSV-Export der Ergebnisse
--tag TAG            Tag für Registry
--no-registry        Kein Registry-Logging
--verbose            Ausführliche Ausgabe
```

---

## Nächste Schritte

Nach dem Research Playground:

1. **Regime-Erkennung** (Phase 19): Strategien nach Marktregime aktivieren
2. **Hyperparameter-Sweeps** (Phase 20): Automatische Parameteroptimierung
3. **Reporting v2** (Phase 21): HTML-Dashboards und bessere Visualisierung
