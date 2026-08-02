# Peak_Trade Canonical Capability Closure, Runtime Recovery & Trading-Path Runbook V1.1 — Forensic Reconciled

**Status:** CANONICAL WORKING RUNBOOK — FORENSICALLY RECONCILED
**Authority:** Repository-Owner / Operator
**Scope:** Peak_Trade Futures-only, Master V2 / Double Play, Research → Shadow → Testnet → Live
**Primary Goal:** Alle bestehenden, vergessenen, nur dokumentierten, nur verdrahteten oder nicht aktivierten Capabilities systematisch bis zu einer nachweisbaren, sicheren Runtime-Closure führen – ohne Live-Trading vorzeitig zu aktivieren.
**Repository Baseline:** `origin&#47;main@4bac3303bd74967c0c81d02c5de16c431301e12e`
**Forensic Comparison Basis:** Cursor audit `PEAK_TRADE_FULL_CAPABILITY_COMPLETENESS_AND_FORGOTTEN_WORK_AUDIT_V1` at the same SHA
**Baseline Validity Rule:** Every implementation PR must revalidate the baseline against its actual `origin/main`; counts and paths in the audit are evidence snapshots, not timeless constants.
**Initial Runtime Status:** `CANONICAL_RUNTIME_ENTRYPOINT_STATUS=BOUND_NOT_ACTIVATED`
**Live Status:** FAIL-CLOSED / NOT IMPLEMENTED / NOT AUTHORIZED
**Dashboard Status:** READ-ONLY CONSUMER, niemals Authority oder SSOT
**Volatility Numeric Max-Age Status:** WATCHDOG / RESEARCH / DIAGNOSTIC ONLY, nicht enforcing
**Multi-Future Status:** NOT AUTHORIZED
**Phase-1 Position Limit:** `MAX_POSITIONS=1`
**Phase-1 Selection Semantics:** `SINGLE_SELECTED_FUTURE`

---



# Trading-First-Leitprinzip (kanonisch)

## Oberste Priorität

Peak_Trade ist kein Capability-Programm, sondern eine Trading-Engine.

Jede neue Capability muss deshalb einen **direkten Beitrag zum kanonischen Trading-Pfad** nachweisen:

```text
Market Data
→ Features
→ Market State
→ Master V2
→ Double Play
→ Bull/Bear
→ Risk
→ Safety
→ Intent
→ Execution
```

Eine Capability ist nur dann P0/P1-relevant, wenn sie:

- die Qualität einer Trading-Entscheidung verbessert,
- die Robustheit der Trading-Runtime erhöht,
- oder eine nachweisbare Lücke im produktiven Trading-Pfad schließt.

Governance, Dokumentation, Watchdogs und Diagnoseprogramme bleiben wichtig, dürfen den Trading-Pfad jedoch niemals prioritätsmäßig verdrängen.

## Trading-Value-Gate

Vor Beginn jeder neuen Capability sind mindestens folgende Fragen zu beantworten:

- Verbessert sie Master V2 oder Double Play?
- Verbessert sie Market-State-, Bull/Bear- oder Selection-Qualität?
- Verbessert sie Risk, Safety oder Runtime-Recovery?
- Schließt sie eine konkrete Lücke zwischen Market Data und Execution?

Falls alle Antworten **Nein** lauten und die Arbeit überwiegend Governance, Dokumentation oder Infrastruktur betrifft, ist sie als nachrangig oder optional zu behandeln.

## Numeric Volatility Max-Age

Numeric Max-Age bleibt ausdrücklich:

- WATCHDOG
- RESEARCH
- DIAGNOSTIC
- NON-ENFORCING

Es ist **kein verpflichtender Trading-Entwicklungspfad**. Eine spätere Enforcement-Diskussion ist nur zulässig, wenn belastbare Evidence zeigt, dass dadurch Master V2 bzw. Double Play objektiv verbessert werden. Andernfalls bleibt Numeric Max-Age ein optionales Forschungsprogramm und darf den Fortschritt der Trading-Runtime nicht verzögern.


# 0. Zweck und verbindliche Lesart

Dieses Runbook ist die kanonische Arbeitsanweisung zur Schließung der derzeit bekannten Capability-, Runtime-, Dokumentations- und Aktivierungslücken in Peak_Trade.

Es ersetzt keine Handelslogik. Es ändert insbesondere nicht automatisch:

- Master V2
- Double Play
- Bull-/Bear-Logik
- Dynamic Scope
- Composition
- Confirmation Semantik
- Entry/Exit-Präzedenz
- Risk- oder Safety-Entscheidungen

Änderungen an diesen Kernlogiken sind nur zulässig, wenn sie in einer separaten Capability ausdrücklich beschrieben, begründet, getestet, vom Owner autorisiert und als Core-Logic-Change gekennzeichnet werden.

Dieses Runbook verfolgt vier gleichzeitig verbindliche Ziele:

1. **Runtime-Wahrheit herstellen**
   Dokumentation, Config, Call-Graph, Tests und tatsächliche Runtime-Reachability müssen übereinstimmen.

2. **Liegengebliebene Capabilities schließen**
   Bestehender Code wird bevorzugt wiederverwendet, aber erst dann als abgeschlossen gewertet, wenn eine vollständige Capability-Closure nachgewiesen ist.

3. **Immer zurück zum Handelsziel arbeiten**
   Jede Capability muss nachweisen, welchen konkreten Beitrag sie zur sicheren, realistischen und später aktivierbaren Handels-Runtime leistet.

4. **Fail-closed bleiben**
   Live-Trading, Testnet-Execution, Paper-Execution, Multi-Future-Runtime und Runtime-Aktivierung bleiben blockiert, bis die jeweils definierten Gates vollständig und beweisbar erfüllt sind.

---

# 1. Kanonische Systemwahrheit

## 1.1 Zielbild

Das langfristige Zielsystem ist:

```text
Futures Discovery
→ Governed Universe
→ Ranking
→ Active-Set Selection
→ Per-Instrument Market State
→ Master V2
→ Double Play
→ Risk
→ Safety
→ Intent
→ Execution
→ Reconciliation
→ Portfolio State
→ Evidence
→ Restart Recovery
→ Operator Oversight
```

Das Zielbild ist nicht identisch mit dem aktuellen Runtime-Zustand.

## 1.2 Aktueller Ist-Zustand

Der aktuelle kanonische Ist-Zustand lautet:

```text
Public Market Data
→ gated Wallclock Session
→ analytical Decision/Economics Bridge
→ integrated offline Master V2 / Double Play
→ intended action
→ simulated economics
→ evidence
```

Nicht produktiv geschlossen oder nicht aktiviert sind derzeit unter anderem:

- Universe → Selected Future → Runtime Authority
- Top-20 → Top-N Active-Set Rotation
- Multi-Future Runtime
- Productive Reconciliation im Runtime-Host
- vollständiges Futures Accounting im Runtime-Pfad
- Canonical Runtime Activation
- Paper/Testnet/Live Order Submission
- Numeric Volatility Max-Age Enforcement
- vollständige Strategy-Registry-Bindung
- vollständige Restart-/Recovery-Beweise

## 1.3 Forensisch bestätigte Baseline-Wahrheit

Der Cursor-Audit am Repository-Stand `4bac3303bd74967c0c81d02c5de16c431301e12e` bestätigt als belastbare Ausgangslage:

```text
CANONICAL_RUNTIME_ENTRYPOINT_STATUS=BOUND_NOT_ACTIVATED
LIVE_TRADING=FAIL_CLOSED
MULTI_FUTURE_RUNTIME_AUTHORIZED=false
PHASE_1_SELECTION=SINGLE_SELECTED_FUTURE
PHASE_1_MAX_POSITIONS=1
DASHBOARD=READ_ONLY_CONSUMER
VOLATILITY_NUMERIC_MAX_AGE=WATCHDOG_ONLY_NON_ENFORCING
TOP20_TO_TOP5_PRODUCTIVE_ROTATION=false
UNIVERSE_RANKING_TRADING_AUTHORITY=false
PRODUCTIVE_RECONCILIATION_BOUND=false
FUTURES_ACCOUNTING_RUNTIME_BOUND=false
ECONOMIC_VALIDITY_OFFLINE_GATE_PASS=false
```

