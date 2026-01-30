# Phase 85: Alert Escalation & On-Call Integration v1

**Status:** ✅ Implementiert  
**Version:** 1.0  
**Datum:** Dezember 2025

---

## 1. Ziel der Phase

Implementierung einer **optionalen Eskalations-Schicht** für kritische Alerts, die On-Call-Dienste (PagerDuty, OpsGenie, etc.) integrieren kann.

**Kernprinzipien:**
- Eskalation ist eine **optionale Anreicherung** der bestehenden Alert-Pipeline
- **Config-gated**: Nur aktiv wenn explizit konfiguriert
- **Environment-gated**: Standardmäßig nur in `live` aktiv
- **Safety-first**: Eskalations-Fehler blockieren **niemals** den Alert-Flow

---

## 2. Nicht-Ziele

- ❌ Echte API-Calls zu externen Diensten (nur Stubs in Phase 85)
- ❌ Alert-Lifecycle-Management (Acknowledge, Resolve) – Phase 86
- ❌ Noise-Reduction / Aggregation – Phase 87
- ❌ Komplexes Routing (Team-basiert, Schedule-basiert)

---

## 3. User Stories

### US-85-1: Kritische Alerts eskalieren
> Als Operator möchte ich, dass CRITICAL Alerts automatisch an meinen On-Call-Dienst eskaliert werden, damit ich bei kritischen Ereignissen sofort benachrichtigt werde.

### US-85-2: Keine Eskalation in Test-Umgebungen
> Als Entwickler möchte ich, dass Eskalation in Paper/Testnet deaktiviert ist, damit ich keine falschen On-Call-Alerts auslöse.

### US-85-3: Eskalation darf Alerts nicht blockieren
> Als Operator möchte ich, dass meine Slack/Email-Alerts auch bei Eskalations-Fehlern zugestellt werden, damit keine kritischen Informationen verloren gehen.

---

## 4. Architektur / Komponenten

### 4.1 Paket-Struktur

```
src/infra/escalation/
├── __init__.py          # Public API
├── models.py            # EscalationEvent, EscalationTarget
├── providers.py         # NullProvider, PagerDutyLikeProviderStub
└── manager.py           # EscalationManager, Factory
```

### 4.2 EscalationEvent

Repräsentiert ein Ereignis, das potenziell eskaliert werden soll:

```python
@dataclass
class EscalationEvent:
    alert_id: str           # Eindeutige Alert-ID
    severity: str           # "CRITICAL", "WARN", "INFO"
    alert_type: str         # "RISK", "EXECUTION", "SYSTEM"
    summary: str            # Kurzer Titel
    details: Optional[Dict] # Zusätzliche Informationen
    symbol: Optional[str]   # Trading-Symbol (z.B. "BTC/EUR")
    session_id: Optional[str]
    created_at: datetime
```

### 4.3 EscalationTarget

Definiert ein On-Call-Ziel:

```python
@dataclass
class EscalationTarget:
    name: str               # "Primary Risk On-Call"
    provider: str           # "null", "pagerduty_stub"
    routing_key: Optional[str]  # PagerDuty Routing Key
    min_severity: str       # Minimale Severity für dieses Target
    enabled: bool
```

### 4.4 EscalationManager

Zentrale Steuerung der Eskalation:

```python
class EscalationManager:
    def maybe_escalate(self, event: EscalationEvent) -> bool:
        """
        Prüft ob eskaliert werden soll und führt ggf. durch.

        Gates:
        1. enabled = True?
        2. current_environment in enabled_environments?
        3. event.severity in critical_severities?

        Returns True wenn eskaliert wurde.
        """
```

### 4.5 Provider

#### NullEscalationProvider
- Tut nichts, loggt optional
- Für Tests und non-live Umgebungen

#### PagerDutyLikeProviderStub
- Baut PagerDuty Events API v2 Payload
- Speichert Payloads für Tests (`sent_payloads`)
- **Phase 85: Keine echten HTTP-Calls**

### 4.6 Integration in Alert-Pipeline

```
AlertPipelineManager.send(alert)
    │
    ├─→ _attach_runbooks(alert)     # Phase 84
    │
    ├─→ _persist_alert(alert)       # Phase 83
    │
    ├─→ _maybe_escalate(alert)      # Phase 85 ← NEU
    │       │
    │       └─→ EscalationManager.maybe_escalate(event)
    │               │
    │               └─→ Provider.send(event, target)
    │
    └─→ channel.send(alert)         # Slack/Email
```

---

## 5. Config-Gating

### 5.1 TOML-Konfiguration

