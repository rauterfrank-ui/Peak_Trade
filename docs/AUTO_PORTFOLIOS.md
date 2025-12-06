# Peak_Trade: Auto-Portfolio-Builder

Der Auto-Portfolio-Builder generiert automatisch Portfolio-Kandidaten aus Sweep- und Market-Scan-Ergebnissen.

---

## Konzept

### Warum automatische Portfolios?

Nach einer Parameter-Optimierung (Sweep) oder einem Market-Scan stellt sich die Frage:
**Welche Strategien und Symbole sollte ich in mein Portfolio aufnehmen?**

Der Auto-Portfolio-Builder beantwortet diese Frage:

1. **Analysiert Sweep-Ergebnisse**: Findet die besten Parameterkombinationen
2. **Rankt nach Metrik**: Sharpe, Return oder CAGR
3. **Erstellt Portfolio-Config**: TOML-Datei für `run_portfolio_backtest.py`

### Workflow

```
Sweeps → Registry → Auto-Builder → TOML-Configs → Portfolio-Backtest
```

---

## CLI-Tool: scripts/build_auto_portfolios.py

### Argumente

| Argument | Beschreibung | Default |
|----------|--------------|---------|
| `--metric` | Ranking-Metrik: `sharpe`, `total_return`, `cagr` | `sharpe` |
| `--min-sharpe` | Minimaler Sharpe für Aufnahme | - |
| `--min-return` | Minimaler Total-Return | - |
| `--max-components` | Max. Komponenten pro Portfolio | `5` |
| `--tag` | Filter auf bestimmten Tag | - |
| `--strategy` | Filter auf Strategie(n) (komma-separiert) | - |
| `--mode` | `combined` oder `per-strategy` | `combined` |
| `--allocation` | `equal` oder `metric_weighted` | `equal` |
| `--initial-equity` | Anfangskapital | `10000.0` |
| `--prefix` | Prefix für Portfolio-Namen | `auto_portfolio` |
| `--output-dir` | Output-Verzeichnis | `config/portfolios` |
| `--include-scans` | Market-Scans einbeziehen | False |
| `--dry-run` | Nur anzeigen, nicht speichern | False |

---

## Beispiele

### 1. Dry-Run (Vorschau)

Zeigt, welche Portfolios generiert würden:

```bash
python scripts/build_auto_portfolios.py --dry-run
```

### 2. Portfolio aus Sweeps generieren

```bash
python scripts/build_auto_portfolios.py \
    --metric sharpe \
    --min-sharpe 0.5 \
    --max-components 3 \
    --output-dir config/portfolios
```

### 3. Mit Tag-Filter

Nur Sweeps mit bestimmtem Tag verwenden:

```bash
python scripts/build_auto_portfolios.py \
    --metric sharpe \
    --tag optimization-v1 \
    --prefix auto_ma \
    --output-dir config/portfolios
```

### 4. Ein Portfolio pro Strategie

Erstellt separate Portfolios für jede Strategie:

```bash
python scripts/build_auto_portfolios.py \
    --mode per-strategy \
    --max-components 3 \
    --output-dir config/portfolios
```

### 5. Metric-weighted Allocation

Gewichtet nach Sharpe statt gleichmäßig:

```bash
python scripts/build_auto_portfolios.py \
    --allocation metric_weighted \
    --max-components 5 \
    --output-dir config/portfolios
```

---

## Generierte TOML-Struktur

Beispiel einer generierten `config/portfolios/auto_portfolio_3comp_20250104_120000.toml`:

```toml
# Auto-Generated Portfolio: auto_portfolio_3comp_20250104_120000
# Created: 2025-01-04T12:00:00Z

[portfolio]
name = "auto_portfolio_3comp_20250104_120000"
initial_equity = 10000.0
allocation_method = "equal"

symbols = ["BTC/EUR", "ETH/EUR", "LTC/EUR"]

asset_weights = [0.3333, 0.3333, 0.3334]

strategy_key = "ma_crossover"

[portfolio.strategies]
"BTC/EUR" = "ma_crossover"
"ETH/EUR" = "ma_crossover"
"LTC/EUR" = "rsi_reversion"

# ==========================================================
# Component Details (for reference)
# ==========================================================

# Component 1: BTC/EUR
#   Strategy: ma_crossover
#   Timeframe: 1h
#   Weight: 0.3333
#   Metric Score: 1.5000
#   Source Run ID: abc-123-def-456
#   Params: { short_window=10, long_window=50 }

# Component 2: ETH/EUR
#   Strategy: ma_crossover
#   ...
```

---

## Kombination mit Portfolio-Backtest

Nach der Generierung können die Portfolios getestet werden:

```bash
# 1. Auto-Portfolio generieren
python scripts/build_auto_portfolios.py \
    --metric sharpe \
    --max-components 3 \
    --output-dir config/portfolios

# 2. Generiertes Portfolio backtesten
python scripts/run_portfolio_backtest.py \
    --config config/portfolios/auto_portfolio_3comp_*.toml \
    --tag auto-portfolio-test

# 3. Ergebnisse analysieren
python scripts/analyze_experiments.py \
    --run-type portfolio_backtest \
    --tag auto-portfolio-test
```

