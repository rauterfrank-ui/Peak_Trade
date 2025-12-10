# Phase 51: Live Operations CLI

## Einleitung

Phase 51 implementiert ein **zentrales Operator-Cockpit** für Live-/Testnet-Operationen:

> `scripts/live_ops.py`

Dieses CLI bündelt die wichtigsten Live-/Testnet-Kommandos in einem **einzigen Entry-Point**, um Operatoren die Arbeit zu erleichtern.

**Wichtig:**
- **Keine** neue Business-Logik – wir bündeln und strukturieren nur, nutzen vorhandene Komponenten
- Das bestehende Verhalten von `preview_live_orders.py` und `preview_live_portfolio.py` bleibt erhalten
- Live-Alerts (Phase 49/50) laufen im Hintergrund weiter (Logging, stderr, Webhook, Slack)

## Architektur / Scope

Live-Ops CLI ist ein **Wrapper** um bestehende Live-Funktionalität:

```
live_ops.py
├── orders      → Wrapper um preview_live_orders.py
├── portfolio   → Wrapper um preview_live_portfolio.py
└── health      → Neuer Health-Check für Live-/Testnet-Setup
```

### Design-Prinzipien

1. **Konsistenz**: Alle Subcommands nutzen ähnliche Flags (`--config`, `--json`)
2. **Wiederverwendung**: Logik aus bestehenden Scripts wird wiederverwendet
3. **Nicht-invasiv**: Bestehende Scripts bleiben funktionsfähig
4. **Best-Effort**: Health-Checks sind leichtgewichtig und blockieren nicht

## Subcommands

### 1. `live_ops orders`

**Ziel:** Preview live orders and run live risk checks

**Wrapper um:** `scripts/preview_live_orders.py`

**Beispielaufrufe:**

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

# Mit Live-Risk-Enforcement
python scripts/live_ops.py orders \
  --signals reports/forward/forward_*_signals.csv \
  --config config/config.toml \
  --enforce-live-risk
```

**Argumente:**
- `--signals`: Pfad zur Forward-Signal-CSV (erforderlich)
- `--config`: Pfad zur TOML-Config (Default: `config/config.toml`)
- `--notional`: Notional pro Trade (Default: aus config)
- `--enforce-live-risk`: Live-Risk-Limits prüfen und bei Verletzung abbrechen
- `--skip-live-risk`: Live-Risk-Limits überspringen
- `--json`: JSON-Output statt Text

**Verhalten:**
- Lädt Signals-CSV
- Generiert `LiveOrderRequest`-Objekte
- Führt Live-Risk-Check durch (falls nicht `--skip-live-risk`)
- Erzeugt Alerts bei Risk-Violations (Phase 49/50)
- Gibt Orders und Risk-Result aus (Text oder JSON)

### 2. `live_ops portfolio`

**Ziel:** Preview live portfolio snapshot and risk evaluation

**Wrapper um:** `scripts/preview_live_portfolio.py`

**Beispielaufrufe:**

```bash
# Standard-Ansicht
python scripts/live_ops.py portfolio --config config/config.toml

# JSON-Output
python scripts/live_ops.py portfolio --config config/config.toml --json

# Ohne Risk-Check
python scripts/live_ops.py portfolio --config config/config.toml --no-risk
```

**Argumente:**
- `--config`: Pfad zur TOML-Config (Default: `config/config.toml`)
- `--json`: JSON-Output statt Text
- `--no-risk`: Risk-Evaluation überspringen
- `--starting-cash`: Starting Cash für prozentuale Daily-Loss-Limits

**Verhalten:**
- Erstellt `LivePortfolioMonitor`
- Erzeugt Portfolio-Snapshot
- Führt Risk-Evaluation durch (falls nicht `--no-risk`)
- Erzeugt Alerts bei Risk-Violations (Phase 49/50)
- Gibt Portfolio-Snapshot und Risk-Result aus (Text oder JSON)

### 3. `live_ops health`

**Ziel:** Run basic Live/Testnet health checks

**Neu in Phase 51**

**Beispielaufrufe:**

```bash
# Text-Output
python scripts/live_ops.py health --config config/config.toml

