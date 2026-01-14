# ExecutionPipeline – Governance & Risk Runbook (Phase 16A V2)

**Version:** v1.1 (Dezember 2025, 2026-ready)
**Gültig für:** `ExecutionPipeline` mit Governance-/Risk-Integration (Phase 16A V2)
**Scope:** Paper, Shadow, Testnet – *kein* Live-Order-Routing
**Zielgruppe:** Operatoren, Entwickler, On-Call-Engineers

---

## 1. Zweck & Kontext

Dieses Runbook beschreibt, wie Operatoren und Entwickler:

1. Die **ExecutionPipeline** mit Governance-/Risk-Checks prüfen.
2. Typische **Blockadegründe** (Governance, Risk, Safety, Invalid) erkennen und korrekt einordnen.
3. Sicherstellen, dass **keine Live-Orders** gesendet werden, solange `live_order_execution` gesperrt ist.
4. Im Incident-Fall strukturiert vorgehen und die richtigen Artefakte sammeln.

**Kernkomponenten der Pipeline:**

| Komponente | Beschreibung |
|------------|--------------|
| `OrderIntent` | Dataclass für Order-Absicht (Symbol, Side, Quantity, Type, Strategy) |
| `ExecutionPipeline.submit_order()` | Governance-/Risk-aware Order-Submission |
| `ExecutionStatus` | Standardisierte Status-Codes für Ergebnis-Klassifikation |
| `ExecutionResult` | Rückgabe-Objekt mit Status, Flags und Metadaten |

**Relevante Exceptions:**

* `ExecutionPipelineError` – Allgemeiner Pipeline-Fehler
* `GovernanceViolationError` – Governance-Regel verletzt
* `LiveExecutionLockedError` – Live-Execution ist gesperrt

---

## 2. Safety-Prinzipien

### 2.1 Governance-Lock für Live-Execution

Live-Execution ist **permanent governance-seitig gesperrt**, bis explizit freigegeben:

```python
# src/governance/go_no_go.py
_FEATURE_STATUS_MAP = {
    "live_order_execution": "locked",  # ← GESPERRT – NICHT ÄNDERN ohne Sign-Off
    # ...
}
```

### 2.2 Verhalten bei `env="live"`

| Konfiguration | Verhalten |
|---------------|-----------|
| `raise_on_governance_violation=True` (Default) | Wirft `LiveExecutionLockedError` |
| `raise_on_governance_violation=False` | Gibt `ExecutionResult` mit `status=BLOCKED_BY_GOVERNANCE` zurück |

### 2.3 Executor-Isolation

**Kein Executor** wird jemals für `env="live"` aufgerufen, solange der Governance-Lock aktiv ist. Die Prüfung erfolgt **vor** dem Executor-Dispatch.

---

## 3. Architektur-Überblick

```text
Strategy → OrderIntent → ExecutionPipeline.submit_order()
                               ↓
                    1. Input Validation (quantity > 0?)
                               ↓
                    2. Governance-Check (live_order_execution?)
                               ↓
                    3. SafetyGuard-Check
                               ↓
                    4. Risk-Check (LiveRiskLimits)
                               ↓
                    5. Executor-Dispatch
                         paper  → PaperOrderExecutor
                         shadow → ShadowOrderExecutor
                         testnet→ TestnetExchangeOrderExecutor
                         live   → 🚫 GESPERRT (Governance-Lock)
                               ↓
                    ExecutionResult (Status + Flags)
```

---

## 4. ExecutionStatus → Operator-Aktion Mapping

Diese Tabelle dient als **Single Source of Truth** für die Operator-Reaktion auf jeden möglichen ExecutionStatus. Ein Operator kann **ohne Code-Blick** sofort erkennen, was bei welchem Status zu tun ist.

### 4.1 Vollständiges Status-Mapping

