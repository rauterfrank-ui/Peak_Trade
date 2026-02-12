# Incident Drill Log

Dieses Dokument protokolliert durchgeführte Incident-Drills (Phase 56 ff.).

**Zweck:**
- Dokumentation aller durchgeführten Drills
- Nachvollziehbarkeit von Erkenntnissen & Follow-Ups
- Basis für kontinuierliche Verbesserung der Incident-Handling-Prozesse

**Verwandte Dokumente:**
- [`INCIDENT_SIMULATION_AND_DRILLS.md`](INCIDENT_SIMULATION_AND_DRILLS.md) – Drill-Playbook mit Szenarien
- [`RUNBOOKS_AND_INCIDENT_HANDLING.md`](RUNBOOKS_AND_INCIDENT_HANDLING.md) – Incident-Runbooks

---

## Drill #001 – 2026-01-27 (UTC) – Szenario 3 (Risk-Limit-Verletzung / Order-Level)

- **Date (UTC)**: 2026-01-27T00:00:00Z (Dokumentationszeitpunkt; Evidence-Run siehe unten)
- **Operator**: frnkhrz
- **Environment / Track**: paper (Unit-/Integration-Test Harness; **keine Live-Orders**, keine Exchange-Order-APIs)
- **Scenario-ID**: `INCIDENT_SIMULATION_AND_DRILLS.md` → **Szenario 3 – Risk-Limit-Verletzung (Order-/Portfolio-Level)** (Order-Level)

### Preconditions / Backups

- **Config**: keine Änderungen (kein `config/config.toml`-Edit nötig)
- **Data**: keine Änderungen (keine Datasets manipuliert)
- **Safety**: Test erzeugt ausschließlich in-memory Orders/Portfolio-Snapshots; keine Secrets, keine Tokens

### Steps executed (reproduzierbar)

1. Risk-Alert-Integrationstest ausführen (simuliert Order-Batch mit Limit-Verletzung → Alert muss feuern).

```bash
python3 -m pytest -q tests&#47;test_live_risk_alert_integration.py::test_order_violation_emits_alert
```

### Observations

- **Risk-Limit-Verletzung wurde erkannt** (`allowed=False` im Risk-Result im Test-Setup).
- **Alert wurde emittiert**: `source=live_risk.orders`, `code=RISK_LIMIT_VIOLATION_ORDERS`, Level = `CRITICAL` (weil `block_on_violation=True`).
- **Kein Crash / best-effort**: Testlauf stabil, keine externen Side-Effects.

### Success criteria

- **PASS** – Begründung: Szenario-Intent “Risk-Limit-Verletzung triggert Alert” ist reproduzierbar erfüllt, ohne Live-Orders/Netzwerk/Secrets.

### Evidence pointers (token-policy safe)

- **Testcase**: `tests&#47;test_live_risk_alert_integration.py::test_order_violation_emits_alert`
- **Implementierung**: `src&#47;live&#47;risk_limits.py` (Alert-Emission bei BREACH/WARNING), `src&#47;live&#47;alerts.py` (Sinks inkl. Webhook/Slack)
- **Command + Output**:

```text
============================== 1 passed in 1.07s ===============================
```

### Follow-ups

- [ ] **P1 (Owner: Operator/frnkhrz)**: Drill #002 als **manueller Operator-Run** gemäß Playbook durchführen (z.B. `live_ops` + temporäre Config-Limits), inkl. Copy/Paste der relevanten Konsolen-Outputs in den Evidence-Abschnitt.
- [ ] **P2 (Owner: Risk/Governance)**: Erfolgskriterien für Szenario 3 präzisieren (z.B. “WARNING vs BREACH” Schwellen) und in Runbook-Checkliste spiegeln.
- [ ] **P3 (Owner: Docs)**: `INCIDENT_DRILL_LOG.md` Zusammenfassung (Zähler) aktualisieren, sobald ≥2 Drills dokumentiert sind.

---

## Drill-Protokoll

| Datum       | Szenario                            | Track (Shadow/Testnet/Live) | Ergebnis (OK/Issues) | Erkenntnisse / Follow-Ups                                     |
|------------|--------------------------------------|-----------------------------|----------------------|----------------------------------------------------------------|
| 2026-01-27 | Risk-Limit-Verletzung (Order-Level)  | Paper (test harness)        | OK                   | Evidence via `tests&#47;test_live_risk_alert_integration.py`; Follow-ups für manuellen Run |
| YYYY-MM-DD | Risk-Limit-Verletzung (Order-Level)  | Testnet                     | OK                   | z.B. Alerts kamen in Slack/Log an, Runbook Schritt 3 angepasst |
| YYYY-MM-DD | Data-Gap / korrupte Candle          | Shadow                      | Issues               | z.B. fehlende Warnung im Data-Layer, TODO für Phase XX         |

---

## Detaillierte Drill-Berichte

### Drill 1: [Datum] – [Szenario]

**Szenario:** [z.B. Risk-Limit-Verletzung Order-Level]

**Track:** [Shadow/Testnet/Live]

**Durchführung:**
- [Schritt-für-Schritt-Beschreibung]

**Ergebnis:**
- ✅ **OK**: [Was hat funktioniert?]
- ⚠️ **Issues**: [Was hat nicht funktioniert?]

**Erkenntnisse:**
- [Was hast du gelernt?]

**Follow-Ups:**
- [ ] [TODO 1]
- [ ] [TODO 2]

**Referenzen:**
- Runbook: [`RUNBOOKS_AND_INCIDENT_HANDLING.md`](RUNBOOKS_AND_INCIDENT_HANDLING.md) – [Abschnitt]
- Drill-Playbook: [`INCIDENT_SIMULATION_AND_DRILLS.md`](INCIDENT_SIMULATION_AND_DRILLS.md) – [Szenario]

---

## Zusammenfassung

**Gesamt-Statistik:**
- Anzahl durchgeführter Drills: [X]
- Erfolgreiche Drills: [Y]
- Drills mit Issues: [Z]

**Wichtigste Erkenntnisse:**
- [Erkenntnis 1]
- [Erkenntnis 2]

**Offene Follow-Ups:**
- [ ] [Follow-Up 1]
- [ ] [Follow-Up 2]

---

**Built with ❤️ and continuous improvement**
