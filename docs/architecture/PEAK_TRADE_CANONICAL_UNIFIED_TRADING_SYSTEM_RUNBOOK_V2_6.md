# Peak Trade — Zeitoptimiertes Runbook zum vollautonomen Futures-Trading-System
---
docs_token: DOCS_TOKEN_PEAK_TRADE_CANONICAL_UNIFIED_TRADING_SYSTEM_RUNBOOK_V2_6
STATUS: CANONICAL_STRATEGIC_TARGET_AND_IMPLEMENTATION_RUNBOOK
VERSION: 2.6
FUTURES_ONLY: true
BITCOIN_DIRECTION_ALLOWED: false
CURRENT_RUNTIME_AUTHORIZATION: false
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
scope: docs-only, strategic-target, non-authorizing
---

> **Repo-Integrationshinweis (2026-06-28):** Dieses Dokument ist das **kanonische strategische Ziel- und Implementierungsrunbook** für genau **ein** Peak-Trade-Futures-Handelssystem mit zwei intern getrennten Authority-Domänen: **TRADING_DECISION_CORE** und **SAFETY_EXECUTION_RUNTIME_CORE**. Es beschreibt ein **ratifiziertes Zielbild** und Implementierungsleitlinien — **nicht** den vollständig implementierten Ist-Zustand. Reale Code-Owner, Baseline-Bindungen und offene Implementierungsgaps sind durch separates read-only Audit (`canonical_peak_trade_trading_system_baseline_and_owner_binding_audit_v1`) zu binden. **Keine** Live-, Order-, Scheduler-, Shadow-, Paper- oder Testnet-Freigabe durch alleinige Lektüre dieses Dokuments.


**Version:** 2.6  
**Status:** Strategisches Ziel- und Implementierungsrunbook  
**Ziel:** Vollautonomer Futures-Betrieb mit stufenweiser, evidenzbasierter Freischaltung  
**Grundsatz:** Schnell zur belastbaren Autonomie, ohne Safety-, Authority-, Handoff-, Trust-Root-, Execution-, Reconciliation-, Trading-Logic- oder Reproduzierbarkeitslücken  
**Keine Anlageberatung.**

---

# 0. Zielbild

Dieses Runbook beschreibt den schnellsten belastbaren Weg vom heutigen Peak-Trade-Stand zu einem **vollautonomen Futures-Trading-System**.

„Vollautonom“ bedeutet im Endzustand:

- Marktbeobachtung, Datenerfassung und Evidence-Erzeugung laufen selbstständig.
- Backtests, Robustness-Prüfungen, Vergleiche, Learning, Completion und Promotion laufen automatisch.
- Versionierte Strategie-, Modell- und Parameter-Artefakte werden automatisch gebaut.
- Runtime Eligibility, Deployment, Aktivierung, Scheduler, Orderausführung, Überwachung und Feedback laufen automatisch.
- Orders, Fills, Positionen und Venue-Zustand werden kontinuierlich reconciled.
- Das System kann sich innerhalb ratifizierter Grenzen selbst verbessern.
- Jede Entscheidung ist versioniert, reproduzierbar, rollback- und recovery-fähig sowie auditierbar.
- Safety-, Risk-, Budget- und Authority-Grenzen bleiben fail-closed.
- Live-Trading wird erst nach Shadow, Paper, Testnet und Canary/Micro-Live freigeschaltet.
- Policy-, Risk- und Capital-Limits dürfen nicht autonom erweitert werden.

Das Ziel ist **nicht** eine dauerhaft manuelle Architektur. Die Zwischenstufen sind kontrollierte Freischaltphasen auf dem Weg zum autonomen Normalbetrieb.

---

# 1. Zeit- und Umsetzungsziel

## 1.1 Zielkorridor

Unter der Annahme, dass vorhandene Peak-Trade-Komponenten konsequent wiederverwendet werden und keine grundlegende Runtime-Neuentwicklung notwendig wird:

| Zielzustand | Realistischer Umsetzungskorridor |
|---|---:|
| Vollständige Offline-Promotion-Kette | 3–5 Wochen |
| Autonome Shadow-/Paper-Kette | 6–9 Wochen |
| Autonome Testnet-Kette mit Reconciliation | 8–12 Wochen |
| Micro-Live/Canary technisch bereit | 12–16 Wochen |
| Vollautonomer Produktionsbetrieb | abhängig von nachgewiesener Runtime-Evidence, nicht nur von Entwicklungszeit |

Diese Korridore sind keine Garantie. Sie sind ein zeitoptimierter Plan für einen bestehenden, modularen Codebestand.

## 1.2 Was bewusst vermieden wird

Um die Umsetzung nicht unnötig zu verlängern:

- keine neue Parallelarchitektur,
- kein kompletter Rewrite,
- kein unnötiges Microservice-Splitting,
- keine neue Datenplattform, falls bestehende Artefakt- und Registry-Pfade genügen,
- keine AI-Komponente für deterministisch lösbare Aufgaben,
- keine Vorabimplementierung aller denkbaren Venues und Instrumente,
- keine allgemeine Multi-Asset-Plattform,
- keine vollständige Perfektion vor Shadow/Testnet,
- keine unnötigen Einzel-PRs bei logisch kohärenten, fokussierten Bundles.

## 1.3 Beschleunigungsprinzip

Jede Implementierungsstufe wird in zwei Schichten gebaut:

1. **Minimum Safe Slice**
   - nur notwendige Contracts, Producer, Validatoren und Tests,
   - vorhandene Owner und Loader wiederverwenden,
   - keine Runtime-Side-Effects.

2. **Operational Hardening**
   - zusätzliche Failure Modes,
   - Stress- und Recovery-Tests,
   - Kosten-, Performance- und Resilience-Optimierung.

So wird früh eine geschlossene Kette erreicht, ohne Safety-Schulden in die Live-Stufe mitzunehmen.

---

# 2. Verbindliche Systemgrenzen

```text
FUTURES_ONLY=true
BITCOIN_DIRECTION_ALLOWED=false
SPOT_ALLOWED=false
SYNTHETIC_SPOT_ALLOWED=false

LIVE_AUTHORIZED=false
READY_FOR_OPERATOR_ARMING=false
ORDERS_ALLOWED=false
SCHEDULER_RUNTIME_ALLOWED=false

PEAK_TRADE_CANONICAL_TRADING_SYSTEM=true
PEAK_TRADE_CANONICAL_TRADING_SYSTEM_SINGLE_SSOT=true
PEAK_TRADE_PARALLEL_TRADING_SYSTEM_ALLOWED=false
TRADING_DECISION_CORE_CANONICAL=true
SAFETY_EXECUTION_RUNTIME_CORE_CANONICAL=true
SAFETY_EXECUTION_RUNTIME_CORE_INDEPENDENT_AUTHORITY=true
SAFETY_EXECUTION_RUNTIME_CORE_EXTERNAL_SYSTEM=false

MASTER_V2_ROLE=COMPOSITION_AND_ORCHESTRATION_OWNER
DOUBLE_PLAY_ROLE=COORDINATION_AND_CONFLICT_OWNER
BULL_ROLE=BULL_SEMANTIC_OWNER
BEAR_ROLE=BEAR_SEMANTIC_OWNER
DYNAMIC_SCOPE_ROLE=DYNAMIC_SELECTION_OWNER
RISK_ROLE=RISK_DECISION_OWNER
SIZING_ROLE=POSITION_SIZING_OWNER
SCOPE_CAPITAL_ROLE=CAPITAL_ENVELOPE_OWNER
KILL_SWITCH_ROLE=EMERGENCY_AUTHORITY_REVOCATION_OWNER
RECONCILIATION_ROLE=RUNTIME_STATE_AUTHORITY_OWNER
KILL_SWITCH_FAIL_CLOSED=true
KILL_SWITCH_BYPASS_ALLOWED=false
KILL_SWITCH_RESET_BY_STRATEGY_ALLOWED=false
KILL_SWITCH_RESET_BY_AI_ALLOWED=false
KILL_SWITCH_RESET_BY_SCHEDULER_ALLOWED=false
KILL_SWITCH_STATE_PERSISTS_ACROSS_RESTART=true
KILL_SWITCH_TRIP_REVOKES_TRADING_AUTHORITY=true

PROMOTION_MAY_REPLACE_TRADING_SEMANTICS=false
AI_MAY_REPLACE_TRADING_SEMANTICS=false
RUNTIME_MAY_BYPASS_MASTER_V2=false
ORDER_INTENT_MAY_BYPASS_CANONICAL_TRADING_CHAIN=false
PARALLEL_TRADING_LOGIC_SSOT_ALLOWED=false
```

Diese Flags bleiben bis zu einem separat autorisierten Freischaltschritt fail-closed.

Für eine spätere Micro-Live-Stufe gelten zunächst maximal:

```text
TOTAL_LIMIT_USD=500
ORDER_LIMIT_USD=25
DAILY_LOSS_LIMIT_USD=25
MAX_POSITIONS=1
```

Das autonome System darf diese Limits nicht selbst erhöhen.

---

# 3. Architekturprinzipien

## 3.1 Ein kanonischer fachlicher Kreislauf

```text
Market + Runtime Evidence
→ Learning Input
→ Backtest / Experiment / Risk Analysis
→ Research Validity
→ Comparison
→ Checkpoint
→ Completion Evidence
→ Promotion Input
→ Promotion Eligibility
→ Promotion Policy Decision
→ Versioned Strategy / Model / Parameter Artifact
→ Runtime Eligibility
→ Deploy Inactive
→ Activation Authority
→ Scheduler
→ Master V2
→ Double Play Coordination
→ Bull/Bear Evaluation
→ Existing Conflict and Composition Logic
→ Dynamic Scope
→ Existing Risk and Sizing Logic
→ Order Intent
→ Independent Safety Kernel
→ Execution
→ Runtime Observation
→ Reconciliation
→ Durable Feedback Evidence
→ Learning Input
```

Es darf langfristig keine parallelen fachlichen Learning-, Promotion- oder Runtime-Authority-Pfade geben.

Ein kanonischer Pfad bedeutet jedoch nicht, dass ein einziger Prozess alle Aufgaben übernimmt. Kritische Safety- und Reconciliation-Funktionen bleiben unabhängig.

## 3.2 Ein kanonisches Peak-Trade-Handelssystem

Die gesamte Peak-Trade-Handels-, Ausführungs- und Sicherheitslogik wird verbindlich als **ein einziges kanonisches Peak-Trade-Handelssystem** behandelt. Zu diesem einen System gehören gemeinsam:

- Master V2,
- Bull,
- Bear,
- Double Play,
- Dynamic Scope,
- Risk,
- Sizing,
- Scope Capital,
- Canonical Order Intent,
- Pre-Trade Safety,
- Execution Permission,
- Adapter Submission,
- KillSwitch,
- Authority und Revocation,
- Reconciliation,
- Recovery und Runtime State Authority.

Keine dieser Komponenten bildet allein ein vollständiges oder paralleles Trading-System. Das kanonische Peak-Trade-Handelssystem besitzt zwei intern getrennte, aber gemeinsam zur selben Single-SSOT gehörende Authority-Domänen:

```text
CANONICAL_PEAK_TRADE_TRADING_SYSTEM
├── TRADING_DECISION_CORE
└── SAFETY_EXECUTION_RUNTIME_CORE
```

Der **Trading Decision Core** erzeugt fachliche Handelsentscheidungen. Der **Safety, Execution & Runtime Authority Core** darf diese Entscheidungen begrenzen, ablehnen, widerrufen, suspendieren und mit dem tatsächlichen Venue-Zustand reconciliieren. Beide sind integrale Bestandteile desselben kanonischen Handelssystems.

Innerhalb des einen Systems besitzt jede Komponente exklusiv ihre definierte Teilsemantik:

- Master V2: Composition und Runtime-Orchestrierung,
- Double Play: Koordination und Konfliktauflösung,
- Bull: Bull-Semantik,
- Bear: Bear-Semantik,
- Dynamic Scope: dynamische Auswahl innerhalb der erlaubten Hülle,
- Risk: Risk-Entscheidung,
- Sizing: Positionsdimensionierung,
- Scope Capital: Kapitalhülle.

Neue Learning-, Promotion-, Deployment-, AI-, Scheduler-, Runtime- oder Execution-Komponenten dürfen dieses Trading Core ausschließlich innerhalb explizit ratifizierter Grenzen konfigurieren, versionieren und aufrufen. Sie dürfen weder das gesamte Trading Core noch einzelne Teilsemantiken stillschweigend ersetzen, duplizieren, umgehen oder semantisch neu interpretieren.

Der KillSwitch, die Authority-/Revocation-Logik, der unabhängige Pre-Trade Safety Kernel, die Execution Permission, die Adapter-Durchsetzung und die Reconciliation gehören vollständig zum selben kanonischen Peak-Trade-Handelssystem. Sie bilden darin den **Safety, Execution & Runtime Authority Core**. Dieser Core ist kein externes oder paralleles System, besitzt aber eine unabhängige und gegenüber dem Trading Decision Core übergeordnete Safety- und Revocation-Authority.

Verbindliche Authority-Richtung:

```text
Trading Decision
→ darf von Safety begrenzt oder abgelehnt werden

Safety / Revocation / Reconciliation
→ darf nicht von Trading Decision, AI, Promotion, Scheduler oder Adapter überschrieben werden
```

### 3.2.1 Kanonizitäts-Hierarchie und geschützte Modul-Owner