| ExecutionStatus | Bedeutung / Kontext | Operator-Aktion | SLA / Zeitfenster |
|-----------------|---------------------|-----------------|-------------------|
| `PENDING` | Order wurde erstellt, wartet auf Submission | ✅ Keine Aktion – normaler Zwischenzustand | – |
| `SUBMITTED` | Order wurde an den Executor/Exchange übergeben | ✅ Keine Aktion – Warten auf Fill-Bestätigung | Innerhalb von 30s auf Update prüfen |
| `FILLED` | Order vollständig ausgeführt | ✅ Keine Aktion – Erfolgsfall | – |
| `PARTIALLY_FILLED` | Order teilweise ausgeführt | ⚠️ Log prüfen – Rest-Quantity überwachen | Innerhalb von 5 Min. prüfen |
| `CANCELLED` | Order wurde storniert (durch System oder manuell) | 📝 Log prüfen – Grund dokumentieren | – |
| `REJECTED` | Order wurde von Exchange/Executor abgelehnt | ⚠️ Rejection-Reason prüfen, ggf. Re-Scheduling | Innerhalb von 5 Min. analysieren |
| `SUCCESS` | Order erfolgreich an Executor übergeben | ✅ Keine Aktion nötig | – |
| `BLOCKED_BY_GOVERNANCE` | Governance-Lock greift (z.B. Live gesperrt) | ✅ Erwartetes Verhalten bei `env=live` – keine Aktion. Bei anderen Envs: Config prüfen | – |
| `BLOCKED_BY_RISK` | Risk-Limit verletzt (Drawdown, Position-Size, etc.) | ⚠️ Risk-Config prüfen, Limit-Werte und aktuelle Exposure analysieren | Innerhalb von 5 Min. analysieren |
| `BLOCKED_BY_SAFETY` | SafetyGuard hat geblockt | ⚠️ SafetyGuard-Logs prüfen, Ursache analysieren | Innerhalb von 5 Min. analysieren |
| `BLOCKED_BY_ENVIRONMENT` | Environment-Check fehlgeschlagen (z.B. falsches Env für Operation) | ⚠️ Environment-Config prüfen, ggf. korrektes Env wählen | Innerhalb von 5 Min. analysieren |
| `INVALID` | Ungültige Eingabe (quantity ≤ 0, unbekanntes Symbol) | 🔧 Strategy-/Sizing-Logik debuggen | Innerhalb von 15 Min. fixen |
| `ERROR` | Unerwarteter Fehler in Pipeline oder Executor | 🚨 Logs sammeln, Stacktrace analysieren, Incident eröffnen | Sofort (< 5 Min.) |
| `EXPIRED` | Order ist abgelaufen (z.B. TimeInForce überschritten) | 📝 Order-Parameter prüfen, ggf. Re-Scheduling | – |

### 4.2 Schnell-Referenz (ASCII)

```
PENDING              → ✅ Warten (normaler Zwischenzustand)
SUBMITTED            → ✅ Warten auf Fill (30s Check)
FILLED               → ✅ Erfolg – keine Aktion
PARTIALLY_FILLED     → ⚠️ Rest-Quantity überwachen
CANCELLED            → 📝 Grund dokumentieren
REJECTED             → ⚠️ Rejection-Reason analysieren
SUCCESS              → ✅ Alles OK
BLOCKED_BY_GOVERNANCE→ ✅ Bei env=live erwartet, sonst Config prüfen
BLOCKED_BY_RISK      → ⚠️ Risk-Limits prüfen
BLOCKED_BY_SAFETY    → ⚠️ SafetyGuard-Logs prüfen
BLOCKED_BY_ENVIRONMENT→ ⚠️ Environment-Config prüfen
INVALID              → 🔧 Strategy-Input debuggen
ERROR                → 🚨 Logs sammeln, Incident eröffnen
EXPIRED              → 📝 TimeInForce/Parameter prüfen
```

---

## 5. Unterscheidung: Bug vs. Expected-Block vs. Governance-Schutz

Diese Matrix hilft Operatoren, Blockaden korrekt einzuordnen und die richtige Reaktion zu wählen.

### 5.1 Einordnungs-Matrix

| Kategorie | Definition | Beispiel-Situationen | Erkennung | Operator-Handlung |
|-----------|------------|----------------------|-----------|-------------------|
| **🐛 Bug** | System verhält sich unerwartet, Fehler im Code, Regression | Paper-Order gibt `ERROR` mit Stacktrace; alle Orders plötzlich `INVALID`; unerwartetes Verhalten nach Deployment | Stacktrace in Logs; unerwarteter Status; Verhalten weicht von Dokumentation ab | Incident-Prozess starten, Logs sammeln, KEIN Override, Entwickler einbinden |
| **🔒 Expected Block** | Blockade ist **bewusst** durch System-Rules | Keine Verbindung zum Exchange (Netzwerk-Issue); Market geschlossen (außerhalb Trading-Hours); Symbol nicht handelbar (Maintenance) | Klare Fehlermeldung im Log; Status entspricht Situation; temporärer Zustand | Warten auf Behebung, ggf. Re-Scheduling, KEIN Override |
| **🛡️ Governance-Schutz** | Blockade ist ein **bewusster Risk-/Governance-Mechanismus** | Live-Execution gesperrt (`BLOCKED_BY_GOVERNANCE`); Max-Drawdown überschritten; Circuit-Breaker aktiv; Daily-Loss-Limit erreicht | Governance-/Risk-Status in Result; spezifische Violation-Details; Metrics zeigen Limit-Überschreitung | KEIN Override, Run stoppen, Governance-Entscheidung einholen, Incident dokumentieren |

