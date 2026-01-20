# Registry Portfolio Backtest CLI

End-to-End Portfolio-Backtest mit echten Marktdaten über die Strategien-Registry.

## Features

- ✅ **Echte Marktdaten**: Lädt OHLCV-Daten von Kraken über den Data-Layer
- ✅ **Registry-Integration**: Nutzt Strategien und Portfolio-Config aus `config.toml`
- ✅ **Multi-Strategie**: Gleichzeitiger Backtest mehrerer Strategien
- ✅ **Risk-Management**: Vollständige Integration des Risk-Layers
- ✅ **Flexible Filterung**: Nach Marktregime oder Custom-Liste
- ✅ **Export**: Ergebnisse als CSV/JSON speichern
- ✅ **Caching**: Automatisches Caching für schnellere Re-Runs

## Schnellstart

```bash
cd ~/Peak_Trade

# Einfachster Aufruf (mit Defaults)
python scripts/run_registry_portfolio_backtest.py

# Nur Config anzeigen (ohne Backtest)
python scripts/run_registry_portfolio_backtest.py --dry-run

# Kraken-Verbindung testen
python scripts/run_registry_portfolio_backtest.py --test-connection
```

## CLI-Parameter

### Data-Parameter

```bash
--symbol BTC/USD          # Trading-Pair (default: BTC/USD)
--timeframe 1h            # Timeframe: 1m, 5m, 15m, 1h, 4h, 1d (default: 1h)
--limit 720               # Anzahl Bars (max. 720) (default: 720)
--no-cache                # Cache deaktivieren (immer frisch von Kraken)
```

### Portfolio-Parameter

```bash
--portfolio default       # Portfolio-Name aus config.toml (default: default)
--strategies ma_crossover momentum_1h  # Custom Strategien (überschreibt active)
--regime trending         # Filtere nach Marktregime (trending/ranging/any)
```

### Output-Parameter

```bash
--output-dir results/my_backtest  # Output-Verzeichnis
--export-trades                   # Trades als CSV
--export-equity                   # Equity-Curve als CSV
--export-stats                    # Stats als JSON
--export-all                      # Alle Exports aktivieren
```

### Kontrolle

```bash
--dry-run                 # Nur Setup anzeigen, kein Backtest
--verbose                 # DEBUG-Level Logging
--test-connection         # Kraken-Verbindung testen
```

## Beispiele

### Standard-Backtest mit Portfolio-Default

```bash
python scripts/run_registry_portfolio_backtest.py
```

Nutzt:
- Symbol: BTC/USD
- Timeframe: 1h
- Bars: 720 (30 Tage)
- Strategien: Alle aktiven aus `config.toml`

### Custom Symbol und Timeframe

```bash
python scripts/run_registry_portfolio_backtest.py \
    --symbol ETH/EUR \
    --timeframe 4h \
    --limit 500
```

### Nur Trending-Strategien

```bash
python scripts/run_registry_portfolio_backtest.py \
    --regime trending
```

Filtert automatisch alle Strategien mit `best_market_regime = "trending"` aus der Registry.

### Custom Strategie-Liste

```bash
python scripts/run_registry_portfolio_backtest.py \
    --strategies ma_crossover momentum_1h
```

Nutzt nur die angegebenen Strategien, ignoriert `strategies.active`.

### Mit vollständigem Export

```bash
python scripts/run_registry_portfolio_backtest.py \
    --limit 500 \
    --output-dir results/btc_usd_1h \
    --export-all
```

Erstellt:
- `results/btc_usd_1h/portfolio_stats_TIMESTAMP.json`
- `results/btc_usd_1h/portfolio_equity_TIMESTAMP.csv`
- `results/btc_usd_1h/trades_STRATEGY_TIMESTAMP.csv` (pro Strategie)

### Verbose Logging (für Debugging)

```bash
python scripts/run_registry_portfolio_backtest.py \
    --verbose \
    --limit 100
```

## Output-Format

### Terminal-Output

```
======================================================================
  Peak_Trade - Registry Portfolio Backtest
======================================================================

📋 KONFIGURATION
----------------------------------------------------------------------
  Symbol:          BTC/USD
  Timeframe:       1h
  Bars:            720
  Cache:           Ja

  Portfolio:       default
  Allocation:      equal
  Total Capital:   $10,000.00

  Strategien:      3 aktiv
  Quelle:          config.toml (strategies.active)
    1. ma_crossover
    2. momentum_1h
    3. rsi_strategy
----------------------------------------------------------------------

======================================================================
  ERGEBNISSE
======================================================================

📊 PORTFOLIO-PERFORMANCE
----------------------------------------------------------------------
  Total Return:         12.34%
  Sharpe Ratio:          1.85
  Max Drawdown:        -8.50%
  Strategien:               3
  Allocation:           equal

📋 STRATEGIE-EINZELERGEBNISSE
----------------------------------------------------------------------

  ma_crossover (Allocation: 33.3%)
    Return:              8.20%
    Sharpe:               1.45
    Max DD:             -5.30%
    Trades:                 15
    Win Rate:            60.0%
    Profit Factor:        1.82
    Blocked:                 3

  [...]

🔍 LIVE-TRADING-VALIDIERUNG
----------------------------------------------------------------------
  ✅ Strategie ERFÜLLT Mindestanforderungen für Live-Trading
----------------------------------------------------------------------
```

