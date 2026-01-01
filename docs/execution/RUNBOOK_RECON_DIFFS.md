# Runbook: Reconciliation Diffs interpretieren

**Version:** 1.0 (WP0D Phase 0 - SIM/PAPER only)  
**Owner:** Execution Team  
**Last Updated:** 2026-01-01

---

## Überblick

Reconciliation Diffs (`ReconDiff`) zeigen Abweichungen zwischen internem Ledger-State und externem Exchange-State. In Phase 0 (SIM/PAPER) ist der externe State gemockt – echte Exchange-Daten kommen in Phase 1+.

**Zweck dieses Runbooks:**
- Recon Diffs interpretieren (Severity, Type, Resolution)
- Typische Ursachen identifizieren
- Entscheidungshilfe: Wann eskalieren, wann ignorieren

---

## Quickstart (CLI)

Schneller Einstieg mit dem CLI-Tool `show_recon_audit.py`:

### 1. Help anzeigen

```bash
python scripts/execution/show_recon_audit.py
```

Zeigt Usage, verfügbare Modi und Optionen.

### 2. Empty State prüfen

```bash
python scripts/execution/show_recon_audit.py summary
```

**Output (text):** `"No RECON_SUMMARY events found."`

**Use Case:** Baseline-Check, ob Audit-Log leer ist.

### 3. JSON Output (maschinenlesbar)

```bash
python scripts/execution/show_recon_audit.py summary --format json
```

**Output:**
```json
{
  "count": 0,
  "event_type": "RECON_SUMMARY",
  "items": [],
  "notes": "No RECON_SUMMARY events found"
}
```

**Use Case:** Integration mit Monitoring-Tools, Alerting-Pipelines.

### 4. Gate-Mode (Exit-Code basiert)

```bash
python scripts/execution/show_recon_audit.py summary --format json --exit-on-findings
echo "Exit code: $?"
```

**Exit-Codes:**
- `0`: Keine Findings (OK)
- `2`: Findings vorhanden (Action required)

**Use Case:** CI/CD Gates, Automated Checks, Pre-Deployment Validation.

**Beispiel CI-Gate:**
```bash
# Fail pipeline if recon findings present
if ! python scripts/execution/show_recon_audit.py summary --exit-on-findings; then
  echo "❌ Recon findings detected, blocking deployment"
  exit 1
fi
```

### 5. Von JSON-Export laden

```bash
# Export audit log to JSON first
python -c "from src.execution.audit_log import AuditLog; \
  log = AuditLog(); \
  log.export_to_file('audit_export.json')"

# Query from file
python scripts/execution/show_recon_audit.py summary --json audit_export.json
```

**Use Case:** Offline-Analysen, Archiv-Queries, Debugging vergangener Runs.

---

## Diff-Taxonomie

### 1. Severity Levels

| Severity   | Bedeutung                           | Schwellenwert                  | Aktion                                      |
|------------|-------------------------------------|--------------------------------|---------------------------------------------|
| **INFO**   | Geringe Abweichung, tolerierbar     | < 0.1% Drift                   | Monitoring, keine Aktion nötig              |
| **WARN**   | Moderate Abweichung, beobachten     | 0.1% - 1% Drift                | Log-Review, bei Häufung eskalieren          |
| **FAIL**   | Signifikante Abweichung, kritisch   | > 1% Drift oder Cash-Mismatch  | Sofortiger Alert, Trading pausieren         |
| **CRITICAL** | Systemfehler, Datenverlust          | (future Phase 1+)              | Incident Response, Kill Switch              |

**Phase 0 Hinweis:** CRITICAL wird in Phase 0 nicht verwendet (kein echtes Exchange API). FAIL ist der höchste Level.

---

### 2. Diff Types

| Type       | Beschreibung                                | Typische Ursache (Phase 0/SIM)                     |
|------------|---------------------------------------------|----------------------------------------------------|
| **POSITION** | Position quantity mismatch                  | Fill-Timing, Simulation-Artefakte                  |
| **CASH**   | Cash balance mismatch                       | Fee-Berechnung, Float-Rundung                      |
| **ORDER**  | Order state divergence (future Phase 1+)    | Exchange ACK delay, Cancel race condition          |
| **FILL**   | Fill missing/orphaned (future Phase 1+)     | Websocket drop, Partial fill nicht verarbeitet     |

**Phase 0:** Nur POSITION und CASH sind aktiv implementiert. ORDER/FILL kommen in Phase 1+.

