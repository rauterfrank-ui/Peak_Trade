# Peak_Trade: Live-/Paper-Workflows

Diese Dokumentation beschreibt die Standard-Workflows für Live- und Paper-Trading.

## Kern-CLI-Argumente (konsistent über alle Scripts)

| Argument | Beschreibung | Default |
|----------|--------------|---------|
| `--config` | Pfad zur TOML-Config | `config.toml` |
| `--tag` | Optionaler Tag für Registry-Logging | - |
| `--enforce-live-risk` | Bei Verletzung mit Exit-Code 1 abbrechen | False |
| `--skip-live-risk` | Risk-Check komplett überspringen | False |
| `--starting-cash` | Startkapital für Daily-Loss-%-Limits | aus Config |
| `--alert-log` | Pfad zur Alert-Logdatei | `logs/alerts.log` |
| `--no-alerts` | Alert-Benachrichtigungen deaktivieren | False |

**Wichtig:** `--enforce-live-risk` und `--skip-live-risk` können nicht gleichzeitig verwendet werden.

---

## Workflow 1: Order-Preview mit Risk-Check

Generiert Orders aus Forward-Signalen und prüft sie gegen Live-Risk-Limits.

```bash
# 1. Forward-Signale generieren
python scripts/generate_forward_signals.py --strategy ma_crossover

# 2. Order-Preview erstellen (mit Risk-Check)
python scripts/preview_live_orders.py \
    --signals reports/forward/forward_ma_crossover_..._signals.csv \
    --notional 500 \
    --tag daily-preview
```

### Registry-Logging
- **run_type:** `live_risk_check`
- **Gespeichert:** Risk-Check-Ergebnis mit Metriken

---

## Workflow 2: Standalone Risk-Check

Prüft eine bestehende Orders-CSV ohne neue Orders zu generieren.

```bash
python scripts/check_live_risk_limits.py \
    --orders reports/live/preview_..._orders.csv \
    --starting-cash 10000 \
    --tag daily-check
```

### Mit Enforcement (Exit bei Verletzung)
```bash
python scripts/check_live_risk_limits.py \
    --orders reports/live/preview_..._orders.csv \
    --enforce-live-risk
```

### Registry-Logging
- **run_type:** `live_risk_check`
- **Gespeichert:** Metriken, allowed-Status, Violations

---

## Workflow 3: Paper-Trade mit Risk-Check

Führt Paper-Trades aus einer Orders-CSV aus.

```bash
# Standard Paper-Trade
python scripts/paper_trade_from_orders.py \
    --orders reports/live/preview_..._orders.csv \
    --starting-cash 10000 \
    --tag paper-session

# Mit Enforcement (kein Trade bei Violation)
python scripts/paper_trade_from_orders.py \
    --orders reports/live/preview_..._orders.csv \
    --starting-cash 10000 \
    --enforce-live-risk \
    --tag paper-session

# Ohne Risk-Check (z.B. für Tests)
python scripts/paper_trade_from_orders.py \
    --orders reports/live/preview_..._orders.csv \
    --skip-live-risk \
    --tag paper-test
```

### Registry-Logging
- **run_type:** `paper_trade` (für den Trade)
- **run_type:** `live_risk_check` (für den vorgeschalteten Check)
- **Gespeichert:** PnL, Equity, Fees, Positionen

---

## Vollständiger Daily-Workflow

```bash
#!/bin/bash
# daily_trade.sh - Täglicher Trading-Workflow

set -e  # Bei Fehler abbrechen

# 1. Forward-Signale generieren
echo "=== Generiere Forward-Signale ==="
python scripts/generate_forward_signals.py \
    --strategy ma_crossover \
    --tag daily

# 2. Order-Preview erstellen
echo "=== Erstelle Order-Preview ==="
python scripts/preview_live_orders.py \
    --signals reports/forward/forward_ma_crossover_*_signals.csv \
    --notional 500 \
    --tag daily

# 3. Standalone Risk-Check (optional, strenger)
echo "=== Standalone Risk-Check ==="
python scripts/check_live_risk_limits.py \
    --orders reports/live/preview_*_orders.csv \
    --starting-cash 10000 \
    --enforce-live-risk \
    --tag daily-check

# 4. Paper-Trade ausführen
echo "=== Paper-Trade ==="
python scripts/paper_trade_from_orders.py \
    --orders reports/live/preview_*_orders.csv \
    --starting-cash 10000 \
    --tag daily-paper

echo "=== Daily-Workflow abgeschlossen ==="
```

---

## Risk-Check Verhalten

### Standard (ohne Flags)
- Risk-Check wird durchgeführt
- Bei Verletzung: **Warnung**, Workflow läuft weiter
- Ergebnis wird in Registry geloggt

### Mit `--enforce-live-risk`
- Risk-Check wird durchgeführt
- Bei Verletzung: **Exit mit Code 1**, Workflow stoppt
- Ergebnis wird in Registry geloggt