Die im Audit genannten Capability-Zählwerte sind ein Inventar-Snapshot und dürfen nicht als Closure-Beweis verwendet werden. Maßgeblich sind je Capability der konkrete produktive Entrypoint, der Call-Graph, der aktive Config-Wert, die Persistence-/Restart-Semantik und verifizierte Evidence.

### Audit-Klassifikationsregel

Ein Audit-Befund ist in genau eine der folgenden Kategorien zu überführen:

| Kategorie | Behandlung |
|---|---|
| `INTENTIONAL_SAFETY_BARRIER` | Nicht als Implementierungsdefekt priorisieren; Guard und Dokumentation erhalten |
| `CURRENT_PHASE_GAP` | In aktueller Single-Future-Closure beheben |
| `DEFERRED_REQUIRED_CAPABILITY` | Sofort mit Owner, Trigger und Zielphase registrieren; Implementierung erst nach Dependencies |
| `ORPHANED_REUSABLE_IMPLEMENTATION` | Reachability und Eignung prüfen; bevorzugt wiederverwenden |
| `LEGACY_DEAUTHORIZED` | Keine Wiederaktivierung; Parallel-Authority verhindern |
| `DOCUMENTATION_DRIFT` | Dokumentarisch korrigieren, ohne Runtime-Claim zu erzeugen |
| `INSUFFICIENT_EVIDENCE` | Keine Schlussfolgerung; gezielte Verifikation vor Mutation |

Insbesondere sind `LiveNotImplementedError`, deaktivierte Live-/Testnet-Flags und `BOUND_NOT_ACTIVATED` derzeit **Safety Barriers**, nicht P0-Implementierungsaufträge. P0 ist ihre eindeutige, nicht missverständliche Erhaltung.

## 1.3 Verbindliche Status-Semantik

Folgende Begriffe dürfen nicht mehr synonym verwendet werden:

| Status | Verbindliche Bedeutung |
|---|---|
| `DOCUMENTED` | Ziel, Vertrag oder Beschreibung existiert |
| `DTO_EXISTS` | Datenstruktur oder Contract existiert |
| `CODE_EXISTS` | Implementierung existiert |
| `CONFIG_EXISTS` | Konfiguration existiert |
| `CONFIG_CONSUMED` | Produktiver Consumer liest die Konfiguration |
| `BOUND` | Komponente ist in einen Call-Graph eingebunden |
| `RUNTIME_REACHABLE` | Ein produktiver Entrypoint kann sie tatsächlich erreichen |
| `ACTIVATED` | Runtime darf sie unter gültigen Gates ausführen |
| `PERSISTED` | Zustand wird dauerhaft gespeichert |
| `RESTART_PROVEN` | Verhalten nach Neustart ist getestet und verifiziert |
| `FAILURE_SAFE` | Fehler führen deterministisch fail-closed |
| `EVIDENCE_PROVEN` | Evidence und Verifier bestätigen das Verhalten |
| `CAPABILITY_CLOSED` | Alle für die Capability definierten Closure-Kriterien sind erfüllt |

Eine Capability darf nur als **fertig**, **complete**, **operational**, **production-ready** oder **closed** bezeichnet werden, wenn ihr definierter Closure-Satz vollständig erfüllt ist.

---

# 2. Authority-Modell

## 2.1 Repository und Runbook

Dieses Runbook ist die Arbeits- und Semantik-Authority für die Capability-Aufarbeitung.

Die Runtime-Authority bleibt im Code und in den explizit ratifizierten Runtime-Contracts.

Dokumentation darf keine Runtime-Autorität simulieren.

## 2.2 Dashboard

Das Dashboard ist ausschließlich:

```text
READ_ONLY_CONSUMER
```

Das Dashboard:

- erzeugt keine Trading-Wahrheit
- besitzt keine Selection Authority
- besitzt keine Ranking Authority
- besitzt keine Risk Authority
- besitzt keine Safety Authority
- besitzt keine Position Authority
- besitzt keine Portfolio Authority
- aktiviert keine Runtime
- konsumiert nur bereits kanonisch persistierte Readmodels
- darf Missing Truth sichtbar machen
- darf niemals fehlende Daten durch erfundene Defaults ersetzen
- darf niemals aus UI-Zustand Trading-Zustand ableiten
- darf niemals zur SSOT erklärt werden

Kanonische Richtung:

```text
Runtime SSOT
→ Evidence / Persistence
→ Readmodel
→ Dashboard
```

Verbotene Richtung:

```text
Dashboard
→ Runtime Decision
```

## 2.3 Universe und Ranking

Universe-, Ranking- und Selection-Daten werden erst dann Trading-Authority, wenn ein expliziter produktiver Owner existiert, der:

- Datenqualität prüft
- Ranking deterministisch erzeugt
- Ergebnis persistiert
- Version und Event-Time bindet
- Restart-Verhalten definiert
- Selection State veröffentlicht
- vom Runtime-Host konsumiert wird
- fail-closed auf Missing/Stale/Invalid reagiert

Ein Dashboard-Producer oder Research-Ranker ist keine Trading-Authority.

## 2.4 Master V2 / Double Play

Master V2 und Double Play bleiben kanonische Trading-Decision-Komponenten.

Die Authority-Kette muss eindeutig bleiben:

```text
Market State
→ Master V2
→ canonical Double Play Composition
→ Risk
→ Safety
→ Intent
```

Legacy-Ops-Evaluatoren dürfen keine parallele Authority besitzen.

## 2.5 Volatility Max-Age

Numeric Max-Age ist aktuell ausschließlich:

```text
WATCHDOG
RESEARCH
DIAGNOSTIC
COUNTERFACTUAL EVIDENCE
NON-ENFORCING
```

Verbindlich:

- Typed Volatility Presence darf Alpha-Gates beeinflussen, soweit bereits ratifiziert.
- Numeric Max-Age darf aktuell keine Trades blockieren.
- Numeric Max-Age darf aktuell keine Double-Play-Entscheidung mutieren.
- Numeric Max-Age darf aktuell keine Risk- oder Safety-Entscheidung ersetzen.
- Numeric Max-Age darf aktuell nur messen, klassifizieren, protokollieren und Evidence erzeugen.
- `enforcement_enabled` muss bis zu einer separaten Ratifikation `false` bleiben.
- Jede Dokumentation muss zwischen `presence_required` und `numeric_max_age_enforced` unterscheiden.
- Ein späteres Enforcement benötigt eigene Schwellenforschung, Strata-Evidence, Failure Semantics, Tests und Owner-GO.

---

# 3. Nicht verhandelbare Safety-Invarianten

## 3.1 Live bleibt blockiert

Bis zu einem separaten Live-Programm müssen folgende Zustände erhalten bleiben:

```text
enable_live_trading=false
live_authorized=false
orders_authorized=false
runtime_bridge_live_activated=false
CANONICAL_RUNTIME_ENTRYPOINT_STATUS=BOUND_NOT_ACTIVATED
```

`ExchangeOrderExecutor` darf weiterhin fail-closed reagieren.

## 3.2 Multi-Future bleibt blockiert

Bis Rotation, Reconciliation, State Isolation, Risk Allocation und Restart vollständig geschlossen sind:

```text
MULTI_FUTURE_RUNTIME_AUTHORIZED=false
MAX_POSITIONS=1
SINGLE_SELECTED_FUTURE=true
```

## 3.3 Kein implizites Hochsetzen von Positionslimits

Jeder Default, Test-Fixture oder Config-Wert mit `max_open_positions > 1` muss:

- als historisch, test-only oder nicht-kanonisch markiert werden, oder
- auf Phase-1 `1` ausgerichtet werden.

Kein produktiver Consumer darf versehentlich den Default `5` verwenden.

## 3.4 Keine erfundenen Defaults

Verboten sind stille Fallbacks für:

- Volatilität
- Mark Price
- Ranking
- Selected Future
- Position State
- Portfolio State
- Event Time
- Staleness
- Risk Limits
- Confirm Tokens
- Authorization State

Fehlende Wahrheit muss als Missing/Invalid/Stale sichtbar und fail-closed behandelt werden.

## 3.5 Confirm-Token-Operatorentlastung bei unveränderter Sicherheit

Der Owner muss nicht manuell Format, Länge oder Inhalt eines Confirm-Tokens erfinden oder in Klartext an Cursor übermitteln.

