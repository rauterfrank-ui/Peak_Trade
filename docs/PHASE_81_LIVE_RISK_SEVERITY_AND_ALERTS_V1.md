# Phase 81 – Live Risk Severity & Alert Runbook v1

**Status:** ✅ Implementiert (v1)
**Bereich:** Live-Track / Risk & Safety
**Scope:** Live-Risk-Severity, UI-Ampel, Alert-Helper, kodifiziertes Operator-Runbook

Mit Phase 81 bekommt der Live-Track eine klar definierte **Risk-Severity-Schicht** (GREEN/YELLOW/RED) inklusive UI-Ampel, Alert-Helfern und einem expliziten Operator-Runbook. Ziel ist ein konsistentes, nachvollziehbares Verhalten im Live-/Shadow-/Paper-Betrieb – weit weg von „Cowboy-Live-Trading".

---

## 1. Ziel der Phase

**Primärziel:**
Einführen einer einheitlichen **Risk-Severity-Bewertung** im Live-Track, die:

* aus den bestehenden Risk-Limits abgeleitet wird,
* im Web-Dashboard als **Ampel/UI-Badges** sichtbar ist,
* zentrale **Alert-Helper** zur Verfügung stellt, und
* ein klar formuliertes **Operator-Runbook** hinterlegt, das bei GREEN/YELLOW/RED konkrete Handlungsempfehlungen vorgibt.

Damit wird der Live-Track von einem „reinen Status-Monitor" zu einem **risk-sensitiven Cockpit**, in dem Entscheidungen strukturiert und reproduzierbar getroffen werden.

---

## 2. Nicht-Ziele

Diese Phase **implementiert explizit NICHT**:

* ❌ Kein automatisches **Auto-Deleveraging** oder Auto-Flatting von Positionen
* ❌ Kein direkter **Broker-Live-Handle** (keine echten Orders, kein Production-Broker)
* ❌ Kein komplexes **ML-/Quant-Risk-Modell** (kein VaR, CVaR, RL-Agent etc.)
* ❌ Keine externe Alert-Pipeline (Slack/E-Mail/PagerDuty) – nur vorbereitende Helper

Phase 81 fokussiert auf die **Risk-Severity-Logik**, UI-Darstellung und das Runbook. Die Verdrahtung in echte Kommunikationskanäle (Slack, Mail, etc.) ist bewusst für eine spätere Phase vorgesehen (z.B. Phase 82).

---

## 3. Architektur-Übersicht

### 3.1 Komponenten

Relevante Module/Klassen für Phase 81:

* `src/live/risk_limits.py`

  * Verantwortlich für **Risk-Limits** und die Herleitung einer **Severity** aus aktuellen Live-Daten.

* `src/live/risk_alert_helpers.py`

  * Enthält **Helper-Funktionen**, um aus Severity + Kontext:

    * Operator-Nachrichten zu generieren,
    * Ziel-Kanäle/Empfänger zu bestimmen (zukünftige Erweiterung),
    * strukturierte Alert-Objekte zu bauen.

* `src/live/risk_runbook.py`

  * Kodifiziert das **Operator-Runbook**:

    * Handlungsempfehlungen für GREEN/YELLOW/RED,
    * Checklisten und Eskalationspfade in Python-Form.

* `src/webui/live_track.py`

  * Verknüpft Risk-/Severity-Daten mit dem Web-Dashboard,
  * Bereitet Daten für Templates auf (Severity-Badges, Panels).

* `templates&#47;...&#47;index.html`

  * Live-Track-Übersicht mit Severity-/Status-Anzeigen.

* `templates&#47;...&#47;session_detail.html`

  * Detail-View pro Live-Session, inkl. Severity-Panel und Runbook-Hinweisen.

* `docs/runbooks/LIVE_RISK_SEVERITY_INTEGRATION.md`

  * Ausführliches **Runbook & Integration-Dokument** (End-to-End-Fluss, UI-Screens, Tests, Konfiguration).

