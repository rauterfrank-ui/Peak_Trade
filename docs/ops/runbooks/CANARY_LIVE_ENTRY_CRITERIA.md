# Canary Live — Eintrittskriterien (Peak_Trade)

> **Zweck:** Freigaberahmen für **maximal konservatives** Echtgeld-Trading (**Canary Live**): ein kleiner, fest umrissener Scope, starke Gates, Operator-Pflicht.  
> **Default:** **NO-LIVE** — Canary ist eine **explizite Ausnahme**, keine Normalität.

**Canary Live =** ein einziges, schriftlich freigegebenes Setup (**1 Exchange · 1 Kontotyp · 1 Symbol · 1 Strategie-Version**), mit **sehr kleinem Notional**, **nur erlaubten Ordertypen**, **anwesendem Operator** und **aktiven Safety-/Observability-Pfaden**; jede Abweichung oder Erweiterung erfordert **neue** Freigabe.

---

## Hinweise (Guardrails)

- **Keine Anlageberatung.** Dieses Dokument beschreibt Governance- und Sicherheitskriterien, keine Empfehlung zum Kauf oder Verkauf von Instrumenten.
- **Keine Zeitprognosen** (kein „in X Wochen live“).
- **Kein implizites Hochskalieren:** Canary ist **kein** Rollout-Programm; größeres Kapital oder mehr Symbole sind **nicht** automatisch erlaubt.
- **Safety-first, Governance-first:** Technische und organisatorische Gates haben Vorrang vor Geschwindigkeit.

---

## Manifest (Scope-Fixierung — vor jeder Session ausfüllen)

Die folgenden Felder müssen **jeweils genau einen Wert** haben und **schriftlich** (z. B. Freigabeformular / Ticket) fixiert sein. Änderungen = **neue** Freigabe.

| Feld | Beispiel (nur illustrativ) | Bindend ist |
|------|---------------------------|-------------|
| Exchange | Kraken | der in der Freigabe benannte Anbieter |
| Kontotyp | Spot (kein Margin/Futures) | der in der Freigabe benannte Kontotyp |
| Symbol | `BTC/EUR` | genau ein Paar |
| Strategie-Version | z. B. `ma_crossover` + Git-Revision / Artefakt-ID | exakt eine deployierte Version |
| Erlaubte Ordertypen | z. B. nur **Limit** (kein Market/Stop ohne Zusatz-Freigabe) | die explizit gelisteten Typen |

**Nicht erlaubt:** parallele Canary-Setups mit anderem Symbol oder anderer Strategie **ohne** separate Freigabe.

---

## Die 8 Freigabekriterien

### 1. Scope-Fixierung

- **Exchange, Kontotyp, Symbol, Strategie-Version** und **erlaubte Ordertypen** sind wie oben **schriftlich** fixiert.
- Jede Code- oder Config-Änderung an Strategie, Routing oder Exchange-Integration unterliegt **Change-Governance** (Review, Tests, dokumentierte Freigabe).

### 2. Kapital- und Risikolimits

Vor Start sind **numerische** Obergrenzen definiert und technisch/operativ durchsetzbar (kein „ungefähr“):

| Limit | Bedeutung |
|-------|-----------|
| Max. Notional **pro Order** | Hard-Cap in Basiswährung/Quote gemäß Freigabe |
| Max. **Tagesverlust** | Erreichen = sofortiger Stopp (siehe Abbruchkriterien) |
| Max. **offene Position** (Notional / Exposure) | Keine Überschreitung |
| Max. **gleichzeitige** Orders | z. B. 1 oder ein explizit kleines N |

### 3. Gating / Freigabe

- **Enabled** und **armed:** Live-Trading nur, wenn beides bewusst gesetzt und nachvollziehbar protokolliert.
- **Confirm-Token** (oder gleichwertiges zweites Kontrollsignal): kein „aus Versehen live“.
- **Dry-Run / Shadow / Testnet** (je nach Peak_Trade-Setup): **nachweislich** erfolgreich für **dieselbe** Strategie-Version und **dieselbe** Integrationskette **vor** Canary-Live (Evidenz dokumentiert).

### 4. Daten- und Zeit-Sicherheit