```text
PEAK_TRADE_CANONICAL_TRADING_SYSTEM=true
PEAK_TRADE_CANONICAL_TRADING_SYSTEM_SINGLE_SSOT=true
PEAK_TRADE_PARALLEL_TRADING_SYSTEM_ALLOWED=false
TRADING_DECISION_CORE_CANONICAL=true
SAFETY_EXECUTION_RUNTIME_CORE_CANONICAL=true
SAFETY_EXECUTION_RUNTIME_CORE_INDEPENDENT_AUTHORITY=true

MASTER_V2_ROLE=COMPOSITION_AND_ORCHESTRATION_OWNER
DOUBLE_PLAY_ROLE=COORDINATION_AND_CONFLICT_OWNER
BULL_ROLE=BULL_SEMANTIC_OWNER
BEAR_ROLE=BEAR_SEMANTIC_OWNER
DYNAMIC_SCOPE_ROLE=DYNAMIC_SELECTION_OWNER
RISK_ROLE=RISK_DECISION_OWNER
SIZING_ROLE=POSITION_SIZING_OWNER
SCOPE_CAPITAL_ROLE=CAPITAL_ENVELOPE_OWNER

KILL_SWITCH_ROLE=EMERGENCY_AUTHORITY_REVOCATION_OWNER
RECONCILIATION_ROLE=RUNTIME_STATE_AUTHORITY_OWNER
```

Verbindliche Bedeutung:

- **Peak Trade** besitzt genau ein kanonisches Handelssystem.
- Dieses eine Handelssystem ist die einzige Trading-, Execution-, Safety- und Runtime-SSOT.
- Der **Trading Decision Core** und der **Safety, Execution & Runtime Authority Core** sind interne Domänen desselben Systems und keine separaten Handelssysteme.
- **Master V2, Double Play, Bull, Bear, Dynamic Scope, Risk, Sizing und Scope Capital** sind keine separaten Trading-Systeme, sondern geschützte Modul-Owner innerhalb dieses einen Trading Core.
- **Master V2** besitzt Composition und Runtime-Orchestrierung, aber nicht die Teilsemantiken der anderen Module.
- **Double Play** besitzt Koordination und Konfliktauflösung, aber nicht Bull-, Bear-, Scope-, Risk- oder Sizing-Semantik.
- **Bull und Bear** bleiben getrennte, transparente und regressionsgetestete Semantik-Owner.
- **Dynamic Scope** bleibt fachlicher Auswahlmechanismus innerhalb der äußeren Authority-, Venue-, Instrument-, Risk- und Capital-Grenzen.
- **Risk, Sizing und Scope Capital** bleiben exklusive Owner ihrer jeweiligen Regeln.
- **KillSwitch und Reconciliation** gehören vollständig zum kanonischen Peak-Trade-Handelssystem, besitzen darin jedoch unabhängige Safety-, Revocation- und Runtime-State-Authority außerhalb der Änderungsgewalt des Trading Decision Core.

### 3.2.2 Single-SSOT-, No-Bypass- und No-Replacement-Invarianten

```text
PROMOTION_MAY_REPLACE_TRADING_SEMANTICS=false
AI_MAY_REPLACE_TRADING_SEMANTICS=false
RUNTIME_ORCHESTRATOR_MAY_BYPASS_MASTER_V2=false
DOUBLE_PLAY_BYPASS_ALLOWED=false
BULL_BEAR_BYPASS_ALLOWED=false
DYNAMIC_SCOPE_BYPASS_ALLOWED=false
RISK_SIZING_OWNER_BYPASS_ALLOWED=false
ORDER_INTENT_MAY_BYPASS_CANONICAL_TRADING_CHAIN=false
TRADING_CORE_SINGLE_SSOT=true
PARALLEL_TRADING_LOGIC_SSOT_ALLOWED=false
SEPARATE_BULL_TRADING_SYSTEM_ALLOWED=false
SEPARATE_BEAR_TRADING_SYSTEM_ALLOWED=false
SEPARATE_DOUBLE_PLAY_TRADING_SYSTEM_ALLOWED=false
SEPARATE_DYNAMIC_SCOPE_TRADING_SYSTEM_ALLOWED=false
IMPLICIT_TRADING_SEMANTIC_MIGRATION_ALLOWED=false

MASTER_V2_STANDALONE_TRADING_SYSTEM_ALLOWED=false
BULL_STANDALONE_TRADING_SYSTEM_ALLOWED=false
BEAR_STANDALONE_TRADING_SYSTEM_ALLOWED=false
DOUBLE_PLAY_STANDALONE_TRADING_SYSTEM_ALLOWED=false
DYNAMIC_SCOPE_STANDALONE_TRADING_SYSTEM_ALLOWED=false
KILL_SWITCH_PARALLEL_SYSTEM_ALLOWED=false
RECONCILIATION_PARALLEL_SYSTEM_ALLOWED=false
SAFETY_EXECUTION_RUNTIME_CORE_EXTERNAL_SYSTEM=false
```

Jeder Consumer, Loader, Orchestrator und Adapter muss fail-closed prüfen, dass ein Order Intent ausschließlich aus der kanonischen Kette stammt. Ein technisch valides Artefakt oder Signal ist nicht ausführbar, wenn seine Lineage Master V2, Double Play, Bull/Bear, Dynamic Scope oder die kanonischen Risk-/Sizing-Owner umgeht.

Zusätzlich gilt: Ein Modul darf nicht als eigenständiges Trading-System deployt, promoted oder aktiviert werden. Promotions- und Runtime-Artefakte müssen immer die Compatibility des vollständigen Trading Core nachweisen; partielle Freigaben einzelner Trading-Core-Module sind unzulässig.

### 3.2.3 Kanonische Gesamt-Handels-, Safety- und Runtime-Kette

```text
Market Context
→ Master V2 Composition
→ Bull Evaluation
→ Bear Evaluation
→ Double Play Resolution
→ Dynamic Scope Selection
→ Risk Decision
→ Sizing Decision
→ Scope Capital Decision
→ Canonical Order Intent
→ Independent Pre-Trade Safety
→ KillSwitch and Authority Validation
→ Single-Use Execution Permission
→ Adapter Submission
→ Venue
→ Reconciliation
→ Runtime State Authority
→ Durable Feedback Evidence
```

Diese gesamte Kette bildet das eine kanonische Peak-Trade-Handelssystem. Kein Learning-, Promotion-, AI-, Scheduler-, Runtime- oder Adapter-Modul darf direkt einen ausführbaren Order Intent erzeugen oder eine Stufe der Kette umgehen. Ebenso darf kein einzelnes Modul außerhalb dieser Kette allein als Trading-System deployt, promoted oder aktiviert werden.

Der Safety, Execution & Runtime Authority Core bleibt technisch unabhängig durchsetzbar. Seine Unabhängigkeit dient der internen Gewaltenteilung innerhalb desselben Handelssystems und begründet kein zweites System.

### 3.2.4 Abgrenzung von Dynamic Scope und Authority Scope

Dynamic Scope ist nicht identisch mit Runtime Authority.

```text
Constitutional / Authority Scope
→ begrenzt, was technisch und rechtlich zulässig ist

Dynamic Scope
→ wählt innerhalb dieser Grenzen fachlich zulässige Märkte, Instrumente, Strategien oder Kapitalbereiche

Master V2 / Double Play / Bull-Bear
→ erzeugen innerhalb des gültigen Dynamic Scope Handelsentscheidungen

Independent Safety Kernel
→ validiert jede konkrete Ausführung erneut
```

Dynamic Scope darf niemals:

- Venue-, Account-, Assetklassen- oder Environment-Authority erweitern,
- Futures-only verlassen,
- Capital-, Daily-Loss-, Leverage- oder Position-Limits erhöhen,
- Risk Policy, KillSwitch oder Reconciliation überschreiben,
- nicht ratifizierte Instrumente freischalten.

Statische `venue_scope`-, `instrument_scope`- oder Authority-Felder dürfen Dynamic Scope nicht ersetzen. Sie bilden die äußere zulässige Hülle, innerhalb der Dynamic Scope arbeitet.

### 3.2.5 Zulässige Änderungen und Change Classes

| Änderung | Change Class | Behandlung |
|---|---|---|
| Parameter-Rekalibrierung innerhalb bestehender Grenzen ohne Semantikänderung | A | später autonom möglich |
| Modelltausch bei identischer Schnittstelle, identischer fachlicher Semantik und nachgewiesener Kompatibilität | B | nach strengen Gates autonom möglich |
| Änderung einer Bull- oder Bear-Entscheidungsregel | C | zunächst externe Ratifikation |
| Änderung der Double-Play-Koordination oder Konfliktauflösung | C | zunächst externe Ratifikation |
| Änderung der Dynamic-Scope-Auswahlsemantik | C | zunächst externe Ratifikation |
| Ersatz oder Umgehung von Master V2 | D | externe Ratifikation zwingend |
| Ersatz eines Risk-, Sizing-, Scope-Capital-, KillSwitch- oder Reconciliation-Owners | D | externe Ratifikation zwingend |
| Einführung einer parallelen Trading-Logic-SSOT | D | unzulässig, sofern nicht ausdrücklich als Migration ratifiziert |

Eine Änderung ist nach ihrer **tatsächlichen Semantik**, nicht nach Dateiname, Diff-Größe oder deklarierter Change Class zu klassifizieren. Bei Unsicherheit gilt fail-closed die höhere Klasse.

### 3.2.6 Trading-Logic Compatibility Evidence

Jedes promotions- oder runtimefähige Strategie-, Modell- oder Parameterartefakt muss ein unveränderliches Compatibility-Artefakt referenzieren:

```text
trading_logic_compatibility_evidence_v1
```

Pflichtfelder:

```text
master_v2_owner_ref
master_v2_contract_digest
double_play_owner_ref
double_play_contract_digest
bull_component_ref
bear_component_ref
bull_bear_semantic_digest
dynamic_scope_owner_ref
dynamic_scope_policy_digest
risk_owner_ref
sizing_owner_ref
scope_capital_owner_ref
kill_switch_owner_ref
kill_switch_contract_digest
kill_switch_policy_digest
kill_switch_state_machine_digest
kill_switch_baseline_ref
kill_switch_independence_check_passed
kill_switch_bypass_check_passed
kill_switch_reset_authority_check_passed
semantic_diff
change_class
bypass_check_passed
parallel_ssot_check_passed
compatibility_test_bundle_ref
```

Fail-closed gilt bei:

- fehlender Owner- oder Digest-Bindung,
- nicht erklärtem semantischem Diff,
- unerlaubter Change Class,
- Bypass der kanonischen Kette,
- zweiter Trading-Logic-SSOT,
- nicht bestandenen Regression-, Replay- oder Compatibility-Tests.

### 3.2.7 Regression- und Contract-Tests

Vor Promotion, Runtime Eligibility und jeder Aktivierung sind mindestens nachzuweisen:

- Master-V2-Contract- und Routing-Tests,
- Double-Play-Kompositions- und Konflikttests,
- getrennte Bull- und Bear-Signaltests,
- Bull/Bear-Regimewechsel- und Grenzfalltests,
- Dynamic-Scope-Allow/Deny- und Boundary-Tests,
- Risk-/Sizing-/Scope-Capital-Owner-Binding-Tests,
- No-Bypass-Tests für direkte Signal- oder Order-Intent-Pfade,
- Golden-Master- oder Replay-Vergleich gegen die ratifizierte Baseline,
- Negative Tests für manipulierte Owner-Refs, Digests und Lineage,
- KillSwitch-Owner-, Contract-, Policy- und State-Machine-Digest-Binding,
- KillSwitch-Trip-, Persistenz-, Restart- und Revocation-Tests,
- No-Bypass-Tests gegen Strategy, AI, Promotion, Scheduler, Runtime und Adapter,
- Negative Tests gegen unautorisierte Reset-, Disarm- und State-Rewrite-Versuche,
- Nachweis, dass KillSwitch und Reconciliation unabhängig wirksam bleiben.

Eine statistisch bessere Performance allein erlaubt keine Semantikänderung und ersetzt keinen Kompatibilitätsnachweis.

## 3.2.8 Kanonische Trading-Core-Ports und eindeutige Reihenfolge

Die kanonische Trading-Core-Kette wird nicht nur als grobe Modulfolge, sondern als Folge expliziter, versionierter Ports definiert. Jede Kante besitzt genau einen Input- und Output-Contract sowie einen eindeutigen fachlichen Owner.

```text
MarketContext
→ MasterV2CompositionRequest
→ BullEvaluation + BearEvaluation
→ DoublePlayResolution
→ DynamicScopeSelection
→ RiskDecision
→ SizingDecision
→ CapitalEnvelopeDecision
→ CanonicalOrderIntent
```

Falls die bestehende Implementierung eine abweichende Reihenfolge besitzt, muss der Baseline-Audit diese reale Reihenfolge ratifizieren und als einzige zulässige Kette registrieren. Nicht zulässig sind mehrdeutige Begriffe oder zusätzliche, ownerlose Zwischenstufen wie eine zweite implizite Conflict- oder Composition-Logik.

Für jeden Port gelten mindestens:

```text
contract_name
contract_version
producer_owner_ref
consumer_owner_ref
input_digest
output_digest
implementation_digest
policy_digest
correlation_id
trading_epoch
```

### Negative Modul-Capabilities

Jeder Modul-Owner erhält neben seinen erlaubten Aufgaben ausdrücklich verbotene Fähigkeiten.

```text
MASTER_V2_MAY_ORCHESTRATE=true
MASTER_V2_MAY_OVERRIDE_BULL_BEAR_SEMANTICS=false
MASTER_V2_MAY_OVERRIDE_DOUBLE_PLAY_RESOLUTION=false
MASTER_V2_MAY_OVERRIDE_RISK=false
MASTER_V2_MAY_BYPASS_DYNAMIC_SCOPE=false

DOUBLE_PLAY_MAY_RESOLVE_CONFLICTS=true
DOUBLE_PLAY_MAY_REWRITE_BULL_SEMANTICS=false
DOUBLE_PLAY_MAY_REWRITE_BEAR_SEMANTICS=false
DOUBLE_PLAY_MAY_OVERRIDE_RISK=false

DYNAMIC_SCOPE_MAY_SELECT_WITHIN_AUTHORITY=true
DYNAMIC_SCOPE_MAY_CHANGE_AUTHORITY=false
DYNAMIC_SCOPE_MAY_CHANGE_RISK_LIMITS=false
DYNAMIC_SCOPE_MAY_CHANGE_POSITION_SIZE=false
DYNAMIC_SCOPE_MAY_GENERATE_EXECUTABLE_ORDER=false

RISK_MAY_ACCEPT_OR_REJECT=true
RISK_MAY_EXPAND_CONSTITUTIONAL_LIMITS=false
SIZING_MAY_SIZE_WITHIN_APPROVED_ENVELOPE=true
SIZING_MAY_INCREASE_CAPITAL_ENVELOPE=false
```

