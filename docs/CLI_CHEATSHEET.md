# Peak_Trade CLI Cheatsheet

Schnellreferenz für alle CLI-Tools im Peak_Trade Framework.

---

## 1. Einzelne Backtests

```bash
# Standard-Backtest
python scripts/run_backtest.py --strategy ma_crossover --symbol BTC/EUR

# Mit mehr Bars
python scripts/run_backtest.py --strategy rsi_reversion --bars 500

# Mit Tag für Registry
python scripts/run_backtest.py --strategy macd --tag research-v1
```

---

## 2. Portfolio-Backtests

```bash
# Standard Portfolio-Backtest (aus config.toml)
python scripts/run_portfolio_backtest.py

# Mit Custom-Config
python scripts/run_portfolio_backtest.py --config config/portfolios/my_portfolio.toml

# Mit Tag
python scripts/run_portfolio_backtest.py --tag portfolio-test
```

---

## 2.1. Portfolio-Recipes & Presets (Research-CLI)

**Vordefinierte Portfolio-Konfigurationen für Research-CLI:**

```bash
# Standard-Run mit Preset
python scripts/research_cli.py portfolio \
  --config config/config.toml \
  --portfolio-preset rsi_reversion_balanced

# Preset + Override: mehr Monte-Carlo-Runs
python scripts/research_cli.py portfolio \
  --config config/config.toml \
  --portfolio-preset rsi_reversion_balanced \
  --mc-num-runs 2000

# Preset + Override: anderes Output-Format
python scripts/research_cli.py portfolio \
  --config config/config.toml \
  --portfolio-preset rsi_reversion_balanced \
  --format markdown

# Custom Recipes-Datei
python scripts/research_cli.py portfolio \
  --config config/config.toml \
  --recipes-config config/custom_recipes.toml \
  --portfolio-preset my_custom_preset
```

**Siehe:** [PORTFOLIO_RECIPES_AND_PRESETS.md](PORTFOLIO_RECIPES_AND_PRESETS.md) für Details.

---

## 3. Parameter-Sweeps

```bash
# Sweep mit TOML-Grid
python scripts/run_sweep.py \
    --strategy ma_crossover \
    --symbol BTC/EUR \
    --grid config/sweeps/ma_crossover.toml \
    --tag optimization-v1

# Sweep mit Inline-JSON
python scripts/run_sweep.py \
    --strategy ma_crossover \
    --grid '{"short_window": [5, 10, 20], "long_window": [50, 100]}'

# Limitierter Sweep
python scripts/run_sweep.py \
    --strategy rsi_reversion \
    --grid config/sweeps/rsi_reversion.toml \
    --max-runs 10

# Dry-Run (nur Kombinationen anzeigen)
python scripts/run_sweep.py \
    --strategy ma_crossover \
    --grid config/sweeps/ma_crossover.toml \
    --dry-run
```

---

## 4. Market-Scans

```bash
# Forward-Scan (echte Exchange-Daten)
python scripts/run_market_scan.py \
    --strategy ma_crossover \
    --symbols "BTC/EUR,ETH/EUR,LTC/EUR" \
    --mode forward \
    --tag morning-scan

# Backtest-Lite-Scan (schnell, Dummy-Daten)
python scripts/run_market_scan.py \
    --strategy rsi_reversion \
    --symbols "BTC/EUR,ETH/EUR,SOL/EUR" \
    --mode backtest-lite

# Dry-Run
python scripts/run_market_scan.py \
    --strategy ma_crossover \
    --symbols "BTC/EUR,ETH/EUR" \
    --dry-run
```

---

## 5. Forward-Signals (Out-of-Sample)

```bash
# Forward-Signal für ein Symbol
python scripts/run_forward_signals.py \
    --strategy ma_crossover \
    --symbol BTC/EUR \
    --timeframe 1h \
    --tag daily-signal
```

---

## 6. Live-Workflows

### Order-Preview

```bash
# Forward-Signale generieren
python scripts/generate_forward_signals.py --strategy ma_crossover

# Order-Preview erstellen
python scripts/preview_live_orders.py \
    --signals reports/forward/forward_*.csv \
    --notional 500
```

### Risk-Check