### 3.2 Datenfluss (Mermaid-Skizze)

```mermaid
flowchart LR
    A[Market Data & Positions] --> B[LiveRiskLimits]
    B --> C{Risk Limits Check}
    C -->|OK / leicht erhöht| D[Severity: GREEN/YELLOW]
    C -->|kritisch| E[Severity: RED]

    D --> F[RiskRunbook (GREEN/YELLOW Empfehlungen)]
    E --> F[RiskRunbook (RED Maßnahmen)]

    D --> G[RiskAlertHelpers]
    E --> G[RiskAlertHelpers]

    G --> H[LiveTrack Backend]
    H --> I[LiveTrack UI (Index + Session Detail)]

    F --> I
    I --> J[Operator Actions]
```

**Kernaussage:**
Die bestehenden Risk-Limits bleiben die „Quelle der Wahrheit". Phase 81 legt eine **Severity-Schicht + Runbook** oben drauf, ohne das fundamentale Risk-Modell zu verändern.

---

## 4. Operator-Runbook (Kurzform)

Das vollständige Runbook ist in `docs/runbooks/LIVE_RISK_SEVERITY_INTEGRATION.md` dokumentiert. Phase 81 ergänzt dies durch eine **kodifizierte Logik** in `src/live/risk_runbook.py` und eine **UI-nahe Darstellung**.

### 4.1 Severity-Level Überblick

| Severity | Bedeutung                            | Operator-Grundhaltung                                   |
| -------- | ------------------------------------ | ------------------------------------------------------- |
| GREEN    | Innerhalb definierter Risk-Limits    | Normalbetrieb, entspanntes Monitoring                   |
| YELLOW   | Nähe zu Limits, erhöhte Sensitivität | Erhöhte Wachsamkeit, vorbereiten auf Eingriffe          |
| RED      | Limits verletzt / Situation kritisch | Bremsen, Positionen stoppen/reduzieren, Ursachenanalyse |

---

### 4.2 GREEN – Normalmodus (Monitoring-Light)

**Typische Situation:**

* Drawdown, Exposure und P&L innerhalb „comfort zone"
* Keine harten Limitverletzungen, keine ungewöhnlichen Spikes

**Operator-Verhalten:**

* Dashboard regelmäßig checken (z.B. alle X Minuten),
* Prüfen:

  * Ist die Anzahl der Trades pro Zeitraum plausibel?
  * Passen P&L und Exposure zu den Strategien/Regimes?
* Keine aktiven Eingriffe nötig, aber:

  * Logging & Notizen für spätere Analyse (optional).

**Runbook-Logik (High Level):**

