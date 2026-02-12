# Live Panels: Positions, Portfolio & Risk - Operator Guide

## Überblick

Die erweiterte Panel-Integration liefert jetzt echte Daten für **alle 6 Panels**:

1. **Alerts** - Alert-Statistiken aus dem Alert-Storage
2. **Live Sessions** - Aktive und historische Sessions
3. **Telemetry** - Telemetry Health-Checks
4. **Positions** ⭐ NEU - Offene Positionen aus aktiven Sessions
5. **Portfolio** ⭐ NEU - PnL, Equity, Exposure
6. **Risk** ⭐ NEU - Risk-Status und Limit-Violations

## Architektur

```
┌─────────────────────────────────────────────────────────────┐
│               WebUI Endpoints & Health Check                 │
│  /api/live/status/snapshot.json                             │
│  /health/detailed                                            │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ uses
                 ▼
┌─────────────────────────────────────────────────────────────┐
│            Service Layer (Single Source of Truth)            │
│         src/webui/services/live_panel_data.py                │
│  • get_alerts_stats()                                        │
│  • get_live_sessions_stats()                                 │
│  • get_telemetry_summary()                                   │
│  • get_positions_snapshot() ⭐ NEU                           │
│  • get_portfolio_snapshot() ⭐ NEU                           │
│  • get_risk_status() ⭐ NEU                                  │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ uses
                 ▼
┌─────────────────────────────────────────────────────────────┐
│          Panel Providers (6 Panels)                          │
│             src/live/status_providers.py                     │
│  • _panel_alerts()                                           │
│  • _panel_live_sessions()                                    │
│  • _panel_telemetry()                                        │
│  • _panel_positions() ⭐ NEU                                 │
│  • _panel_portfolio() ⭐ NEU                                 │
│  • _panel_risk() ⭐ NEU                                      │
└─────────────────────────────────────────────────────────────┘
```

## Neue Panel-Funktionen

### 1. Positions Panel

**Datenquelle**: Aggregiert aus aktiven Sessions (metrics.open_positions, metrics.total_notional)

**Status-Logik**:
- `active`: Wenn offene Positionen vorhanden
- `ok`: Keine Positionen, aber Sessions laufen
- `unknown`: Keine aktiven Sessions

**Details**:
```json
{
  "open_positions": 2,
  "symbols": ["BTC-EUR", "ETH-EUR"],
  "total_notional": 5000.0,
  "positions": [
    {"symbol": "BTC-EUR", "notional": 3000.0, "sessions": 1}
  ],
  "active_sessions": 1
}
```

### 2. Portfolio Panel

**Datenquelle**: Aggregiert PnL/Equity/Exposure aus aktiven Sessions

**Status-Logik**:
- `active`: Aktive Sessions vorhanden
- `ok`: Keine aktiven Sessions, zeigt historische Daten
- `unknown`: Keine Daten verfügbar

**Details**:
```json
{
  "total_pnl": 150.75,
  "unrealized_pnl": 50.0,
  "equity": 10150.75,
  "total_exposure": 5000.0,
  "num_sessions": 2
}
```

### 3. Risk Panel

**Datenquelle**: Risk-Check-Status aus Session-Metrics (risk_check.severity)

**Status-Logik**:
- `error`: Risk-Severity "breach" → BLOCKED
- `warning`: Risk-Severity "warning"
- `ok`: Risk-Severity "ok"
- `unknown`: Keine aktiven Sessions

**Details**:
```json
{
  "status": "ok",
  "severity": "ok",
  "limits_enabled": true,
  "limit_details": [
    {"name": "drawdown", "value": -5.0, "limit": -10.0, "severity": "ok"}
  ],
  "violations": [],
  "active_sessions": 1
}
```

## Health Endpoint mit Panel-Status

### `/health/detailed` - Erweitert

Der Health-Endpoint sammelt jetzt Panel-Status und berechnet **Overall Status**:

**Overall Status Logic**:
- `blocked`: Mindestens ein Panel hat status "error" oder "blocked" → **HTTP 503**
- `degraded`: Mindestens ein Panel hat status "unknown" oder "warning" → **HTTP 200**
- `ok`: Alle Panels ok oder active → **HTTP 200**

**Beispiel-Response**:
```json
{
  "healthy": true,
  "overall_status": "degraded",
  "panels": {
    "alerts": {"status": "warning", "message": "340 items"},
    "live_sessions": {"status": "ok", "message": "0 active / 0 total"},
    "telemetry": {"status": "ok", "message": "Status: ok"},
    "positions": {"status": "ok", "message": "0 open positions"},
    "portfolio": {"status": "ok", "message": "OK"},
    "risk": {"status": "ok", "message": "Status: ok"}
  },
  "checks": {...},
  "summary": {...}
}
```

## Operator How-To

### 1. Snapshot ohne aktive Sessions prüfen

```bash
# Server läuft bereits auf Port 8001
curl http://127.0.0.1:8001/api/live/status/snapshot.json | jq '.panels[] | {id, status}'
```