Verbindlicher Ablauf für Cursor:

1. Zuerst den repository-kanonischen Token-Mint-/Issuance-Pfad ermitteln und verwenden.
2. Nur wenn der kanonische Contract dies ausdrücklich erlaubt, einen kryptographisch sicheren, compliant Token flüchtig im Prozessspeicher erzeugen.
3. Den Token ausschließlich in den vorgesehenen Hidden-Prompt-/stdin-Kanal eingeben.
4. Den Klartext niemals anzeigen, loggen, persistieren, in Shell-History schreiben, committen, als Argument in Prozesslisten exponieren oder in Evidence übernehmen.
5. Nur Digest, Token-ID, Scope, Bindings, Issuance-/Consumption-Status und Redaction-Nachweis dürfen ausgegeben werden.
6. Manuelle Operator-Eingabe nur dann verlangen, wenn der im Repository erzwungene Sicherheitsvertrag automatisierte sichere Eingabe technisch ausschließt; dies muss mit konkretem Code-/Contract-Beleg als `HARD_STOP` dokumentiert werden.
7. Keine Sicherheitskontrolle darf umgangen, abgeschaltet oder durch einen festen Default ersetzt werden.

```text
CONFIRM_TOKEN_PLAINTEXT_EXPOSED=false
CONFIRM_TOKEN_PERSISTED=false
CONFIRM_TOKEN_SHELL_HISTORY=false
CONFIRM_TOKEN_CANONICAL_PATH_USED=true
```

## 3.6 Exit/Risk/Safety bleiben unabhängig

Auch bei fehlender oder alter Volatility müssen erhalten bleiben:

- Mandatory Exit
- Hard Risk Reduce
- Safety Veto
- Kill Switch
- Reconciliation
- Reduce-Only Verhalten
- Position Protection

Alpha darf blockiert werden; Schutzpfade dürfen nicht verschwinden.

## 3.7 Kein Core-Logic-Drift durch Wiring

Wiring-, Activation-, Persistence-, Evidence- oder Watchdog-Slices dürfen die bestehende Double-Play-/Master-V2-Logik nicht stillschweigend verändern.

Jeder Diff muss klassifizieren:

```text
CORE_LOGIC_CHANGE=false
```

oder, falls wahr:

```text
CORE_LOGIC_CHANGE=true
OWNER_RATIFICATION_REQUIRED=true
```

---

# 4. Lokale Arbeitsumgebung und Git-Ausführung

## 4.1 Cursor-Sandbox-Verbot für Git

Git-Operationen dürfen nicht innerhalb einer eingeschränkten Cursor-Sandbox ausgeführt werden, wenn dort `.git` nicht zuverlässig zugänglich ist.

Verbindliche Ausführung:

```text
Cursor Chat
→ Anweisung an Cursor Agent
→ lokales Terminal mit echtem Repository-Zugriff
→ direkte lokale Git-Ausführung
```

Nicht zulässig:

```text
Cursor Sandbox
→ emuliertes oder blockiertes Git
→ Worktree-/Index-/Lock-Fehler ignorieren
```

## 4.2 Jeder Cursor-Auftrag muss enthalten

Jede an Cursor übergebene Umsetzung muss ausdrücklich anweisen:

1. Verwende das lokale Terminal mit direktem Zugriff auf das echte Repository.
2. Verwende keine Cursor-Sandbox für Git-Operationen.
3. Prüfe `pwd`, Repository Root und `.git`.
4. Führe `git fetch`, `git status`, Branching, Commit und Push lokal aus.
5. Stoppe fail-closed, wenn Repository Root, `.git`, Branch oder SHA nicht eindeutig sind.
6. Mutationen nur nach erfolgreichem Preflight.
7. Keine untracked Evidence-Verzeichnisse löschen, verschieben oder committen.
8. Keine bestehende Authorization konsumieren, sofern die Capability dies nicht ausdrücklich verlangt.
9. Keine Netzwerk- oder Trading-Session starten, sofern nicht ausdrücklich autorisiert.
10. Keine Rulesets verändern, außer bei separatem Owner-Merge-GO.

## 4.3 Standard-Preflight

Vor jeder Capability:

```bash
pwd
git rev-parse --show-toplevel
git rev-parse --git-dir
git status --short
git branch --show-current
git rev-parse HEAD
git fetch origin --prune
git rev-parse origin/main
git diff --stat origin/main...HEAD
```

Erwartung vor neuer Arbeit:

```text
BRANCH=main
HEAD=origin/main
TRACKED_WORKTREE_CLEAN=true
UNTRACKED_EVIDENCE_PRESERVED=true
```

Bei Abweichung: HARD STOP.

---

# 5. Capability-Closure-Standard

Jede neue oder reparierte Capability benötigt eine Capability-Datei mit mindestens:

```text
CAPABILITY_ID
TITLE
OWNER_REQUIREMENT
CURRENT_STATE
TARGET_STATE
OUT_OF_SCOPE
AUTHORITY_OWNER
PRODUCTIVE_ENTRYPOINT
CALL_GRAPH
CONFIG_KEYS
PERSISTENCE
RESTART_SEMANTICS
FAILURE_SEMANTICS
SAFETY_INVARIANTS
CORE_LOGIC_CHANGE
TEST_PLAN
EVIDENCE_PLAN
ACTIVATION_STATE
ROLLBACK_PLAN
DOCS_UPDATE
NOTION_UPDATE
```

## 5.1 Mandatory Closure Matrix

Eine Capability ist nur geschlossen, wenn folgende Felder explizit bewertet wurden:

```text
CODE_EXISTS
CONFIG_EXISTS
CONFIG_CONSUMED
PRODUCTIVE_CALLER_EXISTS
RUNTIME_REACHABLE
AUTHORITY_UNAMBIGUOUS
PERSISTENCE_PROVEN
RESTART_PROVEN
FAILURE_SAFE
INTEGRATION_TESTED
NEGATIVE_TESTED
EVIDENCE_PRODUCED
EVIDENCE_VERIFIED
DOCS_ACCURATE
NOTION_ACCURATE
ACTIVATION_EXPLICIT
```

Nicht zutreffende Felder müssen mit Begründung als `N&#47;A` markiert werden.

## 5.2 Status-Regel

Verboten:

```text
STATUS=PASS
```

wenn nur Unit Tests, DTOs oder direkte Funktionsaufrufe grün sind.

Erlaubt:

```text
STATUS=PASS
VERDICT=IMPLEMENTED_NOT_BOUND
```

oder:

```text
STATUS=PASS
VERDICT=BOUND_NOT_ACTIVATED
```

oder:

```text
STATUS=PASS
VERDICT=CAPABILITY_CLOSED
```

Der Verdict muss den tatsächlichen Reifegrad ausdrücken.

---

# 6. Kanonische Aufarbeitungsreihenfolge

Die folgende Reihenfolge ist verbindlich, weil spätere Schritte von früheren Safety- und Authority-Schließungen abhängen.

---

## 6.1 Zwei getrennte Prioritätsachsen

Zur Auflösung des Audit-Scheinwiderspruchs gelten zwei Achsen:

1. **Safety-/Runtime-Abhängigkeiten:** Reconciliation → Single Selection → Futures Accounting → Pre-Activation.
2. **Vergessene fachliche Arbeit:** Rotation Policy sofort in Phase 0 reaktivieren und ratifizierungsreif spezifizieren; technische Top-N-Umsetzung erst in Phase 6/7.

Damit ist Rotation nicht erneut vergessen, ohne unsichere Multi-Position-Runtime vor Reconciliation und State Closure zu bauen.

# PHASE 0 — Wahrheit, Dokumentation und Guardrails bereinigen

## Ziel

Missverständliche Dokumentation entfernen, Runtime-Wahrheit sichtbar machen und verhindern, dass Zielbild, DTO, Offline-Test oder deaktivierte Bindung erneut als produktive Capability gelesen werden.

## Capability 0.1 — Canonical Runtime Truth Map

### Umsetzung

Erzeuge oder überarbeite eine kanonische Datei:

```text
docs/governance/PEAK_TRADE_CANONICAL_RUNTIME_TRUTH_MAP_V1.md
```

Sie muss enthalten:

