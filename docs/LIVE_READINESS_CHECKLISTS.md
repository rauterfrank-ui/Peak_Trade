# Peak_Trade – Live-Readiness-Checklisten

> **Status:** Phase 39 – Live-Deployment-Playbook & Ops-Runbooks
> **Version:** v1.1
> **Scope:** Checklisten für Stufen-Übergänge, keine Aktivierung
> **Hinweis:** Checklisten werden mit jeder Phase aktualisiert

**Verwandte Dokumente:**
- `LIVE_DEPLOYMENT_PLAYBOOK.md` – Stufenplan und Deployment-Flow
- `LIVE_OPERATIONAL_RUNBOOKS.md` – Konkrete Ops-Anleitungen
- `RUNBOOKS_AND_INCIDENT_HANDLING.md` – Incident-Prozesse

---

## 1. Übersicht

### Stufenmodell

Peak_Trade folgt einem 5-Stufen-Modell für den Weg von Research zu (hypothetischem) Live-Trading:

| Stufe | Name | Beschreibung | Status |
|-------|------|--------------|--------|
| 0 | Research-Only | Backtests, Sweeps, Regime-Analyse | **Aktiv** |
| 1 | Shadow | Shadow-Execution (Phase 24) | **Aktiv** |
| 2 | Testnet | Echte Testnet-API-Calls | Nicht implementiert |
| 3 | Shadow-Live | Live-Daten, simulierte Orders | Nicht implementiert |
| 4 | Live | Echte Production-Orders | Nicht implementiert |

### Verwendung der Checklisten

1. **Vor jedem Stufen-Übergang**: Relevante Checklist vollständig durcharbeiten
2. **Dokumentation**: Alle Punkte abhaken und Datum/Person notieren
3. **Review**: Zweite Person prüft die ausgefüllte Checklist
4. **Archivierung**: Ausgefüllte Checklist aufbewahren

### Checklist-Format

```
- [ ] Punkt beschrieben
      Status: [ Offen | In Arbeit | Erledigt ]
      Datum: YYYY-MM-DD
      Verantwortlich: [Name]
      Notizen: [Optional]
```

---

## 2. Checklist: Research → Shadow (Stufe 0 → 1)

### Voraussetzungen

Diese Checklist ist für den Übergang von reinem Research-Modus zu Shadow-Execution.

**Version:** v1.0 (Phase 25)

### 2.1 Code-Qualität

- [ ] **Alle Unit-Tests grün**
      Status: _______________
      Datum: _______________
      Befehl: `bash python3 -m pytest tests/ -v`
      Ergebnis: _____ / _____ passed

- [ ] **Keine bekannten kritischen Bugs im Execution-Layer**
      Status: _______________
      Datum: _______________
      Geprüft von: _______________

- [ ] **Shadow-Executor implementiert und getestet**
      Status: _______________
      Datum: _______________
      Tests: `tests/test_shadow_execution.py`

### 2.2 Strategien

- [ ] **Mindestens eine Strategie mit ausreichender Backtest-Historie**
      Status: _______________
      Strategie(n): _______________
      Backtest-Zeitraum: _______________
      Ergebnis (Sharpe/Return): _______________

- [ ] **Strategie-Parameter dokumentiert**
      Status: _______________
      Dokumentation in: `docs/` oder `config/config.toml`

### 2.3 Konfiguration

- [ ] **`[shadow]`-Sektion in `config/config.toml` konfiguriert**
      Status: _______________
      ```toml
      [shadow]
      enabled = true
      fee_rate = 0.0005
      slippage_bps = 0.0
      ```

- [ ] **`[live_risk]`-Limits konfiguriert (auch wenn nicht live genutzt)**
      Status: _______________
      max_daily_loss_abs: _______________
      max_order_notional: _______________

### 2.4 Infrastruktur

- [ ] **Experiments-Registry funktionsfähig**
      Status: _______________
      Test: Shadow-Run durchführen, Run-ID in Registry prüfen

- [ ] **Logging aktiv**
      Status: _______________
      Log-Level konfiguriert: _______________

### 2.5 Dokumentation

- [ ] **Shadow-Execution-Doku gelesen**
      Status: _______________
      Dokument: `docs/PHASE_24_SHADOW_EXECUTION.md`

- [ ] **Runbook für Shadow-Run bekannt**
      Status: _______________
      Dokument: `docs/RUNBOOKS_AND_INCIDENT_HANDLING.md`

### 2.6 Freigabe

- [ ] **Checklist vollständig ausgefüllt**
      Datum: _______________
      Ausgefüllt von: _______________

- [ ] **Review durch zweite Person**
      Datum: _______________
      Reviewer: _______________