---

## Interpretation Guide

### Scenario 1: POSITION Mismatch (WARN)

**Beispiel:**
```
Severity: WARN
Type: POSITION
Symbol: BTC/EUR
Internal: 0.1 BTC
External: 0.0995 BTC
Delta: 0.0005 (0.5%)
```

**Interpretation:**
- 0.5% Abweichung → WARN-Level (0.1% - 1%)
- Mögliche Ursachen: Timing (Fill noch nicht propagiert), Rundung
- **Aktion:** Log-Review. Bei wiederholtem Auftreten → Eskalation

---

### Scenario 2: POSITION Mismatch (FAIL)

**Beispiel:**
```
Severity: FAIL
Type: POSITION
Symbol: ETH/EUR
Internal: 1.0 ETH
External: 0.95 ETH
Delta: 0.05 (5%)
```

**Interpretation:**
- 5% Abweichung → FAIL-Level (> 1%)
- **Kritisch:** Potential für signifikante PnL-Fehler
- **Aktion:**
  1. Trading pausieren (Risk Kill Switch)
  2. Snapshot prüfen: `recon_engine.export_reconciliation_report()`
  3. Ledger-History inspizieren: Fehlende Fills?
  4. Incident Report erstellen

---

### Scenario 3: CASH Mismatch (FAIL)

**Beispiel:**
```
Severity: FAIL
Type: CASH
Internal: 5000.00 EUR
External: 4995.00 EUR
Delta: 5.00 EUR
```

**Interpretation:**
- Jede Cash-Abweichung > Tolerance (0.5% oder 1 EUR) → FAIL
- Mögliche Ursachen: Fehlende Fee-Buchung, Double-Processing, Simulation-Bug
- **Aktion:**
  1. Trading stoppen (sofort)
  2. Ledger-Replay: Alle Fills + Fees nachvollziehen
  3. Bei Inkonsistenz → Ledger-Repair (Phase 1+)

---

### Scenario 4: Viele INFO-Diffs

**Beispiel:**
```
ReconSummary:
  Total Diffs: 15
  INFO: 15
  WARN: 0
  FAIL: 0
```

**Interpretation:**
- Viele kleine Abweichungen (< 0.1%) können auf systemische Rundungsfehler hinweisen
- **Aktion:**
  - Trend-Analyse: Steigt Anzahl über Zeit?
  - Bei konstant hoher Rate (> 50 INFO/Run) → Tolerance-Adjustment prüfen
  - Kein sofortiger Stop nötig (INFO ist tolerierbar)

---

## ReconSummary Struktur

Jeder Recon-Run erzeugt eine **ReconSummary** mit:

```python
ReconSummary(
    run_id="uuid",
    timestamp="2026-01-01T12:00:00Z",
    session_id="session_123",
    strategy_id="ma_crossover",
    total_diffs=3,
    counts_by_severity={"WARN": 2, "FAIL": 1},
    counts_by_type={"POSITION": 3},
    top_diffs=[...],  # Top-N nach Severity sortiert
    has_critical=False,
    has_fail=True,
    max_severity="FAIL",
)
```

**Audit Trail:**
- 1x `RECON_SUMMARY` Event (aggregate stats)
- Nx `RECON_DIFF` Events (top-N Diffs, default N=10)

**Query:**
```python
# Get all recon summaries
summaries = audit_log.get_entries_by_event_type("RECON_SUMMARY")

# Get specific run's diffs
run_diffs = [
    e for e in audit_log.get_all_entries()
    if e.event_type == "RECON_DIFF" and e.details["run_id"] == "target_run_id"
]
```

---

## Eskalations-Matrix

| Max Severity | Anzahl Diffs | Sofort-Aktion                     | Follow-Up                        |
|--------------|--------------|-----------------------------------|----------------------------------|
| INFO         | < 10         | Keine                             | Monitoring                       |
| INFO         | > 50         | Trend-Analyse                     | Tolerance Review                 |
| WARN         | 1-3          | Log-Review                        | Bei Häufung → Incident           |
| WARN         | > 5          | Trading pausieren (optional)      | Incident Report                  |
| FAIL         | >= 1         | **Trading stoppen**               | **Immediate Incident Response**  |

---

## Tooling & Commands

### 1. Recon-Run manuell triggern

