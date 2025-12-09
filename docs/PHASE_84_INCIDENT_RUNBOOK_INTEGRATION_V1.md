# Phase 84: Incident Runbook Integration

**Status:** ✅ Abgeschlossen  
**Datum:** 2025-12-09  
**Abhängigkeit:** Phase 82 (Alert-Pipeline), Phase 83 (Alert-Historie)

---

## Übersicht

Phase 84 erweitert das Alert-System um automatische Runbook-Verlinkungen.
Jeder Alert erhält basierend auf `category`, `source` und `severity` passende 
Incident-Runbooks, die in Slack/E-Mail und im Web-Dashboard angezeigt werden.

## Features

### 1. Runbook-Registry (`src/infra/runbooks/`)

- **`RunbookLink` Dataclass**: Immutables Modell für Runbook-Metadaten (id, title, url, description)
- **`RUNBOOK_REGISTRY`**: Zentrale Registrierung aller verfügbaren Runbooks
- **`resolve_runbooks_for_alert()`**: Resolver-Funktion für automatische Zuordnung

### 2. Mapping-Logik

Das Mapping basiert auf drei Dimensionen:

| Dimension | Beschreibung | Beispiele |
|-----------|--------------|-----------|
| `category` | Alert-Kategorie | `RISK`, `EXECUTION`, `SYSTEM` |
| `source` | Quelle des Alerts | `live_risk_severity`, `live_risk_limits` |
| `severity` | Dringlichkeit | `INFO`, `WARN`, `CRITICAL` |

**Lookup-Reihenfolge:**
1. Exakter Match: `(category, source, severity)`
2. Ohne Severity: `(category, source, None)`
3. Ohne Source: `(category, None, severity)`
4. Nur Category: `(category, None, None)`

### 3. Registrierte Runbooks

| ID | Titel | Verwendung |
|----|-------|------------|
| `live_alert_pipeline` | Live Alert Pipeline Runbook | Alle Alerts |
| `live_risk_severity` | Live Risk Severity Runbook | RISK + severity-basierte Alerts |
| `live_risk_limits` | Live Risk Limits Runbook | RISK + limit-basierte Alerts |
| `live_deployment` | Live Deployment Playbook | EXECUTION + SYSTEM |
| `incident_drills` | Incident Drills | CRITICAL Alerts |

### 4. Integration in Alert-Pipeline

```python
# AlertPipelineManager._attach_runbooks()
runbooks = resolve_runbooks_for_alert(alert)
if runbooks:
    alert.context["runbooks"] = [
        {"id": rb.id, "title": rb.title, "url": rb.url}
        for rb in runbooks
    ]
```

### 5. Slack-Channel-Erweiterung

Slack-Alerts enthalten jetzt eine **Runbooks-Sektion**:

```
📋 Runbooks:
• Live Risk Severity Runbook – https://...
• Live Alert Pipeline Runbook – https://...
```

### 6. E-Mail-Channel-Erweiterung

E-Mails enthalten im Plain-Text und HTML-Body eine Runbooks-Liste:

**Plain-Text:**
```
📋 Runbooks:
  • Live Risk Severity Runbook: https://...
  • Live Alert Pipeline Runbook: https://...
```

**HTML:**
```html
<h3>📋 Runbooks</h3>
<ul>
  <li><a href="...">📘 Live Risk Severity Runbook</a></li>
</ul>
```

### 7. Web-Dashboard-Erweiterung

Die Alert-Tabelle unter `/live/alerts` enthält eine neue **Runbooks-Spalte**:

- Zeigt bis zu 2 Runbook-Badges pro Alert
- Klickbare Links öffnen in neuem Tab
- Truncation bei langen Titeln
- `+N` Indikator bei mehr als 2 Runbooks

---

## Architektur

```
src/
├── infra/
│   └── runbooks/
│       ├── __init__.py      # Exports
│       ├── models.py        # RunbookLink Dataclass
│       └── registry.py      # Mapping & Resolver
│
├── live/
│   └── alert_pipeline.py    # _attach_runbooks() Integration
│
└── webui/
    └── alerts_api.py        # RunbookSummary Model

templates/
└── peak_trade_dashboard/
    └── alerts.html          # Runbooks-Spalte
```

---

## Beispiel: RISK Alert mit Runbooks

```python
from src.live.alert_pipeline import AlertMessage, AlertSeverity, AlertCategory, AlertPipelineManager

alert = AlertMessage(
    title="Risk Severity changed: GREEN → YELLOW",
    body="⚠️ Daily loss approaching limit (85%)",
    severity=AlertSeverity.WARN,
    category=AlertCategory.RISK,
    source="live_risk_severity",
)

manager.send(alert)

# Nach send() enthält alert.context["runbooks"]:
# [
#   {"id": "live_risk_severity", "title": "Live Risk Severity Runbook", "url": "..."},
#   {"id": "live_alert_pipeline", "title": "Live Alert Pipeline Runbook", "url": "..."},
# ]
```

---

## Tests

### Neue Testdatei: `tests/test_runbook_registry.py`

- `TestRunbookLink`: Dataclass-Tests
- `TestRunbookRegistry`: Registry-Tests
- `TestResolveRunbooks`: Resolver-Tests für alle Kombinationen
- `TestRunbookIntegration`: URL-Format, Eindeutigkeit

### Erweiterungen in `tests/test_alert_pipeline.py`

- `TestPhase84RunbookIntegration`: 
  - Automatisches Anhängen von Runbooks
  - Slack-Payload mit Runbooks
  - Email-Body mit Runbooks
  - Context-Erhaltung

### Erweiterungen in `tests/test_alert_storage.py`

- `test_store_alert_with_runbooks`: Persistierung
- `test_alert_with_runbooks_roundtrip`: Vollständiger Roundtrip

---

## Konfiguration

### Runbook-URLs anpassen

In `src/infra/runbooks/registry.py`:

```python
# Base-URL für GitHub-Docs
BASE_DOCS_URL = "https://github.com/rauterfrank-ui/Peak_Trade/blob/main/docs"
```

### Neue Runbooks hinzufügen

1. In `RUNBOOK_REGISTRY` eintragen:
```python
RUNBOOK_REGISTRY["new_runbook"] = RunbookLink(
    id="new_runbook",
    title="New Runbook Title",
    url=f"{BASE_DOCS_URL}/runbooks/NEW_RUNBOOK.md",
    description="Beschreibung",
)
```

2. In `_ALERT_RUNBOOK_MAPPING` zuordnen:
```python
("CATEGORY", "source_pattern", "SEVERITY"): ["new_runbook", ...],
```

---

## Akzeptanzkriterien

- [x] Alerts aus `live_risk_severity` enthalten Risk-Severity-Runbook
- [x] Alerts aus `live_risk_limits` enthalten Risk-Limits-Runbook
- [x] CRITICAL Alerts enthalten Incident-Drills-Runbook
- [x] Slack-Alerts zeigen Runbooks als klickbare Links
- [x] E-Mail-Alerts enthalten Runbooks in Plain-Text und HTML
- [x] Web-Dashboard zeigt Runbook-Badges in Alert-Tabelle
- [x] Runbooks werden in Alert-Storage persistiert
- [x] Alle Tests bestehen

---

## Changelog

| Datum | Änderung |
|-------|----------|
| 2025-12-09 | Initial Release Phase 84 |