---

## Typische Workflows

### Workflow 1: Vollständige Optimierung

```bash
# 1. Sweeps für mehrere Strategien
python scripts/run_sweep.py \
    --strategy ma_crossover \
    --symbol BTC/EUR \
    --grid config/sweeps/ma_crossover.toml \
    --tag opt-v1

python scripts/run_sweep.py \
    --strategy rsi_reversion \
    --symbol ETH/EUR \
    --grid config/sweeps/rsi_reversion.toml \
    --tag opt-v1

# 2. Auto-Portfolio generieren
python scripts/build_auto_portfolios.py \
    --tag opt-v1 \
    --max-components 5 \
    --min-sharpe 0.5 \
    --output-dir config/portfolios

# 3. Portfolio backtesten
python scripts/run_portfolio_backtest.py \
    --config config/portfolios/auto_portfolio_*.toml
```

### Workflow 2: Strategie-Vergleich

```bash
# 1. Ein Portfolio pro Strategie
python scripts/build_auto_portfolios.py \
    --mode per-strategy \
    --max-components 3 \
    --output-dir config/portfolios

# 2. Alle Portfolios backtesten
for config in config/portfolios/auto_*.toml; do
    python scripts/run_portfolio_backtest.py --config $config
done

# 3. Vergleichen
python scripts/analyze_experiments.py \
    --run-type portfolio_backtest
```

---

## API-Funktionen

### Dataclasses

```python
from src.analytics.portfolio_builder import (
    PortfolioComponentCandidate,
    PortfolioCandidate,
)

# Eine Portfolio-Komponente
comp = PortfolioComponentCandidate(
    symbol="BTC/EUR",
    strategy_key="ma_crossover",
    timeframe="1h",
    weight=0.33,
    source_run_id="abc-123",
    metric_score=1.5,
    params={"short_window": 10, "long_window": 50},
)

# Ein komplettes Portfolio
portfolio = PortfolioCandidate(
    name="my_portfolio",
    components=[comp],
    allocation_method="equal",
    initial_equity=10000.0,
)
```

### Selektion

```python
from src.analytics.portfolio_builder import select_top_sweep_components

# Beste Sweep-Ergebnisse selektieren
components = select_top_sweep_components(
    df,
    metric="sharpe",
    max_per_symbol=1,
    max_total=5,
    min_sharpe=0.5,
)
```

### Builder

```python
from src.analytics.portfolio_builder import (
    build_portfolio_candidates_from_sweeps_and_scans,
    write_portfolio_candidate_to_toml,
)

# Portfolio-Kandidaten bauen
candidates = build_portfolio_candidates_from_sweeps_and_scans(
    df_sweeps=df_sweeps,
    metric="sharpe",
    max_components=5,
    min_sharpe=0.5,
)

# Als TOML exportieren
for cand in candidates:
    write_portfolio_candidate_to_toml(cand, Path(f"config/portfolios/{cand.name}.toml"))
```

---

## Hinweise

### Keine Garantie für Erfolg

Die generierten Portfolios basieren auf **historischen Daten**.
Ein guter Backtest-Sharpe bedeutet nicht, dass die Strategie in Zukunft profitabel ist.

**Empfehlung:**
1. Portfolios auf Out-of-Sample-Daten testen
2. Forward-Testing durchführen
3. Mit kleinen Positionen starten

### Startpunkt für Research

Der Auto-Builder ist ein **Startpunkt**, nicht das Endprodukt:
- Generierte Portfolios manuell überprüfen
- Diversifikation prüfen (nicht nur Crypto-Assets)
- Risk-Limits anpassen

### Sweep-Daten erforderlich

Der Builder benötigt Sweep-Ergebnisse in der Registry:

```bash
# Falls keine Daten vorhanden
python scripts/run_sweep.py \
    --strategy ma_crossover \
    --grid config/sweeps/ma_crossover.toml
```

---

## Troubleshooting

### "No sweep results found"

Führe zuerst Sweeps durch:
```bash
python scripts/run_sweep.py \
    --strategy ma_crossover \
    --grid '{"short_window": [5, 10, 20], "long_window": [50, 100]}'
```

### "No portfolio candidates generated"

Senke die Mindestanforderungen:
```bash
python scripts/build_auto_portfolios.py \
    --min-sharpe 0.0 \
    --max-components 10
```

### TOML-Datei funktioniert nicht

Prüfe die Struktur mit:
```bash
cat config/portfolios/auto_*.toml
```

Die Datei muss `[portfolio]`, `symbols = [...]` und `strategy_key = "..."` enthalten.

---

## Siehe auch

- [SWEEPS_MARKET_SCANS.md](SWEEPS_MARKET_SCANS.md) - Parameter-Optimierung
- [LIVE_WORKFLOWS.md](LIVE_WORKFLOWS.md) - Live-Trading-Workflows
- [STRATEGY_DEV_GUIDE.md](STRATEGY_DEV_GUIDE.md) - Eigene Strategien entwickeln
