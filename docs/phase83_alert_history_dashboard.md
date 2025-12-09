# Phase 83 – Alert-Historie & Status im Web-Dashboard v1

## Übersicht

Phase 83 erweitert das Web-Dashboard um eine **Alert-Historie & Status-Ansicht** für die in Phase 82 eingeführte Alert-Pipeline. Operatoren können im Browser auf einen Blick sehen:

- Welche Alerts in letzter Zeit ausgelöst wurden (Timeline/Tabelle)
- Wie der aktuelle Alert-Status aussieht (Status-Kacheln)
- Welche Sessions besonders häufig Alerts generieren

## Implementierte Komponenten

### 1. Alert Storage Layer (`src/live/alert_storage.py`)

Persistiert Alerts aus der Pipeline für die Web-Dashboard-Historie:

```python
from src.live.alert_storage import AlertStorage, store_alert, list_recent_alerts

# Alert speichern (automatisch bei AlertPipelineManager.send())
store_alert(alert_message)

# Alerts abrufen
recent = list_recent_alerts(limit=100, hours=24)
filtered = list_recent_alerts(severity=["WARN", "CRITICAL"], category=["RISK"])
```

**Features:**
- Append-only JSON-Lines-Storage
- Tägliche Rotation (`alerts_YYYY-MM-DD.jsonl`)
- Filter nach Severity, Category, Session, Zeitfenster
- Thread-safe Writes
- Automatisches Cleanup alter Dateien

**Storage-Struktur:**
```
live_runs/alerts/
  alerts_2025-12-09.jsonl
  alerts_2025-12-10.jsonl
```

### 2. AlertPipelineManager Integration

Der `AlertPipelineManager` speichert Alerts automatisch bei `send()`:

```python
class AlertPipelineManager:
    def __init__(self, channels, persist_alerts=True):
        # persist_alerts=True (default) aktiviert automatisches Speichern
        ...
```

### 3. Web-API Endpoints

#### HTML-View
- `GET /live/alerts` → Alert-Historie-Seite

#### JSON-API
- `GET /api/live/alerts` → Alert-Liste mit Filtern
- `GET /api/live/alerts/stats` → Statistiken für Status-Kacheln

**Query-Parameter:**
- `limit` (1-500): Maximale Anzahl Alerts
- `hours` (1-168): Zeitfenster in Stunden
- `severity` (ARRAY): Filter nach Severity (INFO, WARN, CRITICAL)
- `category` (ARRAY): Filter nach Category (RISK, EXECUTION, SYSTEM)
- `session_id`: Filter nach Session-ID

### 4. Web-Dashboard UI

**Status-Kacheln:**
- Total Alerts im Zeitfenster
- CRITICAL Alerts (mit letztem Zeitpunkt)
- WARN Alerts (nach Kategorie)
- Sessions mit Alerts

**Filter:**
- Zeitfenster (2h, 6h, 24h, 48h, 7d)
- Severity-Checkboxen
- Category-Checkboxen
- Session-ID-Textfeld

**Alert-Tabelle:**
| Spalte | Beschreibung |
|--------|--------------|
| Zeitpunkt | Formatierter Timestamp |
| Severity | Farbiger Badge (🚨 CRITICAL, ⚠️ WARN, ℹ️ INFO) |
| Kategorie | RISK, EXECUTION, SYSTEM |
| Titel/Source | Alert-Titel mit Code-Source |
| Session | Link zur Session-Detail-Seite |

## Dateien

### Erstellte Dateien
| Datei | Zeilen | Beschreibung |
|-------|--------|--------------|
| `src/live/alert_storage.py` | ~350 | Alert-Storage Layer |
| `src/webui/alerts_api.py` | ~200 | Backend-API für Alerts |
| `templates/peak_trade_dashboard/alerts.html` | ~200 | HTML-Template |
| `tests/test_alert_storage.py` | ~350 | Unit-Tests |
| `docs/phase83_alert_history_dashboard.md` | Diese Doku |

### Geänderte Dateien
| Datei | Änderung |
|-------|----------|
| `src/live/alert_pipeline.py` | +persist_alerts Parameter, auto-persist bei send() |
| `src/live/__init__.py` | +7 Exports für Storage |
| `src/webui/app.py` | +3 Endpoints (/live/alerts, API) |
| `templates/peak_trade_dashboard/base.html` | +Navigation-Link "🔔 Alerts" |

## Tests

```bash
# Alert Storage Tests
pytest tests/test_alert_storage.py -v

# Ergebnis: 29 passed
```

## Akzeptanzkriterien

✅ Alerts aus Phase 82 erscheinen in der Historie  
✅ Mindestens letzte N Alerts werden angezeigt (konfigurierbar)  
✅ Filter nach Severity, Kategorie und Zeitfenster funktionieren  
✅ Status-Kacheln geben schnellen Überblick  
✅ Dashboard bleibt performant (< 1s Ladezeit)  
✅ Empty-State bei fehlendem Storage  

## Verwendung

### Zugriff auf Alert-Historie

```
http://localhost:8000/live/alerts
http://localhost:8000/live/alerts?hours=48&severity=CRITICAL
```

### API-Abfragen

```bash
# Alle Alerts der letzten 24h
curl "http://localhost:8000/api/live/alerts?hours=24"

# Nur CRITICAL Alerts
curl "http://localhost:8000/api/live/alerts?severity=CRITICAL"

# Statistiken
curl "http://localhost:8000/api/live/alerts/stats?hours=24"
```

## Nächste Phasen

- **Phase 84:** Runbook-Integration (Links zu Runbooks in Alerts)
- **Phase 85:** On-Call / Schedule-Integration

---

*Phase 83 | Dezember 2025*