```bash
# Standalone Risk-Check
python scripts/check_live_risk_limits.py \
    --orders reports/live/preview_*_orders.csv \
    --starting-cash 10000

# Mit Enforcement
python scripts/check_live_risk_limits.py \
    --orders reports/live/preview_*_orders.csv \
    --enforce-live-risk
```

### Paper-Trading

```bash
# Paper-Trade ausführen
python scripts/paper_trade_from_orders.py \
    --orders reports/live/preview_*_orders.csv \
    --starting-cash 10000 \
    --tag paper-session
```

---

## 7. Auto-Portfolio-Builder

```bash
# Dry-Run (nur Vorschläge anzeigen)
python scripts/build_auto_portfolios.py --dry-run

# Auto-Portfolios generieren
python scripts/build_auto_portfolios.py \
    --metric sharpe \
    --min-sharpe 0.5 \
    --max-components 3 \
    --output-dir config/portfolios

# Mit Tag-Filter
python scripts/build_auto_portfolios.py \
    --metric sharpe \
    --tag optimization-v1 \
    --prefix auto_ma

# Ein Portfolio pro Strategie
python scripts/build_auto_portfolios.py \
    --mode per-strategy \
    --output-dir config/portfolios
```

---

## 8. Experiments-Analyse

```bash
# Alle Experiments auflisten
python scripts/analyze_experiments.py

# Nach Run-Type filtern
python scripts/analyze_experiments.py --run-type sweep
python scripts/analyze_experiments.py --run-type portfolio_backtest

# Nach Strategie filtern
python scripts/analyze_experiments.py --strategy ma_crossover

# Nach Tag filtern
python scripts/analyze_experiments.py --tag optimization-v1

# Bestimmtes Experiment anzeigen
python scripts/show_experiment.py <run_id>

# Experiments auflisten
python scripts/list_experiments.py --run-type forward_signal
```

---

## 9. Strategie-Registry

```bash
# Verfügbare Strategien auflisten
python -c "from src.strategies.registry import list_strategies; print(list_strategies())"
```

---

## 10. Exchange-Tools

```bash
# Exchange-Info prüfen
python scripts/inspect_exchange.py

# Markets scannen
python scripts/scan_markets.py
```

---

## 11. Order-Layer (Sandbox)

```bash
# Paper-Trades aus Orders-Datei (Standard PaperBroker)
python scripts/paper_trade_from_orders.py \
  --orders reports/live/preview_*_orders.csv \
  --starting-cash 10000 \
  --tag paper-sandbox

# Paper-Trades mit neuem Order-Layer
python scripts/paper_trade_from_orders.py \
  --orders reports/live/preview_*_orders.csv \
  --starting-cash 10000 \
  --use-order-layer \
  --tag order-layer-test

# Live-Order-Preview (ohne Ausführung)
python scripts/preview_live_orders.py \
  --signals reports/forward/forward_*.csv \
  --notional 500 \
  --tag preview-only

# Hinweis: Risk-Violations erzeugen automatisch Alerts (siehe [live_alerts] in config.toml).
# Bei konfigurierten Webhook/Slack-URLs werden Alerts auch an externe Systeme gesendet.
```

---

## 11.1. Live Portfolio Monitoring (Phase 48)

```bash
# Portfolio-Status anzeigen (mit Risk-Check)
python scripts/preview_live_portfolio.py --config config/config.toml

# Portfolio-Status ohne Risk-Check
python scripts/preview_live_portfolio.py --config config/config.toml --no-risk

# JSON-Ausgabe
python scripts/preview_live_portfolio.py --config config/config.toml --json

# Mit Custom Starting-Cash für prozentuale Limits
python scripts/preview_live_portfolio.py \
  --config config/config.toml \
  --starting-cash 20000.0
```

**Siehe:** [PHASE_48_LIVE_PORTFOLIO_MONITORING_AND_RISK_BRIDGE.md](PHASE_48_LIVE_PORTFOLIO_MONITORING_AND_RISK_BRIDGE.md) für Details.

**Hinweis:** Risk-Violations erzeugen automatisch Alerts (siehe [live_alerts] in config.toml). Bei konfigurierten Webhook/Slack-URLs werden Alerts auch an externe Systeme gesendet (siehe [PHASE_49_LIVE_ALERTS_AND_NOTIFICATIONS.md](PHASE_49_LIVE_ALERTS_AND_NOTIFICATIONS.md) und [PHASE_50_LIVE_ALERT_WEBHOOKS_AND_SLACK.md](PHASE_50_LIVE_ALERT_WEBHOOKS_AND_SLACK.md)).