## 3.2.9 Decision-Attestation-Chain

Deklarative Owner-Referenzen allein reichen nicht als Nachweis, dass die kanonische Handelslogik tatsächlich ausgeführt wurde. Deshalb erzeugt jeder Trading-Core-Owner eine unveränderliche Decision Attestation:

```text
module_decision_attestation_v1
```

Pflichtfelder:

```text
attestation_id
module_owner_ref
module_contract_digest
implementation_digest
input_digest
output_digest
decision_code
decision_trace_digest
policy_digest
parent_attestation_refs
correlation_id
session_id
trading_epoch
created_at
manifest_digest
```

Der finale `CanonicalOrderIntent` bindet mindestens:

```text
master_v2_attestation_ref
bull_attestation_ref
bear_attestation_ref
double_play_attestation_ref
dynamic_scope_attestation_ref
risk_attestation_ref
sizing_attestation_ref
scope_capital_attestation_ref
```

Ein Order Intent ist ungültig, wenn:

- eine erforderliche Attestation fehlt,
- Input- und Output-Digests keine geschlossene Kette bilden,
- eine Attestation aus einer anderen Session oder Trading Epoch stammt,
- eine veraltete Contract-, Policy- oder Implementation-Version verwendet wurde,
- ein Modul zwar referenziert, aber nachweislich nicht ausgeführt wurde,
- die Attestation Chain eine zusätzliche oder parallele Trading-Logic-SSOT enthält.

## 3.2.10 Maschinenprüfbare Semantic-Diff-Evidence

Die deklarierte Change Class wird nicht ungeprüft übernommen. Jede Änderung am Trading Core oder an promotionsfähigen Konfigurationen erzeugt mehrschichtige Semantic-Diff-Evidence:

```text
trading_logic_semantic_diff_evidence_v1
```

Pflichtbestandteile:

```text
declared_semantic_diff
structural_contract_diff
configuration_domain_diff
decision_trace_diff
golden_replay_diff
boundary_behavior_diff
risk_output_diff
order_intent_diff
```

Eine Änderung ist mindestens Change Class C, wenn bei identischen Inputs eine relevante Änderung entsteht in:

```text
bull_decision
bear_decision
double_play_resolution
dynamic_scope_selection
risk_accept_reject
sizing_output
capital_envelope
canonical_order_intent
```

Performanceverbesserung, kleiner Diff oder unveränderte Schnittstelle reichen nicht aus, um eine semantische Änderung als Klasse A oder B zu behandeln.

## 3.2.11 Dynamic-Scope-Stabilität

Dynamic Scope darf innerhalb der Authority-Hülle dynamisch wählen, aber keine instabile Scope-Fluktuation erzeugen.

```text
minimum_scope_hold_time
scope_change_cooldown
maximum_scope_changes_per_session
scope_change_requires_reconciliation_clean=true
scope_change_requires_no_unknown_outcome=true
scope_change_invalidates_pending_intents=true
scope_change_requires_new_market_snapshot=true
```

Jeder Scope-Wechsel erzeugt ein manifestiertes Scope-Change-Event. Nicht übertragene Intents der alten Auswahl werden invalidiert. Bereits übertragene oder möglicherweise übertragene Orders gehen in Reconciliation und dürfen nicht durch einen Scope-Wechsel logisch vergessen werden.

## 3.3 Evidence ist nicht Authority

Evidence beschreibt Fakten.

Authority erlaubt Handlungen.

| Ebene | Bedeutung |
|---|---|
| LEVEL_1 | Roh-, Analyse- und Research-Evidence |
| LEVEL_2 | Checkpoint, nicht autorisierend |
| LEVEL_3 | Completion Governance |
| LEVEL_4 | Promotion Authority |
| LEVEL_5 | Deployment-/Runtime Authority |

Zusätzlich werden Aktionen über explizite Capabilities begrenzt:

```text
CAN_PRODUCE_RESEARCH
CAN_CREATE_CANDIDATE
CAN_PROMOTE_ARTIFACT
CAN_DEPLOY_INACTIVE
CAN_COMPUTE_SIGNALS
CAN_CREATE_ORDER_INTENTS
CAN_SUBMIT_TESTNET_ORDERS
CAN_SUBMIT_LIVE_ORDERS
CAN_INCREASE_CAPITAL
CAN_CHANGE_RISK_POLICY
```

Ein höheres Level allein verleiht keine impliziten Zusatzrechte.

## 3.4 Evidence-first und Provenance

Jede relevante Stufe erzeugt ein unveränderliches, manifestiertes Artefakt mit:

- eindeutiger ID,
- Contract-Version,
- Input- und Parent-Refs,
- Input- und Output-Digests,
- Code-/Builder-Version,
- Policy-Version,
- Authority-Level und Capabilities,
- Erstellungszeitpunkt,
- MANIFEST.sha256,
- Self-Verification,
- Replay-/Reverification-Information,
- Producer-/Consumer-Beziehung.

Große Rohdaten werden nicht unnötig kopiert. Artefakte referenzieren kanonische, digest-gebundene Inputs.

## 3.5 Deterministik vor AI

Deterministische Logik besitzt Vorrang bei:

- Schema- und Digest-Prüfung,
- Risk- und Capital-Limits,
- Pre-Trade Controls,
- Eligibility,
- Budget-Gates,
- Reconciliation,
- State Transitions,
- Authority-Prüfung,
- Rollback- und Suspension-Entscheidungen.

AI darf analysieren, erklären, priorisieren und Vorschläge erzeugen, aber keine harten Safety- oder Authority-Grenzen überschreiben.

## 3.6 Kostenprinzip

- Offline-first,
- inkrementelle Verarbeitung,
- content-addressed Caching,
- diff-aware CI,
- fokussierte Tests,
- eventgetriebene Offline-Jobs,
- persistente, aber minimale Runtime-Safety-Loops,
- Wiederverwendung vorhandener Artefakte,
- AI-Eskalation nur bei Unsicherheit,
- harte Kostenbudgets pro Pipeline-Stufe,
- Early Exit bei eindeutigen Failures.

## 3.7 Sichere Übergabepunkte

Jeder fachliche oder technische Handoff wird als expliziter, validierbarer Envelope behandelt. Ein Dateipfad, Verzeichnisname oder Prozessstatus allein erzeugt keine Vertrauensstellung.

Ein kanonischer Handoff-Envelope enthält mindestens:

```text
handoff_id
handoff_type
producer_identity
consumer_identity
created_at
expires_at
parent_handoff_id
input_artifact_ids
input_digests
output_artifact_id
output_digest
contract_name
contract_version
policy_digest
authority_ref
capabilities
environment
trading_epoch
idempotency_key
sequence_number
correlation_id
signature
validation_result
```

Jeder Consumer prüft unabhängig und fail-closed:

- unterstützte Contract-Version,
- korrekte Digests und Parent-Referenzen,
- zulässige Policy-Version,
- ausreichende Capability,
- passendes Environment,
- gültige und nicht widerrufene Authority,
- Replay- und Duplicate-Schutz,
- monotone Sequenz,
- Ablaufzeit und Widerrufsstatus.

Ein bereits konsumierter Single-Use-Handoff darf nicht erneut ausgeführt werden.

### 3.7.1 Handoff Trust Policy und Trust Root

Das Feld `signature` allein erzeugt keine Vertrauensstellung. Für jeden Handoff-Typ wird festgelegt, welche Identitäten produzieren, konsumieren und Authority ausstellen dürfen.

```text
handoff_trust_policy_v1
```

Pflichtfelder:

```text
handoff_type
allowed_producer_identities
allowed_consumer_identities
allowed_issuer_identities
signature_algorithm
trusted_key_refs
minimum_contract_version
maximum_ttl_seconds
single_use_required
sequence_scope
required_parent_types
required_capabilities
required_environment_binding
key_rotation_policy_ref
key_revocation_state_ref
```

Für ausführungsrelevante Übergaben gilt grundsätzlich:

```text
producer_identity != authority_issuer_identity
```

Strategy, Promotion, Scheduler, Runtime oder Adapter dürfen ihre eigene Ausführungs-Authority nicht selbst bestätigen. Key Rotation und Revocation invalidieren nicht mehr vertrauenswürdige Signaturen fail-closed.

### 3.7.2 Atomarer Claim- und Consume-Vorgang

Validierung und Verbrauch eines Single-Use-Handoffs müssen atomar erfolgen. Reines „erst prüfen, später als konsumiert markieren“ ist unzulässig.

```text
ISSUED
→ CLAIMED
→ CONSUMED
```

Die Claim-Operation ist eine atomare Compare-and-Set-Operation auf mindestens:

```text
handoff_id
expected_state
expected_digest
expected_consumer_identity
expected_sequence_number
expected_trading_epoch
```

Fehlschlägt der Claim, darf kein Side Effect stattfinden. Nach `CLAIMED` darf genau der gebundene Consumer fortfahren. Abbruch, Timeout oder Prozessverlust nach Claim führen in einen expliziten Recovery-State und niemals zu einem stillen erneuten Konsum.

Für Execution Permissions gilt die strengere Folge:

```text
SAFETY_APPROVED
→ SUBMISSION_CLAIMED
→ SUBMISSION_STARTED
→ CONSUMED
```

Damit werden Doppelorders durch Race Conditions, parallele Worker oder Failover verhindert.

### 3.7.3 Producer-Attestation und Consumer-Validierung

Producer-Validierung ist Evidence, aber keine Consumer-Authority. Deshalb werden getrennt erfasst:

```text
producer_validation_attestation
consumer_validation_result
consumer_validation_timestamp
consumer_policy_digest
consumer_runtime_snapshot_digest
```

Jeder Consumer validiert gegen seinen eigenen aktuellen Policy-, Authority-, Runtime- und Revocation-State. Ein vom Producer gesetztes `validation_result=PASS` darf keinen Consumer-Check ersetzen.

### 3.7.4 Dreifache Gültigkeitsprüfung und TOCTOU-Schutz

Für kritische Handoffs gelten drei verbindliche Prüfzeitpunkte:

```text
validate_on_receive
validate_on_claim
validate_immediately_before_side_effect
```

Unmittelbar vor einem externen Side Effect werden mindestens erneut geprüft:

```text
authority_not_expired
revocation_epoch_current
kill_switch_state_fresh
kill_switch_state=ARMED
trading_epoch_current
executor_epoch_current
handoff_or_permission_not_consumed
handoff_or_permission_not_expired
reconciliation_state=CLEAN
```

Läuft Authority zwischen Intent-Erzeugung, Safety Approval und Adapter Submission ab, ist die Submission verboten.

### 3.7.5 Clock Trust

Ablaufzeiten, Signalalter und Permission-TTL dürfen nicht allein einer ungesicherten Wall Clock vertrauen.

```text
clock_source_id
monotonic_issued_at
wall_clock_issued_at
max_clock_uncertainty_ms
clock_sync_status
```

Lokale TTL-Entscheidungen verwenden monotone Zeit; Wall Clock dient Audit und externer Korrelation. Bei unzureichender Zeitvertrauensstellung gilt:

```text
CLOCK_TRUSTED=false
→ NEW_ORDER_SIDE_EFFECTS_ALLOWED=false
```

Clock Jumps, nicht monotone Zeit oder überschrittene Unsicherheit erzeugen Suspension und Reconciliation.

## 3.8 Authority Lease, Scope und Widerruf

Runtime- und Trading-Authority wird nicht als zeitlich unbegrenzte Freigabe modelliert, sondern als kurzlebiges, scope-gebundenes Lease.

```text
authority_id
authority_type
issued_at
not_before
expires_at
single_use
environment
venue
account_id
instrument_scope
strategy_artifact_digest
risk_policy_digest
deployment_digest
session_id
trading_epoch
max_orders
max_notional
max_runtime_seconds
revocation_epoch
issuer_identity
signature
```

Verbindliche Regeln:

- Testnet-Authority ist technisch nicht gegen einen Live-Adapter verwendbar.
- Änderungen an Strategy-, Deployment- oder Risk-Policy-Digests invalidieren das Lease.
- Suspension, Incident oder Recovery erhöht den `revocation_epoch`.
- Authority aus einem älteren Epoch wird immer abgelehnt.
- Abgelaufene oder bereits konsumierte Single-Use-Leases werden fail-closed abgelehnt.
- Eine Authority ist an genau einen Environment-, Venue-, Account-, Instrument- und Deployment-Kontext gebunden.

## 3.9 Konstitutionelle Grenzen

Das autonome System darf innerhalb ratifizierter Grenzen operieren und sich verbessern. Es darf seine eigene Sicherheitsverfassung nicht autonom erweitern.

Nicht autonom änderbar sind insbesondere:

- Capital- und Daily-Loss-Limits,
- Venue, Account oder Assetklasse,
- Instrumentklasse,
- zulässige Ordertypen,
- Risk-Policy-Owner,
- Safety-Kernel-Owner,
- Reconciliation-Owner,
- API-Key-Rechte,
- Authority- oder Capability-Modell.

Solche Änderungen sind Change Class D und benötigen externe Ratifikation.

---

# 4. Zielarchitektur in fünf Planes

## 4.1 Research Plane

```text
Data Snapshot
→ Feature Build
→ Experiment
→ Robustness Validation
→ Comparison
→ Research Validity Evidence
```

## 4.2 Governance & Promotion Plane

```text
Research Validity Evidence
→ Completion Evidence
→ Promotion Input
→ Promotion Eligibility
→ Promotion Policy Decision
→ Promoted Strategy Artifact
```

## 4.3 Deployment Plane