- [ ] **Owner-Freigabe**
      Datum: _______________
      Freigegeben von: _______________

---

## 3. Checklist: Shadow → Testnet (Stufe 1 → 2)

### Voraussetzungen

Diese Checklist ist für den (zukünftigen) Übergang zu echten Testnet-API-Calls.

**Version:** v1.0 (Phase 25)
**Status:** Vorbereitend, Testnet nicht implementiert

### 3.1 Shadow-Erfahrung

- [ ] **Shadow-Runs über N Wochen ohne kritische Incidents**
      Status: _______________
      Zeitraum: _______________ bis _______________
      Anzahl Runs: _______________
      Kritische Incidents: _______________

- [ ] **Konsistente Performance über verschiedene Zeiträume**
      Status: _______________
      Sharpe Range: _______________ bis _______________
      MaxDD Range: _______________ bis _______________

### 3.2 Risk-Management

- [ ] **Risk-Limits dokumentiert und reviewed**
      Status: _______________
      Reviewer: _______________
      Datum: _______________

- [ ] **Risk-Limits für Testnet explizit definiert**
      Status: _______________
      Testnet-spezifische Limits: _______________

### 3.3 Monitoring & Alerting

- [ ] **Monitoring-System eingerichtet**
      Status: _______________
      Art: [ Logs | Dashboard | Alerting | ... ]

- [ ] **Alert-Kanäle definiert**
      Status: _______________
      Kanäle: [ Email | Slack | SMS | ... ]

- [ ] **Test-Alert erfolgreich gesendet**
      Status: _______________
      Datum: _______________

### 3.4 Infrastruktur

- [ ] **Testnet-API-Zugang konfiguriert**
      Status: _______________
      Exchange: _______________
      Credentials: [ Sicher gespeichert | ENV-Variable | Secret-Manager ]

- [ ] **Testnet-Adapter implementiert und getestet**
      Status: _______________
      Tests: _______________

### 3.5 Runbooks

- [ ] **Testnet-Start-Runbook vorhanden**
      Status: _______________
      Dokument: _______________

- [ ] **Testnet-Stop-Runbook vorhanden**
      Status: _______________
      Dokument: _______________

- [ ] **Incident-Handling-Prozess bekannt**
      Status: _______________

### 3.6 Freigabe

- [ ] **Checklist vollständig ausgefüllt**
- [ ] **Review durch Risk Officer**
- [ ] **Owner-Freigabe**

---

## 4. Checklist: Testnet → Live (Stufe 2/3 → 4)

### Voraussetzungen

Diese Checklist ist für den (hypothetischen) Übergang zu echtem Live-Trading.

**Version:** v1.0 (Phase 25)
**Status:** Rein theoretisch, Peak_Trade ist NICHT in dieser Phase

### WARNUNG

```
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   WARNUNG: Peak_Trade befindet sich NICHT in dieser Phase!           ║
║                                                                      ║
║   Diese Checklist ist rein vorbereitend und beschreibt               ║
║   hypothetische Anforderungen für einen zukünftigen                  ║
║   Live-Modus, der aktuell nicht implementiert ist.                   ║
║                                                                      ║
║   Live-Trading birgt erhebliche finanzielle Risiken!                 ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
```

### 4.1 Testnet-Erfahrung

- [ ] **Testnet-Betrieb über N Wochen stabil**
      Status: _______________
      Zeitraum: _______________
      Incidents: _______________

- [ ] **Alle Testnet-Orders korrekt ausgeführt**
      Status: _______________
      Erfolgsquote: _______________

- [ ] **Risk-Limits wurden nie kritisch verletzt**
      Status: _______________

### 4.2 Governance

- [ ] **Vollständige Governance-Dokumentation vorhanden**
      Status: _______________
      - [ ] GOVERNANCE_AND_SAFETY_OVERVIEW.md
      - [ ] SAFETY_POLICY_TESTNET_AND_LIVE.md
      - [ ] RUNBOOKS_AND_INCIDENT_HANDLING.md
      - [ ] LIVE_READINESS_CHECKLISTS.md

- [ ] **Rollen & Verantwortlichkeiten definiert**
      Status: _______________
      Owner: _______________
      Risk Officer: _______________
      Operator: _______________

- [ ] **Zwei-Personen-Freigabe eingerichtet**
      Status: _______________

### 4.3 Risk & Compliance

- [ ] **Finanzielle Impact-Analyse durchgeführt**
      Status: _______________
      Maximales Kapital at Risk: _______________
      Worst-Case-Szenario dokumentiert: _______________

- [ ] **Symbol-Whitelist definiert**
      Status: _______________
      Erlaubte Symbole: _______________