### Mit `--skip-live-risk`
- Risk-Check wird **übersprungen**
- Workflow läuft ohne Prüfung
- Kein Registry-Eintrag für Risk-Check

---

## Experiments-Registry Run-Types

| run_type | Script | Beschreibung |
|----------|--------|--------------|
| `live_risk_check` | check_live_risk_limits.py, preview_live_orders.py | Risk-Limit-Prüfung |
| `paper_trade` | paper_trade_from_orders.py | Paper-Trade-Ausführung |
| `forward_signal` | generate_forward_signals.py | Forward-Signal-Generierung |
| `backtest` | run_backtest.py | Backtest-Ergebnis |

---

## Forward-Signals (Out-of-Sample)

Forward-Signals sind "virtuelle Trades", die auf aktuellen Marktdaten basieren,
aber keine echten Orders platzieren. Sie dienen als Brücke zwischen Backtest und Live-Trading.

### Quick Start

```bash
# Forward-Signal für ein Symbol generieren
python scripts/run_forward_signals.py \
    --strategy ma_crossover \
    --symbol BTC/EUR \
    --timeframe 1h \
    --bars 200 \
    --tag morning-scan
```

### CLI-Argumente

| Argument | Beschreibung | Default |
|----------|--------------|---------|
| `--config` | Pfad zur TOML-Config | `config.toml` |
| `--strategy` | Strategie-Key (erforderlich) | - |
| `--symbol` | Trading-Pair (erforderlich) | - |
| `--timeframe` | Timeframe für OHLCV-Daten | `1h` |
| `--bars` | Anzahl der letzten Bars | 200 |
| `--tag` | Optionaler Tag für Registry | - |
| `--dry-run` | Nur berechnen, nicht loggen | False |

### Beispiel-Output

```text
[Forward Signal] run_id=abcd-1234-5678-efgh
  Exchange   : kraken
  Symbol     : BTC/EUR
  Timeframe  : 1h
  Timestamp  : 2025-12-05T10:00:00+00:00
  Last Close : 43250.00
  Signal     : +1 (LONG)
  Strategy   : ma_crossover
  Tag        : morning-scan
```

### Registry-Logging

- **run_type:** `forward_signal`
- **Gespeichert:** Symbol, Timeframe, Strategy-Key, letztes Signal, Preis

### Ergebnisse anzeigen

```bash
# Alle Forward-Signal-Runs auflisten
python scripts/list_experiments.py --run-type forward_signal

# Details zu einem Run anzeigen
python scripts/show_experiment.py <run_id>
```

### Unterschied zu generate_forward_signals.py

| Script | Datenquelle | Fokus |
|--------|-------------|-------|
| `run_forward_signals.py` | Echter Exchange-Client | Einzelnes Symbol, Out-of-Sample |
| `generate_forward_signals.py` | Dummy-Daten/Simulation | Symbol-Universum, Batch-Verarbeitung |

---

## Troubleshooting

### "Konflikt: --enforce-live-risk und --skip-live-risk"
Diese Flags schließen sich gegenseitig aus. Verwende nur eines.

### "max_daily_loss_pct nicht geprüft"
Das prozentuale Limit benötigt `--starting-cash`. Stelle sicher, dass:
```bash
--starting-cash 10000
```
oder in config.toml:
```toml
[live]
starting_cash_default = 10000.0
```

### "Daily-PnL immer 0"
Prüfe:
1. Gibt es `reports/experiments/experiments.csv`?
2. Sind Einträge mit `run_type = "paper_trade"` vom heutigen Tag vorhanden?
3. Ist `use_experiments_for_daily_pnl = true` in config.toml?

---

## Notifications & Alerts

Scripts wie `run_forward_signals.py` und `check_live_risk_limits.py` senden automatisch Alerts.

### Alert-Output (Console)

```text
[2025-01-01T12:00:00] [WARNING] [forward_signal] ma_crossover on BTC/EUR (1h): LONG @ 43250.00
[2025-01-01T12:05:00] [CRITICAL] [live_risk] Live-Risk-Verletzung: max_order_notional exceeded
```

### Alert-Levels

| Level | Bedeutung | Beispiel |
|-------|-----------|----------|
| `INFO` | Normale Information | Signal berechnet, Check bestanden |
| `WARNING` | Aufmerksamkeit | Starkes LONG/SHORT-Signal |
| `CRITICAL` | Sofortige Aktion | Risk-Verletzung |

### Alerts deaktivieren

```bash
python scripts/run_forward_signals.py --strategy ma_crossover --symbol BTC/EUR --no-alerts
```

### Eigene Alert-Logdatei

```bash
python scripts/check_live_risk_limits.py --orders orders.csv --alert-log logs/risk_alerts.log
```

### Live-Monitoring

```bash
tail -f logs/alerts.log
```

Siehe auch: [NOTIFICATIONS.md](NOTIFICATIONS.md)