### 5.2 Detaillierte Szenarien

#### 🐛 Bug-Szenarien

| Szenario | Symptom | Wie erkennbar | Handlung |
|----------|---------|---------------|----------|
| Regression nach Deployment | Orders, die vorher funktionierten, schlagen fehl | Zeitliche Korrelation mit Deployment; Tests grün, aber Prod-Verhalten anders | Rollback prüfen, Incident eröffnen |
| Datenbank-Connection-Issue | Alle Orders `ERROR`, Timeout-Meldungen | Stacktrace zeigt DB-Fehler; Health-Checks rot | Infra-Team einbinden, kein Retry ohne Fix |
| Race-Condition | Sporadische `ERROR`-Status, nicht reproduzierbar | Logs zeigen Timing-Issues; nur unter Last | Debug mit detaillierten Logs, Incident eröffnen |

#### 🔒 Expected-Block-Szenarien

| Szenario | Symptom | Wie erkennbar | Handlung |
|----------|---------|---------------|----------|
| Market geschlossen | Orders `REJECTED` mit Reason | Exchange-Hours prüfen; Rejection-Message | Warten auf Market-Open, Re-Scheduling |
| Exchange Maintenance | Alle Orders `REJECTED` oder `ERROR` | Exchange-Status-Page; Ankündigungs-Mails | Warten auf Maintenance-Ende |
| Symbol delisted | Spezifisches Symbol `INVALID` | Exchange-Announcements; Symbol-Liste | Symbol aus Config entfernen |

#### 🛡️ Governance-Schutz-Szenarien

| Szenario | Symptom | Wie erkennbar | Handlung |
|----------|---------|---------------|----------|
| Live-Execution gesperrt | `BLOCKED_BY_GOVERNANCE` bei `env=live` | Governance-Status in Result | ✅ Erwartetes Verhalten – keine Aktion |
| Max-Drawdown erreicht | `BLOCKED_BY_RISK` mit Drawdown-Violation | Risk-Metrics zeigen Limit-Überschreitung | Session schließen, Incident dokumentieren, KEIN Override |
| Daily-Loss-Limit | `BLOCKED_BY_RISK` | P&L-Tracking zeigt Limit | Trading für heute stoppen, morgen neu bewerten |

### 5.3 Entscheidungsbaum

```
Order wird geblockt
       │
       ├─ Status == ERROR mit Stacktrace?
       │     └─ JA → 🐛 BUG → Incident-Prozess
       │
       ├─ Status == BLOCKED_BY_GOVERNANCE?
       │     └─ JA → 🛡️ GOVERNANCE-SCHUTZ → Erwartetes Verhalten prüfen
       │
       ├─ Status == BLOCKED_BY_RISK?
       │     └─ JA → 🛡️ GOVERNANCE-SCHUTZ → Risk-Limits analysieren
       │
       ├─ Status == BLOCKED_BY_SAFETY?
       │     └─ JA → 🛡️ GOVERNANCE-SCHUTZ → SafetyGuard-Logs prüfen
       │
       ├─ Status == BLOCKED_BY_ENVIRONMENT?
       │     └─ JA → 🔒 EXPECTED-BLOCK → Environment-Config prüfen
       │
       ├─ Status == REJECTED mit klarem Reason?
       │     └─ JA → 🔒 EXPECTED-BLOCK → Reason beheben, Re-Scheduling
       │
       └─ Sonst → Logs analysieren, Kategorie bestimmen
```

---

## 6. Pflicht-Artefakte bei Incidents

### 6.1 Artefakt-Checkliste

**Diese Informationen MÜSSEN bei jedem Execution-/Risk-Incident gesammelt werden:**