**Erwartetes Ergebnis** (keine Sessions):
```json
{"id": "alerts", "status": "ok"}
{"id": "live_sessions", "status": "ok"}
{"id": "telemetry", "status": "ok"}
{"id": "positions", "status": "ok"}    # 0 positions
{"id": "portfolio", "status": "ok"}    # Historical PnL
{"id": "risk", "status": "ok"}         # No active sessions
```

### 2. Shadow Session starten

```bash
# Terminal 1: Shadow Session starten
cd ~/Peak_Trade
python3 scripts/run_shadow_paper_session.py \
  --strategy ma_crossover \
  --symbol BTC/EUR \
  --exchange kraken \
  --mode shadow
```

### 3. Panels während Session beobachten

```bash
# Terminal 2: Panel-Status live (alle 3 Sekunden)
watch -n 3 'curl -sS http://127.0.0.1:8001/api/live/status/snapshot.json | \
  python3 -c "import json, sys; data=json.load(sys.stdin); \
  [print(f\"{p[\"id\"]}: {p[\"status\"]} - {p[\"details\"].get(\"total_sessions\", p[\"details\"].get(\"open_positions\", \"?\"))}\") \
   for p in data[\"panels\"]]"'
```

**Erwartete Änderungen während Session**:
- `live_sessions`: Status → `active`, Details zeigen 1 aktive Session
- `positions`: Sobald Order platziert → status `active`, Details zeigen Positionen
- `portfolio`: Zeigt PnL-Updates
- `risk`: Wenn Limits geprüft werden → Details zeigen limit_details

### 4. Health-Status prüfen

```bash
# Overall Status
curl -sS http://127.0.0.1:8001/health/detailed | \
  python3 -c "import json, sys; data=json.load(sys.stdin); \
  print(f\"Overall: {data['overall_status']}\"); \
  [print(f\"  {k}: {v['status']}\") for k,v in data['panels'].items()]"
```

**HTTP Status-Codes**:
```bash
# HTTP 200 - OK oder Degraded
curl -sS -w "\nHTTP: %{http_code}\n" http://127.0.0.1:8001/health/detailed | tail -1
# Erwartung: HTTP: 200

# HTTP 503 - Nur bei Blocked (Risk-Breach)
# (Passiert nur wenn Risk-Limits überschritten werden)
```

### 5. Snapshot HTML im Browser

```bash
open "http://127.0.0.1:8001/api/live/status/snapshot.html"
```

**Was du sehen solltest**:
- ✅ 6 Panels (nicht mehr 3)
- ✅ Alle Panels zeigen echte Daten (keine "not wired" Messages)
- ✅ Positions/Portfolio/Risk sind sichtbar (auch wenn 0 Werte)

### 6. Risk-Breach simulieren (Optional)

Um zu testen, wie `blocked` Status funktioniert:

```bash
# In Session-Code oder Metrics manuell risk_severity auf "breach" setzen
# Dann health/detailed prüfen:
curl -sS http://127.0.0.1:8001/health/detailed | grep overall_status
# Erwartung: "overall_status": "blocked"

curl -sS -w "%{http_code}" http://127.0.0.1:8001/health/detailed -o /dev/null
# Erwartung: 503
```

## Troubleshooting

### Panel zeigt "unknown" trotz laufender Session

**Ursache**: Session-Metrics enthalten keine Position/Portfolio-Daten

**Lösung**:
1. Prüfe Session-Metrics in Registry:
   ```bash
   ls -lt live_runs/sessions/*.jsonl | head -5
   tail -50 live_runs/sessions/shadow_LATEST.jsonl | jq '.metrics'
   ```
2. Stelle sicher, dass Session metrics wie `open_positions`, `total_notional`, `realized_pnl` enthält

### Portfolio zeigt 0.0 PnL obwohl Trades stattfanden

**Ursache**: Metrics werden nicht in Registry geschrieben

**Lösung**:
1. Prüfe ob Session Registry-Updates macht:
   ```bash
   grep "realized_pnl" live_runs/sessions/*.jsonl
   ```
2. Session sollte periodisch `update_session_metrics()` aufrufen

### Risk Panel zeigt "ok" obwohl Drawdown hoch

**Ursache**: Risk-Checks werden nicht in Session-Metrics gespeichert

**Lösung**:
1. Prüfe ob Session Risk-Checks durchführt:
   ```bash
   grep "risk_check" live_runs/sessions/*.jsonl
   ```
2. Session sollte LiveRiskLimits.check_orders() aufrufen und Result in Metrics speichern

### Health-Endpoint gibt immer 200 zurück

**Ursache**: Keine Panel hat status "error"

**Lösung**:
- Das ist korrekt! HTTP 503 kommt nur bei status "blocked" (Risk-Breach)
- `degraded` Status (unknown/warning) gibt absichtlich 200 zurück

## Siehe auch

- [Live Status Panels - Custom Panel Guide](./LIVE_STATUS_PANELS.md)
- [Service Layer API](../../src/webui/services/live_panel_data.py)
- [Panel Providers](../../src/live/status_providers.py)
- [Health Endpoint](../../src/webui/health_endpoint.py)
- [Tests](../../tests/test_live_status_snapshot_panels.py)
