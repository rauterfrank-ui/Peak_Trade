# Phase 48 – Live Portfolio Monitoring & Risk Bridge

## Übersicht

Phase 48 implementiert einen **lesenden Live-/Shadow-Portfolio-Monitor** ("Live Portfolio View") + eine **Bridge zu `LiveRiskLimits`**, damit wir:

1. Zu jedem Zeitpunkt eine **Portfolio-Sicht** haben:
   - Offene Positionen
   - Notional-Exposure (gesamt & pro Symbol)
   - Realisierte + unrealisierte PnL
   - Equity / Cash / Margin (soweit verfügbar)

2. Diese Sicht mit den bestehenden **Live-Risk-Limits** verknüpfen können:
   - `max_total_exposure_notional`
   - `max_symbol_exposure_notional`
   - `max_open_positions`
   - `max_daily_loss_abs` / `max_daily_loss_pct`

3. Über eine **CLI** schnell prüfen können:
   - "Wie sieht mein Live-Portfolio aus?"
   - "Welche Limits sind aktuell **OK**, welche sind **verletzt** oder knapp davor?"

**Wichtig:**
- Phase 48 ist **read-only** – kein Trade-Trigger, keine Auto-Liquidation.
- Fokus: **Monitoring & Klarheit**, nicht "Autopilot".

---

## Architektur

### Komponenten-Übersicht

```
ExchangeClient/Broker
    ↓
LivePortfolioMonitor
    ↓
LivePortfolioSnapshot
    ↓
LiveRiskLimits.evaluate_portfolio()
    ↓
LiveRiskCheckResult
```

### Datenfluss

1. **ExchangeClient/Broker** liefert Positions- und Account-Daten
2. **LivePortfolioMonitor** sammelt Daten und erstellt `LivePortfolioSnapshot`
3. **LiveRiskLimits.evaluate_portfolio()** prüft Snapshot gegen Limits
4. **LiveRiskCheckResult** enthält allowed/reasons/metrics

### Read-Only-Design

Phase 48 implementiert **keine**:
- Trade-Trigger
- Auto-Liquidation
- Alert-Systeme (außer CLI-Ausgabe)
- Automatische Position-Closes

Alles ist **lesend** – der Operator behält die volle Kontrolle.

---

## Komponenten

### 1. `src/live/portfolio_monitor.py`

#### Dataclasses

**`LivePositionSnapshot`**
- Repräsentiert eine einzelne Position
- Felder: `symbol`, `side`, `size`, `entry_price`, `mark_price`, `notional`, `unrealized_pnl`, `realized_pnl`, `leverage`

**`LivePortfolioSnapshot`**
- Repräsentiert das gesamte Portfolio
- Felder: `as_of`, `positions`, `total_notional`, `total_unrealized_pnl`, `total_realized_pnl`, `symbol_notional`, `num_open_positions`, `equity`, `cash`, `margin_used`
- Berechnet Aggregat-Werte automatisch im `__post_init__`

#### Monitor-Klasse

**`LivePortfolioMonitor`**
- Liest Positionen vom Exchange-Client/Broker
- Unterstützt verschiedene Datenquellen:
  - `fetch_positions()` (DataFrame)
  - `positions`-Attribut (Dict, z.B. PaperBroker)
- Konvertiert verschiedene Position-Formate zu `LivePositionSnapshot`
- Optional: Liest Account-Daten (equity, cash, margin)

### 2. `src/live/risk_limits.py` (Erweiterung)

**`LiveRiskLimits.evaluate_portfolio()`**
- Neue Methode für Portfolio-Level Risk-Checks
- Nutzt dieselben Limits wie `check_orders()`, aber auf Portfolio-Zustand angewendet
- Prüft:
  - `max_total_exposure_notional` vs. `snapshot.total_notional`
  - `max_symbol_exposure_notional` vs. `snapshot.symbol_notional`
  - `max_open_positions` vs. `snapshot.num_open_positions`
  - `max_daily_loss_abs` / `max_daily_loss_pct` vs. Daily-PnL

### 3. `scripts/preview_live_portfolio.py`

**CLI-Script für Portfolio-Monitoring**

Features:
- Lädt Config & Exchange-Client
- Erstellt Portfolio-Snapshot
- Führt Risk-Check durch (optional)
- Text-Tabellen- oder JSON-Ausgabe

---

## Nutzung

### CLI-Aufruf

```bash
# Standard-Run (mit Risk-Check)
python scripts/preview_live_portfolio.py --config config/config.toml

# Ohne Risk-Check
python scripts/preview_live_portfolio.py --config config/config.toml --no-risk

# JSON-Ausgabe
python scripts/preview_live_portfolio.py --config config/config.toml --json

# Mit Custom Starting-Cash für prozentuale Limits
python scripts/preview_live_portfolio.py \
  --config config/config.toml \
  --starting-cash 20000.0
```

### Beispiel-Ausgabe (Text)

```
======================================================================
=== Live Portfolio Snapshot (2025-12-07 12:34:56 UTC) ===
======================================================================

Positions:
----------------------------------------------------------------------
symbol       side   size       entry         mark      notional    unreal_pnl
----------------------------------------------------------------------
BTC/EUR      long   0.5000     28000.00     29500.00     14750.00      750.00
ETH/EUR      short  2.0000      1800.00      1750.00      3500.00      100.00

Totals:
----------------------------------------------------------------------
  - num_open_positions   : 2
  - total_notional       : 18250.00
  - total_unrealized_pnl : 850.00
  - total_realized_pnl   : 120.00

Symbol exposure:
----------------------------------------------------------------------
  - BTC/EUR      :     14750.00
  - ETH/EUR      :      3500.00

Risk status:
----------------------------------------------------------------------
  - allowed : True
  - reasons : [] (alle Limits OK)
  - metrics :
    portfolio_total_notional = 18250.00
    portfolio_symbol_notional = {'BTC/EUR': 14750.0, 'ETH/EUR': 3500.0}
    portfolio_num_open_positions = 2
    ...
```