| # | Artefakt | Beschreibung | Quelle | Beispiel |
|---|----------|--------------|--------|----------|
| 1 | `run_id` | Eindeutige ID des Pipeline-Runs | `ExecutionResult.run_id`, CLI-Output | `run_20251209_143245_abc123` |
| 2 | `session_id` | Trading-Session-ID | Session-Manager, Config | `session_paper_20251209` |
| 3 | `environment` | Aktives Environment | Config, `ExecutionResult.environment` | `paper`, `shadow`, `testnet`, `live` (gated) |
| 4 | `strategy_key` | Identifikator der aktiven Strategy | `OrderIntent.strategy_key` | `momentum_btc_v2` |
| 5 | `portfolio_preset` | Portfolio-Konfiguration | Config-Datei | `conservative_crypto`, `aggressive_btc` |
| 6 | `config_snapshot` | Aktuelle Config zum Zeitpunkt des Incidents | `config/config.toml`, JSON-Export | Pfad: `snapshots/config_20251209_143245.json` |
| 7 | `execution_log_path` | Pfad zu relevanten Logfiles | Logging-System | `logs/execution_20251209.log` |
| 8 | `alert_ids` | IDs der ausgelösten Alerts | Slack, E-Mail, Dashboard | `alert_20251209_143245_risk_001` |
| 9 | `timestamp_start` | Start-Zeitpunkt des Runs | `ExecutionResult.timestamp` | `2025-12-09T14:32:45Z` |
| 10 | `timestamp_incident` | Zeitpunkt des Incidents | Logs, Alerts | `2025-12-09T14:33:12Z` |
| 11 | `operator` | Wer hat agiert / ist zuständig | On-Call-Rota, Incident-Owner | `@operator-name` |
| 12 | `severity_level` | Severity wie im Risk-/Alert-System definiert | Alert-System, Runbook | `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` |
| 13 | `governance_status` | Status aller relevanten Governance-Keys | `go_no_go.py`, API | `{"live_order_execution": "locked"}` |
| 14 | `risk_check_result` | Ergebnis der Risk-Prüfung | `ExecutionResult.risk_violation_details` | `{"passed": false, "violations": [...]}` |
| 15 | `stacktrace` | Bei `ERROR`-Status | Logs, Exception-Handler | Vollständiger Python-Traceback |
| 16 | `order_intent` | Die ursprüngliche Order-Absicht | `ExecutionResult.order_intent` | Serialisiertes `OrderIntent`-Objekt |

### 6.2 Quellen-Referenz

