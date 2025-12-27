# Phase 50: Live Alert Webhooks & Slack

## Einleitung

Phase 50 erweitert das Alerts-System aus Phase 49 um externe Notification-Sinks:
- **Generische HTTP-Webhooks** für beliebige Endpunkte
- **Slack-Webhooks** für direkte Benachrichtigungen in Slack-Kanäle

Das System bleibt vollständig **nicht-blockierend** und **best-effort** – HTTP-Fehler werden geloggt, aber nicht an den Trading-Flow weitergegeben.

## Architektur

```
LiveRiskLimits (check_orders / evaluate_portfolio)
    ↓ erzeugt LiveRiskCheckResult
    ↓ (bei Violation)
LiveAlerts (AlertEvent)
    ↓
AlertSink(s) → Logging / stderr / Webhook / Slack
```

### Design-Prinzipien

1. **Best Effort**: Webhook-/Slack-Sinks dürfen den Live-Flow nicht crashen
2. **Timeouts**: Kurze Timeouts (Standard: 3 Sekunden) verhindern Blockaden
3. **Exception-Handling**: Alle HTTP-Fehler werden intern geloggt, aber nicht weitergeworfen
4. **Security**: URLs kommen ausschließlich aus Config, kein dynamischer Input

## Konfiguration

### config/config.toml

```toml
[live_alerts]
# Live Alerts & Notifications (Phase 49 + 50)
enabled = true
min_level = "warning"
sinks = ["log", "slack_webhook"]

log_logger_name = "peak_trade.live.alerts"

# Phase 50: Webhook & Slack
webhook_urls = []
slack_webhook_urls = ["https://hooks.slack.com/services/XXX/YYY/ZZZ"]
webhook_timeout_seconds = 3.0
```

### Konfigurationsfelder

- **`webhook_urls`**: Liste von generischen HTTP-Webhook-URLs (JSON-POST)
- **`slack_webhook_urls`**: Liste von Slack-Webhook-URLs (Slack-Format: `{"text": "..."}`)
- **`webhook_timeout_seconds`**: Timeout für HTTP-Requests (Default: 3.0)
- **`sinks`**: Liste der aktiven Sink-Namen (z.B. `["log", "webhook", "slack_webhook"]`)

### Regeln

- Leere `webhook_urls` / `slack_webhook_urls` → entsprechende Sinks tun nichts
- `sinks` steuert, welche Sink-Typen überhaupt gebaut werden
- `webhook_timeout_seconds` sollte kurz sein (2–5 Sekunden), um Live-Flow nicht zu blockieren

## Verwendung

### Beispiel: Slack-Webhook konfigurieren

1. **Slack-Webhook-URL erstellen**:
   - In Slack: Apps → Incoming Webhooks → Add to Slack
   - Webhook-URL kopieren (z.B. `https://hooks.slack.com/services/XXX/YYY/ZZZ`)

2. **Config anpassen**:
   ```toml
   [live_alerts]
   enabled = true
   min_level = "warning"
   sinks = ["log", "slack_webhook"]
   slack_webhook_urls = ["https://hooks.slack.com/services/XXX/YYY/ZZZ"]
   ```

3. **Alerts werden automatisch bei Risk-Violations gesendet**:
   ```bash
   python scripts/preview_live_orders.py --signals ... --enforce-live-risk
   python scripts/preview_live_portfolio.py
   ```

### Beispiel: Generischer Webhook

```toml
[live_alerts]
enabled = true
min_level = "critical"
sinks = ["webhook"]
webhook_urls = ["https://example.com/alert-endpoint"]
webhook_timeout_seconds = 2.0
```

Der Webhook erhält einen JSON-Payload:
```json
{
  "ts": "2025-01-15T10:30:00+00:00",
  "level": "CRITICAL",
  "source": "live_risk.orders",
  "code": "RISK_LIMIT_VIOLATION_ORDERS",
  "message": "Live risk limit violation for proposed order batch.",
  "context": {
    "num_orders": 3,
    "total_notional": 5000.0
  }
}
```

### Slack-Format