### JSON-Export (Stats)

```json
{
  "portfolio_stats": {
    "total_return": 0.1234,
    "max_drawdown": -0.085,
    "sharpe": 1.85,
    "num_strategies": 3,
    "allocation_method": "equal",
    "ma_crossover_return": 0.082,
    "ma_crossover_sharpe": 1.45,
    "ma_crossover_trades": 15
  },
  "allocation": {
    "ma_crossover": 0.3333,
    "momentum_1h": 0.3333,
    "rsi_strategy": 0.3333
  },
  "strategy_stats": {
    "ma_crossover": {
      "stats": { ... },
      "blocked_trades": 3,
      "mode": "realistic_with_risk_management"
    }
  }
}
```

### CSV-Export (Equity)

```csv
,portfolio,ma_crossover,momentum_1h,rsi_strategy
2025-11-01 00:00:00+00:00,10000.0,3333.33,3333.33,3333.33
2025-11-01 01:00:00+00:00,10050.0,3350.00,3340.00,3360.00
...
```

### CSV-Export (Trades)

```csv
entry_time,entry_price,size,stop_price,exit_time,exit_price,pnl,pnl_pct,exit_reason
2025-11-01 10:00:00+00:00,50000.0,0.15,49000.0,2025-11-01 15:00:00+00:00,51000.0,150.0,2.0,signal
...
```

## Workflow

1. **Daten laden**: Kraken → Normalizer → Cache
2. **Portfolio bestimmen**: Registry → Active/Filtered Strategies
3. **Backtest ausführen**: Engine → Risk-Layer → Trades
4. **Stats berechnen**: Individual + Portfolio-Level
5. **Validierung**: Live-Trading-Kriterien prüfen
6. **Export**: CSV/JSON schreiben

## Troubleshooting

### "Config nicht gefunden"

```bash
# Config liegt in config/config.toml (nicht im Root)
# Prüfe Pfad:
ls -l config/config.toml

# Oder setze Environment Variable:
export PEAK_TRADE_CONFIG=config/config.toml
python scripts/run_registry_portfolio_backtest.py
```

### "Kraken-Verbindung fehlgeschlagen"

```bash
# Teste Verbindung:
python scripts/run_registry_portfolio_backtest.py --test-connection

# Häufige Ursachen:
# - Keine Internetverbindung
# - Kraken API down
# - Rate-Limiting (warte 60 Sekunden)
```

### Keine Trades generiert

```bash
# Mögliche Gründe:
# 1. Zeitfenster zu klein: --limit 500 statt 200
# 2. Strategien finden keine Signale in diesem Markt
# 3. Risk-Management blockiert (siehe "Blocked Trades" in Output)
# 4. Strategie-Parameter passen nicht zum Markt

# Lösung: Mehr Bars oder anderen Zeitraum testen
python scripts/run_registry_portfolio_backtest.py --limit 720
```

### "Pandas FutureWarning"

Diese Warnings sind nicht kritisch, wurden aber in der neuesten Version behoben.

## Integration mit bestehenden Scripts

Dieses Script nutzt dieselben Module wie:
- `scripts/demo_registry_backtest.py` (Demo mit künstlichen Daten)
- `scripts/demo_config_registry.py` (Registry-Demo)

Unterschied:
- **Demo-Scripts**: Künstliche Daten, schnell, für Entwicklung
- **Dieser Script**: Echte Kraken-Daten, langsamer, für echte Backtests

## Nächste Schritte

1. **Parameter-Optimierung**: Strategie-Parameter in `config.toml` anpassen
2. **Regime-Analyse**: Testen welche Strategien in welchen Märkten funktionieren
3. **Walk-Forward**: Mehrere Zeitfenster backtesten
4. **Live-Trading**: Nach erfolgreichen Backtests Paper-Trading starten

## Siehe auch

- [CONFIG_REGISTRY_USAGE.md](CONFIG_REGISTRY_USAGE.md) - Strategien-Registry
- [REGISTRY_BACKTEST_API.md](REGISTRY_BACKTEST_API.md) - Engine-API
- [RISK_MANAGEMENT.md](project_docs/RISK_MANAGEMENT.md) - Risk-Layer Dokumentation