| Artefakt-Typ | Typische Quellen |
|--------------|------------------|
| IDs (run_id, session_id, alert_ids) | CLI-Output, Dashboard, Logging-System |
| Config-Daten | `config/*.toml`, Environment-Variables |
| Logs | `logs/`-Verzeichnis, Console-Output, Logging-Aggregator |
| Alerts | Slack-Channel (#peak-trade-alerts), E-Mail, Dashboard |
| Metrics | Prometheus/Grafana, Dashboard, Risk-Monitor |

### 6.3 Incident-Template

```markdown
## Incident Report – [run_id]

**Zeitpunkt:** [timestamp_incident]
**Operator:** [operator]
**Severity:** [severity_level]

### Kontext
- Environment: [environment]
- Strategy: [strategy_key]
- Session: [session_id]

### Artefakte
- Run-ID: [run_id]
- Config-Snapshot: [config_snapshot]
- Logs: [execution_log_path]
- Alerts: [alert_ids]

### Symptom
[Beschreibung des beobachteten Verhaltens]

### Einordnung
[ ] Bug
[ ] Expected Block
[ ] Governance-Schutz

### Root-Cause
[Analyse nach Behebung]

### Actions Taken
1. [Aktion 1]
2. [Aktion 2]
```

---

## 7. Daily Pre-Session Checks (5-Minuten-Routine)

### 7.1 Ziel

In **< 5 Minuten** klären, ob ExecutionPipeline, Risk-Limits und Alerts „ready" sind, bevor eine Trading-Session startet.

### 7.2 Checkliste

| # | Check | Kommando / Aktion | Erwartung | Zeit |
|---|-------|-------------------|-----------|------|
| 1 | **Config & Secrets validieren** | `python scripts/check_live_readiness.py` | `✅ All checks passed` | 30s |
| 2 | **Governance-Lock aktiv** | `grep "live_order_execution" src/governance/go_no_go.py` | `"locked"` | 10s |
| 3 | **Execution-Tests grün** | `pytest -q tests/test_execution_pipeline*.py` | Alle Tests `PASSED` | 60s |
| 4 | **Testnet-/Shadow-Order-Simulation** | `python scripts/smoke_test_testnet_stack.py` | `SUCCESS` Status | 60s |
| 5 | **Risk-Limits geladen & valide** | `python -c "from risk import LiveRiskLimits; print(LiveRiskLimits.load())"` | Limits angezeigt, keine Errors | 15s |
| 6 | **Alert-Kanäle testen** | Slack/E-Mail-Testalert senden | Alert wird empfangen | 30s |
| 7 | **Dashboard-Health** | Web-UI öffnen (`localhost:8000` oder Prod-URL) | UI lädt, Status-Page zeigt „OK" | 30s |
| 8 | **Paper-Smoke-Test** | `python scripts&#47;smoke_test_paper.py` (illustrative) | `SUCCESS` Status | 30s |

### 7.3 Ausführbare Kommandos

```bash
# 1. Config & Secrets
python scripts/check_live_readiness.py

# 2. Governance-Lock prüfen
grep -n "live_order_execution" src/governance/go_no_go.py

# 3. Tests ausführen
pytest -q tests/test_execution_pipeline*.py

# 4. Testnet-Simulation
python scripts/smoke_test_testnet_stack.py

# 5. Risk-Limits prüfen
python -c "from risk import LiveRiskLimits; print(LiveRiskLimits.load())"

# 6. Alert-Test (Beispiel für Slack)
python -c "from alerts import send_test_alert; send_test_alert(channel='#peak-trade-alerts')"

# 7. Dashboard-Health
curl -s http://localhost:8000/health | jq .

# 8. Paper-Smoke-Test
# python scripts/smoke_test_paper.py
```

### 7.4 Pre-Session-Protokoll

```markdown
## Pre-Session Check – [DATUM]

**Operator:** [NAME]
**Zeit:** [UHRZEIT]

| Check | Status | Notizen |
|-------|--------|---------|
| Config & Secrets | ✅/❌ | |
| Governance-Lock | ✅/❌ | |
| Execution-Tests | ✅/❌ | |
| Testnet-Simulation | ✅/❌ | |
| Risk-Limits | ✅/❌ | |
| Alert-Kanäle | ✅/❌ | |
| Dashboard-Health | ✅/❌ | |
| Paper-Smoke-Test | ✅/❌ | |

**Session-Freigabe:** ✅ Ja / ❌ Nein (Grund: ___)
```

---

## 8. Typische Szenarien: Invalid-Inputs & Risk-Violations

### 8.1 Invalid-Input-Szenarien

Das System reagiert auf ungültige Eingaben mit Status `INVALID` oder `ERROR`. **Keine Order wird an den Exchange gesendet.**

| Szenario | Input-Fehler | System-Reaktion | Operator-Handlung |
|----------|--------------|-----------------|-------------------|
| Null-Quantity | `quantity=0.0` | `INVALID`, `validation_error="Quantity must be > 0"` | Strategy-/Sizing-Logik debuggen |
| Negative Quantity | `quantity=-0.5` | `INVALID`, `validation_error="Quantity must be positive"` | Sizing-Berechnung prüfen |
| NaN/Inf in Quantity | `quantity=float('nan')` | `INVALID` oder `ERROR` | Input-Daten und Berechnungen prüfen |
| Fehlendes Symbol | `symbol=None` oder `symbol=""` | `INVALID`, `validation_error="Symbol required"` | Strategy-Config prüfen |
| Unbekanntes Symbol | `symbol="INVALID/PAIR"` | `INVALID`, `validation_error="Unknown symbol"` | Symbol-Mapping prüfen |
| Ungültiger TimeInForce | `time_in_force="FOREVER"` | `INVALID`, `validation_error="Invalid time_in_force"` | Order-Parameter korrigieren |
| Limit-Order ohne Preis | `order_type="limit"`, `price=None` | `INVALID`, `validation_error="Limit orders require price"` | Order-Builder-Logik prüfen |

**Diagnose-Code:**

```python
result = pipeline.submit_order(intent)

if result.status == ExecutionStatus.INVALID:
    print(f"Validation Error: {result.validation_error}")
    print(f"Invalid Field: {result.invalid_field}")
    print(f"Original Intent: {result.order_intent}")
    # KEINE Retry ohne Fix!
```

**Wichtig:**
- KEIN Override in Live oder Production
- Erst Konfiguration/Strategy-Params fixen
- Neue Backtests durchführen nach Änderungen

### 8.2 Risk-Violation-Szenarien

Das System blockt Orders bei Risk-Limit-Überschreitungen mit Status `BLOCKED_BY_RISK`. **Dies ist ein Governance-Schutz-Mechanismus.**

| Szenario | Limit-Typ | System-Reaktion | Operator-Handlung |
|----------|-----------|-----------------|-------------------|
| Max Position Size überschritten | Position-Limit | `BLOCKED_BY_RISK`, `violation="Max position size exceeded"` | Position-Sizing reduzieren |
| Max Drawdown erreicht | Drawdown-Limit | `BLOCKED_BY_RISK`, `violation="Drawdown limit breached"` | **KEIN Override**, Session schließen, Incident anlegen |
| Max Exposure überschritten | Exposure-Limit | `BLOCKED_BY_RISK`, `violation="Max exposure exceeded"` | Offene Positionen reduzieren |
| Daily Loss Limit erreicht | Daily-Loss | `BLOCKED_BY_RISK`, `violation="Daily loss limit reached"` | **Trading stoppen**, morgen neu bewerten |
| Concentration-Limit | Concentration | `BLOCKED_BY_RISK`, `violation="Asset concentration too high"` | Portfolio diversifizieren |

**Diagnose-Code:**

```python
result = pipeline.submit_order(intent)

if result.status == ExecutionStatus.BLOCKED_BY_RISK:
    print(f"Risk Violation: {result.risk_violation_details}")
    print(f"Current Exposure: {result.current_exposure}")
    print(f"Limit: {result.limit_value}")
    # KEIN Override! Governance-Entscheidung erforderlich.
```

**Wichtig:**
- **KEIN Override** bei Risk-Violations
- Run stoppen / Session schließen
- Incident anlegen mit allen Artefakten
- Ggf. Governance-Entscheidung einholen

### 8.3 Eskalations-Matrix

| Violation-Typ | Severity | Sofort-Aktion | Eskalation |
|---------------|----------|---------------|------------|
| Max Drawdown | 🚨 CRITICAL | Session sofort schließen | On-Call + Risk-Manager |
| Daily Loss Limit | ⚠️ HIGH | Trading für heute stoppen | On-Call informieren |
| Max Exposure | ⚠️ HIGH | Keine neuen Trades, Reduktion prüfen | On-Call informieren |
| Max Position Size | ⚠️ MEDIUM | Order anpassen, kein Override | Log dokumentieren |
| Invalid Input | 📝 LOW | Fix in Config/Strategy | Entwickler informieren |

---

## 9. Standard-Checks

### 9.1 Paper-Umgebung – Erfolgsfall

**Ziel:** Verifizieren, dass in `env="paper"` ein normaler Flow mit `SUCCESS` möglich ist.

```python
from execution import ExecutionPipeline, OrderIntent, ExecutionStatus

pipeline = ExecutionPipeline(env="paper")

intent = OrderIntent(
    symbol="BTC/USD",
    side=OrderSide.BUY,
    quantity=0.01,
    order_type="market",
    strategy_key="smoke_test",
)

result = pipeline.submit_order(intent, raise_on_governance_violation=True)

# Assertions
assert result.status == ExecutionStatus.SUCCESS
assert result.is_blocked_by_governance is False
assert result.is_blocked_by_risk is False
assert result.environment == "paper"
```

**Erwartung:**

* Order wird vom Paper-Executor angenommen
* Keine Governance-/Risk-Blockade
* `ExecutionResult` enthält `run_id`, `timestamp`, `environment`

---

### 9.2 Shadow-/Testnet-Umgebung – Erfolgsfall

Analog zu 9.1, nur mit `env="shadow"` bzw. `env="testnet"`:

| Environment | Verhalten |
|-------------|-----------|
| `shadow` | Kein echtes Order-Routing, nur Logging und State-Tracking |
| `testnet` | Echte Testnet-Order an Exchange-Sandbox, keine echte Börse |

**Wichtig:** In beiden Umgebungen wird `get_governance_status("live_order_execution")` aufgerufen. Blockade nur bei `env="live"`, nicht bei Shadow/Testnet.

---

### 9.3 Live-Umgebung – Governance-Lock

**Ziel:** Sicherstellen, dass Live-Orders **niemals durchgehen**.

#### Variante A – Exception (Default)

```python
pipeline = ExecutionPipeline(env="live")

try:
    pipeline.submit_order(intent, raise_on_governance_violation=True)
    raise AssertionError("Expected LiveExecutionLockedError, got SUCCESS/Result")
except LiveExecutionLockedError as exc:
    assert "live_order_execution" in str(exc)
    print(f"✅ Governance-Lock greift: {exc}")
```

#### Variante B – Blocked Result (ohne Exception)

```python
pipeline = ExecutionPipeline(env="live")

result = pipeline.submit_order(intent, raise_on_governance_violation=False)

assert result.status == ExecutionStatus.BLOCKED_BY_GOVERNANCE
assert result.is_blocked_by_governance is True
assert result.environment == "live"
assert result.executor_called is False  # Kein Executor-Aufruf
```

**In beiden Varianten:**

* ❌ Kein Executor-Call
* ✅ Governance-Status im Result/Log sichtbar
* ✅ Run-ID und Timestamp für Audit-Trail vorhanden

---

### 9.4 Invalid Quantity (`quantity <= 0`)

**Ziel:** Sicherstellen, dass offensichtliche Eingabefehler früh abgefangen werden.

**Typische Szenarien:**

| Input | Erwarteter Status | Grund |
|-------|-------------------|-------|
| `quantity=0.0` | `INVALID` | Null-Quantity nicht erlaubt |
| `quantity=-0.5` | `INVALID` | Negative Quantity nicht erlaubt |
| `quantity=NaN` | `INVALID` oder `ERROR` | Ungültiger numerischer Wert |

```python
intent = OrderIntent(
    symbol="BTC/USD",
    side=OrderSide.BUY,
    quantity=0.0,  # ← Ungültig
    order_type="market",
    strategy_key="test_invalid",
)

result = pipeline.submit_order(intent)

assert result.status == ExecutionStatus.INVALID
assert result.is_blocked_by_governance is False  # Validation vor Governance
assert result.is_blocked_by_risk is False        # Validation vor Risk
assert result.validation_error is not None       # Fehlerdetails vorhanden
```

---

### 9.5 Risk-Blockade

**Ziel:** Prüfen, dass Risk-Limits effektiv blocken.

**Typische Risk-Violations:**

| Limit | Beispiel-Szenario |
|-------|-------------------|
| Max Position Size | Order für 10 BTC, aber Limit ist 5 BTC |
| Max Drawdown | Aktueller Drawdown -8%, Limit ist -5% |
| Max Exposure | Gesamt-Exposure würde 150% erreichen, Limit ist 100% |
| Daily Loss Limit | Tagesverlust bereits bei Limit |

```python
# Risk-Limits so konfigurieren, dass Order verletzt wird
result = pipeline.submit_order(large_order_intent)

assert result.status == ExecutionStatus.BLOCKED_BY_RISK
assert result.is_blocked_by_risk is True
assert result.risk_violation_details is not None  # Details zur Violation
# Executor wurde NICHT aufgerufen
```

---

## 10. Incident-Handling

### 10.1 Symptom: Order in Live scheint durchzugehen

**Severity: CRITICAL** 🚨

**SOFORT-Maßnahmen (innerhalb 5 Minuten):**

1. **STOP** – Trading-Umgebung sofort stoppen:
   ```bash
   # Scheduler/Runner deaktivieren
   systemctl stop peak-trade-scheduler  # oder entsprechender Service
   ```

2. **VERIFY** – Prüfen ob wirklich eine Live-Order gesendet wurde:
   * Exchange-Dashboard / API für offene Orders prüfen
   * Logs nach Executor-Calls durchsuchen

3. **ISOLATE** – Falls bestätigt:
   * Exchange-API-Keys temporär deaktivieren
   * Betroffene Orders manuell canceln

4. **INVESTIGATE** – Config und Code prüfen:
   ```bash
   # Governance-Status prüfen
   grep -n "live_order_execution" src/governance/go_no_go.py

   # Aktuelle Config prüfen
   cat config/config.toml | grep -A5 "\[execution\]"

   # Tests ausführen
   pytest -v tests/test_execution_pipeline_governance.py
   ```

5. **ROOT-CAUSE** – Mögliche Ursachen:
   * `env` falsch gesetzt (Config-Fehler)
   * Legacy-Code-Pfad umgeht Pipeline
   * `go_no_go.py` fälschlich auf `"allowed"` gesetzt
   * Falscher Branch deployed

### 10.2 Symptom: Alle Orders BLOCKED_BY_RISK

**Severity: MEDIUM** ⚠️

**Checkliste:**

1. Risk-Limits-Konfiguration prüfen:
   ```bash
   cat config/risk_limits.toml  # oder entsprechende Config-Datei
   ```

2. Aktuelle Risk-Metriken abrufen:
   ```python
   from risk import LiveRiskLimits
   limits = LiveRiskLimits.load()
   print(limits.current_exposure)
   print(limits.current_drawdown)
   ```

3. Fragen zur Eingrenzung:
   * Betrifft es **alle** Strategien oder nur bestimmte?
   * Betrifft es **alle** Symbole oder nur bestimmte?
   * Seit wann tritt das Problem auf? (Deployment? Config-Änderung?)

4. Temporärer Workaround (nur in Sandbox/Test!):
   ```python
   # NUR FÜR DEBUGGING – nicht in Production!
   result = pipeline.submit_order(intent, skip_risk_check=True)  # falls unterstützt
   ```

### 10.3 Symptom: Viele INVALID-Status

**Severity: LOW-MEDIUM** ⚠️

**Typische Ursachen:**

| Ursache | Diagnose | Lösung |
|---------|----------|--------|
| `quantity <= 0` | Strategy erzeugt Null-/Negativ-Sizing | Sizing-Logik debuggen |
| Unbekanntes Symbol | Typo oder Symbol nicht konfiguriert | Symbol-Mapping prüfen |
| Ungültiger Order-Type | z.B. Limit-Order ohne Preis | Order-Builder-Logik prüfen |
| NaN/Inf in Quantity | Fehlerhafte Berechnung | Input-Daten und Berechnungen prüfen |

**Diagnose-Schritte:**

```python
# Validation-Details aus Result extrahieren
print(f"Validation Error: {result.validation_error}")
print(f"Invalid Field: {result.invalid_field}")
print(f"Original Intent: {result.order_intent}")
```

---

## 11. Wartung & Weiterentwicklung

### 11.1 Änderungen die dieses Runbook betreffen

Bei Änderungen an:

* `ExecutionStatus` (neue Status-Codes)
* Governance-Keys (`live_order_execution`, neue Feature-Flags)
* Executor-Mapping (neue Environments)
* Risk-Check-Logik (neue Limit-Typen)
* `OrderIntent`-Struktur (neue Felder)

### 11.2 Pflicht-Schritte bei Änderungen

1. **Tests anpassen/erweitern:**
   ```bash
   pytest -v tests/test_execution_pipeline*.py
   ```

2. **Runbook aktualisieren:**
   * Version erhöhen (z.B. v1.1 → v1.2)
   * Änderungen im Change-Log dokumentieren
   * Neue Status/Aktionen in Mapping-Tabellen ergänzen

3. **Review & Sign-Off:**
   * Mindestens 1 Reviewer mit Risk/Governance-Kontext
   * Bei Governance-Änderungen: explizites Sign-Off dokumentieren

4. **Deployment-Checkliste:**
   * Runbook-Update VOR Code-Deployment kommunizieren
   * On-Call-Team über Änderungen informieren

---

## 12. Quick-Check Cheat Sheet

### 12.1 Governance-Status prüfen (Python)

```python
from governance.go_no_go import get_governance_status

status = get_governance_status("live_order_execution")
assert status == "locked", f"CRITICAL: Live execution is {status}, expected 'locked'!"
print(f"✅ Governance-Lock aktiv: {status}")
```

### 12.2 Execution-Tests ausführen

```bash
# Schnell-Check (nur kritische Tests)
pytest -q tests/test_execution_pipeline.py tests/test_execution_pipeline_governance.py

# Vollständig mit Coverage
pytest -v --cov=src/execution tests/test_execution_pipeline*.py
```

### 12.3 Notfall: Live sofort sperren

Falls aus irgendeinem Grund Live-Execution entsperrt wurde:

```python
# In src/governance/go_no_go.py
_FEATURE_STATUS_MAP = {
    "live_order_execution": "locked",  # ← SOFORT auf "locked" setzen!
}
```

Dann: Deployment triggern oder Service neustarten.

---

> **Merksatz:** Solange alle Daily-Checks grün sind, gilt die ExecutionPipeline als **governance- und risk-konform betriebsbereit**. Bei Abweichungen: Incident-Prozess starten, nicht raten.

---

## 13. Versionierung & Change-Log

| Version | Datum | Änderungen | Autor |
|---------|-------|------------|-------|
| v1.0 | Dezember 2025 (2026-ready) | Initiales Runbook für ExecutionPipeline-Governance: Safety-Prinzipien, Architektur-Überblick, Standard-Checks, Incident-Handling-Grundlagen | – |
| v1.1 | Dezember 2025 (2026-ready) | **Erweiterung:** ExecutionStatus → Operator-Aktion Mapping-Tabelle (vollständig mit SLA); Bug vs. Expected-Block vs. Governance-Schutz Matrix (mit Entscheidungsbaum); Pflicht-Artefakte-Liste für Incidents (16 Artefakte inkl. Quellen); Daily Pre-Session Checks (5-Minuten-Routine mit 8 Checks); Typische Szenarien für Invalid-Inputs & Risk-Violations (mit Eskalations-Matrix); Versionierung & Change-Log Sektion; Normalisierte run_id/session_id-Beispiele (2025-Format) | – |
| v1.2 | – | *Reserviert für zukünftige Erweiterungen* | – |
| v1.3 | – | *Reserviert für zukünftige Erweiterungen* | – |

**Nächste geplante Updates:**

* Integration mit Alert-Pipeline-Runbook
* Erweiterung um Testnet-spezifische Checks
* Runbook für Live-Freigabe-Prozess (wenn relevant)

---

**Dokument-Status:** ✅ v1.1 (Dezember 2025, 2026-ready)
**Letzte Überprüfung:** 2025-12-09
**Alle Beispiele und IDs auf 2025-Format normalisiert.**