- Baseline SHA
- produktive Entrypoints
- aktiv erreichbare Call-Graphs
- deaktivierte Call-Graphs
- Authority Owner je Capability
- Config-Flags und aktive Werte
- Persistence Owner
- Evidence Owner
- Activation State
- Live/Testnet/Paper/Shadow Status
- Multi-Future Status
- Dashboard Consumer-only Status
- Volatility Numeric Max-Age Watchdog-only Status
- bekannte Gaps
- letzte verifizierte Evidence
- Datum und SHA der Verifikation

### Semantik

Die Datei darf nicht als Zielbild formuliert sein. Sie ist ausschließlich Ist-Zustand.

### Tests

- Doc token/reference checks
- Guard gegen verbotene Formulierungen
- automatischer Abgleich zentraler Constants/Config Keys
- Test, dass `BOUND_NOT_ACTIVATED` nicht als `ACTIVE` dargestellt wird

### Closure

```text
DOCS_ACCURATE=true
RUNTIME_FLAGS_REFERENCED=true
TARGET_VS_CURRENT_SEPARATED=true
DASHBOARD_AUTHORITY_FALSE=true
VOL_MAX_AGE_ENFORCING_FALSE=true
```

## Capability 0.2 — Historical/Target Documentation Labels

Alle historischen oder zielbildorientierten Dokumente müssen einen klaren Header erhalten:

```text
DOCUMENT_CLASS=HISTORICAL
```

oder:

```text
DOCUMENT_CLASS=TARGET_ARCHITECTURE
```

oder:

```text
DOCUMENT_CLASS=CURRENT_RUNTIME_TRUTH
```

Begriffe wie `COMPLETE`, `READY`, `OPERATIONAL` oder `PRODUCTION` müssen im Kontext erklärt oder korrigiert werden.

## Capability 0.3 — Config Truth Alignment

### Pflichtprüfung

- `max_open_positions`
- `enable_live_trading`
- `orders_authorized`
- `paper_execution_authorized`
- `testnet_authorized`
- `runtime_bridge_live_activated`
- `MULTI_FUTURE_RUNTIME_AUTHORIZED`
- `enforcement_enabled`
- `require_confirm_token`

### Erwartung Phase 1

```text
max_open_positions=1
enable_live_trading=false
orders_authorized=false
paper_execution_authorized=false
testnet_authorized=false
runtime_bridge_live_activated=false
MULTI_FUTURE_RUNTIME_AUTHORIZED=false
volatility_numeric_max_age_enforcement=false
```

### Consumer-Trace und effektive Wahrheit

Ein gefundener Code-Default wie `max_open_positions=5` darf nicht blind geändert werden. Zuerst ist nachzuweisen:

- welcher produktive Entrypoint den Wert liest,
- welche Config-Schicht gewinnt,
- ob der Wert dead, test-only, historical oder runtime-effective ist,
- ob ein fehlender Key auf den Default zurückfallen kann.

Closure verlangt einen Test, dass jeder Phase-1-Entrypoint effektiv `max_open_positions=1` erhält und bei fehlender/ungültiger Config fail-closed stoppt, statt auf `5` zurückzufallen.

### Safety

Keine Aktivierung in diesem Schritt.

---

## Capability 0.4 — Deferred-Work Recovery Register und Rotation-Policy-Wiedervorlage

Der als Reminder-only identifizierte Workstream `MULTI_FUTURE_ACTIVE_SET_ROTATION_REPLACEMENT_POLICY_V0` wird in Phase 0 formal wieder in die aktive Roadmap aufgenommen.

Diese Capability in Phase 0 ist **nur Design-/Governance-Recovery**, keine Multi-Future-Implementierung und keine Aktivierung.

Kanonisches Register (SSOT):

```text
docs/governance/deferred_work_recovery_register_v1.json
docs/governance/PEAK_TRADE_DEFERRED_WORK_RECOVERY_REGISTER_V1.md
docs/ops/specs/DEFERRED_WORK_RECOVERY_REGISTER_ROTATION_POLICY_RESUBMISSION_V1.md
src/ops/deferred_work_recovery_register_contract_v1.py
tests/governance/test_deferred_work_recovery_register_v1.py
```

Pflichtartefakte:

- eindeutiger Owner
- ursprüngliche Owner-Anforderung
- Status `DEFERRED_REQUIRED_CAPABILITY`
- Dependencies: Single-Future Selection, Reconciliation, Futures Accounting, State Isolation, Global Risk
- Review Trigger
- Zielphase 6
- explizite Top-N-Semantik
- Entscheidung, ob erste ratifizierte Konfiguration `N=5` wird
- Verbot, Top-5 als bereits bestehende oder regressierte Produktivfunktion zu bezeichnen

Damit wird die vergessene Rotation sofort organisatorisch geschlossen, während die technische Umsetzung weiterhin erst nach den Safety-Dependencies erfolgt.

---

# PHASE 1 — Productive Reconciliation Closure

## Ziel

Positionen, Portfolio State und Exchange-/Sim-State müssen vor jeder späteren Aktivierung oder Multi-Future-Erweiterung deterministisch reconciled werden.

## Capability 1.1 — Runtime Reconciliation Owner

### Wiederverwendung und Provenienzprüfung

Der Audit nennt als wiederverwendbare Basis:

```text
execution/reconciliation.py
```

Vor Mutation muss Cursor den tatsächlichen Repository-Pfad, Export, Caller, Tests, Semantik und Aktualität am aktuellen SHA verifizieren. Der Audit-Pfad ist ein Suchanker, kein ungeprüfter Implementierungsbeweis. Vorhandene Adapter sind nur zu übernehmen, wenn sie Futures-Semantik, Single-Writer, Idempotenz und fail-closed Verhalten erfüllen.

### Erforderlicher Call-Graph

```text
Session Start
→ Load Persisted Portfolio State
→ Read Execution/Position State
→ Reconcile
→ classify:
   MATCH
   RECOVERABLE_DRIFT
   UNRECOVERABLE_DRIFT
   MISSING_TRUTH
→ only on safe result:
   enable decision cycle
```

### Failure Semantics

| Zustand | Verhalten |
|---|---|
| `MATCH` | Runtime darf fortfahren |
| `RECOVERABLE_DRIFT` | deterministische Recovery, Evidence, danach Recheck |
| `UNRECOVERABLE_DRIFT` | HARD STOP / EXIT_ONLY |
| `MISSING_TRUTH` | HARD STOP |
| stale source | HARD STOP |
| duplicate state | HARD STOP |
| conflicting writer | HARD STOP |

### Invarianten

- Reconciliation läuft vor Alpha.
- Reconciliation darf keine neue Position eröffnen.
- Recovery darf nur reduce-only oder state-repair sein.
- Single Writer muss nachweisbar sein.
- Jede Korrektur ist auditierbar.
- Restart ohne Reconciliation ist verboten.

### Tests

- no-position clean start
- matching open position
- quantity drift
- side drift
- missing position
- unknown external position
- stale snapshot
- duplicate snapshot
- restart during recovery
- process crash after persistence before verification
- idempotent replay

### Evidence

- pre-state digest
- external/sim-state digest
- reconciliation decision
- mutation plan
- applied mutation
- post-state digest
- verifier result

### Activation

Noch keine Live-/Order-Aktivierung.

---

# PHASE 2 — Phase-1 Universe → Single Selected Future Authority

## Ziel

Die bereits ratifizierte Phase-1-Kette vollständig schließen:

```text
Discovery
→ Governed Universe
→ Ranking
→ SINGLE_SELECTED_FUTURE
→ Persistence
→ Restart Recovery
→ Runtime Consumption
```

## Capability 2.1 — Governed Futures Universe Producer

### Closure markers

```text
CAPABILITY_ID=CAPABILITY_2_1_GOVERNED_FUTURES_UNIVERSE_PRODUCER_V1
CODE_EXISTS=true
BOUND=true
RUNTIME_REACHABLE=true
PERSISTED=true
RESTART_PROVEN=true
ACTIVATED=false
AUTHORITY_OWNER=ops.governed_futures_universe_producer_v1
PRODUCTIVE_ENTRYPOINT=scripts/ops/run_governed_futures_universe_producer_v1.py
SPEC=docs/ops/specs/MASTER_V2_CAPABILITY_2_1_GOVERNED_FUTURES_UNIVERSE_PRODUCER_V1.md
EVIDENCE=docs/evidence/capability_2_1_governed_futures_universe_producer_v1/
RANKING_CLOSED=false
SINGLE_SELECTED_FUTURE_CLOSED=false
MULTI_FUTURE_CLOSED=false
ALPHA_ALLOWED=false
```