```python
from src.execution.reconciliation import ReconciliationEngine
from src.execution.audit_log import AuditLog

# Init
recon_engine = ReconciliationEngine(position_ledger, order_ledger)
audit_log = AuditLog()

# Run reconciliation
diffs = recon_engine.reconcile()

# Create summary
summary = recon_engine.create_summary(
    diffs=diffs,
    session_id="manual_check_01",
    strategy_id="debug",
    top_n=10,
)

# Emit to audit log
audit_log.append_recon_summary(summary)

# Export summary
print(summary.to_json())
```

---

### 2. Recon-History abfragen

```python
# Get all recon summaries from audit log
summaries = audit_log.get_entries_by_event_type("RECON_SUMMARY")

for entry in summaries:
    print(f"Run: {entry.details['run_id']}, "
          f"Max Severity: {entry.details['max_severity']}, "
          f"Total Diffs: {entry.details['total_diffs']}")
```

---

### 3. Diff-Details inspizieren

```python
# Get specific run's diffs
run_id = "target_run_id"
run_diffs = [
    e for e in audit_log.get_all_entries()
    if e.event_type == "RECON_DIFF" and e.details.get("run_id") == run_id
]

for diff in run_diffs:
    print(f"Type: {diff.details['diff_type']}, "
          f"Severity: {diff.details['severity']}, "
          f"Description: {diff.details['description']}")
```

---

### 4. CLI Tool (Quick Commands)

**Tool:** `scripts/execution/show_recon_audit.py`

Schneller Zugriff auf Recon-Events aus dem AuditLog ohne Python-Code zu schreiben.

#### Beispiel 1: Alle Recon-Summaries anzeigen

```bash
python scripts/execution/show_recon_audit.py summary
```

**Output:**
- Run ID, Timestamp, Session/Strategy
- Total Diffs, Severity Counts, Diff Types
- Critical/Fail Flags, Max Severity

**Use Case:** Schneller Überblick über alle Recon-Runs (z.B. nach Live-Session)

---

#### Beispiel 2: Diffs mit Severity-Filter

```bash
python scripts/execution/show_recon_audit.py diffs --severity FAIL --limit 20
```

**Output:**
- Nur Diffs mit Severity=FAIL
- Diff ID, Timestamp, Type, Description
- Order ID, Resolution Status

**Use Case:** Kritische Diffs identifizieren für Incident-Investigation

---

#### Beispiel 3: Detaillierter Drill-Down für spezifischen Run

```bash
python scripts/execution/show_recon_audit.py detailed --run-id <run_id>
```

**Output:**
- Summary-Übersicht für diesen Run
- Alle Diffs für diesen Run (nicht nur Top-N)
- Vollständiger Context für Debugging

**Use Case:** Deep-Dive nach Alert (z.B. "Run XYZ hat 15 FAIL diffs")

---

#### Weitere Optionen

```bash
# Nach Session filtern
python scripts/execution/show_recon_audit.py summary --session-id session_123

# Nach Run filtern
python scripts/execution/show_recon_audit.py diffs --run-id run_456

# Output limitieren
python scripts/execution/show_recon_audit.py diffs --limit 10

# Von JSON-Export laden (für Archiv-Analysen)
python scripts/execution/show_recon_audit.py summary --json path/to/audit_export.json
```

**Phase 0 Hinweis:** In Phase 0 arbeitet das Tool mit in-memory AuditLog oder JSON-Exporten. Keine Datenbank-Integration (kommt in Phase 1+).

---

## Phase 1+ Roadmap

**Was ändert sich bei echtem Exchange-API:**
1. **External Snapshot:** Echte Daten von Exchange (nicht mehr gemockt)
2. **Neue Diff Types:** ORDER, FILL (aktuell nicht implementiert)
3. **CRITICAL Severity:** Systemfehler (z.B. WebSocket-Ausfall, API-Timeout)
4. **Auto-Repair:** Ledger-Korrektur bei eindeutigen Divergenzen
5. **Alerting:** Slack/PagerDuty-Integration bei FAIL/CRITICAL

**Phase 0 Scope:**
- Nur POSITION + CASH
- Nur INFO/WARN/FAIL
- Kein Auto-Repair (manual inspection only)

---

## Support

**Bei Fragen/Issues:**
- Slack: `#execution-alerts`
- Incident Runbooks: Siehe `docs/runbooks/` oder `docs/LIVE_OPERATIONAL_RUNBOOKS.md`
- Escalation: Execution Team Lead