- **Live-Marktdaten** sind **aktuell** (kein veralteter Snapshot als Entscheidungsgrundlage).
- **UTC / Zeitbasis** ist konsistent (Signale, Logs, Exchange-Zeit).
- Bei **stale data**, **Feed-Ausfall** oder erkennbarer **Zeitdrift:** kein neuer Echtgeld-Handel; ggf. Abbruch (siehe unten).

### 5. Reconciliation

- **Positionen, offene Orders und Kontostand** stimmen mit dem **Exchange-Zustand** überein (definiertes Reconcile-Verfahren).
- **Jede Abweichung** → **sofortiger Stopp** (kein „weiter beobachten“ im Canary-Modus).

### 6. Operator- und Observability-Pflicht

- **Alerts** sind aktiv und auf erreichbare Kanäle geroutet.
- **Execution-Telemetrie** ist aktiv (nachvollziehbare Ereignisse).
- **Logging / Audit-Trail** ist aktiv und auswertbar.
- Ein **menschlicher Operator** hat das relevante Runbook gelesen und **überwacht die Session aktiv** (kein unbeaufsichtigtes Canary).

### 7. Abbruchkriterien (sofort)

Canary endet **sofort**, wenn eines zutrifft — danach nur Wiederaufnahme nach **neuer** Freigabe und Ursachenklärung:

- **Unerwarteter Ordertyp** oder Routing außerhalb des Manifests
- **Daten-/Zeitfehler** oder Verdacht auf stale/incorrect feed
- **Reconcile-Mismatch**
- **Verletzung** eines definierten Risk-Limits
- **Kill-Switch / Freeze / Stop** greift — System muss **deterministisch** in einen sicheren Zustand

### 8. Exit-to-Scale-Regel

- **Kein automatisches Hochskalieren** von Notional, Symbolen, Strategien oder Orderarten.
- **Jede Erweiterung** (mehr Kapital, weitere Symbole, andere Strategie, andere Exchange) erfordert eine **neue, explizite Freigabe** und kann als **neues** Canary- oder Pilot-Setup behandelt werden.

---

## Phasen (Überblick)

| Phase | Beschreibung |
|-------|----------------|
| **C** | Echte Marktdaten; **kein** Echtgeld-Routing (Research/Shadow/Paper je nach Produktdefinition). |
| **A** | **Canary:** genau **1 Symbol**, **1 Strategie-Version**, **kleines** Echtgeld-Notional, **Operator anwesend**, alle Gates aus diesem Dokument. |
| **B** | **Später**, nur nach **separater** Freigabe und eigenem Runbook — nicht aus Canary „herauswachsen“. |

---

## Verwandte Dokumentation (Peak_Trade)

Nur interne Referenzen; Pfade relativ zum Repository-Root `docs/`.

| Thema | Dokument |
|-------|----------|
| Safety / Testnet & Live | [SAFETY_POLICY_TESTNET_AND_LIVE.md](../../SAFETY_POLICY_TESTNET_AND_LIVE.md) |
| Governance-Überblick | [GOVERNANCE_AND_SAFETY_OVERVIEW.md](../../GOVERNANCE_AND_SAFETY_OVERVIEW.md) |
| Workflow-Navigation | [WORKFLOW_FRONTDOOR.md](../../WORKFLOW_FRONTDOOR.md) |
| Kill-Switch | [KILL_SWITCH_RUNBOOK.md](../KILL_SWITCH_RUNBOOK.md) |
| Execution-Telemetrie (Vorfall) | [EXECUTION_TELEMETRY_INCIDENT_RUNBOOK.md](../EXECUTION_TELEMETRY_INCIDENT_RUNBOOK.md) |
| Telemetry & Alerting | [TELEMETRY_ALERTING_RUNBOOK.md](../TELEMETRY_ALERTING_RUNBOOK.md) |
| Live-Modus-Übergang | [LIVE_MODE_TRANSITION_RUNBOOK.md](../../runbooks/LIVE_MODE_TRANSITION_RUNBOOK.md) |
| Stop / Freeze / Rollback | [incident_stop_freeze_rollback.md](./incident_stop_freeze_rollback.md) |
| Risk-Limit-Verletzung | [risk_limit_breach.md](./risk_limit_breach.md) |
| Offene Features / Triage | [RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md](./RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md) |

---

**Version:** 1.0 — Canary-Live-Eintrittskriterien (Governance-Dokument, kein Produktions-Deploy-Befehl).