### Anforderungen

- OKX EEA Futures-only
- Spot ausgeschlossen
- BTC ausgeschlossen, falls weiterhin Owner-Vorgabe
- Instrument-Metadaten vollständig
- Native `instId` gebunden
- tick size, lot size, contract value, expiry/perpetual semantics
- mark-price availability
- trading status
- data quality
- event-time
- producer version
- source digest

### Output

Versioniertes Universe Snapshot DTO (`governed_futures_universe_snapshot.v1`) mit atomarer Persistence, Single-Writer-Schutz und Restart-Load/Validate.

### Failure

Keine geeigneten Instrumente → `UNIVERSE_STATUS=NO_ELIGIBLE_INSTRUMENTS` → keine Selection → `ALPHA_ALLOWED=false`.

### Abgrenzung

Diese Capability erzeugt ausschließlich die kanonische Universe-Wahrheit. Ranking, `SINGLE_SELECTED_FUTURE`, Master V2, Double Play, Execution und Runtime-Aktivierung bleiben außerhalb.

## Capability 2.2 — Productive Ranking Producer

### Anforderungen

Ranking muss:

- deterministisch sein
- auf einem expliziten Event-Time Snapshot basieren
- Datenqualität einbeziehen
- stale/missing Daten ausschließen
- reproduzierbare Tie-Breaker besitzen
- Score-Komponenten persistieren
- Top-20 als Kontext erzeugen
- keine Position eröffnen
- keine UI-Daten konsumieren

### Verbot

Dashboard-Ranking darf nicht zurück in die Runtime fließen.

### Abgrenzung Top-20, Selected Future und späterem Top-N

```text
TOP20 = gerankter Kontext / Candidate Set
SINGLE_SELECTED_FUTURE = einzige Phase-1 Trading-Selection-Authority
TOP_N_ACTIVE_SET = spätere Multi-Future-Authority nach ratifizierter Rotation Policy
```

`Top-5` ist am Baseline-SHA weder produktiv noch regressiert, sondern eine mögliche spätere Konfiguration von Top-N. Diese Begriffe dürfen in Code, Evidence und Docs nicht vermischt werden.

## Capability 2.3 — Single Selected Future Policy

### Phase-1 Semantik

Genau ein Instrument besitzt Selection Authority:

```text
selected_future_count=1
max_positions=1
```

### Selection-Regeln

Die Policy muss definieren:

- Ranking-Zeitpunkt
- Mindestdatenqualität
- Mindesthistorie
- Tie-Breaker
- Refresh-Cadence
- Hysterese
- Mindesthaltezeit der Selection
- Verhalten bei Datenverlust
- Verhalten bei Instrument-Invalidität
- Verhalten bei offener Position
- Restart Recovery
- Manual Override Policy
- Evidence

### Offene Position

Solange eine Position offen ist, darf Selection nicht stillschweigend wechseln.

Erlaubte Zustände:

```text
SELECTED_ACTIVE
SELECTED_DEGRADED
SELECTED_EXIT_ONLY
REPLACEMENT_PENDING
NO_SELECTION
```

### Persistence

Persistiere mindestens:

```text
selection_id
instrument_id
venue_native_id
ranking_snapshot_id
selected_at_event_time
selected_at_wall_time
valid_from
valid_until
policy_version
config_digest
repository_sha
reason_codes
state
```

## Capability 2.4 — Runtime Binding

Erforderlicher Call-Graph:

```text
Persisted Selected Future
→ validate freshness and integrity
→ bind native instrument
→ market data
→ features
→ Master V2
→ Double Play
→ Risk/Safety
→ simulated economics
```

Die Instrument-Allowlist darf nicht länger die alleinige Trading-Selection simulieren.

### Restart

Nach Restart:

- Selection laden
- Digest prüfen
- Validity prüfen
- Ranking Snapshot referenzieren
- Reconciliation ausführen
- erst danach Alpha erlauben

### Tests

- deterministic selection
- no candidates
- stale ranking
- tie
- selected instrument suspended
- mark-price missing
- restart
- config mismatch
- SHA mismatch
- position open during refresh
- duplicate selection writers
- dashboard unavailable
- dashboard contains conflicting display data

---

# PHASE 3 — Futures Accounting Runtime Closure

## Ziel

Die simulierte Futures-Ökonomie muss den vorgesehenen Futures-Accounting-Kernel produktiv verwenden.

## Wiederverwendung

```text
futures_accounting.py
```

## Anforderungen

- contract multiplier
- quantity units
- mark price
- entry price
- realized PnL
- unrealized PnL
- fees
- slippage
- funding, falls im Scope
- margin semantics
- liquidation-distance diagnostics, falls im Scope
- reduce-only behavior
- partial fills
- position flips weiterhin verboten, sofern kanonisch
- deterministic rounding

## Call-Graph

```text
Intent
→ simulated execution
→ fill model
→ futures accounting
→ portfolio state
→ risk state
→ evidence
```

## Tests

- long open/close
- short open/close
- partial reduce
- fee application
- slippage
- mark move
- restart
- idempotency
- zero quantity
- invalid contract metadata
- missing mark
- reduce-only violation
- flip attempt
- rounding edge cases

## Safety

Kein Live-Orderpfad.

---

# PHASE 4 — Phase-1 Canonical Runtime Pre-Activation Closure

## Ziel

Die vollständige Single-Future-Runtime wird erreichbar und beweisbar, bleibt aber bis separatem Owner-GO deaktiviert.

## Erforderlicher Call-Graph

```text
Auth
→ Session Lock
→ Reconciliation
→ Universe Snapshot
→ Ranking Snapshot
→ Persisted Selected Future
→ Public Market Data
→ Feature Pipeline
→ Typed Volatility Presence
→ Master V2
→ Double Play
→ Risk
→ Safety
→ Intent
→ Simulated Futures Execution
→ Futures Accounting
→ Portfolio Persistence
→ Evidence
→ Verifier
```

## Pre-Activation Gates

Mindestens:

```text
RUNTIME_TRUTH_MAP_CURRENT=true
CONFIG_TRUTH_ALIGNED=true
RECONCILIATION_BOUND=true
RECONCILIATION_RESTART_PROVEN=true
UNIVERSE_AUTHORITY_BOUND=true
RANKING_AUTHORITY_BOUND=true
SINGLE_SELECTION_PERSISTED=true
SELECTION_RESTART_PROVEN=true
FUTURES_ACCOUNTING_BOUND=true
DOUBLE_PLAY_PARITY_PROVEN=true
RISK_BOUND=true
SAFETY_BOUND=true
EXIT_PATH_PROVEN=true
EVIDENCE_VERIFIED=true
NO_LIVE_ORDER_PATH=true
MULTI_FUTURE_DISABLED=true
VOL_MAX_AGE_ENFORCEMENT_DISABLED=true
DASHBOARD_CONSUMER_ONLY=true
PRODUCTIVE_ENTRYPOINT_CALL_GRAPH_PROVEN=true
CONFIG_EFFECTIVE_VALUES_PROVEN=true
ECONOMIC_VALIDITY_OFFLINE_GATE_STATE_EXPLICIT=true
LEGACY_PARALLEL_AUTHORITY_ABSENT=true
```

## Aktivierung

Die Capability darf am Ende lauten:

```text
CANONICAL_RUNTIME_ENTRYPOINT_STATUS=READY_FOR_ACTIVATION
```

Nicht:

```text
ACTIVATED
```

Aktivierung ist ein separater Owner-Schritt.

---

# PHASE 5 — Single-Future Shadow/Paper Evidence Program

## Ziel

Die vollständige kanonische Runtime über natürliche Marktphasen beweisen.

## Session Ladder

1. Offline deterministic replay
2. Synthetic failure replay
3. Public-MD no-order shadow
4. Simulated paper economics
5. Restart/recovery session
6. prolonged natural-age observation
7. adverse market stress session

## Mindestmetriken