```text
Promoted Artifact
→ Compatibility Validation
→ Runtime Eligibility
→ Deploy Inactive
→ Deployment Verification
```

## 4.4 Runtime & Execution Plane

```text
Activation Authority
→ Scheduler
→ Signal
→ Order Intent
→ Safety Permission
→ Adapter
→ Venue
```

## 4.5 Safety, Execution & Runtime Authority Plane

```text
Order Intent
→ Independent Pre-Trade Safety
→ Execution Permission

Venue Orders / Fills / Positions / Margin
→ Reconciliation
→ Runtime State Authority

Risk / Data / Health Events
→ Contain
→ Suspend
→ Remediate
→ Recover
→ Resume
```

Diese Plane ist integraler Bestandteil des einen kanonischen Peak-Trade-Handelssystems. Sie darf nicht durch das lernende System, den Trading Decision Core, AI, Promotion oder Scheduler modifiziert, abgeschwächt oder umgangen werden.

---

# 5. Aktueller Ausgangspunkt

Bereits vorhanden oder weitgehend vorhanden:

- Comparison Metric Input Bindings,
- Comparison Definition Binding,
- Comparison Result Binding,
- Common Comparison Durable Evidence Bundle,
- Comparison Lineage Ref Producer,
- Comparison Checkpoint v1,
- Experiment Identity und Domain Refs,
- ConfigPatch-basierter Promotion Loop,
- AI-/Orchestration-Komponenten,
- Runtime-/Execution-Komponenten,
- Risk-/Safety-Gates,
- Live-Override-Loader,
- Runtime Evidence für Orders, Fills, PnL, VaR und Drift.

Noch zu schließen oder zu vereinheitlichen:

- Comparison Checkpoint → Completion Evidence,
- Research Validity → promotionsfähige Completion,
- Completion Evidence → Promotion Input,
- Promotion Decision → versioniertes Strategy-/Model-/Parameter-Artefakt,
- Strategy Artifact → Runtime Eligibility → Deploy Inactive,
- Order Intent → unabhängige Pre-Trade Safety,
- Venue State → Reconciliation → Runtime State Authority,
- Runtime Evidence → Learning Input,
- einheitliche End-to-End-Identität,
- maschinenlesbare Freischalt- und Recovery-Gates.

---

# 6. Zeitoptimierte Implementierungsstrategie

## Track A — Offline Learning und Promotion

Kann weitgehend ohne Runtime-Risiko umgesetzt werden.

## Track B — Runtime Safety und Reconciliation

Beginnt früh parallel, damit die Promotion-Kette nicht fertig ist, bevor die Runtime sicher aktivierbar ist.

## Track C — Observation und Feedback

Wird auf bestehender Runtime Evidence aufgebaut und kurz vor Shadow/Testnet geschlossen.

## Track D — Orchestration und Freischaltung

Wird erst gebaut, wenn die fachlichen Zustände und Safety-Gates stabil sind.

Damit werden lange serielle Warteketten vermieden, ohne unkontrollierte Parallelarchitektur zu erzeugen.

---

# 7. Stufenweises Runbook

## Phase 0 — Autonomy Policy und Zeitbaseline

### Ziel

Eine kleine, verbindliche Policy-Schicht schaffen, ohne ein großes Governance-Projekt zu starten.

### Minimum Safe Slice

1. `system_autonomy_policy_v1`
2. Capability-Modell
3. Change-Class-Modell
4. Kosten- und Runtime-Budgets
5. globale Audit- und Identity-Regeln

### Change Classes

| Klasse | Bedeutung | Autonome Behandlung |
|---|---|---|
| A | Recalibration innerhalb ratifizierter Grenzen | später vollautonom möglich |
| B | Model Replacement mit gleicher Semantik | nach strengen Gates autonom möglich |
| C | Strategy Mutation einschließlich Bull/Bear-, Double-Play- oder Dynamic-Scope-Semantik | hohe Evidence-Hürde, externe Ratifikation erforderlich |
| D | Architektur, Venue, Assetklasse, Authority, Master-V2-, Risk-, Sizing-, Scope-Capital-, KillSwitch- oder Reconciliation-Owner | externe Ratifikation erforderlich |

### Zeitbudget

**2–4 Arbeitstage**, sofern vorhandene Contracts gebunden statt neu erfunden werden.

### Exit-Kriterien

- alle Authority-Übergänge maschinenlesbar,
- Capability-Prüfung fail-closed,
- keine Komponente darf Authority-Felder selbst erfinden,
- keine Live-Freigabe,
- Trading-Core-Preservation-Contract ratifiziert,
- das eine kanonische Peak-Trade-Handelssystem als Single-SSOT registriert,
- Trading Decision Core und Safety, Execution & Runtime Authority Core als interne Domänen desselben Systems registriert,
- kanonische Modul-Owner und Contract-Digests für Master V2, Double Play, Bull, Bear, Dynamic Scope, Risk, Sizing und Scope Capital registriert,
- unabhängige interne Safety-/Runtime-Authority-Owner und Contract-Digests für KillSwitch und Reconciliation registriert,
- No-Bypass- und Parallel-SSOT-Negativtests PASS.

---

## Phase 1 — Comparison → Completion Evidence

### Paket

```text
comparison_completion_evidence_v1
```

### Ziel

Einen verifizierten `comparison_checkpoint_v1` in ein LEVEL_3 Completion-Evidence-Artefakt überführen.

### Input

- genau ein verifizierter Comparison-Checkpoint-Bundle-Pfad.

### Pflichtfelder

```text
is_completion_evidence=true
evidence_does_not_authorize_promotion=true
evidence_does_not_authorize_runtime=true
completion_does_not_select=true
completion_does_not_accept=true
```

### Zeitoptimierung

- nur Checkpoint als direkter Input,
- keine Producer-Neuausführung,
- keine Rohdatenkopien,
- bestehende Bundle-/Manifest-Helfer wiederverwenden,
- zunächst nur ein kanonischer Producer und Validator.

### Zeitbudget

**3–5 Arbeitstage.**

### Exit-Kriterien

- deterministisch,
- MANIFEST RC=0,
- Self-Verification PASS,
- Replay PASS,
- FOCUSED CI ≤ 25 Minuten,
- keine Promotion- oder Runtime-Side-Effects.

---

## Phase 2 — Research Validity und Anti-Overfitting

### Paket

```text
research_validity_evidence_v1
```

oder als enger Binding-Slice:

```text
comparison_completion_research_validity_binding_v1
```

### Ziel

Verhindern, dass ein historisch guter, aber überfiteter Kandidat promotionsfähig wird.

### Minimum Safe Slice

Pflichtfelder:

```text
dataset_identity
data_cutoff_timestamp
train_validation_test_partition
number_of_trials
selection_procedure
walk_forward_result
cost_stress_result
slippage_stress_result
funding_stress_result
parameter_stability_result
regime_breakdown
overfitting_risk_result
```

### Erweiterte Hardening-Felder

```text
purge_window
embargo_window
deflated_sharpe_ratio
probability_of_backtest_overfitting
minimum_track_record_length
liquidity_capacity_result
latency_stress_result
negative_control_result
```

Die erweiterten Felder können schrittweise ergänzt werden, sofern der erste sichere Slice bereits verhindert, dass Validität nur über eine einzelne Performance-Metrik definiert wird.

### Pflichtmetrik-Gruppen

- Sharpe / Sortino,
- Max Drawdown,
- Profit Factor,
- Trade Count und Exposure,
- Fees, Funding und Slippage,
- Walk-Forward-Stabilität,
- Parameterstabilität,
- Regime-Verteilung,
- Multiple-Testing-/Overfitting-Risiko.

### Zeitbudget

**5–8 Arbeitstage** für Binding und Mindestgates.  
**Weitere 3–5 Tage** für vollständige statistische Hardening-Tests, falls bestehende Komponenten fehlen.

### Exit-Kriterien

- Completion kann Research Validity referenzieren,
- kein promotionsfähiger Kandidat ohne robuste Out-of-Sample-Evidence,
- Kosten- und Slippage-Stress verpflichtend,
- Fail-closed bei fehlender oder widersprüchlicher Evidence.

---

## Phase 3 — Completion → Promotion Input

### Paket

```text
comparison_completion_promotion_input_binding_v1
```

### Ziel

Eine einzige kanonische Brücke in den bestehenden Promotion Loop schaffen.

### Regeln

- kein Winner wird implizit ausgewählt,
- keine Promotion Decision,
- keine Runtime Mutation,
- bestehender ConfigPatch-Pfad wird nur als Kompatibilitätsconsumer weitergeführt,
- beide Pfade laufen auf denselben Promotion-Input-Owner zu.

### Zeitbudget

**3–5 Arbeitstage.**

### Exit-Kriterien

- ein gemeinsamer Promotion-Input-Contract,
- keine zweite Promotion-Pipeline,
- keine Consumer-Mutation,
- vollständige Identität und Lineage.

---

## Phase 4 — Promotion Eligibility und Policy Decision

### Komponenten

```text
promotion_eligibility_evidence_v1
promotion_policy_decision_v1
ai_promotion_assessment_v1
```

### Ziel

AI-Analyse, Eligibility und Authority sauber trennen.

### AI-Rolle

AI darf:

- Evidence zusammenfassen,
- Konflikte markieren,
- Unsicherheit quantifizieren,
- alternative Erklärungen liefern,
- einen nicht autorisierenden Vorschlag erzeugen.

AI darf nicht:

- Authority-Felder setzen,
- Risk Limits ändern,
- Promotion eigenständig autorisieren,
- Runtime aktivieren,
- Digests oder Identitäten verändern,
- Master V2, Double Play, Bull/Bear, Dynamic Scope oder bestehende Risk-/Sizing-Owner ersetzen oder umgehen.

### Decision Outputs

```text
APPROVE
REJECT
DEFER_INSUFFICIENT_EVIDENCE
ABSTAIN_POLICY_AMBIGUITY
BLOCK_SAFETY
BLOCK_BUDGET
BLOCK_REPRODUCIBILITY
```

### Zeitbudget

**5–8 Arbeitstage**, wenn der bestehende Promotion Loop wiederverwendet wird.

### Exit-Kriterien

- Policy Engine ist kanonischer Decision Owner,
- AI Assessment bleibt nicht autorisierend,
- positive und negative Entscheidungen sind reproduzierbar,
- kein direkter Runtime-Side-Effect.

---

## Phase 5 — Versioniertes Strategy-/Model-/Parameter-Artefakt

### Paket

```text
promoted_strategy_configuration_v1
```

### Inhalt

```text
strategy_id
strategy_version
model_version
parameter_set
feature_set
risk_profile_ref
sizing_profile_ref
venue_scope
instrument_scope
completion_ref
promotion_decision_ref
input_digests
builder_version
policy_version
rollback_parent
activation_constraints
change_class
semantic_diff
cumulative_change_since_last_full_validation
trading_logic_compatibility_ref
master_v2_contract_digest
double_play_contract_digest
bull_bear_semantic_digest
dynamic_scope_policy_digest
risk_sizing_owner_refs
```

### Migration

- `config/live_overrides/auto.toml` wird zum abgeleiteten Kompatibilitätsoutput,
- `config/auto/learning.override.toml` wird ebenfalls abgeleitet,
- das versionierte Artefakt wird kanonischer Owner der **versionierten Konfiguration und Provenance**, nicht der Trading-Semantik,
- Master V2, Double Play, Bull/Bear, Dynamic Scope sowie Risk-, Sizing- und Scope-Capital-Owner bleiben kanonische fachliche Owner,
- jedes Artefakt muss `trading_logic_compatibility_evidence_v1` referenzieren,
- jede semantische Änderung wird anhand der tatsächlichen Wirkung als Change Class C oder D behandelt.

### Zeitbudget

**5–8 Arbeitstage.**

### Exit-Kriterien

- immutable und digest-gebunden,
- Provenance vollständig,
- rollback-fähig,
- bestehende Loader können über Adapter lesen,
- kein manueller TOML-Handoff,
- keine Umgehung oder Ersetzung der kanonischen Trading-Logic-Owner,
- Golden-Master-, Replay- und No-Bypass-Tests PASS.

---

## Phase 6 — Runtime Safety, sichere Handoffs und Reconciliation

Diese Phase beginnt parallel zu Phase 3–5 und ist vor autonomer Aktivierung zwingend. Die Contracts für Authority, Handoff, Session-Ownership und Order-Lifecycle werden vor der ausführenden Safety-Logik festgelegt.

### Paketgruppe und Reihenfolge

```text
handoff_trust_policy_v1
authority_lease_and_revocation_v1
secure_handoff_envelope_v1
handoff_atomic_claim_consume_v1
clock_trust_and_expiry_v1
trading_session_single_writer_v1
canonical_order_lifecycle_v1
order_intent_idempotency_v1
trading_core_decision_attestation_v1
adapter_submission_contract_v1
venue_capability_snapshot_v1
runtime_state_reconciliation_v1
unknown_execution_outcome_recovery_v1
independent_pretrade_safety_kernel_v1
```

### Ziel

Den Safety, Execution & Runtime Authority Core als integralen, aber unabhängig durchsetzbaren Teil des einen kanonischen Peak-Trade-Handelssystems schließen und sicherstellen, dass Peak Trade jederzeit eindeutig weiß:

- welche Authority aktuell gültig ist,
- welcher Executor handeln darf,
- welche Order-Intents erzeugt und konsumiert wurden,
- welche Orders, Fills und Positionen tatsächlich existieren,
- ob neuer Exposure-Aufbau zulässig ist,
- welcher Recovery-Pfad bei Unsicherheit gilt,
- dass jeder Order Intent aus Master V2 → Double Play → Bull/Bear → Dynamic Scope → bestehender Risk-/Sizing-Logik stammt.

### Trading-Logic-Lineage vor Aktivierung

Vor `ACTIVATION_PREPARED` muss die Runtime zusätzlich prüfen:

```text
master_v2_owner_valid
master_v2_contract_digest_valid
double_play_owner_valid
double_play_contract_digest_valid
bull_bear_components_valid
bull_bear_semantic_digest_valid
dynamic_scope_owner_valid
dynamic_scope_policy_digest_valid
risk_sizing_owner_bindings_valid
trading_logic_compatibility_evidence_valid
canonical_order_intent_lineage_valid
parallel_trading_logic_ssot_detected=false
```

Ein fehlender, veralteter oder widersprüchlicher Nachweis blockiert Aktivierung und Order-Intent-Erzeugung.

### Aktivierung als atomarer Übergang

Der Übergang von `DEPLOYED_INACTIVE` zu aktivem Trading wird als Zwei-Phasen-Protokoll umgesetzt:

```text
DEPLOYED_INACTIVE
→ ACTIVATION_PREPARED
→ ACTIVATION_COMMITTED
→ TRADING_SESSION_OPEN
```

#### Prepare

- Strategy-, Deployment- und Risk-Policy-Digests prüfen,
- Runtime Eligibility erneut prüfen,
- gültiges Authority Lease prüfen,
- Safety Kernel und KillSwitch Health prüfen,
- Reconciliation muss `CLEAN` sein,
- Venue Account State und offene Orders prüfen,
- erwartete Position bestätigen,
- Margin-, Leverage- und Position-Mode verifizieren,
- Datenfeed- und Clock-Freshness prüfen,
- Rollback- und Recovery-Fähigkeit bestätigen.

#### Commit

- neue `trading_epoch` atomar erzeugen,
- Single-Writer-Lease erwerben,
- monotonen `executor_epoch` beziehungsweise Fencing Token festlegen,
- Activation Event persistent schreiben,
- erst danach Signal- und Order-Intent-Erzeugung erlauben.

Fehlschlägt ein Schritt, bleibt das System `DEPLOYED_INACTIVE`.

### Single-Writer- und Fencing-Garantie

Pro Kombination aus

```text
venue
account
instrument
trading_epoch
```

darf genau ein Execution Owner aktiv sein.

Verbindlich sind:

- Lease oder Fencing Token statt reinem Prozess-Lock,
- monoton steigender `executor_epoch`,
- jeder Order Intent trägt den gültigen Epoch,
- alte Epochs werden vom Adapter abgelehnt,
- Lease-Verlust führt sofort zur Suspension,
- kein automatischer Failover ohne vollständige Venue-Reconciliation.

### Kanonische Order-Lifecycle-State-Machine

```text
INTENT_CREATED
INTENT_VALIDATED
SAFETY_APPROVED
SUBMISSION_STARTED
ACKNOWLEDGED
PARTIALLY_FILLED
FILLED
CANCEL_REQUESTED
CANCEL_PENDING
CANCELLED
REJECTED
EXPIRED
UNKNOWN_OUTCOME
RECONCILIATION_REQUIRED
TERMINAL_RECONCILED
```

Erlaubte und verbotene Zustandsübergänge werden maschinenlesbar definiert. Ein Transport-Timeout bedeutet niemals automatisch, dass eine Order nicht angenommen wurde.

Für `UNKNOWN_OUTCOME` gilt zwingend:

```text
kein erneutes Submit
→ Query by Client Order ID
→ Open Orders Snapshot
→ Recent Orders Snapshot
→ Fill Snapshot
→ Position Snapshot
→ Terminalklassifikation oder fortgesetzte Suspension
```

### Deterministische Retry-Matrix

Es gibt keinen generischen Order-Retry.

| Fehlerklasse | Verbindliches Verhalten |
|---|---|
| Lokaler Fehler vor Netzwerkübertragung | gleicher Intent darf erneut versucht werden |
| Timeout nach möglicher Übertragung | `UNKNOWN_OUTCOME`, kein Resubmit |
| Venue-Rejection | terminal, kein Retry ohne neuen Intent |
| Rate Limit | bounded Backoff, Intent-Freshness und Authority erneut prüfen |
| Auth Failure | sofortige Suspension |
| Precision-/Schema-Rejection | terminaler Implementation Error |
| Duplicate Client Order ID | Venue-State abfragen, keine neue ID erzeugen |
| WebSocket Gap | Order-Erzeugung pausieren, REST-Reconciliation |
| Partial Fill plus Cancel Timeout | vollständige Fill-/Position-Reconciliation |

Ein neuer Client Order ID darf niemals verwendet werden, um einen ungeklärten alten Auftrag erneut zu senden.

### Order- und State-Kette

```text
Order Intent
→ Deterministic Client Order ID
→ aktuelle Pre-Trade-Reconciliation
→ Single-Use Execution Permission
→ Submission Attempt
→ Venue Acknowledgement oder UNKNOWN_OUTCOME
→ Open Order Snapshot
→ Fill Stream
→ Position Snapshot
→ Margin Snapshot
→ Reconciliation Result
→ Runtime State Authority
```

### Single-Use Execution Permission und TOCTOU-Schutz

Unmittelbar vor jeder Submission werden aktuelle Zustände neu gebunden:

```text
Order Intent
+ Runtime State
+ Venue State
+ Risk Counters
+ Market Data
+ Authority Lease
→ Execution Permission
```

Die Permission enthält mindestens:

```text
execution_permission_id
intent_digest
approved_quantity
approved_limit_price
max_market_price
expires_at
single_use=true
risk_snapshot_digest
position_snapshot_digest
authority_id
trading_epoch
executor_epoch
```

Ändert sich einer der gebundenen Zustände oder läuft die Permission ab, ist eine neue Safety-Prüfung erforderlich.

### Reconciliation als Composite Authority

Die Venue ist autoritativ für akzeptierte Orders, Fills, Position und Margin. Der lokale Event Log ist autoritativ für Intent, Authority, Safety-Prüfung und Submission-Versuche.

```text
Local Intent Ledger
+ Submission Ledger
+ Venue Orders
+ Venue Fills
+ Venue Positions
+ Venue Margin
→ Reconciled Runtime State
```

### Vier Reconciliation-Ebenen

1. **R1 Event-Reconciliation** — Sequenz, IDs und Events laufend prüfen.
2. **R2 Periodischer Snapshot** — Orders, Fills, Position und Margin vollständig abgleichen.
3. **R3 Pre-Trade-Reconciliation** — vor exposure-erhöhenden Orders aktuellen Venue-State bestätigen.
4. **R4 Recovery-Reconciliation** — nach Restart, Netzunterbrechung, Unknown Outcome oder Failover vollständiger Neuaufbau.

Trigger sind unter anderem:

- WebSocket Sequence Gap,
- REST-/WebSocket-Widerspruch,
- Prozess-Restart,
- Clock Jump,
- API-Key-Rotation,
- Venue-Maintenance,
- unerwartete Balance-, Margin- oder Positionsänderung.

### Reconciliation-Barriere

```text
reconciliation_state != CLEAN
→ OPENING_ORDER_ALLOWED=false
→ INCREASING_ORDER_ALLOWED=false
```

`REDUCE_ONLY_ORDER_ALLOWED` und `EMERGENCY_CLOSE_ALLOWED` sind ausschließlich über eine ratifizierte Remediation Policy zulässig.

### Pre-Trade Safety Kernel

Jeder Order-Intent muss unabhängig prüfen:

```text
runtime_authority_valid
authority_lease_not_expired
authority_revocation_epoch_current
artifact_digest_valid
session_authorized
trading_epoch_current
executor_epoch_current
instrument_allowed
venue_allowed
account_allowed
position_limit
gross_exposure_limit
order_notional_limit
daily_loss_limit
leverage_limit
price_collar
stale_market_data_guard
mark_index_divergence_guard
spread_guard
orderbook_depth_guard
expected_market_impact_guard
signal_expiry_guard
duplicate_intent_guard
open_order_limit
message_rate_limit
margin_buffer
kill_switch_state
reconciliation_state_clean
```

### Instrument-, Preis- und Mengenvalidierung

Vor Session-Start und regelmäßig während der Session werden gegen die Venue geprüft:

```text
margin_mode
position_mode
leverage
reduce_only_semantics
hedge_mode
one_way_mode
settlement_asset
contract_multiplier
tick_size
lot_size
minimum_notional
maximum_order_size
```

Menge und Preis werden vor der finalen Safety-Prüfung normalisiert:

```text
raw_quantity
→ contract conversion
→ lot rounding
→ min/max validation
→ notional recalculation
→ erneute Risk-Prüfung
```

### Market-Data- und Execution-Guards

```text
max_mark_index_divergence
max_last_mark_divergence
max_spread_bps
max_orderbook_age_ms
minimum_top_of_book_depth
max_expected_market_impact
max_price_move_since_signal
signal_expiry
execution_permission_expiry
```

Wo technisch sinnvoll werden bounded marketable limits gegenüber unbeschränkten Market Orders bevorzugt.

### Daily-Loss-Definition

Die kanonische Safety-Berechnung umfasst konservativ:

```text
realized_pnl
+ unrealized_pnl
- fees
- funding
- estimated_close_cost
- unresolved_fill_reserve
```

Zeitzone, Tagesgrenze, Neustartverhalten, verspätete Fills und widersprüchliche PnL-Quellen werden maschinenlesbar definiert. Bei Konflikten gilt die konservativste belastbare Berechnung.

### Partial Fills und Cancel/Replace

Partielle Fills sind Normalzustände, keine Ausnahme. Restmengen werden nicht blind erneut platziert. Signalalter, aktuelle Position, Risk und Authority werden erneut geprüft.

Cancel/Replace wird nicht als atomar angenommen:

```text
CANCEL_REQUESTED
→ Venue-Bestätigung oder Reconciliation
→ Restmenge feststellen
→ Position und Fills aktualisieren
→ neuer Intent für verbleibenden Bedarf
```

### Secrets und Blast-Radius-Isolation

Für Live-Execution gelten mindestens:

```text
READ=true
TRADE=true
WITHDRAW=false
TRANSFER=false
SUBACCOUNT_ADMIN=false
API_KEY_MANAGEMENT=false
```

Zusätzlich, sofern unterstützt:

- separater Subaccount,
- separater API-Key pro Environment und Execution Service,
- IP-Allowlisting,
- Secret Manager statt Config-Datei,
- keine Secrets in Evidence oder Logs,
- automatisierte Redaction-Tests.

Der erste Live-Pfad bleibt kontoseitig und fachlich isoliert:

```text
one_venue
one_instrument
one_execution_owner
one_dedicated_subaccount
one_bounded_capital_envelope
```

### End-to-End Decision–Authority–Execution–Reconciliation Chain

Der ausführbare Pfad wird als geschlossene Digest- und Attestation-Kette modelliert:

```text
Market Snapshot
→ Trading-Core Decision Attestation Chain
→ Canonical Order Intent
→ Current Runtime/Venue Snapshot
→ Safety Decision Attestation
→ Single-Use Execution Permission
→ Adapter Submission Claim
→ Venue Outcome
→ Reconciliation Attestation
```

Jede Stufe bindet den Output-Digest der vorherigen Stufe. Eine unterbrochene, widersprüchliche oder nicht reproduzierbare Kette blockiert Aktivierung beziehungsweise neue Exposure.

### Adapter Submission Contract

Der Adapter ist eine letzte Durchsetzungsgrenze, aber kein fachlicher Decision Owner.

```text
adapter_submission_contract_v1
```

Verbindliche Regeln:

```text
adapter_may_normalize_representation=true
adapter_may_change_semantics=false
adapter_may_change_quantity_upward=false
adapter_may_change_order_type=false
adapter_may_replace_client_order_id=false
adapter_may_retry_unknown_outcome=false
adapter_may_remove_reduce_only=false
adapter_may_silently_change_position_mode=false
adapter_may_generate_new_intent=false
```

Zulässig sind ausschließlich deterministische Formattransformationen, deren Input und Output digest-gebunden und vollständig rekonstruierbar sind.

### Venue Capability Snapshot und Drift Handling

Venue- und Instrumentfähigkeiten werden als versionierter Snapshot gebunden:

```text
venue_capability_snapshot_v1
```

Mindestens enthalten:

```text
venue
account_scope
instrument
contract_multiplier
tick_size
lot_size
minimum_notional
maximum_order_size
position_mode
margin_mode
leverage_cap
supported_order_types
reduce_only_semantics
snapshot_timestamp
capability_digest
```

Der Snapshot wird an Runtime Eligibility, Activation, Order Intent und Execution Permission gebunden. Bei Drift gilt:

```text
VENUE_CAPABILITY_DIGEST_CHANGED
→ SUSPEND_NEW_ORDERS
→ INVALIDATE_UNUSED_EXECUTION_PERMISSIONS
→ RECONCILE
→ REVALIDATE_RUNTIME_ELIGIBILITY
```

### Kanonische Degradation-Matrix

Fail-closed wird als konkrete Capability-Reduktion modelliert:

```text
OBSERVATION_ONLY
NO_NEW_EXPOSURE
CANCEL_ONLY
REDUCE_ONLY
EMERGENCY_CLOSE_ONLY
FULLY_ISOLATED
```

| Zustand | Observation | Cancel | Reduce-only | Neue Exposure |
|---|---:|---:|---:|---:|
| Reconciliation unclean | ja | policy-gebunden | policy-gebunden | nein |
| KillSwitch tripped | ja | policy-gebunden | nur Recovery Authority | nein |
| Authority expired/revoked | ja | nur Incident Policy | nur Recovery Authority | nein |
| Market Data stale | ja | ja | policy-gebunden | nein |
| Adapter degraded | ja | falls sicher | falls sicher | nein |
| Clock untrusted | ja | policy-gebunden | policy-gebunden | nein |
| Trust Root unklar | ja | nein | nur separat validierte Recovery Authority | nein |

Keine Komponente darf einen strengeren Zustand autonom in einen weniger restriktiven Modus hochstufen.

### Zeitbudget

**12–18 Arbeitstage**, sofern Adapter-, Order- und Runtime-Evidence bereits vorhanden sind. Die zusätzlichen Contracts erhöhen den initialen Spezifikationsaufwand geringfügig, reduzieren jedoch Retry-, Split-Brain-, Replay- und Recovery-Risiken erheblich.

