# Live-Risk Severity – UI, Alerts & Runbook Integration

**Version:** v1.0  
**Datum:** 2025-12-09  
**Status:** Implementiert & getestet

---

## 1️⃣ Übersicht

Das bestehende Live-Risk Severity-System (`OK`, `WARNING`, `BREACH`) wurde **end-to-end** integriert:

* in das **Web-Dashboard** (Risk-Ampel auf Session-Ebene),
* in **Alerting & Logging** (Slack/CLI/Logs),
* in ein **operationalisiertes Runbook** mit klaren Handlungsempfehlungen für Operatoren.

Damit wird aus der reinen Limit-Logik ein vollwertiges **Risk-Operations-Modul** für Live-/Paper-/Shadow-Sessions.

---

## 2️⃣ Architektur

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Live-Risk-Layer                              │
├─────────────────────────────────────────────────────────────────────┤
│  risk_limits.py                                                     │
│  ├── RiskCheckSeverity (OK, WARNING, BREACH)                        │
│  ├── LiveRiskCheckResult                                            │
│  │   ├── severity: RiskCheckSeverity                                │
│  │   ├── risk_status: "green" | "yellow" | "red"                    │
│  │   └── limit_details: List[LimitCheckDetail]                      │
│  └── LiveRiskLimits.check_orders() / evaluate_portfolio()           │
├─────────────────────────────────────────────────────────────────────┤
│  risk_alert_helpers.py    (NEU)                                     │
│  ├── format_risk_alert_message()                                    │
│  ├── format_slack_risk_alert()                                      │
│  ├── trigger_risk_alert()                                           │
│  ├── RiskAlertFormatter (Terminal/CLI)                              │
│  └── get_operator_guidance()                                        │
├─────────────────────────────────────────────────────────────────────┤
│  risk_runbook.py          (NEU)                                     │
│  ├── RunbookEntry (immediate_actions, checklist, escalation)        │
│  ├── get_runbook_for_status()                                       │
│  └── format_runbook_for_operator()                                  │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Konsumenten                                  │
├─────────────────────────────────────────────────────────────────────┤
│  Web-Dashboard (live_track.py + Templates)                          │
│  ├── Risk-Ampel in Sessions-Tabelle                                 │
│  ├── Risk-Badge in Session-Detail                                   │
│  └── Inline Operator-Empfehlungen                                   │
├─────────────────────────────────────────────────────────────────────┤
│  Alerting (alerts.py + risk_alert_helpers.py)                       │
│  ├── Slack-Webhooks                                                 │
│  ├── CLI/Terminal-Ausgabe                                           │
│  └── Python-Logging (WARNING/ERROR)                                 │
├─────────────────────────────────────────────────────────────────────┤
│  Execution-Pipeline (pipeline.py)                                   │
│  └── Order-Blocking bei BREACH                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3️⃣ Web-Dashboard-Integration

### Betroffene Komponenten

| Datei | Änderungen |
|-------|------------|
| `src/webui/live_track.py` | `LiveSessionSummary` und `LiveSessionDetail` mit `risk_status`, `risk_severity`, `risk_limit_details` |
| `templates/.../index.html` | Risk-Ampel in Sessions-Tabelle und "Letzte Session"-Kachel |
| `templates/.../session_detail.html` | Risk-Status-Badge, Limit-Details-Tabelle, Operator-Empfehlungen |

### Darstellung der Ampel

| Status | Icon | Badge | Beschreibung |
|--------|------|-------|--------------|
| 🟢 **GREEN** | `✅` | OK | Alle Limits komfortabel eingehalten |
| 🟡 **YELLOW** | `⚠️` | WARNING | Limit im Warnbereich (80-99%) |
| 🔴 **RED** | `⛔` | BREACH | Limit verletzt, Orders blockiert |

### Session-Detail-View

Bei WARNING oder BREACH zeigt die Detail-Ansicht:

1. **Prominentes Risk-Badge** mit Farbe und Icon
2. **Limit-Details-Karten** mit:
   - Limit-Name
   - Aktueller Wert / Limit-Wert
   - Ratio als Prozent
   - Progress-Bar
   - Severity-Badge (OK/WARNING/BREACH)
3. **Operator-Empfehlungen** (inline Runbook-Auszug)

---

## 4️⃣ Alerting & Logging

### Neue Datei: `src/live/risk_alert_helpers.py`

#### Funktionen

```python
# Message-Formatierung
format_risk_alert_message(result, source, include_details, max_details)
format_slack_risk_alert(result, source, session_id)
format_limit_detail(detail)

# Alert-Trigger
trigger_risk_alert(result, alert_sink, source, session_id, extra_context)

# Operator-Guidance
get_operator_guidance(risk_status) -> OperatorGuidance
get_guidance_for_result(result) -> OperatorGuidance

# CLI/Terminal-Formatierung
RiskAlertFormatter.format_terminal(result)  # Mit ANSI-Farben
RiskAlertFormatter.format_compact(result)   # Einzeiler
```