- cycles
- distinct observations
- duplicate observations
- missing observations
- decisions
- HOLD/ENTRY/REDUCE/EXIT counts
- blocked reasons
- reconciliation results
- selected-future changes
- stale data events
- volatility presence events
- numeric max-age strata
- safety vetoes
- risk vetoes
- simulated fills
- fees
- slippage
- realized/unrealized PnL
- max drawdown
- profit factor
- Sharpe, nur bei ausreichender Stichprobe
- turnover
- restart count
- recovery outcomes
- evidence verifier result

## Numeric Max-Age während dieser Phase

Weiterhin ausschließlich Watchdog:

```text
enforcement_enabled=false
```

Auswertung:

- age distributions
- outcome strata
- actionability strata
- counterfactual blocked/not-blocked
- safety interactions
- missingness
- event-time quality

Keine Schwelle wird ohne eigene Ratifikation aktiviert.

---

# PHASE 6 — Active-Set Rotation Replacement Policy V0

## Ziel

Vor jeder Multi-Future-Implementierung eine vollständige fachliche und sicherheitstechnische Policy ratifizieren.

## Capability-ID

```text
MULTI_FUTURE_ACTIVE_SET_ROTATION_REPLACEMENT_POLICY_V0
```

## Pflichtentscheidungen

### Active Set

- `active_set_size`
- initial empfohlenes Ziel: konfigurierbar
- erste ratifizierte Multi-Future-Konfiguration darf `N=5` sein
- technische Implementierung bleibt Top-N-fähig

### Promotion

- Mindestscore
- Mindestdatenqualität
- Mindestverweildauer im Candidate Set
- erforderliche Distanz zum schlechtesten Active-Instrument
- Bestätigung über mehrere distinct observations
- Cooldown

### Demotion

- Score-Verlust
- Datenqualitätsverlust
- Instrument invalid
- stale market data
- spread/liquidity degradation
- risk disqualification
- prolonged non-actionability
- manual emergency removal

### Hysterese

Promotion nur, wenn:

```text
candidate_score >= incumbent_score + replacement_margin
```

über definierte distinct observations.

### Offene Positionen

Ein Instrument mit offener Position darf nicht hart aus der Runtime entfernt werden.

Zustände:

```text
ACTIVE_ALPHA
ACTIVE_POSITION_ONLY
DEMOTION_PENDING
EXIT_ONLY
RETIRED
```

Nach Demotion:

- keine neue Position
- keine Positionsvergrößerung
- Risk/Safety/Exit bleiben aktiv
- reduce-only erlaubt
- State bleibt bis Flat + Reconciliation bestehen
- Evidence bleibt instrumentenspezifisch erhalten

### Kapitalallokation

- global risk budget
- per-instrument risk budget
- correlation budget
- concentration limit
- max concurrent exposure
- max active positions
- max gross exposure
- max net directional exposure
- liquidity-adjusted sizing
- deterministic allocation order

### State Isolation

Jedes Instrument benötigt isolierten Zustand für:

- market observations
- confirmation counters
- scope
- composition
- position
- risk
- safety
- volatility
- selection state
- evidence
- restart checkpoint

### Restart

Nach Restart:

- Active Set laden
- offene Positionen laden
- per-instrument state laden
- Reconciliation je Instrument
- Ranking Snapshot prüfen
- pending promotions/demotions rekonstruieren
- erst danach Alpha

## Output

Die Phase endet nur mit ratifizierter Policy, noch ohne Multi-Future-Aktivierung.

---

# PHASE 7 — Multi-Future Runtime Implementation

## Ziel

Top-N Active Set technisch umsetzen, zunächst weiterhin deaktiviert.

## Architecture

```text
Global Universe Owner
→ Global Ranking Owner
→ Active Set Policy
→ Per-Instrument Runtime Context
→ Per-Instrument Master V2 / Double Play
→ Global Portfolio Risk
→ Global Safety
→ Intent Arbitration
→ Simulated Execution
→ Reconciliation
```

## Single Writer

Es muss genau einen globalen Portfolio-/Execution-Writer geben.

Per-Instrument Decisions dürfen nicht direkt Orders oder Fills schreiben.

## Intent Arbitration

Arbitration muss definieren:

- ordering
- simultaneous intents
- capital contention
- risk contention
- reduce/exit precedence
- safety precedence
- duplicate intent handling
- stale intent rejection
- version/digest binding

## Tests

- 2, 5 und N instruments
- simultaneous entries
- simultaneous exits
- one stale instrument
- one invalid instrument
- demotion with open position
- promotion under capacity
- no capacity
- global kill switch
- restart
- partial persistence failure
- writer conflict
- duplicate events
- event ordering
- capital contention
- correlation limits
- deterministic replay

## Status am Ende

```text
MULTI_FUTURE_RUNTIME_IMPLEMENTED=true
MULTI_FUTURE_RUNTIME_AUTHORIZED=false
```

---

# PHASE 8 — Multi-Future Shadow/Paper Activation

## Voraussetzung

Separate Owner-Autorisierung.

## Erste Konfiguration

Empfohlen:

```text
active_set_size=5
max_open_positions<=5
live_orders=false
testnet_orders=false
paper_simulation=true
```

## Stufen

1. no-order shadow
2. simulated paper
3. restart/recovery
4. adverse rotation stress
5. long-running natural session
6. economic validity assessment

## Abbruchbedingungen

- unreconciled position
- missing active-set state
- conflicting selection writers
- excessive churn
- rotation oscillation
- stale ranking
- evidence verifier failure
- risk budget breach
- state isolation breach
- dashboard-derived authority detected
- numeric max-age accidentally enforcing
- live/testnet path reachable

---

# PHASE 9 — Strategy Registry Closure

## Ziel

Bestehende Strategy Registry kontrolliert an Suitability/Composition anbinden, ohne Double-Play-Authority zu umgehen.

## Regel

Keine Strategie darf direkte Trading-Authority erhalten.

Kanonische Richtung:

```text
Strategy Signal
→ Suitability
→ Master V2 / Double Play Composition
→ Risk
→ Safety
```

Nicht zulässig:

```text
Strategy
→ direct order
```

## Tests

- registry entry missing
- disabled strategy
- incompatible regime
- conflicting strategies
- no suitable strategy
- restart
- config version mismatch
- deterministic signal replay

---

# PHASE 10 — Numeric Volatility Max-Age Decision Program

## Ziel

Erst nach ausreichender Evidence entscheiden, ob Numeric Max-Age Enforcement fachlich und sicherheitstechnisch sinnvoll ist.

## Aktueller Status

```text
WATCHDOG_ONLY=true
ENFORCEMENT=false
```

## Erforderliche Evidence

- age histogram
- market regime strata
- volatility strata
- actionability strata
- selected instrument strata
- data quality strata
- decision outcomes
- safety/risk outcomes
- simulated economic outcomes
- false-positive block analysis
- false-negative stale acceptance analysis
- session-to-session stability
- threshold sensitivity
- walk-forward analysis
- Monte Carlo / resampling
- stress scenarios

## Separate Ratifikation

Eine spätere Capability muss explizit definieren:

```text
threshold
reference_time
clock source
missing behavior
stale behavior
alpha behavior
exit behavior
risk behavior
safety behavior
grace period
recovery semantics
evidence
rollback
```

Bis dahin darf keine Implementierung `enforcement_enabled=true` setzen.

---

# PHASE 11 — Canonical Runtime Activation

## Ziel

Single-Future oder später Multi-Future Runtime aktivieren, weiterhin ohne Live-Orders.

## Voraussetzungen

- alle Pre-Activation Gates PASS
- Owner-GO
- clean repository state
- exact SHA binding
- authorization lifecycle valid
- confirm token über kanonischen sicheren Pfad
- evidence paths prepared
- rollback prepared
- Live/Testnet disabled
- rulesets unverändert, außer separater Merge-Transaktion

## Statusänderung

Nur dieser Schritt darf ändern:

```text
CANONICAL_RUNTIME_ENTRYPOINT_STATUS:
BOUND_NOT_ACTIVATED
→ ACTIVATED_NO_LIVE_ORDERS
```

Nicht zulässig:

```text
→ LIVE
```

---

# PHASE 12 — Testnet und Live als separate Programme

Testnet und Live sind ausdrücklich nicht Teil der vorherigen Capability-Closure.