### Exit-Kriterien

- Authority Lease, Revocation und Environment-Binding getestet,
- sichere Handoff-Envelopes mit Replay-Schutz getestet,
- atomare Aktivierung und Single-Writer-Fencing getestet,
- Restart- und Timeout-Recovery getestet,
- keine Doppelorder bei Retry oder Failover,
- unbekannte Venue-Antwort führt fail-closed zu Reconciliation,
- unerwartete Position führt zur Suspension,
- kein AI-, Strategy- oder Scheduler-Modul kann Safety umgehen,
- kein AI-, Promotion-, Scheduler- oder Runtime-Modul kann Master V2, Double Play, Bull/Bear, Dynamic Scope oder bestehende Risk-/Sizing-Owner umgehen,
- manipulierte oder fehlende Trading-Logic-Lineage wird fail-closed abgelehnt,
- KillSwitch und Reduce-only-Pfade getestet,
- keine Exposure-Erhöhung bei unsauberem Reconciliation-State,
- vollständiger Audit-Trail von Authority bis Fill.

---

## Phase 7 — Runtime Eligibility und Deployment

### Komponenten

```text
runtime_eligibility_evidence_v1
deployment_candidate_v1
deployed_inactive_verification_v1
```

### Ziel

Promotion, Deployment und Aktivierung als getrennte Zustände modellieren.

### Zustände

```text
CANDIDATE
RESEARCH_VALID
PROMOTED
RUNTIME_ELIGIBLE
DEPLOYABLE
DEPLOYED_INACTIVE
ACTIVATED
TRADING
SUSPENDED
ROLLED_BACK
RETIRED
```

### Prüfungen

- Contract-Version,
- Venue- und Instrument-Kompatibilität,
- Risk- und Capital-Limits,
- Datenverfügbarkeit,
- Adapter Health,
- Rollback-Verfügbarkeit,
- Config-Validität,
- Model-/Feature-Kompatibilität,
- Scheduler Readiness,
- KillSwitch,
- Reconciliation Readiness,
- Budget,
- Trading-Logic Compatibility Evidence,
- Master-V2-/Double-Play-/Bull-Bear-/Dynamic-Scope-Owner-Bindings,
- kanonische Order-Intent-Lineage,
- No-Bypass- und Parallel-SSOT-Prüfung.

### Zeitbudget

**5–8 Arbeitstage.**

### Exit-Kriterien

- vollständig offline prüfbar,
- kein Order- oder Scheduler-Side-Effect,
- Deploy Inactive und Activation getrennt,
- Activation nur über gültiges Authority Lease,
- Strategy-, Deployment-, Risk-Policy- und Environment-Digests gebunden,
- Single-Writer-, Reconciliation- und KillSwitch-Readiness bestätigt,
- Master V2, Double Play, Bull/Bear und Dynamic Scope unverändert kanonisch gebunden,
- keine parallele oder abkürzende Trading-Logic-SSOT,
- klarer PASS/FAIL-Status.

---

## Phase 8 — Runtime Observation und Feedback

### Paketgruppe

```text
runtime_observation_bundle_v1
runtime_to_learning_input_v1
runtime_performance_comparison_input_v1
```

### Runtime Evidence

- Orders,
- Fills,
- offene und geschlossene Positionen,
- PnL,
- Fees,
- Funding,
- Slippage,
- Latency,
- Risk Events,
- KillSwitch Events,
- Reconciliation Events,
- Signal-Version,
- Strategy-Version,
- Model-Version,
- Parameter-Version,
- Promotion Decision,
- Runtime Session,
- Venue,
- Instrument,
- Regime,
- Runtime Health.

### Zeitbudget

**7–10 Arbeitstage**, sofern vorhandene Runtime Evidence erweitert statt ersetzt wird.

### Exit-Kriterien

- vollständige End-to-End-Identität,
- automatische Transformation zu Learning Inputs,
- keine manuelle Übertragung,
- kein Identitätsverlust,
- Runtime-vs-Backtest-Abweichungen messbar.

---

## Phase 9 — Autonome Shadow-/Paper-/Testnet-Orchestration

### Ziel

Die gesamte Kette ohne echtes Kapital automatisch durchlaufen.

### Reihenfolge

```text
REPLAY_ONLY
→ SHADOW_ONLY
→ PAPER_ONLY
→ TESTNET_ONLY
```

### Champion/Challenger

```text
LIVE_PRIMARY
ROLLBACK_STANDBY
CHALLENGER_SHADOW
CHALLENGER_PAPER
CHALLENGER_TESTNET
```

Ein Challenger ersetzt den Champion nicht unmittelbar nach einer Promotion.

### Automatischer Ablauf

```text
New Evidence
→ Research/Comparison
→ Completion
→ Promotion Evaluation
→ Strategy Artifact
→ Runtime Eligibility
→ Deploy Inactive
→ Activate Shadow/Paper/Testnet
→ Observe
→ Reconcile
→ Feed Back
```

### Zeitbudget

**7–12 Arbeitstage**, sofern die einzelnen Zustände bereits als idempotente Commands oder Producer vorliegen.

### Exit-Kriterien

- geschlossener Loop,
- keine manuellen Dateihandoffs,
- keine Live Orders,
- automatische Suspension und Recovery,
- Champion/Challenger funktionsfähig,
- Kostenbudgets aktiv.

---

# 8. Maschinenlesbare Freischalt-Gates

Begriffe wie „stabil“ oder „belastbar“ reichen nicht. Jede Stufe benötigt konkrete SLOs.

## 8.1 Shadow/Paper/Testnet

Mindestens zu messen:

```text
MIN_RUNTIME_HOURS
MIN_INDEPENDENT_SESSIONS
MIN_ORDER_COUNT
MIN_FILL_COUNT
MAX_RECONCILIATION_ERRORS
MAX_UNKNOWN_ORDER_OUTCOMES
MAX_UNPLANNED_RESTARTS
MAX_DATA_STALENESS_EVENTS
MAX_KILL_SWITCH_LATENCY_MS
KILL_SWITCH_CANONICAL_OWNER_VALID=true
KILL_SWITCH_CONTRACT_DIGEST_VALID=true
KILL_SWITCH_POLICY_DIGEST_VALID=true
KILL_SWITCH_STATE_MACHINE_DIGEST_VALID=true
KILL_SWITCH_STATE_FRESH=true
KILL_SWITCH_STATE=ARMED
KILL_SWITCH_BYPASS_DETECTED=false
KILL_SWITCH_PARALLEL_SSOT_DETECTED=false
KILL_SWITCH_REVOCATION_EPOCH_CURRENT=true
KILL_SWITCH_RESTART_PERSISTENCE_PASS=true
KILL_SWITCH_RESET_AUTHORITY_VALID=true
MAX_STATE_RECOVERY_TIME_SECONDS
MAX_SLIPPAGE_MODEL_ERROR
MAX_FEE_MODEL_ERROR
ZERO_UNEXPLAINED_POSITIONS=true
ROLLBACK_DRILL_PASS=true
RECOVERY_DRILL_PASS=true
```

Konkrete Schwellen werden strategie- und frequenzabhängig ratifiziert. Keine Freischaltung darf allein an einer kurzen Laufzeit oder einer einzelnen PnL-Kennzahl hängen.

## 8.2 Research und Promotion

```text
MIN_WALK_FORWARD_WINDOWS
MAX_PBO
MIN_DEFLATED_SHARPE
MAX_DRAWDOWN
MIN_PROFIT_FACTOR
MIN_TRADE_COUNT
MAX_PARAMETER_SENSITIVITY
MAX_COST_STRESS_DEGRADATION
MAX_SLIPPAGE_STRESS_DEGRADATION
REQUIRED_REGIME_COVERAGE
NO_DATA_LEAKAGE=true
NO_LINEAGE_GAPS=true
```

## 8.3 Runtime Operations

```text
MAX_RECONCILIATION_DELAY
MAX_MARKET_DATA_AGE
MAX_ADAPTER_ERROR_RATE
MAX_ORDER_RETRY_COUNT
MAX_POSITION_DRIFT
MAX_MARGIN_UTILIZATION
MAX_DAILY_LOSS
MAX_TOTAL_EXPOSURE
```

## 8.4 Authority-, Handoff- und Execution-Gates

```text
AUTHORITY_LEASE_VALID=true
AUTHORITY_REVOCATION_EPOCH_CURRENT=true
ENVIRONMENT_BINDING_VALID=true
STRATEGY_DIGEST_BINDING_VALID=true
RISK_POLICY_DIGEST_BINDING_VALID=true
DEPLOYMENT_DIGEST_BINDING_VALID=true
SINGLE_WRITER_LEASE_VALID=true
EXECUTOR_EPOCH_CURRENT=true
TRADING_EPOCH_CURRENT=true
HANDOFF_REPLAY_DETECTED=false
HANDOFF_SEQUENCE_VALID=true
EXECUTION_PERMISSION_SINGLE_USE=true
EXECUTION_PERMISSION_NOT_EXPIRED=true
UNKNOWN_OUTCOME_COUNT=0
ZERO_UNRECONCILED_EXPOSURE=true

MASTER_V2_OWNER_VALID=true
MASTER_V2_CONTRACT_DIGEST_VALID=true
DOUBLE_PLAY_OWNER_VALID=true
DOUBLE_PLAY_CONTRACT_DIGEST_VALID=true
BULL_BEAR_COMPONENTS_VALID=true
BULL_BEAR_SEMANTIC_DIGEST_VALID=true
DYNAMIC_SCOPE_OWNER_VALID=true
DYNAMIC_SCOPE_POLICY_DIGEST_VALID=true
RISK_SIZING_OWNER_BINDINGS_VALID=true
TRADING_LOGIC_COMPATIBILITY_EVIDENCE_VALID=true
CANONICAL_ORDER_INTENT_LINEAGE_VALID=true
TRADING_LOGIC_BYPASS_DETECTED=false
PARALLEL_TRADING_LOGIC_SSOT_DETECTED=false
```

---

## 8.5 Trust-, Atomic-Consume-, Clock- und Attestation-Gates

```text
HANDOFF_TRUST_POLICY_VALID=true
HANDOFF_SIGNATURE_TRUSTED=true
HANDOFF_SIGNER_NOT_REVOKED=true
HANDOFF_ATOMIC_CLAIM_PASS=true
HANDOFF_ALREADY_CLAIMED=false
HANDOFF_CONSUMER_IDENTITY_VALID=true
PRODUCER_VALIDATION_NOT_USED_AS_CONSUMER_AUTHORITY=true
CLOCK_TRUSTED=true
CLOCK_UNCERTAINTY_WITHIN_LIMIT=true
TOCTOU_REVALIDATION_PASS=true

TRADING_CORE_ATTESTATION_CHAIN_VALID=true
TRADING_CORE_ATTESTATION_CHAIN_COMPLETE=true
TRADING_CORE_INPUT_OUTPUT_DIGEST_CHAIN_VALID=true
SEMANTIC_DIFF_EVIDENCE_VALID=true
DYNAMIC_SCOPE_STABILITY_GATES_PASS=true

ADAPTER_SUBMISSION_CONTRACT_VALID=true
ADAPTER_SEMANTIC_MUTATION_DETECTED=false
VENUE_CAPABILITY_SNAPSHOT_VALID=true
VENUE_CAPABILITY_DRIFT_DETECTED=false

KILL_SWITCH_WRITER_EPOCH_CURRENT=true
KILL_SWITCH_EVENT_SEQUENCE_VALID=true
KILL_SWITCH_EVENT_DIGEST_CHAIN_VALID=true
KILL_SWITCH_INDEPENDENT_READ_PATHS_HEALTHY=true
```

# 9. Recovery-, KillSwitch- und Resume-Modell

„Rollback“ allein reicht nicht, weil reale Orders, Fills und Positionen irreversible Effekte erzeugen.

## 9.1 Recovery-Zustände

```text
CONTAIN
SUSPEND_NEW_ORDERS
CANCEL_OPEN_ORDERS
RECONCILE
POSITION_REMEDIATION
SOFTWARE_ROLLBACK
RECOVERY_VALIDATION
RESET_AUTHORIZED
RESUME_OR_RETIRE
```

## 9.2 Unabhängiger, kanonischer KillSwitch

Der KillSwitch ist ein geschützter, unabhängiger und kanonischer Safety-Owner. Er liegt außerhalb der Strategie-, Master-V2-, Double-Play-, Bull/Bear-, Dynamic-Scope-, AI-, Promotion-, Scheduler-, Runtime-Orchestrator- und Adapter-Hoheit. Keine dieser Komponenten darf seinen Zustand, seine Trigger, seine Policy, seine Persistenz oder seine Reset-Semantik ersetzen, abschwächen, umgehen oder parallel duplizieren.

### 9.2.1 Kanonische Owner- und No-Bypass-Invarianten

```text
KILL_SWITCH_CANONICAL_OWNER=true
KILL_SWITCH_FAIL_CLOSED=true
KILL_SWITCH_PARALLEL_SSOT_ALLOWED=false
KILL_SWITCH_BYPASS_ALLOWED=false
KILL_SWITCH_STATE_REWRITE_ALLOWED=false
KILL_SWITCH_AUTO_DISARM_ALLOWED=false
KILL_SWITCH_RESET_BY_STRATEGY_ALLOWED=false
KILL_SWITCH_RESET_BY_MASTER_V2_ALLOWED=false
KILL_SWITCH_RESET_BY_DOUBLE_PLAY_ALLOWED=false
KILL_SWITCH_RESET_BY_BULL_BEAR_ALLOWED=false
KILL_SWITCH_RESET_BY_DYNAMIC_SCOPE_ALLOWED=false
KILL_SWITCH_RESET_BY_AI_ALLOWED=false
KILL_SWITCH_RESET_BY_PROMOTION_ALLOWED=false
KILL_SWITCH_RESET_BY_SCHEDULER_ALLOWED=false
KILL_SWITCH_RESET_BY_RUNTIME_ALLOWED=false
KILL_SWITCH_RESET_BY_ADAPTER_ALLOWED=false
KILL_SWITCH_STATE_PERSISTS_ACROSS_RESTART=true
KILL_SWITCH_TRIP_REVOKES_TRADING_AUTHORITY=true
```

