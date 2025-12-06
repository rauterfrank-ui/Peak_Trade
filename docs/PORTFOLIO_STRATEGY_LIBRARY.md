# Portfolio Strategy Library (Phase 26)

## Übersicht

Der **Portfolio-Strategy-Layer** ist ein modularer Gewichtungs-Layer für Multi-Asset-Portfolios in Peak_Trade. Er bestimmt, wie Kapital auf verschiedene Symbole verteilt wird.

**Wichtig:** Dieser Layer ist ausschließlich für **Research, Backtest und Shadow-Trading** gedacht. Er ist **NICHT für Live-Trading** freigegeben!

## Architektur

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATENFLUSS                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Data (OHLCV)                                                  │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────────────┐                                          │
│   │ Single-Strategie │  (z.B. MA-Crossover)                    │
│   │ generate_signals │                                          │
│   └────────┬────────┘                                          │
│            │ Signale: {BTC: 1, ETH: 0, LTC: -1}                 │
│            ▼                                                    │
│   ┌─────────────────────────────────────────┐                  │
│   │       PORTFOLIO STRATEGY LAYER          │ ◄── Phase 26     │
│   │  ┌─────────────────────────────────┐    │                  │
│   │  │     PortfolioContext            │    │                  │
│   │  │  - timestamp                    │    │                  │
│   │  │  - symbols                      │    │                  │
│   │  │  - prices                       │    │                  │
│   │  │  - current_positions            │    │                  │
│   │  │  - strategy_signals             │    │                  │
│   │  │  - returns_history (für Vol)    │    │                  │
│   │  └─────────────────────────────────┘    │                  │
│   │                  │                       │                  │
│   │                  ▼                       │                  │
│   │  ┌─────────────────────────────────┐    │                  │
│   │  │     PortfolioStrategy           │    │                  │
│   │  │  - EqualWeight                  │    │                  │
│   │  │  - FixedWeights                 │    │                  │
│   │  │  - VolTarget                    │    │                  │
│   │  └─────────────────────────────────┘    │                  │
│   └────────────────────┬────────────────────┘                  │
│                        │                                        │
│                        ▼                                        │
│        Target Weights: {BTC: 0.5, ETH: 0.3, LTC: 0.2}          │
│                        │                                        │
│                        ▼                                        │
│   ┌─────────────────────────────────────────┐                  │
│   │         BacktestEngine                  │                  │
│   │  - Position Sizing                      │                  │
│   │  - Order Execution                      │                  │
│   │  - PnL Tracking                         │                  │
│   └─────────────────────────────────────────┘                  │
│                        │                                        │
│                        ▼                                        │
│                   Stats / Report                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Verfügbare Portfolio-Strategien

### 1. Equal-Weight (`equal_weight`)

Verteilt Kapital gleichmäßig auf alle Symbole im Universe.

**Formel:** `w_i = 1/n` für alle Symbole

**Use Case:** Baseline, kein Vorwissen über optimale Gewichtung

**Config:**
```toml
[portfolio]
enabled = true
strategy_name = "equal_weight"
```

### 2. Fixed-Weights (`fixed_weights`)

Verwendet vordefinierte, feste Gewichte aus der Config.

**Use Case:** Manuelle Asset-Allocation, bekannte Präferenzen

**Config:**
```toml
[portfolio]
enabled = true
strategy_name = "fixed_weights"

[portfolio.fixed_weights]
"BTC/EUR" = 0.50
"ETH/EUR" = 0.30
"LTC/EUR" = 0.20
```

### 3. Vol-Target (`vol_target`)

Gewichtet Symbole invers zu ihrer Volatilität (Risk-Parity-Ansatz).

**Formel:** `w_i ~ 1/vol_i`

**Use Case:** Risikoausgleich, alle Assets tragen gleiches Risiko bei

**Config:**
```toml
[portfolio]
enabled = true
strategy_name = "vol_target"
vol_lookback = 20          # Lookback für Vol-Berechnung
vol_target = 0.15          # Ziel-Volatilität (annualisiert)
```

## Config-Referenz

Vollständige Config-Optionen in `config.toml`:

```toml
[portfolio]
# Aktiviert/Deaktiviert den Portfolio-Layer
enabled = true

# Portfolio-Strategie: equal_weight, fixed_weights, vol_target
strategy_name = "equal_weight"

# Symbole im Universe (optional, sonst aus Daten)
symbols = ["BTC/EUR", "ETH/EUR", "LTC/EUR"]

# Rebalancing-Frequenz
rebalance_frequency = 24   # Alle N Bars

# Constraints
max_single_weight = 0.50   # Max 50% in einem Symbol
min_weight = 0.01          # Symbole unter 1% werden ignoriert
normalize_weights = true   # Gewichte auf Summe 1.0 normalisieren

# Vol-Target-Parameter
vol_lookback = 20
vol_target = 0.15

# Fixed Weights (nur für strategy_name = "fixed_weights")
[portfolio.fixed_weights]
"BTC/EUR" = 0.50
"ETH/EUR" = 0.30
"LTC/EUR" = 0.20
```

## Verwendung