Sie benötigen jeweils:

- separate Architektur
- separate Authorization
- separate Confirm-Token-Semantik
- separate Risk Limits
- separate Reconciliation
- separate Kill Switches
- separate Rollback-/Disable-Pfade
- separate Evidence
- separate Owner-GO
- separate Runbooks

Live darf erst begonnen werden, wenn:

- canonical runtime activation stabil
- paper economics valide
- reconciliation produktiv bewiesen
- restart recovery bewiesen
- multi-session evidence stabil
- no critical gaps
- no documentation/runtime drift
- operator controls getestet
- emergency disable getestet

---

# 7. Cursor-Arbeitsauftrag-Standard

Jede Capability soll Cursor als einzelner klarer Auftrag übergeben werden.

## Pflichtstruktur

```text
OWNER_GO=true
OPERATOR_AUTHORIZATION_EXPLICIT=true
CAPABILITY_ID=<id>
EXPECTED_ORIGIN_MAIN_SHA=<sha>
CORE_LOGIC_CHANGE_ALLOWED=false
LIVE_TRADING_ALLOWED=false
TESTNET_ALLOWED=false
NETWORK_SESSION_ALLOWED=false
AUTHORIZATION_CONSUMPTION_ALLOWED=false
RULESET_MUTATION_ALLOWED=false
NOTION_MUTATION_ALLOWED=<true|false>
```

## Pflichtanweisung für lokale Ausführung

```text
Arbeite ausschließlich im lokalen Repository über das echte lokale Terminal.
Verwende keine Cursor-Sandbox für Git-Operationen.
Prüfe vor jeder Mutation Repository Root, .git, Branch, HEAD, origin/main und Worktree.
Stoppe fail-closed bei jeder Abweichung.
```

## Pflicht-Output von Cursor

```text
STATUS
VERDICT
REVIEW_MODE
CAPABILITY_ID
OWNER_GO
EXPECTED_ORIGIN_MAIN_SHA
ACTUAL_ORIGIN_MAIN_SHA
ACTUAL_HEAD_SHA_BEFORE
ACTUAL_BRANCH_BEFORE
WORKTREE_CLEAN_BEFORE
UNTRACKED_EVIDENCE_PRESERVED
FILES_CHANGED
CORE_LOGIC_CHANGED
CONFIG_CHANGED
PRODUCTIVE_CALLER_ADDED
RUNTIME_REACHABLE
ACTIVATION_CHANGED
LIVE_PATH_CHANGED
TESTS_RUN
TESTS_PASS
EVIDENCE_CREATED
DOCS_UPDATED
NOTION_UPDATED
BRANCH_CREATED
COMMIT_SHA
PR_NUMBER
HARD_STOP
NEXT_SAFE_STEP
BASELINE_SHA_REVALIDATED
PRODUCTIVE_ENTRYPOINTS_ENUMERATED
CALL_GRAPH_BEFORE
CALL_GRAPH_AFTER
CONFIG_CONSUMER_TRACE
PERSISTENCE_OWNER
RESTART_SEMANTICS_PROVEN
FAILURE_INJECTION_RESULTS
LEGACY_AUTHORITY_CHECK
CONFIRM_TOKEN_PLAINTEXT_EXPOSED
```

---

# 8. PR- und Merge-Semantik

## 8.1 Capability-PR

Jeder PR muss eine ganze Capability oder einen klar abgeschlossenen, eigenständig beweisbaren Capability-Schritt enthalten.

Keine kosmetischen Mini-Slices ohne Closure-Wert.

## 8.2 PR-Beschreibung

Pflicht:

- Problem
- aktuelle Runtime-Wahrheit
- Zielzustand
- Call-Graph vorher/nachher
- Authority vorher/nachher
- Config
- Persistence
- Restart
- Failure semantics
- Safety
- Tests
- Evidence
- Core-Logic-Change
- Activation state
- Rollback
- Out of scope

## 8.3 Merge

Ruleset darf nur bei explizitem Owner-Merge-GO kurzzeitig deaktiviert und unmittelbar exakt wiederhergestellt werden.

Merge-Transaktion:

```text
snapshot ruleset
→ verify only blocker
→ temporarily disable
→ squash merge
→ restore exact ruleset
→ verify active
→ sync local main
→ verify HEAD=origin/main
→ verify worktree
```

Keine andere Repository- oder Runtime-Mutation während dieser Transaktion.

---

# 9. Dokumentationsregeln

## 9.1 Map of Truth

Eine Map of Truth darf nur zwei klar getrennte Bereiche enthalten:

```text
CURRENT RUNTIME TRUTH
TARGET ARCHITECTURE
```

Beide dürfen niemals sprachlich vermischt werden.

## 9.2 Verbotene missverständliche Aussagen

Nicht ohne Qualifikation verwenden:

- complete
- operational
- production-ready
- live-ready
- fully integrated
- autonomous
- active
- end-to-end

Beispiel korrekt:

```text
Offline integration complete; productive runtime remains BOUND_NOT_ACTIVATED.
```

## 9.3 Dashboard

Jede Dashboard-Dokumentation muss enthalten:

```text
AUTHORITY_EFFECT=NONE
READ_ONLY_CONSUMER=true
TRADING_INPUT=false
SSOT=false
```

## 9.4 Numeric Max-Age

Jede Volatility-Max-Age-Dokumentation muss enthalten:

```text
WATCHDOG_ONLY=true
RESEARCH_ONLY=true
ENFORCEMENT_ENABLED=false
ALPHA_MUTATION=false
RISK_MUTATION=false
SAFETY_MUTATION=false
```

---

# 10. Notion-Synchronisation

Notion ist Dokumentations- und Übersichtsfläche, nicht Runtime-SSOT.

Jede Notion-Seite muss anzeigen:

- repository SHA
- document class
- runtime state
- authority effect
- activation state
- evidence date
- stale marker, falls SHA nicht aktuell
- source file path

Notion darf keine neuere Wahrheit vortäuschen als der Repository-Stand.

---

# 11. Audit- und Drift-Prevention

Nach jeder dritten Capability oder jedem Activation-relevanten Merge muss ein erneuter Completeness Audit laufen.

## Audit-Fragen

- Welche Capabilities sind nur dokumentiert?
- Welche besitzen Code, aber keinen produktiven Caller?
- Welche sind gebunden, aber nicht erreichbar?
- Welche sind erreichbar, aber deaktiviert?
- Welche sind aktiv, aber ohne Restart-Beweis?
- Welche besitzen keine Failure Semantics?
- Welche besitzen keine Evidence?
- Welche Docs übertreiben?
- Welche Notion-Seiten sind stale?
- Welche Configs sind dead?
- Welche Defaults widersprechen dem SSOT?
- Welche Legacy-Komponenten besitzen potenzielle Parallel-Authority?
- Welche Komponenten wurden als fertig markiert, obwohl nur Unit Tests existieren?
- Welche Owner-Anforderungen wurden deferred, ohne Wiedervorlage?
- Welche Capabilities führen konkret zurück zur Handels-Runtime?
- Welche Arbeit erzeugt nur Infrastruktur ohne Trading-Path-Wert?

## Deferred Work Register

Kanonische Authority (Capability 0.4):

```text
docs/governance/deferred_work_recovery_register_v1.json
docs/governance/PEAK_TRADE_DEFERRED_WORK_RECOVERY_REGISTER_V1.md
```

Keine parallelen Register. Reminder-only Surfaces (z. B. `docs/planning/deferred/MULTI_FUTURE_ACTIVE_SET_ROTATION_REPLACEMENT_POLICY_V0_DEFERRED_REMINDER.md`) sind nicht Authority.

Jede deferred Capability benötigt mindestens:

```text
CAPABILITY_ID
TITLE
CLASSIFICATION
OWNER_REQUIREMENT
TRADING_PATH_VALUE
CURRENT_STATE
TARGET_STATE
DEFERRED_REASON
BLOCKING_DEPENDENCIES
DEPENDENCY_STATUS
AUTHORITY_OWNER
TARGET_PHASE
REVIEW_TRIGGER
REVIEW_DATE_OR_EVENT
EXPIRY_OR_REASSESSMENT_RULE
IMPLEMENTATION_AUTHORIZED
ACTIVATION_AUTHORIZED
CORE_LOGIC_CHANGE_ALLOWED
CURRENT_RUNTIME_EFFECT
EXPECTED_FUTURE_RUNTIME_EFFECT
SAFETY_INVARIANTS
SOURCE_REFERENCES
REPOSITORY_SHA
LAST_VERIFIED_AT
CURRENT_STATUS
NEXT_REQUIRED_DECISION
CLOSURE_CRITERIA
```

