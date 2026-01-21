# Peak_Trade – Mindmap & Ideen-Ordner

Dieser Ordner sammelt **alle Ideen, Experimente, R&D-Spuren und ToDos**, die nicht direkt als Phase im Roadmap-Dokument leben – aber trotzdem wichtig sind.

Ziel:

* Ideen von **Stunde 0 an logisch geordnet** zu haben
* Jede Idee hat eine **bewusste Bewertung** (Impact, Effort, Risk, Urgency)
* Die wichtigsten Themen sind immer sichtbar (Top-Liste, Tiers)

---

## 1. Struktur

Empfohlene Struktur:

* `00_MINDMAP_OVERVIEW.md`
  → Cockpit: Top-20-Ideen, Ranking, aktueller Fokus

* `10_STRATEGY_IDEAS.md`
  → Strategien, Signals, Filters, Portfolio-Logik

* `20_DATA_INFRA_IDEAS.md`
  → Data Layer, Caches, Loader, Normalisierung, Synthetic Data

* `30_EXECUTION_RISK_IDEAS.md`
  → Order-Execution, Routing, RiskLimits, Safety-Gates, Monitoring

* `40_MONITORING_DASHBOARD_IDEAS.md`
  → Web-Dashboards, CLI-Views, Alerts, Logging-Verbesserungen

* `50_AI_WORKFLOW_IDEAS.md`
  → AI-Assistants, Automatisierung, Agenten, Prompt-Bibliothek

* `template&#47;IDEA_TEMPLATE.md`
  → Template für einzelne Ideen, wenn sie größer werden

---

## 2. Bewertung & Ranking

Jede Idee bekommt vier Scores von **1 (niedrig) bis 5 (hoch)**:

* **Impact**
  „Wie groß ist der Nutzen für Peak_Trade als Ganzes?"
  (Plattform-Stabilität, PnL-Potenzial, Risiko-Reduktion…)

* **Urgency**
  „Wie zeitkritisch / unblockend ist das für andere Themen?"

* **Effort**
  „Wie viel Aufwand ist das grob?"
  (1 = kleines Ticket, 5 = großes Teilprojekt)

* **Risk/Safety-Nutzen**
  „Wie sehr verbessert diese Idee Sicherheit, Robustheit, Transparenz?"

Daraus wird ein einfacher Prioritäts-Score berechnet:

```text
PriorityScore = Impact + Urgency + RiskSafety – Effort
```

* Minimal: **1**
* Maximal: **14**

### Tiers

Aus dem Score ergeben sich Tiers:

* **T1 – Core / Safety-First**
  Score ≥ 10
  → beeinflusst Kern-Sicherheit, zentrale Architektur oder unblockt wichtige Phasen.

* **T2 – Strong / Booster**
  Score 7–9
  → sinnvoll, starker Hebel, aber kein akuter Blocker.

* **T3 – Würzig / R&D / Nice-to-have**
  Score ≤ 6
  → Experimente, Explorations, Spielwiese – können später wichtig werden, müssen aber nicht.

### Status

Jede Idee hat einen Status:

* `NEW` – frisch eingefangen, noch nicht bewertet
* `REVIEWED` – Scores vergeben, Tier zugeordnet
* `PLANNED` – in einer Phase / Sprint / Runbook verankert
* `IN_PROGRESS` – aktiv in Arbeit
* `DONE` – umgesetzt
* `ARCHIVED` – verworfen oder obsolet

---

## 3. Workflow

### 3.1 Neue Idee hinzufügen

1. Datei nach Kategorie wählen (z.B. `10_STRATEGY_IDEAS.md`).
2. Unter einer Überschrift einen neuen Eintrag mit Kurzbeschreibung anlegen.
3. Minimal ausfüllen:
   * Kurz-Titel
   * 1–2 Sätze Beschreibung
   * Status = `NEW`
4. Optional: Direkt grobe Scores (Impact/Effort/…).

### 3.2 Regelmäßiges Review

Empfehlung: 1× pro Woche oder nach Abschluss einer Phase.

1. `00_MINDMAP_OVERVIEW.md` öffnen.
2. Die wichtigsten offenen Ideen aus den Detail-Dateien einsammeln.
3. Für diese Ideen:
   * Scores prüfen/aktualisieren
   * Tier prüfen (T1/T2/T3)
   * Status anpassen (z.B. `REVIEWED` → `PLANNED`).
4. Tabelle in `00_MINDMAP_OVERVIEW.md` nach Score sortieren.

So bleibt der Mindmap-Ordner ein **lebendes System**, kein Ideen-Friedhof.

---

## 4. Verbindung zu Roadmap & Phasen

* Wenn eine Idee „reif" ist → in die offizielle Roadmap/Phase übernehmen (z.B. `PHASE_XX_*.md`).
* Im Ideen-Eintrag notieren:
  * `Linked Phase: PHASE_22_EXECUTION_PIPELINE` (Beispiel)
* Nach Umsetzung:
  * Status = `DONE`
  * Kurz notieren, in welcher Commit-Range / Version das umgesetzt wurde.

---

## 5. Tipp: Naming & IDs

Optional können Ideen eine ID bekommen:

* `IDEA-STRAT-001` – Strategie
* `IDEA-DATA-003` – Data/Infra
* `IDEA-RISK-005` – Execution/Risk
* `IDEA-DASH-002` – Monitoring/Dashboard
* `IDEA-AI-004` – AI/Automation

Diese IDs helfen, Ideen in Commits, Tickets und Runbooks wiederzufinden.

---

Dieses Dokument ist die „Spielregel" für den Mindmap-Ordner.
Alles Weitere (Detail-Listen, konkrete Ideen) lebt in den anderen Dateien.