---

## 12. Live-Ops CLI (Phase 51)

Zentrales Operator-Cockpit für Live-/Testnet-Operationen.

| Command                                             | Beschreibung                         |
| --------------------------------------------------- | ------------------------------------ |
| `python scripts/live_ops.py orders --signals ...`   | Live-Orders-Preview + Risk-Check     |
| `python scripts/live_ops.py portfolio --config ...` | Live-Portfolio-Snapshot + Risk-Check |
| `python scripts/live_ops.py health --config ...`    | Health-Check für Live-/Testnet-Setup |

### Orders-Preview

```bash
# Standard-Ansicht
python scripts/live_ops.py orders \
  --signals reports/forward/forward_*_signals.csv \
  --config config/config.toml

# JSON-Output
python scripts/live_ops.py orders \
  --signals reports/forward/forward_*_signals.csv \
  --config config/config.toml \
  --json
```

**Siehe:** [PHASE_51_LIVE_OPS_CLI.md](PHASE_51_LIVE_OPS_CLI.md) für Details.

### Portfolio-Monitoring

```bash
# Standard-Ansicht
python scripts/live_ops.py portfolio --config config/config.toml

# JSON-Output
python scripts/live_ops.py portfolio --config config/config.toml --json

# Ohne Risk-Check
python scripts/live_ops.py portfolio --config config/config.toml --no-risk
```

**Siehe:** [PHASE_48_LIVE_PORTFOLIO_MONITORING_AND_RISK_BRIDGE.md](PHASE_48_LIVE_PORTFOLIO_MONITORING_AND_RISK_BRIDGE.md) für Details.

### Health-Check

```bash
# Text-Output
python scripts/live_ops.py health --config config/config.toml

# JSON-Output
python scripts/live_ops.py health --config config/config.toml --json
```

**Hinweis:** Health-Check prüft Config, Exchange, Alerts und Live-Risk-Limits. Exit-Code 0 = OK/DEGRADED, 1 = FAIL.

**Siehe:** [PHASE_51_LIVE_OPS_CLI.md](PHASE_51_LIVE_OPS_CLI.md) für Details.

---

## 13. Scheduler & Job Runner

```bash
# Scheduler Dry-Run (nur anzeigen)
python scripts/run_scheduler.py --config config/scheduler/jobs.toml --dry-run --once

# Alle fälligen Jobs einmal ausführen
python scripts/run_scheduler.py --config config/scheduler/jobs.toml --once

# Scheduler als Daemon starten (alle 60s prüfen)
python scripts/run_scheduler.py --config config/scheduler/jobs.toml --poll-interval 60

# Nur Jobs mit bestimmten Tags
python scripts/run_scheduler.py --include-tags forward,daily --once

# Jobs mit bestimmten Tags ausschließen
python scripts/run_scheduler.py --exclude-tags heavy --once

# Verbose Output
python scripts/run_scheduler.py --dry-run --verbose --once

# Ohne Registry-Logging
python scripts/run_scheduler.py --no-registry --once

# Ohne Alerts
python scripts/run_scheduler.py --no-alerts --once

# Scheduler-Jobs in Registry anzeigen
python scripts/list_experiments.py --run-type scheduler_job
```

---

## Häufige Kombinationen

### Vollständiger Optimierungs-Workflow

```bash
# 1. Parameter-Sweep
python scripts/run_sweep.py \
    --strategy ma_crossover \
    --grid config/sweeps/ma_crossover.toml \
    --tag opt-v1

# 2. Auto-Portfolio generieren
python scripts/build_auto_portfolios.py \
    --tag opt-v1 \
    --min-sharpe 0.5 \
    --output-dir config/portfolios

# 3. Portfolio backtesten
python scripts/run_portfolio_backtest.py \
    --config config/portfolios/auto_portfolio_*.toml \
    --tag auto-test
```

### Morning-Scan + Trade