Ein Reminder-only Dokument ohne Review Trigger ist nicht ausreichend.

---

# 12. Priorisierte Capability-Liste

## Sofort

1. Canonical Runtime Truth Map
2. Historical/Target Docs Labeling
3. Config Truth Alignment (`max_open_positions=1`)
4. Productive Reconciliation Runtime Binding
5. Universe → Ranking → Single Selected Future Persistence
6. Single Selected Future Runtime Binding
7. Futures Accounting Runtime Wiring

## Danach

8. Canonical Runtime Pre-Activation Closure
9. Single-Future Shadow/Paper Evidence
10. Active-Set Rotation Replacement Policy V0
11. Multi-Future Runtime Implementation
12. Multi-Future Shadow/Paper Evidence
13. Strategy Registry Closure
14. Numeric Volatility Max-Age Decision Program
15. Canonical Runtime Activation ohne Live Orders

## Erst ganz am Ende

16. Testnet Execution
17. Live Exchange Execution

---

# 13. Definition of Done des Gesamtprogramms

Das Aufarbeitungsprogramm gilt erst dann als abgeschlossen, wenn:

```text
DOCUMENTATION_RUNTIME_DRIFT=false
DASHBOARD_AUTHORITY=false
UNIVERSE_TRADING_AUTHORITY_EXPLICIT=true
SINGLE_SELECTED_FUTURE_RUNTIME_CLOSED=true
RECONCILIATION_PRODUCTIVE=true
RESTART_RECOVERY_PROVEN=true
FUTURES_ACCOUNTING_BOUND=true
MASTER_V2_RUNTIME_REACHABLE=true
DOUBLE_PLAY_AUTHORITY_UNAMBIGUOUS=true
RISK_BOUND=true
SAFETY_BOUND=true
EXIT_PATH_PROVEN=true
EVIDENCE_VERIFIED=true
VOL_MAX_AGE_WATCHDOG_SEMANTICS_EXPLICIT=true
MULTI_FUTURE_POLICY_RATIFIED=true
MULTI_FUTURE_RUNTIME_TESTED=true
CANONICAL_RUNTIME_ACTIVATION_EXPLICIT=true
LIVE_FAIL_CLOSED=true
```

Live-Trading muss dabei weiterhin `false` sein, sofern kein separates Live-Programm vollständig ratifiziert und autorisiert wurde.

---

# 14. Erste konkrete Cursor-Umsetzung

Der erste Cursor-Auftrag nach Ablage dieses Runbooks soll keine Trading-Runtime verändern.

Er soll ausschließlich:

1. dieses Runbook im Repository ablegen,
2. bestehende Map-of-Truth-, Feature-State-, Runtime-Authority- und Runbook-Dokumente inventarisieren,
3. eine kanonische `PEAK_TRADE_CANONICAL_RUNTIME_TRUTH_MAP_V1.md` erstellen,
4. historische und Zielbild-Dokumente klassifizieren,
5. missverständliche Runtime-Claims korrigieren,
6. Dashboard als Consumer-only markieren,
7. Numeric Volatility Max-Age als Watchdog-only markieren,
8. `BOUND_NOT_ACTIVATED` sichtbar machen,
9. `MAX_POSITIONS=1` und `SINGLE_SELECTED_FUTURE` als aktuelle Phase-1-Semantik festhalten,
10. keine Runtime-, Config-, Auth-, Session-, Network-, Notion- oder Activation-Mutation durchführen.

Erst nach Review und Merge dieser Wahrheitsbasis beginnt die technische Capability-Aufarbeitung.

---

# 14A. Forensischer Soll-/Ist-Abgleich gegen Cursor-Audit

## 14A.1 Bestätigte Übereinstimmungen

| Audit-Befund | Runbook-Status | Ergebnis |
|---|---|---|
| Canonical Runtime `BOUND_NOT_ACTIVATED` | Header, Phasen 4/11 | konsistent |
| Live fail-closed | Safety-Invarianten, Phase 12 | konsistent |
| Dashboard Consumer-only | Authority-Modell, Docs-Regeln | konsistent |
| Numeric Max-Age non-enforcing | Authority-Modell, Phase 10 | konsistent |
| Phase-1 `MAX_POSITIONS=1` | Header, Safety, Phase 2 | konsistent |
| Phase-1 `SINGLE_SELECTED_FUTURE` | Header, Phase 2 | konsistent |
| Top20→Top5 nicht produktiv | Phase 6/7 und neue Begriffsabgrenzung | präzisiert |
| Universe Ranking keine Trading Authority | Phase 2 | konsistent |
| Reconciliation nicht produktiv gebunden | Phase 1 | adressiert |
| Futures Accounting unwired | Phase 3 | adressiert |
| Runtime Activation separat | Phase 4/11 | konsistent |
| Strategy Registry unwired | Phase 9 | adressiert |
| Docs können Zielbild überhöhen | Phase 0/9 | adressiert |

## 14A.2 Geschlossene Lücken dieser Revision

1. Audit-Snapshot ist jetzt explizit von zeitloser Runtime-Wahrheit getrennt.
2. Intentional Safety Barriers werden nicht mehr als Implementierungs-P0 missverstanden.
3. Rotation Policy wird sofort organisatorisch reaktiviert, aber technisch weiterhin dependency-safe sequenziert.
4. Top-20, Single Selected Future und Top-N/Top-5 besitzen eindeutige Semantik.
5. Confirm-Token-Ablauf entlastet den Owner ohne Klartext-Leak oder Gate-Umgehung.
6. `max_open_positions=5` wird über Consumer-Trace und Effective-Config-Test behandelt, nicht durch blindes Search/Replace.
7. Audit-genannte Codepfade müssen am aktuellen SHA verifiziert werden.
8. Closure-Output verlangt jetzt Call-Graph-, Config-Consumer-, Restart-, Failure- und Legacy-Authority-Belege.
9. `ECONOMIC_VALIDITY_OFFLINE_GATE_PASS=false` wird als expliziter Aktivierungszustand geführt.
10. Die Reihenfolge trennt sofortige Roadmap-Recovery von späterer Multi-Future-Implementierung.

## 14A.3 Nicht aus dem Audit beweisbare Punkte

Die folgenden Aussagen dürfen nicht allein aus dem Cursor-Text als endgültig übernommen werden und benötigen Repository-/Evidence-Verifikation am aktuellen SHA:

- exakte Zahl und Klasse aller 54 Capabilities,
- tatsächliche Runtime-Wirksamkeit einzelner Config-Defaults,
- exakter Pfad und Eignung aller als wiederverwendbar genannten Module,
- produktive Reichweite von Scheduler-/Legacy-Jobs,
- Vollständigkeit der Restart-Beweise,
- Aktualität externer Notion-Seiten,
- ob einzelne `partial`, `gated`, `productive active` Klassifikationen intern widerspruchsfrei sind.

Bei Unklarheit gilt `INSUFFICIENT_EVIDENCE`, nicht Vermutung.

---

# 15. Kanonischer Schlussgrundsatz

Peak_Trade arbeitet nicht von Infrastruktur weg, sondern immer zurück zum sicheren Handels-Pfad.

Jede Capability muss daher beantworten:

```text
Welchen konkreten, nachweisbaren Schritt schließt diese Arbeit zwischen
Market Data und sicherem, reconciled, evidenzbasiertem Trading?
```

Kann diese Frage nicht klar beantwortet werden, ist die Arbeit entweder:

- nicht ausreichend spezifiziert,
- nicht priorisiert,
- nur dokumentarisch,
- ein technischer Debt-Schritt,
- oder nicht Teil des aktuellen Trading-Pfads.

Keine Capability darf künftig allein deshalb als abgeschlossen gelten, weil Code, Tests oder Dokumentation existieren.

Verbindlich ist:

```text
Implemented
≠ Bound
≠ Reachable
≠ Activated
≠ Safe
≠ Proven
≠ Closed
```