# JSON-Output
python scripts/live_ops.py health --config config/config.toml --json
```

**Argumente:**
- `--config`: Pfad zur TOML-Config (Default: `config/config.toml`)
- `--json`: JSON-Output statt Text

**Health-Checks:**

1. **Config-Ladung & Basiskonsistenz**
   - Kann `PeakConfig` geladen werden?
   - Sind zentrale Blöcke vorhanden: `[environment]`, `[live_risk]`, `[live_alerts]`?
   - Ergebnis: `config_ok: bool`, `config_errors: list[str]`

2. **Exchange-Client/Market Access – Smoke-Test**
   - Versucht, Exchange-Client zu initialisieren
   - Ergebnis: `exchange_ok: bool`, `exchange_errors: list[str]`

3. **Alert-System-Konfiguration**
   - `LiveAlertsConfig.from_dict(...)` + `build_alert_sink_from_config(...)`
   - Prüft auf Warnungen (z.B. `sinks` enthält `webhook`, aber keine URLs)
   - Ergebnis: `alerts_enabled: bool`, `alert_sinks_configured: list[str]`, `alert_config_warnings: list[str]`

4. **Live-Risk-Limits – Konsistenzcheck**
   - Prüft, ob Limits > 0 und konsistent sind
   - Beispiel: `max_symbol_exposure_notional <= max_total_exposure_notional`
   - Ergebnis: `live_risk_ok: bool`, `live_risk_warnings: list[str]`

**Overall-Status:**
- `OK`: Alle Checks bestanden
- `DEGRADED`: Mindestens ein Check fehlgeschlagen, aber kein harter Fehler
- `FAIL`: Kritischer Pfad (Config oder Exchange) schlägt fehl

**Exit-Codes:**
- `0`: OK oder DEGRADED
- `1`: FAIL

## Bezug zu Alerts & Runbooks

### Alerts

Alerts kommen weiterhin aus Phase 49/50:
- `live_ops orders` und `live_ops portfolio` triggern Alerts indirekt (Risk-Violations)
- Alert-Konfiguration kommt aus `[live_alerts]` in `config.toml`
- Keine neuen Alert-Features in Phase 51

### Runbooks

Live-Ops CLI kann in Runbooks referenziert werden:

**Beispiel-Runbook-Einträge:**

1. **Vor Live-Session:**
   ```bash
   # Health-Check ausführen
   python scripts/live_ops.py health --config config/config.toml
   
   # Bei FAIL: Session nicht starten
   ```

2. **Bei Incident:**
   ```bash
   # Portfolio-Status als JSON für Analyse
   python scripts/live_ops.py portfolio --config config/config.toml --json > portfolio_snapshot.json
   ```

3. **Tägliche Checks:**
   ```bash
   # Portfolio-Status prüfen
   python scripts/live_ops.py portfolio --config config/config.toml
   
   # Orders-Preview vor Ausführung
   python scripts/live_ops.py orders --signals reports/forward/..._signals.csv
   ```

## Integration mit bestehenden Scripts

### `preview_live_orders.py`

- **Bleibt funktionsfähig** – keine Änderungen
- `live_ops orders` nutzt die gleiche Logik
- Operatoren können weiterhin `preview_live_orders.py` direkt verwenden

### `preview_live_portfolio.py`

- **Bleibt funktionsfähig** – keine Änderungen
- `live_ops portfolio` nutzt die gleiche Logik
- Operatoren können weiterhin `preview_live_portfolio.py` direkt verwenden

## Verwendung in der Praxis

### Typische Workflows

**1. Täglicher Portfolio-Check:**
```bash
python scripts/live_ops.py portfolio --config config/config.toml
```

**2. Orders-Preview vor Ausführung:**
```bash
python scripts/live_ops.py orders \
  --signals reports/forward/forward_20250115_signals.csv \
  --config config/config.toml \
  --enforce-live-risk
```

**3. Health-Check für Monitoring:**
```bash
python scripts/live_ops.py health --config config/config.toml --json | jq .
```

**4. Incident-Response:**
```bash
# Portfolio-Status als JSON für Analyse
python scripts/live_ops.py portfolio --config config/config.toml --json > incident_portfolio.json
```

## Tests

Alle Subcommands sind vollständig getestet:
- `tests/test_live_ops_cli.py`: CLI-Parsing, JSON-Output, Error-Handling

```bash
pytest tests/test_live_ops_cli.py -v
```

## Limitierungen & Future Work

### Aktuelle Limitierungen

- **Keine persistente Historie**: Health-Checks werden nicht gespeichert
- **Keine automatischen Checks**: Health-Check muss manuell ausgeführt werden
- **Keine erweiterten Exchange-Tests**: Nur Client-Initialisierung, keine echten API-Calls

### Geplante Erweiterungen

- **Weitere Subcommands**: z.B. `live_ops alerts` (Alert-Historie anzeigen)
- **Health-Check-Scheduling**: Automatische Health-Checks via Cron/Scheduler
- **Erweiterte Exchange-Tests**: Echte API-Calls für Connectivity-Tests
- **Health-Dashboard**: Web-UI für Health-Status

## Siehe auch

- [PHASE_48_LIVE_PORTFOLIO_MONITORING_AND_RISK_BRIDGE.md](PHASE_48_LIVE_PORTFOLIO_MONITORING_AND_RISK_BRIDGE.md)
- [PHASE_49_LIVE_ALERTS_AND_NOTIFICATIONS.md](PHASE_49_LIVE_ALERTS_AND_NOTIFICATIONS.md)
- [PHASE_50_LIVE_ALERT_WEBHOOKS_AND_SLACK.md](PHASE_50_LIVE_ALERT_WEBHOOKS_AND_SLACK.md)
- [CLI_CHEATSHEET.md](CLI_CHEATSHEET.md)
- [LIVE_TESTNET_TRACK_STATUS.md](LIVE_TESTNET_TRACK_STATUS.md)