#### Alert-Level-Mapping

| Severity | Alert-Level | Logger | Alert-Code |
|----------|-------------|--------|------------|
| OK | – | (Debug) | – |
| WARNING | `AlertLevel.WARNING` | `logger.warning()` | `RISK_LIMIT_WARNING` |
| BREACH | `AlertLevel.CRITICAL` | `logger.error()` | `RISK_LIMIT_BREACH` |

#### Beispiel: Slack-Alert bei WARNING

```
⚠️ *RISK WARNING* – Monitoring erhöhen
Session: `session_20251209_001`
Source: `live_risk.orders`
Status: `yellow`

*Limit-Status:*
🟡 `max_total_exposure`: 8500.00 / 10000.00 (85.0%)

*Empfohlene Aktionen:*
• Positionen und offene Orders überprüfen
• Trading-Intensität reduzieren
• Daily-PnL im Auge behalten
```

---

## 5️⃣ Runbook / Operator-Sicht

### Neue Datei: `src/live/risk_runbook.py`

#### Datenstruktur: `RunbookEntry`

```python
@dataclass
class RunbookEntry:
    status: RiskStatus                      # "green" | "yellow" | "red"
    severity: str                           # "ok" | "warning" | "breach"
    title: str
    icon: str
    summary: str
    description: str

    immediate_actions: List[str]            # Sofort-Aktionen
    monitoring_actions: List[str]           # Monitoring-Empfehlungen
    communication_actions: List[str]        # Kommunikation
    recovery_actions: List[str]             # Erholung/Stabilisierung

    escalation_threshold: Optional[str]     # Wann eskalieren
    escalation_contacts: List[str]          # An wen

    checklist: List[RunbookChecklist]       # Detaillierte Checkliste
    monitoring_interval: str                # z.B. "1-5 min"
    auto_actions: List[str]                 # Was das System automatisch tut
    documentation_required: List[str]       # Erforderliche Dokumentation
```

#### Runbook pro Status

##### GREEN (OK)

```
✅ Risk Status: OK

SOFORTIGE AKTIONEN:
  1. Keine sofortigen Aktionen erforderlich

MONITORING (Standard 5-15 min):
  • Routinemäßiges Monitoring fortsetzen
  • Nächsten regulären Check-In abwarten

AUTOMATISCHE SYSTEM-AKTIONEN:
  ➤ Normaler Trading-Betrieb
  ➤ Orders werden ausgeführt
```

##### YELLOW (WARNING)

```
⚠️ Risk Status: WARNING

SOFORTIGE AKTIONEN:
  1. Dashboard öffnen und betroffene Limits identifizieren
  2. Aktuelle Positionen und offene Orders überprüfen
  3. Exposure-Verteilung analysieren (Konzentration?)
  4. Daily-PnL-Entwicklung prüfen

MONITORING (Erhöht 1-5 min):
  • Limit-Ratios kontinuierlich beobachten
  • Alarme für weitere Verschlechterung aktivieren

RECOVERY / STABILISIERUNG:
  • Trading-Intensität reduzieren
  • Auf defensive Strategien umschalten
  • Position-Sizing anpassen
  • Stop-Loss-Orders prüfen/nachjustieren

ESKALATION: Bei Trend Richtung BREACH oder nach 30 min ohne Verbesserung
  Kontakte: Trading-Team-Lead, Risk-Manager

CHECKLISTE:
  🔴 [ ] Betroffene Limits im Dashboard identifizieren (< 2 min, Operator)
  🔴 [ ] Aktuelle Positionen auflisten (< 3 min, Operator)
  🔴 [ ] Exposure-Verteilung prüfen (< 5 min, Operator)
  🟡 [ ] Team informieren (< 2 min, Operator)
```

##### RED (BREACH)

```
⛔ Risk Status: BREACH

SOFORTIGE AKTIONEN:
  1. SOFORT: Alle Trading-Aktivitäten pausieren
  2. Dashboard öffnen: Welche Limits sind verletzt?
  3. Zeitpunkt und Kontext des BREACH notieren
  4. Bestehende Positionen auflisten
  5. Offene Orders identifizieren

KOMMUNIKATION:
  • Team-Lead SOFORT informieren
  • Risk-Manager benachrichtigen
  • Incident-Channel öffnen

RECOVERY / STABILISIERUNG:
  • Offene Orders prüfen und ggf. STORNIEREN
  • Bestehende Positionen evaluieren
  • Bei Over-Exposure: Kontrollierter Positionsabbau
  • Warten bis Limits wieder im grünen Bereich

AUTOMATISCHE SYSTEM-AKTIONEN:
  ➤ Neue Orders werden BLOCKIERT
  ➤ CRITICAL-Alerts werden gesendet
  ➤ Logging auf ERROR-Level

ESKALATION: SOFORT bei BREACH
  Kontakte: Trading-Team-Lead (sofort), Risk-Manager (sofort),
            Management (bei > 2% Verlust)

ERFORDERLICHE DOKUMENTATION:
  ☐ Incident-Log mit Zeitstempel
  ☐ Liste der verletzten Limits mit Werten
  ☐ Snapshot aller Positionen
  ☐ Screenshots von Dashboard/Charts
  ☐ Root-Cause (sobald bekannt)
  ☐ Lessons Learned (für Postmortem)
```