### Beispiel-Ausgabe (JSON)

```json
{
  "as_of": "2025-12-07T12:34:56.123456",
  "positions": [
    {
      "symbol": "BTC/EUR",
      "side": "long",
      "size": 0.5,
      "entry_price": 28000.0,
      "mark_price": 29500.0,
      "notional": 14750.0,
      "unrealized_pnl": 750.0,
      "realized_pnl": 120.0,
      "leverage": null
    }
  ],
  "totals": {
    "num_open_positions": 2,
    "total_notional": 18250.0,
    "total_unrealized_pnl": 850.0,
    "total_realized_pnl": 120.0
  },
  "symbol_notional": {
    "BTC/EUR": 14750.0,
    "ETH/EUR": 3500.0
  },
  "risk": {
    "allowed": true,
    "reasons": [],
    "metrics": {...}
  }
}
```

---

## Python-API

### Portfolio-Snapshot erstellen

```python
from src.live.portfolio_monitor import LivePortfolioMonitor
from src.live.broker_base import BaseBrokerClient

# Exchange-Client erstellen (z.B. PaperBroker, Kraken-Client, etc.)
exchange_client = create_exchange_client(...)

# Monitor erstellen
monitor = LivePortfolioMonitor(exchange_client)

# Snapshot erstellen
snapshot = monitor.snapshot()

print(f"Offene Positionen: {snapshot.num_open_positions}")
print(f"Total Notional: {snapshot.total_notional:.2f}")
```

### Risk-Check durchführen

```python
from src.live.risk_limits import LiveRiskLimits
from src.core.peak_config import load_config

# Risk-Limits laden
cfg = load_config("config/config.toml")
risk_limits = LiveRiskLimits.from_config(cfg, starting_cash=10000.0)

# Portfolio-Snapshot erstellen
snapshot = monitor.snapshot()

# Risk-Check
result = risk_limits.evaluate_portfolio(snapshot)

if not result.allowed:
    print("⚠️ Portfolio verletzt Limits:")
    for reason in result.reasons:
        print(f"  - {reason}")
else:
    print("✅ Portfolio innerhalb aller Limits")
```

---

## Limitierungen & Future Work

### Aktuelle Limitierungen

1. **Read-Only**: Keine automatischen Aktionen bei Limit-Verletzungen
2. **Kein Alert-System**: Nur CLI-Ausgabe, keine eMail/Slack-Integration
3. **Kein GUI**: Nur Text/JSON-Ausgabe
4. **Exchange-Client**: Aktuell hauptsächlich PaperBroker, echte Exchange-Integration folgt später

### Mögliche Erweiterungen (zukünftige Phasen)

1. **Alert-System**:
   - eMail/Slack-Benachrichtigungen bei Limit-Verletzungen
   - Proaktive Warnungen bei Annäherung an Limits

2. **Live-Dashboard**:
   - Web-UI für Portfolio-Monitoring
   - Real-time Updates
   - Grafische Visualisierung

3. **Auto-Stop** (optional):
   - Automatisches Stoppen von Trades bei Limit-Verletzungen
   - Liquidation von Positionen (mit Bestätigung)

4. **Erweiterte Analytics**:
   - Portfolio-Korrelation
   - Diversifikations-Metriken
   - Regime-bewusste Risk-Adjustments

5. **Multi-Exchange-Support**:
   - Aggregation über mehrere Exchanges
   - Cross-Exchange Risk-Management

---

## Integration in bestehende Workflows

### Vor Live-Start

```bash
# Portfolio-Status prüfen
python scripts/preview_live_portfolio.py --config config/config.toml

# Prüfen ob Limits OK sind
# → Risk status: allowed = True
```

### Während Live-Trading

```bash
# Regelmäßig Portfolio-Status checken
python scripts/preview_live_portfolio.py --config config/config.toml

# Bei Verdacht auf Limit-Verletzung
python scripts/preview_live_portfolio.py --config config/config.toml --json > portfolio_status.json
```

### Incident-Handling

Bei einem Incident:
1. **Portfolio-Status prüfen**: `preview_live_portfolio.py`
2. **Risk-Status analysieren**: Welche Limits sind verletzt?
3. **Entscheidung treffen**: Manuell Positionen schließen oder warten

---

## Tests

### Unit-Tests

```bash
# Portfolio-Monitor Tests
pytest tests/test_live_portfolio_monitor.py -v

# Risk Bridge Tests
pytest tests/test_live_risk_limits_portfolio_bridge.py -v

# CLI Tests
pytest tests/test_preview_live_portfolio.py -v
```

### Integration-Tests

```bash
# Alle Live-Portfolio-Tests
pytest tests/test_live_portfolio*.py tests/test_preview_live_portfolio.py -v
```

---

## Siehe auch

- `docs/LIVE_TESTNET_PREPARATION.md` - Live/Testnet-Setup
- `docs/LIVE_OPERATIONAL_RUNBOOKS.md` - Operational Runbooks
- `src/live/risk_limits.py` - Live-Risk-Limits-Dokumentation
- `src/live/portfolio_monitor.py` - Portfolio-Monitor-Implementierung

---

**Built with ❤️ and safety-first monitoring**