- [ ] **Leverage-Limits definiert (falls relevant)**
      Status: _______________
      Max. Leverage: _______________

### 4.4 Runbooks & Incident

- [ ] **Live-Start-Runbook vorhanden und getestet**
      Status: _______________

- [ ] **Live-Stop-Runbook vorhanden und getestet**
      Status: _______________

- [ ] **Kill-Switch implementiert und getestet**
      Status: _______________
      Test-Datum: _______________

- [ ] **Incident-Response-Plan vollständig**
      Status: _______________

### 4.5 Technische Readiness

- [ ] **Live-Adapter implementiert**
      Status: _______________

- [ ] **Alle Unit-/Integration-Tests grün**
      Status: _______________

- [ ] **Security-Review durchgeführt**
      Status: _______________
      Reviewer: _______________

- [ ] **API-Credentials sicher gespeichert**
      Status: _______________
      Methode: [ ENV | Secret-Manager | Hardware-Token ]

### 4.6 Monitoring & Operations

- [ ] **24/7-Monitoring eingerichtet** (falls erforderlich)
      Status: _______________

- [ ] **Alerting für kritische Events aktiv**
      Status: _______________

- [ ] **Backup-Strategie definiert**
      Status: _______________

### 4.7 Freigabe

- [ ] **Checklist vollständig ausgefüllt**
      Datum: _______________

- [ ] **Risk-Officer-Freigabe**
      Datum: _______________
      Unterschrift: _______________

- [ ] **Owner-Freigabe**
      Datum: _______________
      Unterschrift: _______________

- [ ] **Zweite Person Freigabe (Two-Man-Rule)**
      Datum: _______________
      Unterschrift: _______________

---

## 5. Anwendung & Pflege

### 5.1 Verwendung der Checklists

1. **Kopieren**: Bei jedem Stufen-Übergang eine Kopie der Checklist erstellen
2. **Ausfüllen**: Jeden Punkt einzeln durchgehen und dokumentieren
3. **Review**: Ausgefüllte Checklist von zweiter Person prüfen lassen
4. **Archivieren**: Ausgefüllte Checklist mit Datum speichern

### 5.2 Aktualisierung der Checklists

Checklists sollten aktualisiert werden, wenn:

- Neue Anforderungen identifiziert werden
- Architektur-Änderungen erfolgen
- Nach Incidents neue Prüfpunkte erforderlich sind
- Neue Phasen implementiert werden

### 5.3 Versionierung

```
Format: vX.Y

X = Major-Version (bei strukturellen Änderungen)
Y = Minor-Version (bei Ergänzungen/Korrekturen)

Beispiel:
- v1.0: Initiale Version (Phase 25)
- v1.1: Neue Prüfpunkte nach Incident #123
- v2.0: Neue Stufe hinzugefügt
```

### 5.4 Checklist-Archiv

Empfohlene Struktur:

```
reports/
└── checklists/
    ├── 2025-12-04_research_to_shadow_v1.0.md
    ├── 2026-01-15_shadow_to_testnet_v1.1.md
    └── ...
```

---

## 6. Referenzen

| Dokument | Beschreibung |
|----------|--------------|
| `LIVE_DEPLOYMENT_PLAYBOOK.md` | Stufenplan, Gatekeeper, Deployment-Flow |
| `LIVE_OPERATIONAL_RUNBOOKS.md` | Konkrete Ops-Anleitungen |
| `GOVERNANCE_AND_SAFETY_OVERVIEW.md` | Governance-Übersicht, Rollen |
| `SAFETY_POLICY_TESTNET_AND_LIVE.md` | Safety-Policies |
| `RUNBOOKS_AND_INCIDENT_HANDLING.md` | Runbooks und Incident-Prozesse |
| `PHASE_23_LIVE_TESTNET_BLUEPRINT.md` | Technischer Blueprint |
| `PHASE_37_TESTNET_ORCHESTRATION_AND_LIMITS.md` | Testnet-Orchestrierung |
| `PHASE_38_EXCHANGE_V0_TESTNET.md` | Exchange-Anbindung v0 |

---

## 7. Changelog

- **v1.1** (Phase 39, 2025-12): Aktualisiert
  - Verweise auf neue Dokumente hinzugefügt (LIVE_DEPLOYMENT_PLAYBOOK.md, LIVE_OPERATIONAL_RUNBOOKS.md)
  - Referenztabelle erweitert
  - Version auf v1.1 aktualisiert

- **v1.0** (Phase 25, 2025-12): Initial erstellt
  - Research → Shadow Checklist
  - Shadow → Testnet Checklist (vorbereitend)
  - Testnet → Live Checklist (hypothetisch)
  - Anwendungs- & Pflege-Hinweise
  - Keine Code-Änderungen