Slack-Webhooks erhalten ein einfaches Format:
```json
{
  "text": "[CRITICAL] live_risk.orders - RISK_LIMIT_VIOLATION_ORDERS: Live risk limit violation for proposed order batch.\ncontext: {'num_orders': 3}"
}
```

## Limitierungen & Future Work

### Aktuelle Limitierungen

- **Kein Throttling**: Jeder Alert löst sofort einen HTTP-Request aus
- **Keine Retries**: Fehlgeschlagene Requests werden nicht wiederholt
- **Keine Deduplizierung**: Identische Alerts werden mehrfach gesendet
- **Kein Alert-Dashboard**: Keine persistente Alert-Historie

### Geplante Erweiterungen

- **Throttling**: Rate-Limiting pro Sink (z.B. max. 1 Alert pro Minute)
- **Retries**: Exponential Backoff für fehlgeschlagene Requests
- **Alert-Deduplizierung**: Gleiche Alerts innerhalb eines Zeitfensters zusammenfassen
- **Erweiterte Slack-Formatierung**: Rich Text, Buttons, Code-Blocks
- **Weitere Sinks**: Email, PagerDuty, Discord, etc.

## Integration mit Phase 49

Phase 50 baut direkt auf Phase 49 auf:
- Alle bestehenden Sinks (Logging, Stderr) bleiben unverändert
- `LiveAlertsConfig` wurde um Webhook-Felder erweitert
- `build_alert_sink_from_config()` baut automatisch Webhook-/Slack-Sinks, wenn konfiguriert

Siehe auch: [PHASE_49_LIVE_ALERTS_AND_NOTIFICATIONS.md](PHASE_49_LIVE_ALERTS_AND_NOTIFICATIONS.md)

## Tests

Alle neuen Sinks sind vollständig getestet:
- `tests/test_live_alerts.py`: Unit-Tests für `WebhookAlertSink` und `SlackWebhookAlertSink`
- `tests/test_live_risk_alert_integration.py`: Integration-Tests für Webhook-Integration mit `LiveRiskLimits`

```bash
pytest tests/test_live_alerts.py -v
pytest tests/test_live_risk_alert_integration.py::test_risk_violation_triggers_webhook -v
```

## Sicherheitshinweise

1. **URLs in Config**: Webhook-URLs sollten niemals aus User-Input stammen
2. **Sensible Daten**: `context` kann sensible Metriken enthalten – prüfe vor dem Loggen
3. **Rate-Limiting**: Externe Services können Rate-Limits haben – Throttling ist geplant
4. **HTTPS**: Verwende ausschließlich HTTPS-URLs für Webhooks

## Troubleshooting

### Alerts werden nicht gesendet

1. **Config prüfen**:
   ```bash
   # Prüfe ob [live_alerts] korrekt konfiguriert ist
   python -c "from src.config import load_config; print(load_config().get('live_alerts'))"
   ```

2. **Logs prüfen**:
   ```bash
   # Suche nach Webhook-Fehlern
   grep "Failed to send alert to webhook" logs/*.log
   ```

3. **Test-Webhook**:
   ```python
   from src.live.alerts import AlertEvent, AlertLevel, WebhookAlertSink
   from datetime import datetime, timezone

   sink = WebhookAlertSink(urls=["https://example.com/test"])
   alert = AlertEvent(
       ts=datetime.now(timezone.utc),
       level=AlertLevel.WARNING,
       source="test",
       code="TEST",
       message="Test alert",
   )
   sink.send(alert)
   ```

### Slack-Webhook funktioniert nicht

1. **Webhook-URL prüfen**: Stelle sicher, dass die URL korrekt ist
2. **Slack-App prüfen**: Incoming Webhooks müssen aktiviert sein
3. **Format prüfen**: Slack erwartet `{"text": "..."}` – das wird automatisch generiert

## Siehe auch

- [PHASE_49_LIVE_ALERTS_AND_NOTIFICATIONS.md](PHASE_49_LIVE_ALERTS_AND_NOTIFICATIONS.md)
- [LIVE_TESTNET_TRACK_STATUS.md](LIVE_TESTNET_TRACK_STATUS.md)
- [CLI_CHEATSHEET.md](CLI_CHEATSHEET.md)