```bash
# 1. Symbole scannen
python scripts/run_market_scan.py \
    --strategy ma_crossover \
    --symbols "BTC/EUR,ETH/EUR,LTC/EUR" \
    --mode forward \
    --tag morning

# 2. Forward-Signals
python scripts/run_forward_signals.py \
    --strategy ma_crossover \
    --symbol BTC/EUR

# 3. Order-Preview
python scripts/preview_live_orders.py \
    --signals reports/forward/*.csv \
    --notional 500 \
    --enforce-live-risk
```

---

## Wichtige Flags

| Flag | Beschreibung |
|------|--------------|
| `--dry-run` | Nur anzeigen, nicht ausführen |
| `--tag` | Tag für Registry-Filterung |
| `--config` | Custom TOML-Config-Pfad |
| `--strategy` | Strategie-Key |
| `--symbol` | Trading-Pair |
| `--timeframe` | Timeframe (1h, 4h, 1d) |
| `--bars` | Anzahl Bars |
| `--enforce-live-risk` | Abbruch bei Risk-Violation |
| `--skip-live-risk` | Risk-Check überspringen |

---

## Für Entwickler

**Architektur & Developer-Guides:**

- [`ARCHITECTURE_OVERVIEW.md`](ARCHITECTURE_OVERVIEW.md) – High-Level-Architektur mit Diagramm und Layer-Beschreibung
- [`DEV_GUIDE_ADD_STRATEGY.md`](DEV_GUIDE_ADD_STRATEGY.md) – Neue Strategie hinzufügen (inkl. CLI-Beispiele)
- [`DEV_GUIDE_ADD_EXCHANGE.md`](DEV_GUIDE_ADD_EXCHANGE.md) – Neuen Exchange-Adapter hinzufügen
- [`DEV_GUIDE_ADD_LIVE_RISK_LIMIT.md`](DEV_GUIDE_ADD_LIVE_RISK_LIMIT.md) – Neues Live-Risk-Limit hinzufügen
- [`DEV_GUIDE_ADD_PORTFOLIO_RECIPE.md`](DEV_GUIDE_ADD_PORTFOLIO_RECIPE.md) – Neues Portfolio-Rezept hinzufügen (inkl. CLI-Beispiele)

Die Developer-Guides erklären typische Erweiterungen Schritt für Schritt, inkl. CLI-Beispiele für Tests und Integration.

---

## Siehe auch

- [AUTO_PORTFOLIOS.md](AUTO_PORTFOLIOS.md) - Auto-Portfolio-Builder
- [SWEEPS_MARKET_SCANS.md](SWEEPS_MARKET_SCANS.md) - Parameter-Optimierung
- [LIVE_WORKFLOWS.md](LIVE_WORKFLOWS.md) - Live-Trading
- [NOTIFICATIONS.md](NOTIFICATIONS.md) - Alerts & Notifications
- [SCHEDULER_DAEMON.md](SCHEDULER_DAEMON.md) - Scheduler & Job Runner
- [ORDER_LAYER_SANDBOX.md](ORDER_LAYER_SANDBOX.md) - Order-Layer (Sandbox)

---

## Live-Ops Quick Commands (Operator-Favoriten)

**Die 3 wichtigsten Commands für Live-/Testnet-Operationen:**

```bash
# 1. Health-Check Live-/Testnet-Setup
python scripts/live_ops.py health --config config/config.toml

# 2. Portfolio-Snapshot (Text)
python scripts/live_ops.py portfolio --config config/config.toml

# 3. Portfolio-Snapshot (JSON für Tools)
python scripts/live_ops.py portfolio --config config/config.toml --json
```

**Mit diesen 3 Commands weißt du sofort:**
- ✅ Ob das Live-/Testnet-Setup gesund ist
- ✅ Welche Positionen aktuell offen sind
- ✅ Wie das Portfolio-Risk-Profil aussieht
- ✅ Ob Risk-Limits eingehalten werden

**Weitere nützliche Varianten:**

```bash
# Health-Check mit JSON-Output
python scripts/live_ops.py health --config config/config.toml --json

# Portfolio ohne Risk-Check (schneller)
python scripts/live_ops.py portfolio --config config/config.toml --no-risk

# Orders-Preview (wenn Signale vorhanden)
python scripts/live_ops.py orders \
  --signals reports/forward/forward_*_signals.csv \
  --config config/config.toml
```