* `risk_runbook.py` liefert für GREEN:

  * knappen Status-Text („System im Normalbereich"),
  * optionale Hinweis-Checkliste („Monitoring-Frequenz", „Logfile-Check").

---

### 4.3 YELLOW – Erhöhte Wachsamkeit

**Typische Trigger:**

* Metriken nähern sich einem harten Limit (z.B. Daily-Loss nahe Schwellenwert),
* Ungewöhnliche Volatilität, Spikes in Trade-Frequenz oder Slippage,
* Einzelne Limitverletzungen, die noch nicht „systemkritisch" sind.

**Operator-Verhalten:**

1. **Sofort prüfen:**

   * Aktuelle P&L (realisiert + unrealisiert),
   * Offene Positionen (Größe, Hebel, Instrumente),
   * Letzte N Trades (Hit-Rate, Slippage, Fehler?).

2. **Maßnahmen vorbereiten:**

   * Order-Flow ggf. verlangsamen (z.B. manuell keine neuen Trades triggern),
   * Anpassen der Monitoring-Frequenz (z.B. auf < X Minuten),
   * Klären, ob das Verhalten durch ein bekanntes Regime erklärbar ist.

3. **Dokumentation:**

   * Kurzer Log-Eintrag (Timestamp, Ursache, erste Einschätzung),
   * Falls wiederkehrend: Issue/Notiz im R&D-Backlog.

**Runbook-Logik (High Level):**

* `risk_runbook.py` liefert für YELLOW:

  * eine fokussierte Checkliste,
  * klare Empfehlung „kein neues Risiko aufbauen, bevor die Lage verstanden ist".

---

### 4.4 RED – Harte Bremsung

**Typische Trigger:**

* Harte Limitverletzung (z.B. Max-Drawdown überschritten),
* System-Anomalien (z.B. Order-Fehler, Connectivity-Issues),
* Unerwartete Marktbewegungen mit signifikantem Impact.

**Operator-Verhalten:**

1. **Sofortmaßnahmen:**

   * Neue Order-Generierung stoppen (Pause-Modus aktivieren),
   * Offene Positionen bewerten – ggf. manuell reduzieren/schließen,
   * Logs und Metriken sichern für Post-Mortem.

2. **Eskalation:**

   * Falls konfiguriert: Alert an definierte Kanäle senden,
   * Dokumentation des Vorfalls (Timestamp, Auslöser, ergriffene Maßnahmen).

3. **Analyse:**

   * Ursachenforschung durchführen,
   * Entscheidung treffen: Weiterbetrieb nach Fix oder längerer Stopp.

**Runbook-Logik (High Level):**

* `risk_runbook.py` liefert für RED:

  * Eskalations-Checkliste,
  * klare Anweisung „System pausieren, kein neues Risiko".

---

## 5. UI-Integration

### 5.1 Dashboard-Ampel

Das Live-Track-Dashboard zeigt prominent eine **Severity-Ampel**:

* 🟢 GREEN – Alles im grünen Bereich
* 🟡 YELLOW – Erhöhte Aufmerksamkeit erforderlich
* 🔴 RED – Kritischer Zustand, Eingriff notwendig

### 5.2 Session-Detail-View

Pro Session werden angezeigt:

* Aktueller Severity-Status mit Timestamp,
* Relevante Metriken (P&L, Drawdown, Exposure),
* Kontext-sensitive Runbook-Hinweise basierend auf aktuellem Status.

---

## 6. Alert-Helper (Vorbereitung)

`src/live/risk_alert_helpers.py` stellt Helper bereit für:

* **Alert-Objekt-Erstellung:** Strukturierte Alerts mit Severity, Message, Timestamp, Kontext.
* **Channel-Routing (Stub):** Vorbereitung für spätere Integration (Slack, E-Mail, etc.).
* **Formatting:** Konsistente Nachrichtenformatierung für verschiedene Ausgabekanäle.

> **Hinweis:** Die tatsächliche Anbindung an externe Dienste erfolgt in Phase 82.

---

## 7. Testabdeckung

Phase 81 beinhaltet Tests für:

* Severity-Berechnung aus Risk-Limits,
* Runbook-Empfehlungen pro Severity-Level,
* Alert-Helper-Funktionen,
* UI-Integration (Smoke-Tests für Ampel-Darstellung).

---

## 8. Zusammenfassung

Phase 81 etabliert eine **Risk-Severity-Schicht** im Live-Track:

| Aspekt              | Umsetzung                                          |
| ------------------- | -------------------------------------------------- |
| Severity-Levels     | GREEN / YELLOW / RED                               |
| UI-Integration      | Dashboard-Ampel, Session-Detail-Badges             |
| Runbook             | Kodifiziert in `risk_runbook.py`, UI-Hinweise      |
| Alert-Helper        | Strukturierte Alerts, Channel-Routing vorbereitet  |
| Nicht enthalten     | Auto-Deleveraging, Broker-Integration, ML-Modelle  |

---

*Dokument erstellt: Phase 81 – Live Risk Severity & Alert Runbook v1*