```toml
[escalation]
# Global an/aus
enabled = false

# Nur in diesen Umgebungen eskalieren
enabled_environments = ["live"]

# Provider: "null" oder "pagerduty_stub"
provider = "null"

# Nur diese Severities eskalieren
critical_severities = ["CRITICAL"]

[escalation.targets.primary]
name = "Primary Risk On-Call"
provider = "pagerduty_stub"
routing_key = ""  # PagerDuty Integration Key
min_severity = "CRITICAL"
enabled = true

[escalation.providers.pagerduty]
api_url = "https://events.pagerduty.com/v2/enqueue"
enable_real_calls = false  # Phase 85: IMMER false!
```

### 5.2 Defaults (Safe)

| Setting | Default | Bedeutung |
|---------|---------|-----------|
| `enabled` | `false` | Eskalation deaktiviert |
| `enabled_environments` | `["live"]` | Nur in live |
| `provider` | `"null"` | Kein echter Provider |
| `critical_severities` | `["CRITICAL"]` | Nur CRITICAL |

---

## 6. Safety & Gating

### 6.1 Defensive Error Handling

```python
def _maybe_escalate(self, alert: AlertMessage) -> None:
    """Eskalation ist optional - Fehler werden NIEMALS propagiert."""
    if self._escalation_manager is None:
        return

    try:
        # ... Eskalation durchführen ...
    except Exception as e:
        # KRITISCH: Fehler NIEMALS propagieren
        self._logger.debug(f"Failed to escalate alert: {e}")
```

### 6.2 Garantien

1. **Eskalations-Fehler blockieren nie die Alert-Pipeline**
   - Slack/Email-Alerts werden immer zugestellt
   - Alert-Storage funktioniert unabhängig von Eskalation

2. **Keine echten API-Calls in Phase 85**
   - PagerDutyLikeProviderStub speichert nur Payloads
   - `enable_real_calls` ist standardmäßig `false`

3. **Environment-Gating**
   - Default: Nur in `live` aktiv
   - Paper/Testnet: Keine Eskalation

---

## 7. Tests & Akzeptanzkriterien

### 7.1 Neue Tests

| Test-Datei | Tests |
|------------|-------|
| `tests/test_escalation_manager.py` | 25+ Unit-Tests |
| `tests/test_alert_pipeline.py` | 8+ Integration-Tests |

### 7.2 Akzeptanzkriterien

| AC | Beschreibung | Status |
|----|--------------|--------|
| AC-85-1 | Non-critical Severity → keine Eskalation | ✅ |
| AC-85-2 | Critical in disabled Environment → keine Eskalation | ✅ |
| AC-85-3 | Critical in enabled Environment → Provider aufgerufen | ✅ |
| AC-85-4 | Provider-Exception → Error geschluckt, Alert geht weiter | ✅ |
| AC-85-5 | Config-Gating funktioniert | ✅ |
| AC-85-6 | Integration mit Alert-Storage funktioniert | ✅ |

### 7.3 Test-Ausführung

```bash
# Escalation-Manager Tests
python3 -m pytest tests/test_escalation_manager.py -v

# Alert-Pipeline Integration Tests
python3 -m pytest tests/test_alert_pipeline.py::TestPhase85EscalationIntegration -v

# Alle Alert-bezogenen Tests
python3 -m pytest -k "alert or escalation" -v
```

---

## 8. Dateien

### 8.1 Neue Dateien

```
src/infra/escalation/__init__.py
src/infra/escalation/models.py
src/infra/escalation/providers.py
src/infra/escalation/manager.py
tests/test_escalation_manager.py
docs/PHASE_85_ALERT_ESCALATION_AND_ON_CALL_V1.md
```

### 8.2 Modifizierte Dateien

```
src/live/alert_pipeline.py  # +_maybe_escalate(), +escalation_manager
config/config.toml          # +[escalation] Section
tests/test_alert_pipeline.py # +TestPhase85EscalationIntegration
docs/PEAK_TRADE_STATUS_OVERVIEW.md
```

---

## 9. Nächste Schritte

### Phase 86: Alert Lifecycle & Acknowledge
- Alert-Status-Tracking (open, acknowledged, resolved)
- Acknowledge-API für On-Call
- Timeout-basiertes Re-Alerting

### Phase 87: Noise Reduction & Aggregation
- Alert-Deduplication
- Rate-Limiting pro Source
- Aggregation ähnlicher Alerts

### Phase 88: Real Provider Integration
- Echte PagerDuty API-Calls
- OpsGenie-Integration
- Slack-Escalation-Kanal

---

## 10. Zusammenfassung

> **Escalation für kritische Alerts ist nun als config-gated, optional enrichment der Alert-Pipeline implementiert. Eskalations-Fehler können Alerts niemals blockieren.**

Die Implementierung folgt dem bewährten Muster aus Phase 84 (Runbook-Integration):
- Defensive Error-Handling
- Config-Gating mit sicheren Defaults
- Keine externen Abhängigkeiten in Phase 85
- Umfassende Test-Abdeckung