---

## 6️⃣ Tests & Qualitätssicherung

### Neue Test-Dateien

| Datei | Tests | Abdeckung |
|-------|-------|-----------|
| `tests/test_risk_alert_helpers.py` | 26 | Formatting, Trigger, Guidance |
| `tests/test_risk_runbook.py` | 26 | Runbook-Struktur, Content |
| `tests/test_risk_severity.py` | 34 | Severity-Enum, Aggregation, Limits |
| `tests/test_risk_scenarios.py` | 16 | Realistische Szenarien |

**Gesamt: 102 Tests, alle bestanden ✅**

### Getestete Szenarien

1. **Multi-Day Drawdown** – Akkumulation über mehrere Tage
2. **Gap Risk** – Flash Crash mit sofortigem BREACH
3. **Over-Exposure** – Total/Symbol/Positions-Limits
4. **Kombinierte Risiken** – Mehrere WARNING + ein BREACH
5. **Recovery** – Tageswechsel-Reset

---

## 7️⃣ Konfiguration

### Config-Beispiel (`config.toml`)

```toml
[live_risk]
enabled = true
max_daily_loss_abs = 500.0
max_daily_loss_pct = 5.0
max_total_exposure_notional = 10000.0
max_symbol_exposure_notional = 3000.0
max_open_positions = 5
max_order_notional = 2000.0
block_on_violation = true
warning_threshold_factor = 0.8  # WARNING ab 80%

[live_alerts]
enabled = true
min_level = "warning"
sinks = ["log", "slack_webhook"]
slack_webhook_urls = ["https://hooks.slack.com/..."]
```

---

## 8️⃣ Usage-Beispiele

### Im Code: Risk-Check mit Alerting

```python
from src.live.risk_limits import LiveRiskLimits
from src.live.risk_alert_helpers import trigger_risk_alert, format_risk_alert_message
from src.live.alerts import build_alert_sink_from_config

# Risk-Check durchführen
limits = LiveRiskLimits.from_config(cfg, starting_cash=10000.0)
result = limits.check_orders(orders)

# Alert bei WARNING oder BREACH
if result.severity != RiskCheckSeverity.OK:
    trigger_risk_alert(
        result,
        alert_sink,
        source="live_risk.orders",
        session_id="session_123",
    )

# Terminal-Ausgabe
from src.live.risk_alert_helpers import RiskAlertFormatter
formatter = RiskAlertFormatter(use_colors=True)
print(formatter.format_terminal(result))
```

### Im Code: Runbook abrufen

```python
from src.live.risk_runbook import get_runbook_for_status, format_runbook_for_operator

runbook = get_runbook_for_status("red")
print(format_runbook_for_operator(runbook))

# Oder für ein Result:
from src.live.risk_runbook import get_runbook_for_severity
runbook = get_runbook_for_severity(result.severity.value)
```

---

## 9️⃣ Rückwärtskompatibilität

Die Erweiterung ist **vollständig rückwärtskompatibel**:

- `LiveRiskCheckResult` hat Defaults für neue Felder (`severity=OK`, `limit_details=[]`)
- Bestehende Aufrufer funktionieren unverändert
- Alle 102 Risk-Tests bleiben grün
- Keine Breaking Changes an Public APIs

---

## 🔟 Nächste Schritte (Optional)

- [ ] Email-Alerting bei BREACH
- [ ] Pager-Integration (PagerDuty/OpsGenie)
- [ ] Automatisches Position-Hedging bei WARNING
- [ ] Risk-Dashboard als eigenständige View
- [ ] Historische Risk-Events-Timeline
- [ ] Severity-Trends über Zeit (Analytics)

---

### Verwandte Runbooks

- [`LIVE_ALERT_PIPELINE_SLACK_EMAIL_RUNBOOK_V1`](LIVE_ALERT_PIPELINE_SLACK_EMAIL_RUNBOOK_V1.md) – Versand der Alerts (Slack/E-Mail) inkl. Severity
- [`INCIDENT_RUNBOOK_INTEGRATION_V1`](INCIDENT_RUNBOOK_INTEGRATION_V1.md) – Wie Alerts automatisch mit Incident-Runbooks verknüpft werden (Phase 84)

---

**Maintainer:** Peak_Trade Team  
**Letzte Aktualisierung:** 2025-12-09