### Python API

```python
from src.portfolio import (
    PortfolioConfig,
    PortfolioContext,
    make_portfolio_strategy,
)

# 1. Config erstellen
config = PortfolioConfig(
    enabled=True,
    name="vol_target",
    vol_lookback=20,
)

# 2. Strategie instanziieren
strategy = make_portfolio_strategy(config)

# 3. Context erstellen
context = PortfolioContext(
    timestamp=pd.Timestamp.now(),
    symbols=["BTC/EUR", "ETH/EUR"],
    prices={"BTC/EUR": 50000.0, "ETH/EUR": 3000.0},
    current_positions={"BTC/EUR": 0.0, "ETH/EUR": 0.0},
    returns_history=returns_df,  # Für Vol-Target
    equity=10000.0,
)

# 4. Zielgewichte berechnen
weights = strategy.generate_target_weights(context)
# {"BTC/EUR": 0.4, "ETH/EUR": 0.6}
```

### Backtest-Integration

```python
from src.backtest.engine import run_portfolio_strategy_backtest
from src.strategies.ma_crossover import generate_signals

# Multi-Asset Daten
data = {
    "BTC/EUR": btc_df,
    "ETH/EUR": eth_df,
}

# Backtest mit Portfolio-Layer
result = run_portfolio_strategy_backtest(
    data_dict=data,
    strategy_signal_fn=generate_signals,
    strategy_params={"fast_window": 20, "slow_window": 50},
    portfolio_config=config,
    initial_capital=10000.0,
    fee_bps=10.0,
    rebalance_interval=24,
)

print(f"Return: {result.portfolio_stats['total_return']:.2%}")
print(f"Sharpe: {result.portfolio_stats['sharpe']:.2f}")
```

### Demo-Script

```bash
# Equal-Weight (Default)
python scripts/demo_portfolio_backtest.py

# Vol-Target
python scripts/demo_portfolio_backtest.py --strategy vol_target

# Fixed-Weights mit höherem Kapital
python scripts/demo_portfolio_backtest.py --strategy fixed_weights --initial-capital 50000
```

## Ergebnis-Struktur

`PortfolioStrategyResult` enthält:

| Attribut | Beschreibung |
|----------|--------------|
| `combined_equity` | Gesamte Portfolio-Equity-Curve |
| `symbol_equities` | Equity pro Symbol |
| `target_weights_history` | Zielgewichte über Zeit |
| `actual_weights_history` | Tatsächliche Gewichte über Zeit |
| `portfolio_stats` | Aggregierte Stats (Return, Sharpe, etc.) |
| `trades_per_symbol` | Trades pro Symbol |
| `portfolio_strategy_name` | Name der verwendeten Strategie |
| `metadata` | Zusätzliche Informationen |

## Eigene Portfolio-Strategie erstellen

```python
from src.portfolio.base import BasePortfolioStrategy, PortfolioContext
from src.portfolio.config import PortfolioConfig

class MyPortfolioStrategy(BasePortfolioStrategy):
    """Custom Portfolio-Strategie."""

    def __init__(self, config: PortfolioConfig) -> None:
        super().__init__(config)
        self.name = "MyPortfolioStrategy"

    def _compute_raw_weights(
        self, context: PortfolioContext
    ) -> dict[str, float]:
        """
        Implementiere deine Gewichtungslogik hier.

        Returns:
            Dict mit Gewichten pro Symbol
        """
        universe = self.get_universe(context)

        # Beispiel: Signal-basierte Gewichtung
        weights = {}
        for symbol in universe:
            signal = context.get_signal(symbol)
            if signal > 0:
                weights[symbol] = 1.0
            elif signal < 0:
                weights[symbol] = 0.0
            else:
                weights[symbol] = 0.5

        return weights
```

## Best Practices

1. **Rebalancing-Frequenz:** Zu häufiges Rebalancing erhöht Transaktionskosten
2. **Vol-Lookback:** 20-60 Bars ist typisch für stabile Vol-Schätzung
3. **Max-Weight-Constraint:** Verhindert Über-Konzentration in einem Asset
4. **Normalisierung:** Immer aktivieren, außer du willst bewusst Leverage

## Limitations

- **Kein Live-Trading:** Der Layer ist nur für Research/Backtest konzipiert
- **Long-Only:** Aktuell keine Short-Gewichtung unterstützt
- **Keine Korrelations-Berücksichtigung:** Vol-Target verwendet keine Korrelationsmatrix
- **Synchrone Daten:** Alle Symbole müssen gleiche Zeitstempel haben

## Roadmap

- [ ] Short-Gewichtung für Long/Short-Portfolios
- [ ] Korrelations-basiertes Risk-Parity
- [ ] Momentum-basierte Gewichtung
- [ ] Black-Litterman Integration
- [ ] Live-Trading-Adapter (Phase 27+)

---

**Siehe auch:**
- `docs/BACKTEST_ENGINE.md` - Backtest-Engine Dokumentation
- `docs/ARCHITECTURE.md` - Projekt-Architektur
- `scripts/demo_portfolio_backtest.py` - Demo-Script