Ein Order Intent, eine Execution Permission oder eine Adapter-Submission ist unzulässig, wenn der kanonische KillSwitch-Zustand nicht eindeutig `ARMED` ist. Fehlt der State, ist er veraltet, widersprüchlich, nicht verifizierbar oder stammt er nicht vom kanonischen Owner, gilt fail-closed:

```text
ORDERS_ALLOWED=false
OPENING_ORDER_ALLOWED=false
INCREASING_ORDER_ALLOWED=false
```

### 9.2.2 Kanonische KillSwitch-State-Machine

```text
DISARMED
ARMING_VALIDATION
ARMED
TRIPPED
CONTAINING
SUSPEND_NEW_ORDERS
CANCEL_OPEN_ORDERS
RECONCILING
POSITION_REMEDIATION
RECOVERY_PENDING
RECOVERY_VALIDATED
RESET_AUTHORIZED
REARMING_VALIDATION
ARMED
RETIRED
```

Nur ausdrücklich definierte Zustandsübergänge sind zulässig. Direkte Übergänge von `TRIPPED`, `CONTAINING`, `RECONCILING`, `POSITION_REMEDIATION` oder `RECOVERY_PENDING` nach `ARMED` sind verboten.

### 9.2.3 Trip-Semantik

Ein KillSwitch-Trip muss atomar und dauerhaft mindestens folgende Wirkungen auslösen:

```text
kill_switch_state=TRIPPED
ORDERS_ALLOWED=false
OPENING_ORDER_ALLOWED=false
INCREASING_ORDER_ALLOWED=false
SCHEDULER_RUNTIME_ALLOWED=false
revocation_epoch=revocation_epoch+1
active_authority_leases=INVALIDATED
unused_execution_permissions=INVALIDATED
pending_unsubmitted_intents=INVALIDATED
new_trading_session_allowed=false
reconciliation_required=true
```

Zusätzlich gilt:

- Der Trip wird vor jeder weiteren exposure-erhöhenden Aktion ausgewertet.
- Der Trip darf nicht durch Prozess-Restart, Deployment, Failover, Config-Reload oder Adapter-Reconnect verloren gehen.
- Bereits an die Venue übertragene oder möglicherweise übertragene Orders werden nicht als lokal rückgängig angenommen; sie gehen in Containment und Reconciliation.
- `UNKNOWN_OUTCOME` bleibt ungeklärt, bis Venue Orders, Fills, Position und Margin reconciled wurden.
- Der lokale KillSwitch-Zustand und der erhöhte `revocation_epoch` werden vor der Bestätigung eines Resets dauerhaft manifestiert.

### 9.2.4 Trigger-Klassen

Der KillSwitch muss mindestens folgende deterministischen Triggerklassen unterstützen:

```text
RISK_LIMIT_BREACH
DAILY_LOSS_LIMIT_BREACH
CAPITAL_LIMIT_BREACH
MARGIN_OR_LEVERAGE_BREACH
UNEXPECTED_POSITION
UNRECONCILED_EXPOSURE
UNKNOWN_ORDER_OUTCOME
RECONCILIATION_FAILURE
AUTHORITY_INVALID_OR_EXPIRED
SINGLE_WRITER_LEASE_LOSS
EXECUTOR_EPOCH_MISMATCH
TRADING_EPOCH_MISMATCH
MARKET_DATA_STALE_OR_INVALID
MARK_INDEX_DIVERGENCE
VENUE_OR_ADAPTER_FAILURE
DATA_OR_CLOCK_SEQUENCE_ANOMALY
MANIFEST_OR_DIGEST_MISMATCH
RUNTIME_HEALTH_FAILURE
MANUAL_EMERGENCY_TRIP
```

Trigger dürfen erweitert, aber nicht autonom entfernt, gelockert oder in nicht fail-closed Warnungen umgewandelt werden. Änderungen an Trigger-Semantik, Schwellen-Owner oder Reset-Authority sind Change Class D.

### 9.2.5 Pre-Trade-, Runtime- und Adapter-Durchsetzung

Der KillSwitch wird unabhängig an mehreren Grenzen geprüft:

```text
Activation Prepare
→ Scheduler Admission
→ Signal-to-Intent Boundary
→ Pre-Trade Safety Kernel
→ Execution Permission Issuance
→ Adapter Submission Boundary
→ Runtime Health Loop
```

Mindestens der Pre-Trade Safety Kernel und der Adapter prüfen den kanonischen KillSwitch-State unabhängig. Ein älterer gecachter `ARMED`-State darf keinen aktuelleren `TRIPPED`-State überschreiben. Die Prüfung muss an `kill_switch_state_digest`, `revocation_epoch`, `trading_epoch`, `executor_epoch` und einen Freshness-Nachweis gebunden sein.

### 9.2.5a KillSwitch Writer-Fencing und manipulationssichere Event-Kette

Auch der kanonische KillSwitch besitzt genau einen gültigen State Writer pro Writer Epoch. Prozess-Locks allein reichen nicht.

```text
kill_switch_writer_epoch
kill_switch_event_sequence
previous_event_digest
current_event_digest
```

Jedes Event bindet seinen Vorgänger:

```text
current_event_digest = hash(previous_event_digest + canonical_event_payload)
```

Verbindlich gilt:

- nur der höchste gültige `kill_switch_writer_epoch` darf neue State Events schreiben,
- niedrigere oder unbekannte Writer Epochs werden abgelehnt,
- Sequenzlücken, konkurrierende Nachfolger oder gebrochene Digest-Ketten führen zu `TRIPPED` beziehungsweise fortgesetzter Suspension,
- State Rollback auf ein älteres `ARMED`-Event ist verboten,
- Recovery darf die Event-Kette nicht neu beginnen, sondern muss sie nachvollziehbar fortsetzen.

### 9.2.5b Unabhängige technische Read Paths

Die unabhängige Prüfung durch Safety Kernel und Adapter darf nicht nur logisch doppelt, aber technisch vom selben flüchtigen Cache abhängig sein.

```text
SAFETY_KERNEL_KILLSWITCH_READ_PATH != ADAPTER_KILLSWITCH_READ_PATH
```

Mindestens gilt:

- der Safety Kernel liest den kanonischen persistierten State,
- der Adapter prüft zusätzlich eine lokal verfügbare monotone Revocation-/Trip-Projektion,
- beide prüfen `kill_switch_state_digest`, `revocation_epoch`, `trading_epoch`, `executor_epoch` und Freshness,
- bei Ausfall, Unlesbarkeit oder Widerspruch gilt niemals „last known ARMED“, sondern:

```text
kill_switch_state_unavailable=true
→ adapter_submission_allowed=false
```

### 9.2.6 Containment und Remediation

Nach einem Trip gilt folgende Priorität:

```text
1. neue exposure-erhöhende Orders sperren
2. Authority und Execution Permissions widerrufen
3. offene und möglicherweise offene Orders feststellen
4. ratifizierte Cancel-Policy anwenden
5. Venue Orders, Fills, Position und Margin reconciliieren
6. policy-gebundene Position Remediation ausführen
7. Recovery Evidence erzeugen
```

`REDUCE_ONLY` oder `CLOSE_WITH_BOUNDED_MARKETABLE_LIMIT` dürfen nur durch eine separat ratifizierte Remediation Policy und eine eng gebundene Recovery Authority zugelassen werden. Der KillSwitch-Trip selbst erzeugt keine freie Ausführungsberechtigung.

### 9.2.7 Reset- und Rearming-Authority

Ein Reset ist keine Zustandsmutation durch Strategy oder Runtime. Er ist ein neuer, evidence-gebundener Authority-Vorgang.

Pflichtvoraussetzungen:

```text
R4_RECONCILIATION_PASS=true
ZERO_UNRECONCILED_EXPOSURE=true
OPEN_ORDERS_STATE_KNOWN=true
POSITION_STATE_KNOWN=true
MARGIN_STATE_KNOWN=true
ROOT_CAUSE_CLASSIFIED=true
REMEDIATION_COMPLETE=true
RECOVERY_VALIDATION_PASS=true
RESET_AUTHORITY_VALID=true
NEW_AUTHORITY_LEASE_REQUIRED=true
NEW_TRADING_EPOCH_REQUIRED=true
NEW_EXECUTOR_EPOCH_REQUIRED=true
```

Reset und Rearming müssen getrennt bleiben:

```text
RECOVERY_VALIDATED
→ RESET_AUTHORIZED
→ REARMING_VALIDATION
→ ARMED
```

Eine gültige Reset Authority allein erlaubt noch keine Orders. Erst nach neuer Runtime Eligibility, neuer Activation, neuem Authority Lease und neuer Trading-/Executor-Epoch darf erneut gehandelt werden.

### 9.2.8 KillSwitch Evidence und Audit-Trail

Jeder Trip, jeder Zustandsübergang, jede Remediation und jeder Reset erzeugt unveränderliche Evidence mit mindestens:

```text
kill_switch_event_id
kill_switch_owner_ref
kill_switch_contract_digest
kill_switch_policy_digest
previous_state
new_state
trigger_class
trigger_evidence_refs
occurred_at
observed_at
revocation_epoch_before
revocation_epoch_after
trading_epoch
executor_epoch
active_authority_ids_invalidated
execution_permissions_invalidated
open_order_snapshot_ref
fill_snapshot_ref
position_snapshot_ref
margin_snapshot_ref
reconciliation_result_ref
remediation_policy_ref
recovery_authority_ref
reset_authority_ref
manifest_digest
```

### 9.2.9 Pflicht- und Negativtests

Vor Shadow, Paper, Testnet, Canary und jeder Live-Aktivierung sind mindestens nachzuweisen:

- Trip bei jedem ratifizierten Trigger,
- Persistenz über Restart, Deployment und Failover,
- atomare Erhöhung des `revocation_epoch`,
- Invalidierung alter Authority Leases, Intents und Execution Permissions,
- Ablehnung gecachter oder veralteter `ARMED`-Zustände,
- No-Bypass durch Master V2, Double Play, Bull/Bear, Dynamic Scope, AI, Scheduler, Runtime und Adapter,
- Ablehnung unautorisierter Reset-, Disarm- und State-Rewrite-Versuche,
- kein automatisches Rearming nach Recovery,
- R4-Reconciliation vor Reset,
- keine Exposure-Erhöhung bei `TRIPPED` oder unklarem KillSwitch-State,
- kontrollierter Reduce-only-/Close-Pfad nur mit gültiger Remediation Authority,
- vollständiger Audit-Trail vom Trigger bis zur neuen Aktivierung.

### 9.2.10 Verbindliche Eigenschaften

- separater, kanonischer Safety-Owner,
- persistierter und manifestierter Zustand,
- Restart, Redeploy oder Failover setzt den KillSwitch nicht zurück,
- Strategy-, Master-V2-, Double-Play-, Bull/Bear-, Dynamic-Scope-, AI-, Promotion-, Scheduler-, Runtime- oder Adapter-Code kann ihn nicht deaktivieren,
- Trip erhöht `revocation_epoch` und invalidiert alte Trading-Authorities,
- Reset nur über gültige Recovery- und Reset-Authority,
- Resume ist immer eine neue Aktivierung,
- Parallel-SSOT und alternative KillSwitch-Pfade sind verboten.

## 9.3 Position Remediation

Für die erste Live-Stufe zulässige policy-gebundene Aktionen:

```text
HOLD_AND_MONITOR
SUSPEND_NEW_ORDERS
CANCEL_OPEN_ORDERS
REDUCE_ONLY
CLOSE_WITH_BOUNDED_MARKETABLE_LIMIT
MANUAL_ESCALATION
```

`HEDGE` ist in der ersten Live-Stufe nicht autonom zulässig, da dadurch Bruttoexposure, Basisrisiko und Reconciliation-Komplexität steigen können.

Keine Remediation darf aus freiem AI-Reasoning entstehen.

## 9.4 Resume ist eine neue Aktivierung

Nach Incident, KillSwitch Trip oder Suspension ist `RESUME` kein einfaches Fortsetzen.

Erforderlich sind:

- vollständige R4-Reconciliation,
- neue Runtime Eligibility,
- neues Authority Lease,
- neue `trading_epoch`,
- neuer `executor_epoch`,
- erneute Venue-, Account-, Position- und Open-Order-Prüfung,
- Invalidierung alter Intents und Execution Permissions.

## 9.5 Automatische Trigger

- Daily Loss Limit,
- Risk- oder Capital-Limit,
- Data Quality Failure,
- Venue-/Adapter Failure,
- Reconciliation Failure,
- unerwartete Position,
- unbekannter Orderstatus,
- Manifest-/Digest-Mismatch,
- Runtime Health Failure,
- Kostenbudgetüberschreitung,
- Authority-Ablauf oder Revocation,
- Lease-Verlust oder Split-Brain-Verdacht,
- Clock- oder Sequence-Anomalie,
- Market-Data- oder Orderbook-Staleness,
- Margin- oder Leverage-Drift.

---

# 10. AI- und Modellkosten

## Tier 0 — Kein Modell

Für:

- Validatoren,
- Digests,
- Schema Checks,
- Risk Gates,
- Thresholds,
- Reconciliation,
- State Machines,
- deterministische Rankings.

## Tier 1 — Günstiges Modell

Für:

- Zusammenfassungen,
- Klassifikation,
- standardisierte Ursachenanalyse,
- Proposal-Erstellung.

## Tier 2 — Starkes Modell

Nur für:

- widersprüchliche Evidence,
- komplexe Regimewechsel,
- Promotion-Konflikte,
- ungewöhnliche Anomalien.

## Tier 3 — Multi-Agent

Nur für:

- High-impact Strategy Mutation,
- Architekturänderungen,
- unbekannte Fehlerbilder,
- Safety-/Risk-Unklarheiten.

## Budgetregeln

- AI-Aufruf nur bei explizitem Trigger,
- Cache nach Input-Digests,
- keine erneute Analyse unveränderter Evidence,
- deterministischer Fallback,
- `ABSTAIN` statt erzwungener Entscheidung,
- Tages- und Laufbudgets fail-closed.

---

# 11. Beschleunigter kritischer Pfad

Der schnellste belastbare Pfad lautet:

```text
1. Autonomy Policy + Canonical Trading Core Preservation Contract
2. Trading-Core Single-SSOT Registry + Module-Owner/Digest Compatibility Baseline
3. Comparison Completion Evidence
4. Research Validity Binding
5. Completion → Promotion Input
6. Promotion Policy Decision
7. Promoted Strategy Artifact
8. Handoff Trust Policy + Authority Lease + Secure Handoff Contracts
9. Atomic Claim/Consume + Clock Trust + TOCTOU Revalidation
10. Trading Session Single Writer + Canonical Order Lifecycle
11. Trading-Core Decision Attestation + Semantic-Diff Evidence
12. Runtime Reconciliation + Unknown-Outcome-Recovery
13. Adapter Submission Contract + Venue Capability Drift Guards
14. Independent Pre-Trade Safety Kernel + KillSwitch Writer-Fencing
15. Runtime Eligibility + Deploy Inactive
16. Runtime Observation + Feedback
17. Autonomous Shadow/Paper/Testnet
18. Live Canary / Micro-Live
19. Full Autonomous Production
```

## Parallelisierung

Nach Abschluss von Phase 1 dürfen zwei Tracks parallel laufen:

### Track A

```text
Research Validity
→ Promotion Input
→ Promotion Decision
→ Strategy Artifact
```

### Track B

```text
Authority Lease
→ Secure Handoff
→ Single Writer / Fencing
→ Canonical Order Lifecycle
→ Order Intent Idempotency
→ Reconciliation
→ Unknown-Outcome-Recovery
→ Safety Kernel
```

Anschließend werden beide Tracks in Runtime Eligibility und Testnet-Orchestration zusammengeführt.

Diese Parallelisierung spart Zeit, ohne zwei fachliche SSOTs zu erzeugen.

---

# 12. Realistischer Gesamtplan

## Meilenstein M1 — Offline Autonomy Foundation

**Dauer:** etwa 3–5 Wochen

Enthält:

- Autonomy Policy,
- Canonical Trading Core Preservation Contract,
- Trading-Core Single-SSOT Registry,
- Modul-Owner-/Digest-Registry und Compatibility Baseline,
- Completion Evidence,
- Research Validity,
- Promotion Input,
- Policy Decision,
- Strategy Artifact.

Ergebnis:

```text
Protected Canonical Trading Logic
+ Verified Research/Comparison
→ Reproducible Compatible Promoted Artifact
```

Noch keine Runtime-Aktivierung.

## Meilenstein M2 — Safe Autonomous Runtime Foundation

**Dauer:** parallel und anschließend insgesamt etwa 4–7 Wochen

Enthält:

- Authority Lease und Revocation,
- Secure Handoff Envelope,
- Single-Writer- und Fencing-Garantie,
- kanonische Order-State-Machine,
- Order Intent Idempotency,
- Reconciliation,
- Safety Kernel,
- Unknown-Outcome-Recovery,
- Runtime Eligibility,
- Deploy Inactive.

Ergebnis:

```text
Promoted Artifact
→ Safe Deployable Runtime Candidate
```

## Meilenstein M3 — Autonomous Non-Live Loop

**Gesamtkorridor ab Start:** etwa 8–12 Wochen

Enthält:

- Runtime Observation,
- Feedback,
- Shadow/Paper/Testnet Orchestrator,
- Champion/Challenger,
- Recovery Drills.

Ergebnis:

```text
Closed Autonomous Testnet Loop
```

## Meilenstein M4 — Live Canary Readiness

**Gesamtkorridor ab Start:** etwa 12–16 Wochen

Enthält:

- Micro-Live Authority,
- harte Limits,
- Live Reconciliation,
- Position Remediation,
- Incident- und Recovery-Prozeduren,
- nachgewiesene Shadow/Paper/Testnet-SLOs.

Ergebnis:

```text
Technically Ready for Bounded Live Canary
```

Die tatsächliche Live-Freigabe bleibt ein separater expliziter Authority-Schritt.

---

# 13. Was nicht vor Micro-Live vollständig sein muss

Zur Vermeidung unnötiger Verzögerungen können folgende Punkte nachgelagert gehärtet werden, sofern der Minimum Safe Slice vorhanden ist:

- Multi-Venue-Orchestration,
- mehrere gleichzeitig aktive Instrumente,
- automatische Strategy-Mutation Klasse C; insbesondere keine autonome Änderung an Master V2, Double Play, Bull/Bear oder Dynamic Scope,
- vollautomatische Model-Family-Erzeugung,
- komplexe Multi-Agent-Debatten,
- allgemeine Portfolio-Capital-Allocation,
- hochskalierte Datenplattform,
- vollständig automatisierte regulatorische Dokumentation,
- dynamische Risk-Limit-Erhöhung,
- autonome Venue-Onboarding-Prozesse.

Der erste autonome Pfad bleibt bewusst:

```text
eine Venue
→ ein qualifiziertes Futures-Instrument
→ ein Champion
→ maximal ein Challenger
→ feste Risk-/Capital-Limits
```

---

# 14. Erfolgskriterien für echte Vollautonomie

Das System gilt erst dann als vollautonom, wenn:

- kein manueller Dateihandoff erforderlich ist,
- keine manuelle Auswahl von Vergleichsergebnissen im Normalbetrieb nötig ist,
- keine manuelle Promotion im Normalbetrieb nötig ist,
- keine manuelle Shadow/Paper/Testnet-Aktivierung nötig ist,
- Live-Canary innerhalb fester Limits automatisch betrieben werden kann,
- Orders und Positionen kontinuierlich reconciled werden,
- unbekannte Orderzustände fail-closed behandelt werden,
- vollständige Feedback-Kette existiert,
- automatische Containment- und Recovery-Pfade bestehen,
- der kanonische KillSwitch an Activation-, Scheduler-, Pre-Trade- und Adapter-Grenzen unabhängig durchgesetzt wird,
- ein KillSwitch-Trip Authority Leases, Execution Permissions und nicht übertragene Intents atomar invalidiert,
- kein Restart, Redeploy, Failover oder Recovery-Prozess den KillSwitch automatisch zurücksetzt,
- jeder Reset evidence-gebunden ist und eine neue Aktivierung mit neuer Trading- und Executor-Epoch erfordert,
- Kosten- und Risk-Gates automatisch wirken,
- alle Entscheidungen reproduzierbar sind,
- vollständiger Audit-Trail existiert,
- Strategy-/Model-/Parameter-Versionierung eindeutig ist,
- alle Live-Aktionen aus gültigen, nicht abgelaufenen und nicht widerrufenen Authority-Leases ableitbar sind,
- jeder Runtime-Handoff digest-, sequence- und replay-geschützt ist,
- pro Venue-/Account-/Instrument-/Epoch-Kontext genau ein Execution Owner aktiv ist,
- jede Order einem kanonischen Lifecycle und einer Single-Use Execution Permission folgt,
- Unknown Outcomes niemals durch blindes Resubmit behandelt werden,
- Resume nach Incident immer eine neue Aktivierung mit neuer Trading Epoch ist,
- AI keine Risk-, Capital-, Safety- oder Authority-Grenzen selbst verändern kann,
- Master V2, Bull, Bear, Double Play, Dynamic Scope, Risk, Sizing und Scope Capital gemeinsam dauerhaft den Trading Decision Core des einen kanonischen Peak-Trade-Handelssystems bilden,
- KillSwitch, Authority, Pre-Trade Safety, Execution Permission, Adapter-Durchsetzung, Reconciliation, Recovery und Runtime State Authority dauerhaft den Safety, Execution & Runtime Authority Core desselben Systems bilden,
- kein einzelnes Trading-Core-Modul als separates Trading-System behandelt oder aktiviert wird,
- Master V2 dauerhaft Composition- und Runtime-Orchestrierungs-Owner innerhalb des Trading Core bleibt,
- Double Play dauerhaft Koordinations- und Konflikt-Owner innerhalb des Trading Core bleibt,
- Bull- und Bear-Komponenten getrennte, transparente und regressionsgetestete Semantik-Owner innerhalb des Trading Core bleiben,
- Dynamic Scope innerhalb der Authority-Grenzen dynamischer Auswahl-Owner des Trading Core bleibt,
- kein Order Intent die kanonische Trading-Kette umgehen kann,
- jede Promotion und Aktivierung gültige Trading-Logic Compatibility Evidence besitzt,
- jeder ausführungsrelevante Handoff atomar geclaimt und genau einmal konsumiert wird,
- Signaturen gegen eine versionierte Handoff Trust Policy und einen nicht widerrufenen Trust Root geprüft werden,
- Producer-Validierung niemals die unabhängige Consumer-Validierung ersetzt,
- Authority, KillSwitch, Epochs und Reconciliation unmittelbar vor jedem externen Side Effect erneut geprüft werden,
- Clock-Unklarheit neue Order-Side-Effects fail-closed blockiert,
- die tatsächliche Ausführung aller Trading-Core-Module über eine geschlossene Decision-Attestation-Chain nachgewiesen wird,
- Semantic Diffs durch Replay-, Boundary-, Risk- und Order-Intent-Vergleiche maschinenprüfbar sind,
- der Adapter keine fachliche Semantik verändern oder Unknown Outcomes blind wiederholen kann,
- Venue-Capability-Drift laufende Sessions suspendiert und erneute Eligibility erfordert,
- der KillSwitch durch Writer-Fencing, monotone Sequenzen und eine manipulationssichere Digest-Kette geschützt ist,
- Safety Kernel und Adapter den KillSwitch über technisch unabhängige Read Paths prüfen,
- keine parallele Trading-Logic-, Safety-, KillSwitch-, Reconciliation- oder Runtime-Authority-SSOT existiert.

---

# 15. Nächste konkrete Aktion

Vor dem nächsten ausführenden Implementierungsschritt wird ein begrenzter read-only Baseline- und Owner-Audit durchgeführt:

```text
canonical_peak_trade_trading_system_baseline_and_owner_binding_audit_v1
```

Der Audit bindet die realen kanonischen Owner, Contracts, Digests, Call-Graph-Kanten und Regressionstests für:

```text
Canonical Peak Trade Trading System

Trading Decision Core
- Master V2
- Double Play
- Bull
- Bear
- Dynamic Scope
- Risk / Sizing / Scope Capital

Safety, Execution & Runtime Authority Core
- Pre-Trade Safety
- Authority / Revocation
- Execution Permission
- Adapter Submission Boundary
- KillSwitch
- Reconciliation
- Recovery / Runtime State Authority
```

Er erzeugt keine neue Handelslogik und keine Runtime-Mutation. Danach bleibt der nächste fachliche Implementierungsschritt:

```text
comparison_completion_evidence_v1
```

Dieser Slice ist:

- klein,
- offline,
- deterministisch,
- risikoarm,
- direkt anschlussfähig,
- in wenigen Arbeitstagen umsetzbar,
- an die Trading-Logic-Preservation-Baseline gebunden.

Unmittelbar danach folgt:

```text
research_validity_evidence_v1
```

oder ein enger Binding-Slice zu bereits vorhandener Robustness-Evidence.

Parallel dazu sollte die read-only Architektur- und Gap-Prüfung für folgende Runtime-Contracts beginnen, in dieser Reihenfolge:

```text
handoff_trust_policy_v1
authority_lease_and_revocation_v1
secure_handoff_envelope_v1
handoff_atomic_claim_consume_v1
clock_trust_and_expiry_v1
trading_session_single_writer_v1
canonical_order_lifecycle_v1
order_intent_idempotency_v1
trading_core_decision_attestation_v1
adapter_submission_contract_v1
venue_capability_snapshot_v1
runtime_state_reconciliation_v1
unknown_execution_outcome_recovery_v1
independent_pretrade_safety_kernel_v1
```

Die Trust-, Authority-, Secure-Handoff-, Atomic-Consume-, Clock-Trust- und Single-Writer-Contracts sind vor einer ausführenden Safety- oder Testnet-Orchestration verbindlich zu spezifizieren. Noch keine Runtime-Mutation, keine Orders und keine Freischaltung ohne separaten GO.

---

# 16. Verbindliche Leitlinie

Das Endziel ist ein **vollautonomes Futures-Trading-System**.

Die Umsetzung wird bewusst zeitoptimiert:

- Wiederverwendung vor Neubau,
- zwei parallele Tracks statt langer serieller Kette,
- Minimum Safe Slice vor Hardening,
- eine Venue und ein Instrument im ersten autonomen Pfad,
- keine unnötige Plattformgeneralisierung,
- keine AI dort, wo deterministische Logik genügt,
- keine Safety-, Authority-, Handoff- oder Reconciliation-Schulden,
- kein blindes Retry bei unklarem Orderausgang,
- Single-Writer und Fencing vor autonomer Ausführung,
- keine Parallel-SSOT,
- genau ein kanonisches Peak-Trade-Handelssystem statt separater Trading-, Safety-, KillSwitch- oder Reconciliation-Systeme,
- Trading Decision Core und Safety, Execution & Runtime Authority Core als interne, klar getrennte Authority-Domänen desselben Systems,
- kein Ersatz oder Bypass des Handelssystems oder seiner Modul- und Authority-Owner,
- jede Promotion und Runtime-Aktivierung mit Trading-Logic Compatibility Evidence,
- kein Live-Pfad ohne belastbare Evidence.

Jede Stufe muss:

- die nächste Automatisierungsstufe vorbereiten,
- eine Sackgasse vermeiden,
- keine doppelte Evidence erzeugen,
- keine unnötigen Kosten verursachen,
- reproduzierbar und auditierbar sein,
- jederzeit fail-closed bleiben.
