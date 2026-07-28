# Peak Trade — Kanonisches Vollautonomie-Runbook v4.4.12
## Core-System-Konsistenz, Reuse-First-Integration & Economic Viability

**Status:** Kanonisches strategisches und operatives Implementierungsrunbook
**Version:** 4.4.12-full-canonical-system-parity-before-system-economic-evidence
**Stand:** 12. Juli 2026
**Operator:** Frank Rauter  
**Systemziel:** Vollautonomes, futures-only Peak-Trade-System mit deterministischer, konsistenter und auditierbarer Handelslogik; realistischer Profitabilitätsvalidierung; unabhängiger Safety Authority; gefenceter Single-Writer-Runtime; vollständiger Reconciliation; sicherer Restart-/Recovery-Semantik; einer durchgängigen Research→Validation→Promotion→Runtime→Feedback-Kette; und einem klar getrennten Pfad von initialer Single-Future-Safety-Phase zu späterer Multi-Future-Portfolio-Runtime nach separaten Gates.  
**Keine Anlageberatung.**

**Integrierte Erweiterung:** Offline Linear Evidence Layer / OLS v1.1 als rein diagnostischer Economic-Validation-Support ohne Runtime-, Trading-, Promotion- oder Sizing-Authority.

**Parameter-Governance:** Kein eigenständiges zweites Runbook. Ausschließlich schlanke, der kanonischen Handelslogik untergeordnete Mess-, Kosten-, Reproduzierbarkeits- und Kalibrierungsregeln.


---

# STATE-INDEPENDENT CONTINUATION CONTRACT — Verbindliche Arbeitsweise in neuen Chats

Dieses Runbook ist die kanonische, inhaltlich stabile Verfahrens- und Sicherheits-SSOT. Sein fachlicher Wert hängt nicht davon ab, dass nach jedem PR ein eingebetteter Statusblock oder eine Desktop-Kopie überschrieben wird.

```text
RUNBOOK_CANONICAL_NORMS_ARE_STATE_INDEPENDENT=true
RUNBOOK_REWRITE_AFTER_MERGE_REQUIRED=false
DESKTOP_RUNBOOK_SYNC_REQUIRED=false
CURSOR_MAY_NOT_REWRITE_RUNBOOK_FOR_PROGRESS_TRACKING=true
CURRENT_STATE_MUST_NOT_WEAKEN_CANONICAL_NORMS=true
```

Die vollständige Handelslogik, Safety-, Risk-/Sizing-, Reconciliation-, Promotion-, Evidence- und Authority-Semantik dieses Dokuments bleibt unverändert maßgeblich.

## Verbindliche Fortsetzungsregel

Ein neuer Chat oder eine neue Arbeitssitzung muss dieses Runbook als gültige kanonische Vorgehensgrundlage verwenden. Fortschritt wird nicht dadurch hergestellt, dass das Runbook neu geschrieben wird, sondern durch belegte Abschlussstände:

```text
1. letzter im Chat oder Übergabeprotokoll genannter manifest-verifizierter Merge-Closeout,
2. zugehörige Source-, Implementation- und Closeout-Evidence,
3. Repo-Progress-Owner, sofern direkter Repo-Zugriff besteht,
4. andernfalls der letzte im Runbook dokumentierte Checkpoint als sicherer Fallback.
```

```text
LATEST_VERIFIED_EXTERNAL_EVIDENCE_OVERRIDES_EMBEDDED_PROGRESS_ONLY=true
LATEST_VERIFIED_EXTERNAL_EVIDENCE_MAY_NOT_OVERRIDE_CANONICAL_NORMS=true
RUNBOOK_MAY_NOT_BE_REJECTED_AS_STALE_WITHOUT_CONTRADICTORY_NEWER_EVIDENCE=true
NO_AUTOMATIC_RUNBOOK_MUTATION=true
```

Ein neuerer belegter Projektstand supersediert ausschließlich:

```text
HEAD
ORIGIN_MAIN
LATEST_MERGED_PR
abgeschlossene Phase
Evidence-Pfade
Progress-Flags
NEXT_STEP
```

Er supersediert niemals:

```text
CONSTITUTIONAL_SAFETY_INVARIANTS
CANONICAL_TRADING_LOGIC
MASTER_V2_SEMANTICS
DOUBLE_PLAY_SEMANTICS
SCOPE_ENTRY_EXIT_REVERSAL_SEMANTICS
RISK_AND_SIZING_CONTRACTS
SAFETY_KERNEL
KILLSWITCH
RECONCILIATION
AUTHORITY_BOUNDARIES
PROMOTION_GATES
IMPLEMENTATION_SEQUENCE
```

## Verhalten ohne direkten Repo-Zugriff

Liegt ein manifest-verifizierter Final Report oder Merge-Closeout im Chat vor, ist dieser als aktueller Fortschrittsstand zu verwenden. Der nächste Schritt wird unmittelbar aus diesem Abschlussstand und der kanonischen Sequenz dieses Runbooks abgeleitet.

```text
FINAL_REPORT_ACCEPTED_AS_SESSION_PROGRESS_EVIDENCE=true
NO_REPO_ACCESS_DOES_NOT_INVALIDATE_RUNBOOK=true
NO_GENERIC_STALE_RUNBOOK_REJECTION=true
NO_RUNBOOK_REFRESH_PR_REQUIRED=true
```

Fehlt ein neuerer Abschlussstand vollständig, gilt der eingebettete Fallback-Checkpoint. Vor einer tatsächlichen Repo-Mutation muss der erzeugte Cursor-Befehl weiterhin read-only prüfen:

```text
origin/main HEAD
local HEAD
HEAD_EQUALS_ORIGIN_MAIN
worktree status
latest relevant merged PR
relevante Progress-Owner
referenzierte MANIFEST.sha256
```

Eine Abweichung korrigiert den geplanten Slice, nicht das Runbook.

## Fail-closed bleibt erhalten

```text
UNKNOWN_OR_CONTRADICTORY_PROGRESS_STATE
→ READ_ONLY_RECONCILIATION
→ NO_MUTATION_UNTIL_RESOLVED
```

```text
NO_ECONOMIC_EVALUATION_FROM_UNVERIFIED_STATE=true
NO_RUNTIME_WORK_FROM_UNVERIFIED_STATE=true
NO_AUTHORITY_FROM_PROGRESS_EVIDENCE=true
NO_NEGATIVE_EVIDENCE_OVERRIDE=true
NO_POLICY_RESCUE=true
```

Diese State-Unabhängigkeit lockert keine fachliche oder sicherheitsrelevante Grenze. Sie verhindert ausschließlich, dass Fortschrittsmetadaten die kanonische Runbook-SSOT fortlaufend verändern.

---

# FALLBACK CURRENT-STATE CHECKPOINT — post PR #5078

Dieser Checkpoint ist der letzte in dieser Datei dokumentierte belastbare Stand. Neuere manifest-verifizierte Abschlussberichte dürfen ihn als Fortschrittsstand supersedieren, ohne diese Datei zu verändern.

```text
FALLBACK_CURRENT_STATE_SCHEMA=PEAK_TRADE_EXTERNAL_PROGRESS_COMPATIBILITY_V1
FALLBACK_CURRENT_STATE_HEAD=5a5ab570022cae47ec5442638ab0180f66caa1e4
FALLBACK_CURRENT_STATE_ORIGIN_MAIN=5a5ab570022cae47ec5442638ab0180f66caa1e4
HEAD_EQUALS_ORIGIN_MAIN=true
WORKTREE_CLEAN=true

LATEST_MERGED_PR=5078
LATEST_MERGED_PR_TITLE=Phase 3 dataset materialization: CS MA-crossover panel rank-rotation v0
PR5078_MERGE_CLOSEOUT_COMPLETE=true
SOURCE_MANIFEST_VERIFY_RC=0
IMPLEMENTATION_MANIFEST_VERIFY_RC=0
CLOSEOUT_MANIFEST_VERIFY_RC=0

RESEARCH_SCOPE=cross_sectional_ma_crossover_panel_rank_rotation/v0
DATASET_MATERIALIZED=true
DATASET_ID=pit_okx_linear_usdt_non_bitcoin_pt1h_panel
DATASET_SCHEMA=pit_okx_pt1h_panel_ohlcv_dataset_manifest_v1
DATASET_STAGING_VERSION=2
INSTRUMENT_COUNT=399
BITCOIN_PRESENT=false
BAR_INTERVAL=PT1H
WINDOW_START_UTC=2026-07-06T10:00:00Z
WINDOW_END_UTC=2026-07-10T08:00:00Z
ROW_COUNT_TOTAL=37905
DATASET_DIGEST=c753c5795ab40d26237a066702cb72a06065bfce0143440ec0ccadfe249cc0e0

UNDERLYING_SIGNAL_BINDING=ma_crossover/v1
PRIOR_SINGLE_INSTRUMENT_EVIDENCE=TERMINAL_NEGATIVE
UNCHANGED_SINGLE_INSTRUMENT_RETRY_BLOCKED=true
PANEL_ARCHETYPE_EVIDENCE=NOT_PREVIOUSLY_EXECUTED
MATERIAL_DIFFERENCE=CROSS_SECTIONAL_MULTI_INSTRUMENT_PANEL_RANK_ROTATION

ECONOMIC_EVALUATION_EXECUTED=false
RUNTIME_EFFECT=NONE
AUTHORITY_EFFECT=NONE
ECONOMIC_VALIDITY_OFFLINE_GATE_PASS=false
RUNTIME_REWIRE_ADMISSIBLE=false

DURABLE_CLOSEOUT_BUNDLE=/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/pr5078_merge_closeout_cross_sectional_ma_crossover_panel_rank_rotation_v0_phase3_dataset_materialization_v0_20260710T094803Z

NEXT_STEP=VERSIONED_BINDING_RATIFICATION_REQUIRES_SEPARATE_OPERATOR_GO
```

Interpretation:

```text
Phase 3 Dataset Materialization ist abgeschlossen.
Das Panel-Dataset ist vorhanden und digest-gebunden.
Die Panel-Hypothese ist noch nicht vollständig versioniert gebunden.
Es wurde keine Economic Evaluation ausgeführt.
Es entstand keine Runtime- oder Trading-Authority.
Der nächste kanonische Schritt ist eine separat autorisierte, offline-only versionierte Binding-Ratifikation.
```

---

# 0. Zweck dieser Version

Dieses Runbook konsolidiert:

1. die vollständige Zielsemantik aus Runbook v4.3,
2. den realen Repo-Ist-Zustand aus dem systemweiten Multi-Agent-Audit,
3. die bestätigte Reuse-First-Strategie,
4. die Notwendigkeit belastbarer Economic-Viability-Evidence,
5. die korrigierte Implementierungsreihenfolge,
6. die klare Trennung zwischen vorhandener Capability, tatsächlicher Verdrahtung und nachgewiesener Profitabilität,
7. die Klarstellung, dass `MAX_POSITIONS=1` eine initiale Safety-/Stability-Phase ist und das langfristige Ziel weiterhin ein futures-only Multi-Instrument-Portfolio-System aus einem Top20-Futures-Universum bleibt,
8. die ausdrückliche Klarstellung, dass belastbare System-Economic-Evidence erst nach vollständiger kanonischer Umsetzung und Verdrahtung der gesamten relevanten Peak-Trade-Kette zulässig ist: Trading Decision Core, Bull/Bear State Switch, Scope/Exit/Reversal, Survival/Suitability, Double Play, Capital/Risk/Sizing, Safety/KillSwitch/Reconciliation, Promotion Gates, Observability/AI-Layer und Feedback-Pfade,
9. die feste operative Regel, dass jeder Merge-Closeout nach dem Merge gegen `origin/main` synchronisiert und die Closeout-Evidence per `MANIFEST.sha256` mit `RC=0` verifiziert werden muss,
10. die Klarstellung, dass referenzierte Source-Evidence-Bundles ebenfalls per `MANIFEST.sha256` mit `RC=0` erneut verifiziert werden müssen; falls ein Closeout keinen Source-Evidence-Bezug hat, muss dieser Fall explizit als `SOURCE_EVIDENCE_NOT_REFERENCED=true` dokumentiert werden und darf nicht stillschweigend als verifiziert gelten,
11. die operative Sequenzklarstellung, dass das vollständige Core-System zuerst kanonisch fertiggestellt und manifest-verifiziert werden muss, bevor irgendeine Runtime-, Shadow-, Paper-, Testnet-, Canary-, Live-, Zero-Order- oder sonstige ausführungsnahe Evidence-Erzeugung als nächster Arbeitsstrom zulässig ist,
12. die Einbettung des Offline Linear Evidence Layer / OLS v1.1 als deterministischen, manifest-verifizierten Diagnose-, Kalibrierungs- und Evidence-Support für Kostenmodellierung, Signal-Orthogonalität, Faktor-Exposure, Parameter-Sensitivität und Drift-Diagnostik, ohne die kanonische Trading-SSOT, Safety-, Promotion-, Risk-/Sizing- oder Runtime-Grenzen zu verändern.

Diese Version ersetzt nicht die vorhandene Master-V2-, Backtest-, Monte-Carlo-, Walk-Forward-, Portfolio-, Safety- oder Evidence-Infrastruktur.

Sie definiert, wie die vorhandenen Komponenten ohne parallele SSOTs in eine kanonische, wirtschaftlich prüfbare Gesamtkette überführt werden.

---

# 0.1 Zentrale Entscheidung

```text
PEAK_TRADE_REBUILD_REQUIRED=false
REUSE_FIRST=true
GREENFIELD_ECONOMIC_VALIDATION_STACK_ALLOWED=false
PARALLEL_TRADING_SSOT_ALLOWED=false
PARALLEL_PROFITABILITY_SSOT_ALLOWED=false
FULL_CANONICAL_SYSTEM_COMPLETION_BEFORE_SYSTEM_ECONOMIC_EVIDENCE=true
FULL_CANONICAL_SYSTEM_COMPLETION_BEFORE_RUNTIME_EVIDENCE=true
NO_RUNTIME_EVIDENCE_BEFORE_CORE_SYSTEM_COMPLETE=true
RAW_SIGNAL_EVALUATION_IS_NOT_SYSTEM_ECONOMIC_EVIDENCE=true

OFFLINE_LINEAR_EVIDENCE_LAYER_ALLOWED=true
OLS_RUNTIME_AUTHORITY=false
OLS_ORDER_AUTHORITY=false
OLS_ENTRY_EXIT_AUTHORITY=false
OLS_SIZING_AUTHORITY=false
OLS_PROMOTION_PASS_AUTHORITY=false
OLS_ALLOWED_FOR_ECONOMIC_EVIDENCE_SUPPORT=true
OLS_ALLOWED_FOR_COST_CALIBRATION_DIAGNOSTICS=true
OLS_ALLOWED_FOR_SIGNAL_ORTHOGONALITY_DIAGNOSTICS=true
OLS_ALLOWED_FOR_FACTOR_EXPOSURE_DIAGNOSTICS=true
OLS_ALLOWED_FOR_PARAMETER_SENSITIVITY_DIAGNOSTICS=true
OLS_ALLOWED_FOR_ROLLING_DRIFT_DIAGNOSTICS=true
```

Der aktuelle Peak-Trade-Stack enthält bereits:

- Master-V2-/Double-Play-Pure-Stack,
- Backtest Engine,
- Walk-Forward,
- Monte Carlo,
- Stress-Tests,
- Portfolio-Backtests,
- Performance-Metriken,
- Strategy Profiles,
- SafetyGuard,
- KillSwitch,
- Reconciliation,
- Evidence- und Manifest-Infrastruktur.

Die bestätigten Lücken sind primär:

- semantische Completion,
- fehlende kanonische Wiring-Pfade,
- Research-/Runtime-Drift,
- parallele Owner,
- fehlende persistierte Netto-Performance-Evidence,
- fehlende technische Profitabilitäts-/Robustness-Gates in Promotion,
- fehlender manifestierter Nachweis, dass Economic Validation bereits die vollständige kanonische Systemkette und nicht nur isolierte Research-/Signal-Archetypen bewertet.

---

# 0.1A Vollständige kanonische Systemparität vor System-Economic-Evidence

Die Economic Validation bewertet ausschließlich die tatsächlich ausgeführte kanonische Systemkette. Negative oder nicht aussagekräftige wirtschaftliche Ergebnisse dürfen daher nicht automatisch der kanonischen Peak-Trade-Handelslogik zugeschrieben werden.

Vor jeder fachlichen Interpretation von Economic-Ergebnissen ist nachzuweisen, dass die vollständige kanonische Systemkette tatsächlich verdrahtet und in der Evaluation verwendet wurde. Vorhandener Code genügt nicht; die vollständige Kette muss tatsächlich verdrahtet sein. Backtest-, Offline- und Runtime-Entscheidungskette müssen dieselbe kanonische Decision Chain verwenden.

```text
FULL_CANONICAL_SYSTEM_PARITY_REQUIRED=true
FULL_CANONICAL_SYSTEM_WIRING_REQUIRED=true
BACKTEST_RUNTIME_DECISION_PARITY_REQUIRED=true
RESEARCH_RUNTIME_DRIFT_ALLOWED=false

FULL_CANONICAL_SYSTEM_COMPLETION_BEFORE_SYSTEM_ECONOMIC_EVIDENCE=true
FULL_CANONICAL_SYSTEM_COMPLETION_BEFORE_RUNTIME_EVIDENCE=true

RAW_SIGNAL_EVALUATION_IS_NOT_SYSTEM_ECONOMIC_EVIDENCE=true
PARTIAL_PIPELINE_EVALUATION_IS_NOT_SYSTEM_ECONOMIC_EVIDENCE=true
ISOLATED_RESEARCH_EVIDENCE_IS_NOT_CANONICAL_SYSTEM_EVIDENCE=true
```

Zur kanonischen Systemkette gehören mindestens:

```text
Canonical Market Context
→ Scope Initialization
→ Scope Event Generation
→ Bull/Bear Directional Assessment
→ Bull/Bear State Switch
→ Survival
→ Suitability
→ Double Play
→ Entry
→ Position Management
→ Exit / Reversal
→ Capital
→ Risk
→ Position Sizing
→ Safety
→ KillSwitch
→ Reconciliation
→ Economic Validation
```

System-Economic-Evidence ist ausschließlich zulässig, wenn die vollständige kanonische Peak-Trade-Systemkette evaluiert wurde. Research-only-, Raw-Signal- oder Partial-Pipeline-Evaluationen dürfen nicht als kanonische System-Economic-Evidence interpretiert werden.

Ergibt eine Offline-Economic-Evaluation nur eine geringe Stichprobe oder ein wirtschaftlich negatives Resultat, ist zunächst read-only zu prüfen, ob die vollständige kanonische Systemkette tatsächlich evaluiert wurde und vollständige kanonische Parität sowie Verdrahtung vorlagen. Fehlende Wiring-Pfade oder semantische Completion sind zuerst reuse-first und semantikneutral zu schließen. Erst anschließend ist eine erneute Economic Evaluation fachlich belastbar und dürfen Economic-Ergebnisse fachlich interpretiert werden.

Dieser Abschnitt erzeugt keine neue Runtime-, Trading-, Promotion- oder Authority-Semantik.

```text
IMPLEMENTATION_CONTRACT_ADDITIVE_ONLY=true
CORE_TRADING_SEMANTICS_CHANGED=false
CANONICAL_TRADING_LOGIC_CHANGED=false
MASTER_V2_SEMANTICS_CHANGED=false
DOUBLE_PLAY_SEMANTICS_CHANGED=false
SCOPE_ENTRY_EXIT_REVERSAL_SEMANTICS_CHANGED=false
RISK_SIZING_SEMANTICS_CHANGED=false
SAFETY_SEMANTICS_CHANGED=false
KILLSWITCH_SEMANTICS_CHANGED=false
RECONCILIATION_SEMANTICS_CHANGED=false
AUTHORITY_SEMANTICS_CHANGED=false
PROMOTION_GATE_SEMANTICS_CHANGED=false
ECONOMIC_VALIDITY_GATE_CHANGED=false
```

---

# 0.2 Normative Begriffe

```text
MUST
→ zwingend; Nichterfüllung blockiert den Schritt

MUST_NOT
→ verboten

SHOULD
→ Standard; Abweichung nur mit dokumentierter Begründung und Evidence

MAY
→ optionale Erweiterung ohne Authority- oder Semantikänderung
```

---

# 0.3 Runbook-Hierarchie

```text
PART_I_CONSTITUTION
PART_II_CANONICAL_TRADING_LOGIC
PART_III_ECONOMIC_VALIDITY_AND_RESEARCH_INTEGRATION
  └── OFFLINE_LINEAR_EVIDENCE_LAYER_OLS_DIAGNOSTICS
PART_IV_RUNTIME_SAFETY_AND_EXECUTION
PART_V_IMPLEMENTATION_AND_VALIDATION_LADDER
PART_VI_OPERATIONAL_AUTONOMY_AND_PRODUCTION
```

Konfliktrangfolge:

```text
CONSTITUTIONAL_SAFETY_INVARIANTS
> CANONICAL_TRADING_LOGIC_CONTRACTS
> ECONOMIC_VALIDITY_CONTRACTS
> RUNTIME_AUTHORITY_CONTRACTS
> IMPLEMENTATION_SEQUENCE
> NARRATIVE_GUIDANCE
```

---

# PART I — CONSTITUTION

# 1. Unveränderliche Systemgrenzen

```text
FUTURES_ONLY=true
BITCOIN_DIRECTION_ALLOWED=false
SPOT_ALLOWED=false
SYNTHETIC_SPOT_ALLOWED=false

PEAK_TRADE_CANONICAL_TRADING_SYSTEM=true
PEAK_TRADE_CANONICAL_TRADING_SYSTEM_SINGLE_SSOT=true
PEAK_TRADE_PARALLEL_TRADING_SYSTEM_ALLOWED=false

LIVE_AUTHORIZED=false
READY_FOR_OPERATOR_ARMING=false
ORDERS_ALLOWED=false
SCHEDULER_RUNTIME_ALLOWED=false

SHADOW_AUTHORIZED=false
PAPER_AUTHORIZED=false
TESTNET_AUTHORIZED=false
CANARY_AUTHORIZED=false
FULL_AUTONOMOUS_PRODUCTION_AUTHORIZED=false
```

Initiale spätere Canary-Limits:

```text
TOTAL_LIMIT_USD=500
ORDER_LIMIT_USD=25
DAILY_LOSS_LIMIT_USD=25
MAX_POSITIONS=1
MAX_ACTIVE_DIRECTIONAL_SIDE=1
SIMULTANEOUS_LONG_SHORT_EXPOSURE_ALLOWED=false
```

Diese Canary-Limits definieren ausschließlich die initiale Safety-/Stability-Runtime-Phase. Sie sind keine finale Produktgrenze.

```text
PHASE_1_RUNTIME_MODEL=SINGLE_SELECTED_FUTURE
PHASE_1_PURPOSE=SAFETY_STABILITY_RECONCILIATION_RECOVERY_RUNTIME_PROOF
PHASE_1_MAX_POSITIONS=1

FUTURE_TARGET_MODEL=MULTI_SELECTED_FUTURES_PORTFOLIO_RUNTIME
TOP20_FUTURES_UNIVERSE_TARGET=true
MULTI_SELECTED_FUTURES_ALLOWED_AFTER_SEPARATE_GATES=true
MULTI_FUTURE_RUNTIME_AUTHORIZED=false
```

Kein autonomer Prozess darf diese Grenzen erhöhen.

---

# 2. Kanonische Authority-Domänen

```text
CANONICAL_PEAK_TRADE_SYSTEM
├── TRADING_DECISION_CORE
├── CAPITAL_RISK_AND_SIZING_CORE
├── ECONOMIC_VALIDATION_CORE
├── SAFETY_EXECUTION_RUNTIME_CORE
└── LEARNING_PROMOTION_CORE
```

## 2.1 Trading Decision Core

```text
Canonical Market Context
→ Scope Initialization
→ Scope Event Generation
→ Bull/Bear Assessment
→ State Switch
→ Survival
→ Suitability
→ Double Play
→ Canonical Trading Decision
```

## 2.2 Capital, Risk und Sizing Core

```text
Canonical Trading Decision
→ Scope Capital Envelope
→ Pre-Sizing Risk
→ Canonical Position Sizing
→ Post-Sizing Risk
→ Canonical Order Intent
```

## 2.3 Economic Validation Core

```text
Canonical Trading Decision Path
→ Backtest Execution Model
→ Costs
→ Offline Linear Evidence / OLS Diagnostics
→ Walk-Forward
→ Monte Carlo
→ Stress
→ Portfolio/Regime Evaluation
→ Economic Viability Evidence
```

## 2.4 Safety, Execution und Runtime Core

```text
Canonical Order Intent
→ Safety Kernel
→ Runtime Eligibility
→ Authority Lease
→ Single-Use Permission
→ Submission
→ Venue
→ Reconciliation
→ Recovery
```

## 2.5 Learning und Promotion Core

```text
Admissible Economic Evidence
→ Candidate
→ Validation
→ Promotion Decision
→ Deploy Inactive
→ Runtime Eligibility
```

Keine Domain darf ihre eigene Kontrollinstanz überschreiben.

---

# 3. Grundsatz: technische Korrektheit und wirtschaftliche Gültigkeit

Peak Trade benötigt zwei unabhängige Gates:

```text
SYSTEM_CORRECTNESS_GATE
ECONOMIC_VALIDITY_GATE
```

## 3.1 System Correctness

Prüft:

- Determinismus,
- State- und Authority-Semantik,
- Safety,
- Reconciliation,
- Recovery,
- Runtime-Integrität.

## 3.2 Economic Validity

Prüft:

- Netto-Erwartungswert,
- Kostenrealismus,
- Out-of-Sample-Stabilität,
- Walk-Forward,
- Monte Carlo,
- Stress,
- Regime-Stabilität,
- Drawdown,
- Portfolio-Beitrag,
- Reproduzierbarkeit.

## 3.3 Zusammenführung

```text
SYSTEM_CORRECTNESS_PASS
AND ECONOMIC_VALIDITY_PASS
→ eligible_for_shadow_candidate
```

Weder ein grüner Backtest noch ein grüner Safety-Test genügt allein.

### 3.3A Pre-Economic Zero-Order Evidence Stage (governed exception, additive)

Zwischen Integrated Offline Replay und dem Economic-Validity-Offline-Gate ist
eine **streng begrenzte** Evidence-Stufe zulässig:

```text
GOVERNED_PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_STAGE_V1=true
PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_SESSION_V1=true
```

```text
INTEGRATED_OFFLINE_REPLAY
→ PRE_ECONOMIC_ZERO_ORDER_EVIDENCE
→ ECONOMIC_VALIDITY_OFFLINE_GATE
→ PROMOTION / STEP 29R / 29T / 29U
```

Diese Stufe:

- erzeugt ausschließlich Evidence,
- besitzt keine Promotion-/Shadow-/Runtime-/Trading-Authority
  (`authority_effect=NONE`, `activation_effect=NONE`, `economic_gate_effect=NONE`),
- arbeitet ausschließlich Zero-Order (`orders_allowed=false`),
- blockiert Broker-/Order-Endpunkte (`broker_writes_allowed=false`),
- erlaubt maximal `21600` Sekunden,
- erfordert explizites Operator-GO,
- bricht fail-closed ab bei Order-Intent, Broker-Write, unbekanntem Session-State,
  Telemetrieverlust, Kill-State-Fehler, Risk-Engine-Fehler oder unvollständiger
  Entscheidungslogik-Bindung,
- setzt **nicht** `ECONOMIC_VALIDITY_OFFLINE_GATE_PASS`,
- autorisiert **nicht** STEP 29R / 29T / 29U / Paper / Testnet / Live.

`ECONOMIC_VALIDITY_OFFLINE_GATE_PASS` bleibt unverändert zwingende Voraussetzung für:

```text
STEP_29R_RUNTIME_REWIRE
STEP_29T_ZERO_ORDER_RUNTIME
STEP_29U_SHADOW
PAPER
TESTNET
LIVE
```

Kanonischer Session-Contract:
`docs/ops/runbooks/PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_SESSION_V1.md`.
Runtime-Ausführung bleibt `BLOCKED`, bis eine separate
Implementation-Readiness-Capability bestanden ist.

## 3.4 Vollständigkeitsprinzip vor System-Economic-Evidence

Peak Trade darf erst dann als vollständiges System wirtschaftlich beurteilt werden, wenn die vollständige kanonische Kette implementiert, verdrahtet und manifest-verifiziert ist.

```text
FULL_SYSTEM_COMPLETION_REQUIRED_BEFORE_SYSTEM_ECONOMIC_VALIDITY=true
PARTIAL_RESEARCH_SIGNAL_EVIDENCE_MAY_NOT_BE_PRESENTED_AS_SYSTEM_EVIDENCE=true
```

Dazu gehören mindestens:

```text
Canonical Market Context
→ Scope Initialization
→ Scope Event Generator
→ Bull/Bear Assessment
→ Bull/Bear State Switch
→ Survival
→ Suitability
→ Double Play
→ Entry / Position Management / Exit / Reversal Policy
→ Capital / Risk / Sizing
→ Canonical Order Intent
→ Safety Kernel
→ KillSwitch Policy
→ Runtime Eligibility and Authority Semantics
→ Reconciliation and Unknown Outcome Handling
→ Promotion Economic Gate
→ Observability / Explainability / AI-Layer
→ Feedback / Learning Boundary
```

Economic-Evaluation-Läufe, die nur eine Strategie-, Ranking-, Slot- oder Rohsignal-Hypothese simulieren, bleiben zulässige Research-Negativ- oder Explorations-Evidence. Sie dürfen aber nicht als vollständige Peak-Trade-System-Evidence, Promotion-Evidence oder Runtime-Rewire-Voraussetzung verwendet werden.

```text
RAW_SIGNAL_BACKTEST_ALLOWED=true
RAW_SIGNAL_BACKTEST_SCOPE=EXPLORATORY_OR_NEGATIVE_EVIDENCE_ONLY
SYSTEM_ECONOMIC_CLAIM_REQUIRES_FULL_CANONICAL_CHAIN=true
```

## 3.5 Core-System-Completion vor Runtime- oder ausführungsnaher Evidence

Die kanonische Arbeitsreihenfolge ist ausdrücklich Core-System-first.

Bevor Peak Trade irgendeine Runtime-, Shadow-, Paper-, Testnet-, Canary-, Live-, Zero-Order- oder sonstige ausführungsnahe Evidence-Erzeugung als nächsten Arbeitsstrom nutzt, muss das vollständige kanonische Core-System fertig verdrahtet, deterministisch geprüft und manifest-verifiziert sein.

```text
CORE_SYSTEM_FIRST_OPERATING_RULE=true
FULL_CANONICAL_SYSTEM_COMPLETION_BEFORE_RUNTIME_EVIDENCE=true
NO_RUNTIME_EVIDENCE_BEFORE_CORE_SYSTEM_COMPLETE=true
NO_ZERO_ORDER_RUNTIME_EVIDENCE_BEFORE_CORE_SYSTEM_COMPLETE=true
NO_SHADOW_PAPER_TESTNET_EVIDENCE_BEFORE_CORE_SYSTEM_COMPLETE=true
NO_CANARY_OR_LIVE_EVIDENCE_BEFORE_CORE_SYSTEM_COMPLETE=true
```

Diese Klarstellung ändert keine Safety-, Runtime-, Order-, Credential-, Shadow-, Paper-, Testnet-, Canary- oder Live-Authority. Sie ist eine Sequenzregel: Erst vollständige kanonische Core-Parität, danach überhaupt erst spätere Evidence-Stufen.

```text
SAFETY_SEMANTICS_CHANGED=false
RUNTIME_AUTHORITY_CHANGED=false
ORDER_AUTHORITY_CHANGED=false
CREDENTIAL_AUTHORITY_CHANGED=false
ECONOMIC_GATE_CHANGED=false
PROMOTION_GATE_CHANGED=false
```

## 3.6 Offline Linear Evidence / OLS als Economic-Support, nicht als Authority

Der Offline Linear Evidence Layer ist ein zulässiger Diagnose- und Kalibrierungs-Layer innerhalb der Economic-Validation-Domäne. Er darf die kanonische Handelslogik nicht erweitern, ersetzen, umgehen oder als eigenes Signal interpretieren.

```text
OLS_ROLE=OFFLINE_EVIDENCE_DIAGNOSTIC_AND_CALIBRATION_LAYER
LINEAR_MODEL_OUTPUT_IS_NOT_TRADING_DECISION=true
LINEAR_MODEL_OUTPUT_IS_NOT_PROMOTION_PASS=true
LINEAR_MODEL_OUTPUT_IS_NOT_RUNTIME_AUTHORITY=true
LINEAR_MODEL_OUTPUT_IS_NOT_MULTI_FUTURE_AUTHORITY=true
NO_RUNTIME_AUTHORITY_FROM_LINEAR_EVIDENCE=true
NO_ECONOMIC_CLAIM_FROM_OLS_ALONE=true
```

OLS darf als unterstützende Evidence genutzt werden für:

```text
COST_SLIPPAGE_DIAGNOSTICS
SIGNAL_ORTHOGONALITY_DIAGNOSTICS
FACTOR_EXPOSURE_DIAGNOSTICS
PARAMETER_SENSITIVITY_DIAGNOSTICS
ROLLING_LINEAR_DRIFT_DIAGNOSTICS
ECONOMIC_EVIDENCE_EXPLAINABILITY
```

OLS darf nicht genutzt werden für:

```text
ENTRY_SIGNAL
EXIT_SIGNAL
REVERSAL_SIGNAL
POSITION_SIZING
ORDER_INTENT_CREATION
STRATEGY_SELECTION_AUTHORITY
PROMOTION_PASS_AUTHORITY
RUNTIME_REWIRE_AUTHORITY
ACTIVE_SET_REPLACEMENT_AUTHORITY
```

Ein OLS-Scaffolding-Slice darf vor finaler System-Economic-Evidence gebaut werden, wenn er strikt offline-only bleibt und keinen Economic-Pass-Claim erzeugt. Produktive OLS-Diagnostics für System-Economic-Evidence dürfen erst nach manifest-verifizierter Full-Canonical-System-Backtest-Parität als entscheidungsrelevante Unterstützung verwendet werden.

Bis `FULL_CANONICAL_CHAIN_WIRED=true` und `BACKTEST_RUNTIME_DECISION_PARITY_PASS=true` manifest-verifiziert sind, bleibt der zulässige Arbeitsmodus auf Core-System-Completion, Offline-Parity-Assessment und narrow Reuse-First-Rewire beschränkt.

```text
ALLOWED_BEFORE_FULL_CORE_COMPLETION=CORE_SYSTEM_COMPLETION,OFFLINE_PARITY_ASSESSMENT,NARROW_REUSE_FIRST_REWIRE
DISALLOWED_BEFORE_FULL_CORE_COMPLETION=RUNTIME_EVIDENCE,SHADOW_EVIDENCE,PAPER_EVIDENCE,TESTNET_EVIDENCE,CANARY_EVIDENCE,LIVE_EVIDENCE,ORDER_SUBMISSION,CREDENTIAL_USE,ARMING
```

---

# PART II — CANONICAL TRADING LOGIC

# 4. Verbindliches Systemziel

Peak Trade bewertet einen ausgewählten Futures-Kontrakt mit zwei spezialisierten Richtungs-Layern:

```text
Bull-/Long-Layer
Bear-/Short-Layer
```

Beide gehören zu einem einzigen kanonischen Trading-System.

Master V2 und Double Play koordinieren die Seiten.

Nur eine Seite darf Directional Exposure besitzen.

---

# 5. Orthogonales Zustandsmodell

Jeder Runtime- und Decision-Snapshot führt mindestens:

```text
direction_state
trading_gate
position_state
execution_state
reconciliation_state
safety_mode
authority_state
data_integrity_state
economic_validation_state
```

Beispiel:

```text
direction_state=LONG_SELECTED
trading_gate=BLOCKED
position_state=OPEN_REDUCING
execution_state=PARTIALLY_FILLED
reconciliation_state=PARTIAL
safety_mode=NO_NEW_POSITIONS
authority_state=EXIT_ONLY
data_integrity_state=TRUSTED
economic_validation_state=NOT_APPLICABLE_RUNTIME
```

---

# 6. Kanonische Richtungszustände

```text
NEUTRAL_OBSERVE

LONG_ARMED
LONG_SELECTED

SHORT_ARMED
SHORT_SELECTED

SWITCH_LONG_TO_SHORT_PENDING
SWITCH_SHORT_TO_LONG_PENDING

CHOP_GUARD_BLOCK
```

`LONG_SELECTED` und `SHORT_SELECTED` bedeuten ausschließlich fachliche Richtungswahl.

Sie implizieren nicht:

- Order Submission,
- Fill,
- Position,
- Trading Authority,
- offenen Trading Gate.

---

# 7. Reversal- und Flat-Invariante

Verboten:

```text
LONG_SELECTED → SHORT_SELECTED
SHORT_SELECTED → LONG_SELECTED
```

Gegenseite erst nach:

```text
venue_position_quantity == 0
AND no_open_increase_orders
AND no_unresolved_reduce_orders
AND no_submission_unknown
AND order_snapshot_fresh
AND fill_snapshot_fresh
AND position_snapshot_fresh
AND intent_ledger_matches_venue
AND reconciliation_state == RECONCILED
```

```text
OPPOSITE_SIDE_REQUIRES_RECONCILED_FLAT=true
VENUE_FLAT_ALONE_SUFFICIENT=false
```

---

# 8. Canonical Market Context

Jeder Entscheidungszyklus beginnt mit genau einem immutable:

```text
CanonicalMarketContextV1
```

## 8.1 Pflichtfelder

```text
context_id
instrument_id
trading_epoch
market_event_time
decision_time
bar_interval
bar_finality_status
mark_price
index_price
best_bid
best_ask
spread
volume
open_interest
funding_rate
volatility_estimate
trend_feature_set
momentum_feature_set
liquidity_feature_set
market_structure_feature_set
data_integrity_status
clock_trust_status
warmup_status
feature_contract_version
input_digest
```

## 8.2 Preis- und Zeitregeln

```text
PRIMARY_DECISION_PRICE=VENUE_MARK_PRICE
EXECUTION_REFERENCE_PRICE=BEST_BID_ASK_OR_VENUE_MARKET_SNAPSHOT
LIQUIDATION_REFERENCE_PRICE=VENUE_DEFINED_MARK_OR_INDEX_PRICE

TRADING_DECISION_ON_UNFINALIZED_BAR_ALLOWED=false
SCOPE_CONFIRMATION_ON_UNFINALIZED_BAR_ALLOWED=false
OUT_OF_ORDER_MARKET_EVENT_ALLOWED=false
DUPLICATE_MARKET_EVENT_MUST_BE_IDEMPOTENT=true
```

Intrabar-Daten dürfen Risk, Integrity und Exit-Safety speisen, aber keine neue Entry- oder Reversal-Bestätigung erzeugen, solange keine separat ratifizierte Intrabar-Policy existiert.

## 8.3 Warmup

```text
WARMUP_REQUIRED
WARMUP_COMPLETE
WARMUP_INVALID
```

Solange Warmup nicht vollständig ist:

```text
NO_NEW_DIRECTIONAL_POSITION=true
NO_SCOPE_CONFIRMATION=true
OBSERVATION_AND_RECONCILIATION_ONLY=true
```

---

# 9. Canonical Scope Initialization

Scope-Zustände:

```text
SCOPE_UNINITIALIZED
SCOPE_WARMING_UP
SCOPE_VALID
SCOPE_STALE
SCOPE_INVALID
```

Initialisierung nur wenn:

```text
warmup_status == WARMUP_COMPLETE
AND data_integrity_status == TRUSTED
AND clock_trust_status == TRUSTED
AND required_window_complete
AND instrument_metadata_valid
```

Kanonische Initialisierung:

```text
reference_price = finalized_mark_price
initial_volatility_distance = volatility_estimate * reference_price
initial_scope_band = clamp(
    initial_volatility_distance,
    min_scope_band,
    max_scope_band
)

neutral_upper_boundary = reference_price + initial_scope_band
neutral_lower_boundary = reference_price - initial_scope_band
trailing_anchor = reference_price
```

Kein Codepfad darf implizite Default-Werte einsetzen.

---

# 10. Deterministic Scope Event Generator

Der Scope Event Generator ist ein eigener deterministischer Owner.

```text
SCOPE_EVENT_GENERATOR_ROLE=CANONICAL_SCOPE_EVENT_OWNER
```

## 10.1 Inputs

```text
CanonicalMarketContextV1
current_scope
current_direction_state
confirmation_state
cooldown_state
scope_policy
```

## 10.2 Outputs

```text
NOOP
UPSCOPE_CANDIDATE
UPSCOPE_CONFIRMED
DOWNSCOPE_CANDIDATE
DOWNSCOPE_CONFIRMED
ADVERSE_EXIT_CANDIDATE
CHOP_DETECTED
SCOPE_BLOCKED
```

## 10.3 Invarianten

```text
CURRENT_SCOPE_IS_IMMUTABLE_WITHIN_DECISION_CYCLE=true
NEXT_SCOPE_EFFECTIVE_NEXT_TRADING_EPOCH_ONLY=true
NO_SCOPE_EVENT_FROM_UNFINALIZED_DATA=true
NO_SCOPE_EVENT_FROM_UNTRUSTED_DATA=true
NO_SCOPE_EVENT_AUTHORITY_EFFECT=true
NO_SCOPE_EVENT_ORDER_EFFECT=true
```

## 10.4 Schwellen

```text
up_candidate_threshold = trailing_anchor + up_distance
adverse_exit_threshold = trailing_anchor - adverse_exit_distance
reversal_candidate_threshold = trailing_anchor - reversal_distance
```

Für Short gespiegelt.

Zwingend:

```text
0 < up_distance <= hard_max_scope_distance
0 < adverse_exit_distance <= hard_max_adverse_distance
0 < reversal_distance <= hard_max_reversal_distance
adverse_exit_distance <= reversal_distance
```

## 10.5 Confirmation

```text
confirmation_unit=FINALIZED_TRADING_EPOCH
candidate_count_requires_consecutive_epochs=true
candidate_reset_on_opposite_or_no_longer_true=true
candidate_count >= confirmation_epochs
→ CONFIRMED
```

---

# 11. Dynamic Scope

Dynamic Scope ist:

- Preis-/Strukturhülle,
- bounded,
- deterministisch,
- read-before-write.

Dynamic Scope ist nicht:

- Capital Allocation,
- Position Sizing,
- Trailing Stop,
- Exit Policy,
- Reversal Policy,
- KillSwitch,
- Runtime Authority.

Getrennt zu führen:

```text
trailing_anchor
scope_band
adverse_exit_threshold
reversal_candidate_threshold
reversal_confirmation_state
```

---

# 12. Bull- und Bear-Assessment

Beide Seiten erzeugen:

```text
DirectionalAssessmentV1
```

Pflichtfelder:

```text
assessment_id
side
instrument_id
trading_epoch
status
signal_strength
confidence
feature_refs
scope_event_ref
survival_preconditions
hard_block_reasons
reason_codes
valid_until_epoch
semantic_digest
```

Status:

```text
INVALID
BLOCKED
OBSERVE
CANDIDATE
CONFIRMED
```

Bull und Bear verwenden denselben Contract und dieselbe Auswertungsreihenfolge.

Pflichttest:

```text
price_path
→ mathematically mirrored price_path
→ structurally mirrored Bull/Bear outcome
```

---

# 13. Survival

Subchecks:

```text
DATA_COMPLETENESS_CHECK
COST_SURVIVAL_CHECK
VOLATILITY_SURVIVAL_CHECK
SEQUENCE_SURVIVAL_CHECK
DRAWDOWN_SURVIVAL_CHECK
LIQUIDATION_BUFFER_CHECK
```

Kostenmodell:

```text
expected_roundtrip_cost =
    entry_fee
  + expected_entry_slippage
  + exit_fee
  + expected_exit_slippage
  + expected_funding_cost

net_expected_edge = expected_gross_edge - expected_roundtrip_cost
```

Aggregation:

```text
ANY_HARD_FAIL → FAIL
ANY_REQUIRED_UNKNOWN → BLOCKED
ALL_REQUIRED_PASS → PASS
```

---

# 14. Suitability

Suitability bestimmt, welche bereits registrierte Strategie für Seite und Regime geeignet ist.

```text
NO_IMPLICIT_STRATEGY_SELECTION_BY_LIST_ORDER=true
NO_FALLBACK_STRATEGY=true
UNKNOWN_REGIME_BLOCKS_NEW_ENTRY=true
```

Mehrere passende Strategien benötigen eine versionierte Ranking Policy mit stabiler Tie-Break-Regel.

---

# 15. Double Play

Double Play:

- koordiniert Bull und Bear,
- löst Konflikte,
- konsumiert Survival und Suitability,
- erzeugt Canonical Trading Decision.

Double Play darf nicht:

- Orders senden,
- Risk duplizieren,
- Sizing duplizieren,
- KillSwitch resetten,
- Authority ausstellen,
- Reconciliation überschreiben.

Konfliktregel:

```text
BOTH_SIDES_CONFIRMED
→ CHOP_GUARD_BLOCK
→ NO_NEW_ENTRY
→ EXISTING_POSITION_MANAGEMENT_CONTINUES
```

---

# 16. Decision Precedence

```text
1. Safety / Authority Revocation
2. Hard Risk Reduction
3. Reconciliation Requirement
4. Mandatory Exit Policy
5. Existing Position Management
6. Reversal Processing
7. New Entry
8. Favorable Scope Trailing
9. Observation / No Action
```

Kanonische Outcomes:

```text
NO_ACTION
OBSERVE
HOLD
REDUCE
EXIT
ENTER_LONG
ENTER_SHORT
CANCEL_PENDING
RECONCILE_ONLY
BLOCKED
```

---

# 17. Entry-, Position-Management- und Exit-Policy

## 17.1 Entry Preconditions

```text
direction_state in {LONG_ARMED, SHORT_ARMED}
AND selected_assessment.status == CONFIRMED
AND survival.status == PASS
AND suitability.status == PASS
AND position_state == FLAT_RECONCILED
AND reconciliation_state == RECONCILED
AND trading_gate in {ENTRY_ALLOWED, INCREASE_ALLOWED}
AND safety_mode == NORMAL
AND data_integrity_state == TRUSTED
AND clock_trust_valid
AND cooldown_pass
```

## 17.2 Exit-Klassen

```text
SAFETY_EXIT
HARD_RISK_EXIT
ADVERSE_SCOPE_EXIT
PROFIT_PROTECTION_EXIT
TIME_EXIT
STRATEGY_INVALIDATION_EXIT
REVERSAL_PREPARATION_EXIT
```

## 17.3 Exit-Invariante

```text
reduce_only=true
quantity <= reconciled_open_position_quantity
position_flip_allowed=false
```

Ein Reversal erzeugt zuerst Exit und Reconciled-flat, niemals direkt eine Gegenorder.

---

# 18. Canonical Trading Decision

Output:

```text
CanonicalTradingDecisionEvidenceV1
```

Pflichtfelder:

```text
decision_id
instrument_id
trading_epoch
input_refs
current_scope_ref
next_scope_ref
scope_event
previous_side_state
next_side_state
bull_assessment
bear_assessment
survival_result
suitability_result
composition_result
decision_outcome
reason_codes
decision_precedence_trace
market_context_ref
selected_strategy_ref
entry_or_exit_policy_ref

execution_eligible=false
adapter_compatible=false
quantity_status=NOT_BOUND
authority_effect=NONE
runtime_effect=NONE
```

---

# PART III — ECONOMIC VALIDITY AND RESEARCH INTEGRATION


# PART III-A — SCHMALE PARAMETER- UND MESSGOVERNANCE

## 18A.0 Maßgeblichkeit der Handelslogik

Dieses Kapitel ersetzt kein eigenes Parameter-Runbook und definiert keine zusätzliche Handelslogik.

```text
CANONICAL_TRADING_LOGIC_IS_PRIMARY_SSOT=true
PARAMETER_GOVERNANCE_IS_SUBORDINATE=true
PARAMETER_GOVERNANCE_MAY_NOT_CREATE_NEW_TRADING_GATES=true
PARAMETER_GOVERNANCE_MAY_NOT_TIGHTEN_CANONICAL_FILTERS_BY_DEFAULT=true
PARAMETER_GOVERNANCE_MAY_NOT_REORDER_DECISION_PRECEDENCE=true
PARAMETER_GOVERNANCE_MAY_NOT_OVERRIDE_SAFETY_OR_RECONCILIATION=true
```

Maßgeblich bleiben ausschließlich die in PART II definierten Contracts für Market Context, Scope, Bull/Bear, State Switch, Survival, Suitability, Double Play, Entry, Position Management, Exit und Reversal.

Parameter dienen nur dazu, diese bereits ratifizierte Semantik technisch eindeutig auszudrücken, realistisch zu messen und innerhalb ausdrücklich zulässiger Research-Surfaces zu kalibrieren.

## 18A.1 Was aus der Parameter-Governance übernommen wird

Übernommen werden ausschließlich Regeln mit unmittelbarem Qualitätsgewinn und ohne zusätzliche Trade-Selektion:

```text
POINT_IN_TIME_DATA_BINDING_REQUIRED=true
NO_LOOKAHEAD_REQUIRED=true
NO_SURVIVORSHIP_BIAS_REQUIRED=true
DETERMINISTIC_REPLAY_REQUIRED=true
VERSIONED_PARAMETER_BINDING_REQUIRED=true
REALISTIC_DYNAMIC_COSTS_REQUIRED=true
GROSS_COST_NET_ATTRIBUTION_REQUIRED=true
ACCOUNTING_RECONCILIATION_REQUIRED=true
TIME_ORDERED_VALIDATION_REQUIRED=true
FINAL_OOS_PROTECTED=true
NO_POST_HOC_RESULT_RESCUE=true
REPRODUCIBLE_EVIDENCE_REQUIRED=true
```

Diese Regeln verbessern die Wahrheit des Messergebnisses. Sie dürfen nicht bestimmen, ob der Core eine fachlich gültige Marktentscheidung erzeugt.

## 18A.2 Was ausdrücklich nicht übernommen wird

Nicht zulässig sind zusätzliche oder doppelte Filter, die außerhalb von PART II entstehen:

```text
NO_SECOND_PARAMETER_DRIVEN_TRADING_SYSTEM=true
NO_ADDITIONAL_CONFIRMATION_LAYER_FROM_RESEARCH_GOVERNANCE=true
NO_ADDITIONAL_COOLDOWN_LAYER_FROM_RESEARCH_GOVERNANCE=true
NO_ADDITIONAL_SURVIVAL_FILTER_FROM_EVIDENCE_POLICY=true
NO_ADDITIONAL_SUITABILITY_FILTER_FROM_EVIDENCE_POLICY=true
NO_ADDITIONAL_CHOP_GUARD_FROM_PARAMETER_POLICY=true
NO_TRADE_COUNT_TARGET=true
NO_MINIMUM_SIGNAL_FREQUENCY_TARGET=true
NO_PARAMETER_CHANGE_ONLY_TO_CREATE_MORE_TRADES=true
NO_PARAMETER_CHANGE_ONLY_TO_IMPROVE_PNL=true
```

Economic Diagnostics, OLS, Capture-Metriken, Counterfactuals und Sensitivitätsanalysen bleiben `DIAGNOSTIC_ONLY`. Sie dürfen keine Entry-, Exit-, Reversal-, Sizing-, Ranking- oder Runtime-Authority erhalten.

## 18A.3 Parameterklassen

Jeder veränderbare Wert wird genau einer schlanken Klasse zugeordnet:

### A — Constitutional Core

Teil der ratifizierten Handelssemantik oder Safety-Invariante.

```text
OPTIMIZATION_ALLOWED=false
CHANGE_REQUIRES_INDEPENDENT_SEMANTIC_DEFECT_PROOF=true
```

### B — Observed Venue and Instrument Binding

Point-in-time gebundene Tatsachen wie Tick Size, Lot Size, Gebühren, Funding, Contract Multiplier und Margin Schedule.

```text
OPTIMIZATION_ALLOWED=false
POINT_IN_TIME_BINDING_REQUIRED=true
```

### C — Explicitly Calibratable Research Parameter

Nur Parameter, deren Kalibrierbarkeit bereits aus der kanonischen Handelslogik oder einer separaten ratifizierten Hypothese hervorgeht.

```text
CALIBRATION_ALLOWED_WITHIN_PREDECLARED_RANGE=true
CORE_SEMANTIC_CHANGE_ALLOWED=false
SAFETY_RELAXATION_ALLOWED=false
```

### D — Diagnostic Only

Werte für Sensitivität, Attribution oder kontrafaktische Analyse.

```text
TRADING_EFFECT=NONE
PROMOTION_PASS_AUTHORITY=false
RUNTIME_EFFECT=NONE
```

Ein nicht klassifizierter Parameter bleibt unverändert und darf nicht optimiert werden. Er wird dadurch nicht automatisch zu einem neuen Constitutional-Core-Contract.

## 18A.4 Minimaler Parameter Registry Contract

Nur tatsächlich verwendete und veränderbare Parameter benötigen:

```text
parameter_name
owner
class
semantic_description
unit
default_value
allowed_range_if_calibratable
mutation_allowed
calibration_method
version
```

Kein vollständiges Registry- und Evidence-Paket ist für jeden konstanten oder rein technischen Wert erforderlich.

## 18A.5 Schutz vor unbeabsichtigter Filter-Starvation

Das System benötigt keinen künstlichen Mindest-Trade-Count. Es muss aber sichtbar sein, ob die kanonische Kette wegen Marktbedingungen oder wegen kumulativer Selektivität keine Trades erzeugt.

Für Baseline- und Parameterläufe genügt ein kompakter Decision Funnel:

```text
market_epochs_total
directional_candidate_count
directional_confirmed_count
survival_pass_count
suitability_pass_count
double_play_entry_eligible_count
entry_preconditions_pass_count
risk_sizing_admissible_count
portfolio_admissible_count
trades_opened_count
```

Zusätzlich werden die häufigsten kanonischen Blockgründe ausgegeben.

```text
ZERO_TRADE_IS_NOT_AUTOMATIC_FAILURE=true
ZERO_TRADE_REQUIRES_CAUSAL_CLASSIFICATION=true
FILTER_STARVATION_DIAGNOSTIC_ONLY=true
FILTER_STARVATION_DIAGNOSTIC_MAY_NOT_AUTO_RELAX_CORE=true
```

Zulässige Hauptursachen:

```text
NO_CANONICAL_MARKET_OPPORTUNITY
CANONICAL_POLICY_BLOCKED
SAFETY_OR_DATA_INTEGRITY_BLOCKED
RISK_OR_CAPACITY_BLOCKED
IMPLEMENTATION_OR_BINDING_DEFECT
INSUFFICIENT_DATA
```

Eine detaillierte kombinatorische Filteranalyse ist nur erforderlich, wenn der Funnel einen konkreten Verdacht auf unbeabsichtigte kumulative Blockierung zeigt. Sie ist nicht standardmäßig ein weiteres Gate.

## 18A.6 Kalibrierungsprozess

Die Reihenfolge bleibt schlank:

```text
1. Canonical Core und Safety unverändert binden.
2. Baseline auf der vollständigen kanonischen Kette ausführen.
3. Daten-, Kosten- und Accounting-Qualität bestätigen.
4. Nur ausdrücklich kalibrierbare Parameter untersuchen.
5. Parameterbereiche vor Validation und finalem OOS einfrieren.
6. Stabile Regionen statt einzelner Bestpunkte bewerten.
7. Walk-Forward, Monte Carlo und Stress nur für den finalen Kandidaten beziehungsweise die finale robuste Region durchführen.
8. Finales OOS genau einmal für die jeweilige Research-Generation verwenden.
```

```text
EXPLORATORY_TRAIN_CALIBRATION_ALLOWED=true
PARAMETER_RANGES_FROZEN_BEFORE_VALIDATION=true
FINAL_OOS_TOUCHED_ONCE=true
BEST_SINGLE_PARAMETER_POINT_IS_NOT_EVIDENCE=true
ROBUST_REGION_PREFERRED=true
```

Es besteht keine Pflicht, jede mögliche Parameterkombination oder jede denkbare Interaktion vollständig zu testen. Der Untersuchungsumfang muss proportional zum wirtschaftlichen und semantischen Risiko sein.

## 18A.7 Kosten und Economic Attribution

Folgende Inhalte der früheren Parameter-MD bleiben verbindlich, weil sie keine Handelsfilter erzeugen:

```text
NO_IMPLICIT_ZERO_COST_BACKTEST=true
COSTS_COMPUTED_PER_FILL_AND_TRADE=true
OBSERVED_AND_MODELLED_COSTS_SEPARATELY_REPORTED=true
FUNDING_TREATED_AS_CASHFLOW=true
GROSS_PNL_REPORTED=true
TOTAL_COST_REPORTED=true
NET_PNL_REPORTED=true
TRADE_ACCOUNTING_RECONCILES=true
PORTFOLIO_ACCOUNTING_RECONCILES=true
```

Kostenmodelle dürfen konservativ sein, aber nicht willkürlich so hoch angesetzt werden, dass sie als zusätzlicher Strategy- oder Entry-Filter fungieren. Survival verwendet ausschließlich das in PART II ratifizierte Kosten- und Edge-Verständnis.

## 18A.8 Evidence nach Zweck

Evidence wird proportional erzeugt:

### Baseline und Diagnose

```text
reference_contract.json
decision_trace.jsonl
trade_ledger.jsonl
cost_attribution.json
compact_decision_funnel.json
final_report.txt
MANIFEST.sha256
```

### Finale Economic Adjudication

Zusätzlich:

```text
walk_forward_results.json
monte_carlo_results.json
stress_results.json
parameter_sensitivity.json
sample_sufficiency.json
economic_viability_evidence_v1.json
```

```text
MANIFEST_VERIFY_RC=0
MANIFEST_INTEGRITY_IS_NOT_PROFITABILITY=true
```

## 18A.9 Entscheidungsschutz

```text
PARAMETER_RESULT_MAY_NOT_REDEFINE_CANONICAL_SEMANTICS=true
NEGATIVE_RESULT_MAY_NOT_TRIGGER_AUTOMATIC_FILTER_RELAXATION=true
LOW_TRADE_COUNT_MAY_NOT_TRIGGER_AUTOMATIC_FILTER_RELAXATION=true
POSITIVE_RESULT_MAY_NOT_BYPASS_ROBUSTNESS_OR_SAFETY=true
```

Eine Parameteränderung ist nur zulässig, wenn sie:

```text
within_explicitly_calibratable_surface
AND within_predeclared_range
AND preserves_canonical_behavioral_contract
AND preserves_safety_and_reconciliation
AND is evaluated on time-ordered data
```

## 18A.10 Kanonische Kurzregel

```text
Die Handelslogik entscheidet, wann gehandelt wird.
Safety entscheidet, ob gehandelt werden darf.
Parameter drücken die ratifizierte Logik aus und dürfen nur auf ausdrücklich kalibrierbaren Surfaces untersucht werden.
Economic Validation misst wahrheitsgetreu, ob diese Logik nach realistischen Kosten wirtschaftlich trägt.
Diagnostik erklärt Ergebnisse, erzeugt aber keine zusätzliche Handelsentscheidung.
```



# 19. Audit-bestätigter Ist-Zustand

```text
PROFITABILITY_CAPABILITY_STATUS=TECHNICAL_CAPABILITY_PRESENT
ECONOMIC_VALIDITY_STATUS=FULL_CANONICAL_BASELINE_TERMINAL_FAIL
RESEARCH_RUNTIME_DRIFT_STATUS=CANONICAL_RESEARCH_WIRING_COMPLETED
MONTE_CARLO_STATUS=NOT_EXECUTED_BASELINE_NEGATIVE
WALK_FORWARD_STATUS=NOT_EXECUTED_BASELINE_NEGATIVE
PORTFOLIO_BACKTEST_STATUS=TECHNICAL_CAPABILITY_PRESENT
PROMOTION_INTEGRATION_STATUS=ECONOMIC_GATE_BOUND_FAIL_CLOSED
DUPLICATE_OWNER_STATUS=CONSOLIDATION_GOVERNED
FULL_CANONICAL_CHAIN_WIRED=true
BACKTEST_RUNTIME_DECISION_PARITY_PASS=true
STEP29M_FLEET_STATUS=TERMINAL_FAIL_RESEARCH_GENERATION_CLOSED
STEP30A_STATUS=COMPLETE_POLICY_FAIL
STEP29N_STATUS=COMPLETE_FAIL_CLOSED_BLOCKED
STEP29O_STATUS=COMPLETE_PASS
STEP29R_STATUS=PRECONDITION_ASSESSED_NOT_ADMISSIBLE
CURRENT_RESEARCH_GENERATION_CLOSED=true
FAILED_BINDINGS_REGISTERED=true
UNCHANGED_RETRY_BLOCKED=true
POLICY_RESCUE_ALLOWED=false
ECONOMIC_VALIDITY_OFFLINE_GATE_PASS=false
RUNTIME_REWIRE_ADMISSIBLE=false
```

Diese Werte bedeuten:

- Die technische Research- und Evidence-Capability ist vorhanden.
- Die bisher geprüften Bindings haben keine Economic Validity nachgewiesen.
- Runtime-Rewire und alle ausführungswirksamen Stufen bleiben blockiert.
- Negative Evidence ist terminal und darf nicht durch Governance- oder Policy-Änderung wegdefiniert werden.
- Weitere Research-Arbeit ist nur als versionierter, reproduzierbarer und offline-only Scope zulässig.
- Core-System und kanonische Handelslogik bleiben unverändert.

## 19.1 Terminale negative Economic Evidence

Manifest-verifizierte abgeschlossene Bindings:

| Binding | Net Return | Profit Factor | Trades | Primäre Failure-Klasse |
|---|---:|---:|---:|---|
| `macd/v1-v3` | -2,33 % | 0,817 | 717 | `NEGATIVE_RAW_STRATEGY_EDGE` |
| `breakout_donchian/v1` | -1,60 % | 0,845 | 328 | `NEGATIVE_RAW_STRATEGY_EDGE` |
| `ma_crossover/v1` | -2,48 % | 0,161 | 6 | `NEGATIVE_RAW_STRATEGY_EDGE` |
| `rsi_reversion/step30a` | -4,82 % | 0,836 | 465 | `SIGNAL_EDGE_PLUS_TURNOVER_PLUS_ROBUSTNESS` |
| `composite_breakout_confirmation_vol_gated_donchian_v1` | -2,34 % | 0,739 | 217 | `FEHLENDE_NETTO_EDGE_NEGATIVE_GROSS_EDGE` |

```text
FAILED_BINDINGS_ARE_NEGATIVE_EVIDENCE=true
FAILED_BINDINGS_MAY_NOT_BE_RETRIED_UNCHANGED=true
POLICY_CHANGE_DOES_NOT_CHANGE_HISTORICAL_EVIDENCE=true
```

## 19.2 Aktive Research-Governance

```text
OPERATOR_POLICY_DECISION=AUTHORIZE_BOUNDED_MULTI_CANDIDATE_FUTURES_RESEARCH_FLEET_V0
NO_NEW_CANDIDATE_HOLD=REVOKED
MULTI_CANDIDATE_RESEARCH_FLEET_ALLOWED=true
EXACTLY_ONE_CANDIDATE_LIMIT=false
```

Die Aufhebung des Holds verändert ausschließlich die Research-Governance.

Sie verändert nicht:

- Canonical Market Context,
- Scope Initialization oder Scope Event Generator,
- Bull-/Bear-Assessment,
- Survival oder Suitability,
- Double Play,
- Entry-/Position-/Exit-Policy,
- Capital/Risk/Sizing,
- Safety Kernel,
- Reconciliation,
- Runtime Authority.

```text
CORE_SYSTEM_MUTATION_ALLOWED=false
CANONICAL_TRADING_LOGIC_MUTATION_ALLOWED=false
MASTER_V2_MUTATION_ALLOWED=false
DOUBLE_PLAY_MUTATION_ALLOWED=false
RISK_SIZING_MUTATION_ALLOWED=false
SAFETY_RUNTIME_MUTATION_ALLOWED=false
```

---

# 20. Reuse-First Economic Validation

Es wird kein neuer Economic-Validation-Stack aufgebaut.

Wiederzuverwenden:

```text
scripts/run_backtest.py
src/backtest/engine.py
src/backtest/walkforward.py
src/experiments/monte_carlo.py
src/experiments/stress_tests.py
src/experiments/portfolio_robustness.py
src/backtest/stats.py
src/experiments/evidence_chain.py
src/experiments/strategy_profiles.py
src/core/experiments.py
```

Neue Komponenten sind nur zulässig, wenn eine bestätigte Lücke nicht durch Adapter, Rewire oder Consolidation geschlossen werden kann.

---


# 20.1 Offline Linear Evidence Layer / OLS — Reuse-First Economic Diagnostics

Der Offline Linear Evidence Layer wird als Teil der Economic-Validation-Domäne geführt. Er ist kein neues Trading-System, keine Strategy-SSOT und kein Runtime-Pfad.

```text
OFFLINE_LINEAR_EVIDENCE_LAYER_ALLOWED=true
OFFLINE_LINEAR_EVIDENCE_LAYER_HAS_AUTHORITY=false
LINEAR_EVIDENCE_LAYER_CAN_BLOCK_OR_WARN=true
LINEAR_EVIDENCE_LAYER_CAN_SUPPORT_ECONOMIC_EVIDENCE=true
LINEAR_EVIDENCE_LAYER_CAN_NOT_PROMOTE=true
LINEAR_EVIDENCE_LAYER_CAN_NOT_ARM=true
LINEAR_EVIDENCE_LAYER_CAN_NOT_REWIRE_RUNTIME=true
```

Empfohlener Owner, sofern kein bestehender passender Research-/Evidence-Owner im Repo näher liegt:

```text
src/research/linear_evidence/
  __init__.py
  contracts.py
  feature_matrix.py
  fitters.py
  diagnostics.py
  cost_model.py
  signal_orthogonality.py
  factor_exposure.py
  sensitivity.py
  drift.py
  report.py

scripts/research/
  offline_linear_cost_model_diagnostics_v0.py
  offline_signal_orthogonality_diagnostics_v0.py
  offline_factor_exposure_diagnostics_v0.py
  offline_parameter_sensitivity_surface_v0.py
  offline_rolling_linear_drift_diagnostics_v0.py
```

Vor einem neuen Owner gilt unverändert:

```text
REUSE_AS_IS
→ REUSE_WITH_NARROW_ADAPTER
→ REWIRE_EXISTING_COMPONENT
→ CONSOLIDATE_TO_EXISTING_OWNER
→ NEW_IMPLEMENTATION_JUSTIFIED
```

Pflicht-Importgrenzen:

```text
NO_IMPORT_FROM_RUNTIME_EXECUTION_PATH=true
NO_IMPORT_FROM_ORDER_ADAPTERS=true
NO_IMPORT_FROM_SCHEDULER=true
NO_IMPORT_FROM_LIVE_CONFIG=true
NO_NEW_RUNTIME_DEPENDENCY=true
DO_NOT_ADD_NEW_DEPENDENCY_WITHOUT_OWNER_DECISION=true
```

Datenfluss:

```text
Existing Backtest / Offline Replay Evidence
→ canonical decision records
→ trade records / simulated fills / cost records
→ deterministic feature matrix builder
→ OLS / linear diagnostics
→ manifest-verified LinearModelEvidenceV1
→ optional references in EconomicViabilityEvidenceV1
```

Solver-Policy für v0:

```text
V0_SOLVER=numpy.linalg.lstsq
MANUAL_INVERSE_XTX_ALLOWED=false
V1_OPTIONAL_SOLVERS=Ridge,Huber,WinsorizedFit
STATS_INFERENCE_OPTIONAL=true
P_VALUES_NOT_PRIMARY_GATE=true
```

Validation-Policy:

```text
VALIDATION_SPLIT_MUST_BE_TIME_ORDERED=true
RANDOM_SPLIT_DEFAULT_ALLOWED=false
NO_LOOKAHEAD=true
FINALIZED_BAR_ONLY=true
FEATURE_TIME_LESS_THAN_TARGET_TIME=true
TARGET_SHIFT_EXPLICIT=true
FEATURE_ORDER_STABLE=true
FEATURE_DIGEST_STABLE=true
```

Failure Taxonomy ist Pflicht:

```text
FAILURE_TAXONOMY_REQUIRED=true
failure_class
detector
blocking_point
safe_fallback
operator_visible_consequence
```

Pflicht-Failure-Klassen für v0:

```text
INSUFFICIENT_DATA
FEATURE_LEAKAGE_DETECTED
TARGET_BINDING_MISSING
RUNTIME_IMPORT_BOUNDARY_VIOLATION
ORDER_ADAPTER_IMPORT_BOUNDARY_VIOLATION
SCHEDULER_IMPORT_BOUNDARY_VIOLATION
RANDOM_VALIDATION_SPLIT_BLOCKED
COST_POLICY_BELOW_FLOOR_BLOCKED
```

## 20.2 OLS-Scaffolding vor Economic Evidence

Ein kleiner OLS-Scaffolding-Slice ist zulässig, bevor vollständige System-Economic-Evidence erzeugt wird, wenn alle folgenden Bedingungen erfüllt sind:

```text
OFFLINE_ONLY=true
NO_RUNTIME_EVIDENCE=true
NO_CONFIG_DEFAULT_CHANGE_FOR_BACKTEST_COSTS_IN_V0=true
NO_STRATEGY_SELECTION_CHANGED=true
NO_PROMOTION_PASS_CREATED=true
SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE=false
RUNTIME_REWIRE_ADMISSIBLE=false
MANIFEST_VERIFY_RC=0
```

Zulässige Scaffolding-Bestandteile:

```text
LinearModelEvidenceV1 contracts
FeatureMatrixBindingV1 contracts
Deterministic Fixture Truth Pack
Feature-matrix leakage guards
numpy.linalg.lstsq baseline fitter
basic diagnostics
import-boundary tests
manifest-verified diagnostic report
```

Nicht zulässig im Scaffolding:

```text
Backtest cost default changes
Strategy-selection binding
Economic pass claim
Promotion binding
Runtime rewire
Runtime evidence
Shadow/Paper/Testnet/Canary/Live
Orders/Cancels/Credentials/Arming
```

# 21. Verbindlicher Research-/Runtime-Paritätsgrundsatz

```text
CANONICAL_TRADING_LOGIC_MUST_BE_SHARED=true
SEPARATE_BACKTEST_SIGNAL_LOGIC_ALLOWED=false
SEPARATE_RUNTIME_SIGNAL_LOGIC_ALLOWED=false
```

Die gleiche kanonische Decision-Semantik muss in:

- Offline Replay,
- Backtest,
- Walk-Forward,
- Monte Carlo,
- Stress,
- Shadow,
- Paper,
- Testnet,
- Runtime

verwendet werden.

Abweichungen dürfen nur in der Execution-Simulation oder Environment-Authority liegen, nicht in der Handelslogik.

---## 21.1 System-Parität vor entscheidungsrelevanter Economic Validation

Vor jeder Economic Validation, die als System-Economic-Evidence gelten soll, muss nachgewiesen werden, dass Backtest, Offline Replay und spätere Runtime dieselbe kanonische Entscheidungskette nutzen.

```text
BACKTEST_MUST_USE_CANONICAL_DECISION_CHAIN=true
OFFLINE_REPLAY_MUST_USE_CANONICAL_DECISION_CHAIN=true
RESEARCH_ORCHESTRATOR_MAY_NOT_BYPASS_STATE_SWITCH_FOR_SYSTEM_EVIDENCE=true
RESEARCH_ORCHESTRATOR_MAY_NOT_BYPASS_SCOPE_EXIT_FOR_SYSTEM_EVIDENCE=true
RESEARCH_ORCHESTRATOR_MAY_NOT_BYPASS_RISK_SIZING_FOR_SYSTEM_EVIDENCE=true
RESEARCH_ORCHESTRATOR_MAY_NOT_BYPASS_SAFETY_RECONCILIATION_FOR_SYSTEM_EVIDENCE=true
```

Pflichtnachweis:

```text
BULL_BEAR_STATE_SWITCH_WIRED_TO_BACKTEST=true
ADVERSE_SCOPE_EXIT_WIRED_TO_BACKTEST=true
REVERSAL_PREPARATION_WIRED_TO_BACKTEST=true
FLAT_BEFORE_OPPOSITE_SIDE_WIRED_TO_BACKTEST=true
CAPITAL_RISK_SIZING_WIRED_TO_BACKTEST=true
SAFETY_KERNEL_SEMANTICS_WIRED_TO_BACKTEST=true
KILLSWITCH_BOUNDARY_REPRESENTED_IN_BACKTEST=true
RECONCILIATION_SEMANTICS_REPRESENTED_IN_BACKTEST=true
PROMOTION_GATE_SEMANTICS_BOUND=true
AI_LAYER_OBSERVABILITY_BOUNDARY_DOCUMENTED=true
```

Ein Backtest darf Execution-Transport, Venue-Netzwerk und echte Orders simulieren oder ausklammern. Er darf aber für System-Economic-Evidence nicht andere Entry-, Exit-, Reversal-, State-, Risk-, Safety- oder Promotion-Semantik verwenden als die kanonische Runtime-Kette.

```text
SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE =
    FULL_CANONICAL_CHAIN_WIRED
    AND BACKTEST_RUNTIME_DECISION_PARITY_PASS
    AND REALISTIC_COSTS_BOUND
    AND ROBUSTNESS_EVIDENCE_PASS
```

---

# 22. Realistische Kostenbindung

Der Default-Backtest darf keine impliziten Nullkosten verwenden.

Aktuell bestätigter Drift:

```text
DEFAULT_BACKTEST_FEE_BPS=0
DEFAULT_BACKTEST_SLIPPAGE_BPS=0

CONFIG_FEE_BPS=10
CONFIG_SLIPPAGE_BPS=5
```

Kanonische Regel:

```text
NO_IMPLICIT_ZERO_COST_BACKTEST=true
NO_ECONOMIC_CLAIM_WITH_ZERO_COST_DEFAULT=true
```

Pflichtkomponenten:

- Maker-/Taker-Fees,
- Slippage,
- Spread,
- Funding,
- Tick-/Lot-Rounding,
- Mindestmenge,
- Mindestnotional,
- Partial Fills,
- Latenzannahmen,
- Mark-/Index-/Execution-Preis,
- Long-/Short-Symmetrie.

---


# 22.1 OLS Cost-/Slippage-Diagnostics

OLS darf für Kosten- und Slippage-Diagnostics genutzt werden, sobald die benötigten Backtest-/Replay-/Fill-/Cost-Records offline und manifestiert vorliegen. Der erste produktive Use Case ist:

```text
NEXT_LINEAR_EVIDENCE_PRODUCTIVE_SLICE=OFFLINE_LINEAR_COST_MODEL_DIAGNOSTICS_V0
```

Modellziel:

```text
realized_slippage_bps = f(
  spread_bps,
  volatility_estimate,
  order_notional_to_depth,
  funding_rate_abs,
  liquidity_score,
  side,
  regime
)
```

Pflichtinputs, sofern vorhanden:

```text
instrument_id
side
bar_interval
decision_time
mark_price
best_bid
best_ask
spread_bps
volume
open_interest
funding_rate
volatility_estimate
depth_near_touch
order_notional
simulated_or_realized_fill_price
execution_reference_price
```

Outputs:

```text
CostModelCalibrationEvidenceV1
coefficients
residual_diagnostics
rmse_bps
mae_bps
max_abs_error_bps
condition_number
outlier_count
validation_error_bps
status
reason_codes
```

Konservative Cost-Policy:

```text
NO_CONFIG_DEFAULT_CHANGE_FOR_BACKTEST_COSTS_IN_V0=true
CALIBRATED_COST_POLICY=CONSERVATIVE_NOT_MEAN
CALIBRATED_COST_BPS_BASELINE_REQUIRED=true
CALIBRATED_COST_BPS_P75_REQUIRED=true
CALIBRATED_COST_BPS_P90_REQUIRED=true
CALIBRATED_COST_BPS_STRESS_REQUIRED=true
BACKTEST_DEFAULT_COST_POLICY=CONSERVATIVE_NOT_MEAN
```

Der Mittelwert einer OLS-Prognose ist keine ausreichende Sicherheitsannahme. Für Economic Evidence sind p75/p90- oder Stress-Kosten als Review-Grundlage maßgeblich. OLS-Cost-Diagnostics dürfen Backtest-Defaultkosten in v0 nicht automatisch ändern.

```text
OLS_COST_DIAGNOSTICS_CAN_SUPPORT_REALISTIC_COSTS_BOUND=true
OLS_COST_DIAGNOSTICS_CAN_NOT_SET_REALISTIC_COSTS_BOUND_ALONE=true
NO_ECONOMIC_CLAIM_WITH_OLS_COST_MODEL_ALONE=true
```

# 23. EconomicViabilityEvidenceV1

Pflichtartefakt:

```text
EconomicViabilityEvidenceV1
```

Pflichtfelder:

```text
strategy_id
strategy_version
instrument_id_or_universe
canonical_trading_logic_version
data_period
training_period
validation_period
out_of_sample_period
fee_model_version
slippage_model_version
funding_model_version
execution_model_version
config_digest
implementation_digest
data_digest

gross_return
net_return
net_expectancy
profit_factor
sharpe
sortino
max_drawdown
calmar
trade_count
turnover
fee_drag
funding_drag
slippage_impact
tail_loss
time_in_market
long_contribution
short_contribution
regime_breakdown
portfolio_contribution

walk_forward_results
monte_carlo_results
stress_results
parameter_sensitivity_results

status
reason_codes
manifest_digest
```

Optionale, unterstützende Linear-Evidence-Referenzen, sofern nach Policy erzeugt:

```text
cost_model_calibration_ref
signal_orthogonality_ref
factor_exposure_ref
parameter_sensitivity_ref
rolling_linear_drift_ref
linear_diagnostics_status
linear_diagnostics_reason_codes
```

Diese Felder sind Referenzen auf manifest-verifizierte Diagnose-Artefakte. Sie erzeugen keinen Economic-Pass und dürfen fehlende Walk-Forward-, Monte-Carlo-, Stress- oder OOS-Evidence nicht ersetzen.

Status:

```text
RESEARCH_ONLY
PROMISING
ROBUSTNESS_FAILED
ECONOMICALLY_VIABLE_OFFLINE
SHADOW_VALIDATED
PAPER_VALIDATED
TESTNET_VALIDATED
```

---


# 23.1 LinearModelEvidenceV1

Pflichtartefakt für alle OLS-/Linear-Diagnostics:

```text
LinearModelEvidenceV1
```

Mindestfelder:

```text
evidence_type
model_family
target_name
feature_names
n_samples
n_features
solver
fit_intercept
coefficients
diagnostics
feature_matrix_digest
target_digest
config_digest
time_range
instrument_universe_digest
row_count_before_filter
row_count_after_filter
dropped_rows_by_reason
validation_policy
cost_policy_output
status
authority_effect
runtime_effect
```

Zulässige Statuswerte:

```text
DIAGNOSTIC_ONLY
CALIBRATION_CANDIDATE
CALIBRATION_VALIDATION_FAILED
CALIBRATION_VALIDATED_OFFLINE
ROBUSTNESS_FAILED
INSUFFICIENT_DATA
LEAKAGE_BLOCKED
RANK_DEFICIENT_BLOCKED
```

Zulässige Reason Codes:

```text
INSUFFICIENT_SAMPLE_COUNT
HIGH_CONDITION_NUMBER
OUTLIER_DOMINATED
VALIDATION_ERROR_TOO_HIGH
COEFFICIENT_SIGN_UNSTABLE
FEATURE_LEAKAGE_RISK
TARGET_BINDING_MISSING
COST_COMPONENT_MISSING
ROBUSTNESS_COMPARISON_MISSING
RANDOM_VALIDATION_SPLIT_BLOCKED
COST_POLICY_BELOW_FLOOR_BLOCKED
RUNTIME_IMPORT_BOUNDARY_VIOLATION
ORDER_ADAPTER_IMPORT_BOUNDARY_VIOLATION
SCHEDULER_IMPORT_BOUNDARY_VIOLATION
```

Authority-Felder sind fix:

```text
authority_effect=NONE
runtime_effect=NONE
cost_policy_output=diagnostic_only unless separately ratified
```

# 24. Economic Validity Gate

```text
PROFITABLE_BACKTEST != ECONOMICALLY_VIABLE
```

Mindestbedingungen:

```text
net_expectancy_after_costs > 0
profit_factor_above_policy_threshold
max_drawdown_within_policy
walk_forward_stability_pass
out_of_sample_pass
parameter_robustness_pass
monte_carlo_pass
stress_test_pass
sufficient_trade_count
no_single_trade_or_regime_dominance
```

Konkrete Grenzwerte sind versionierte Policy und dürfen nicht nachträglich zur Ergebnisoptimierung verändert werden.

---

# 25. Walk-Forward, Monte Carlo und Stress

## 25.1 Walk-Forward

Vorhandenen Owner wiederverwenden:

```text
src/backtest/walkforward.py
```

Pflicht:

- explizite OOS-Fenster,
- stabile Rolling-Splits,
- keine nachträgliche Parameteranpassung im Testfenster,
- MV2-Bindung,
- realistische Kosten.

## 25.2 Monte Carlo

Research- und Risk-Monte-Carlo bleiben getrennte Domänen:

```text
src/experiments/monte_carlo.py
→ Strategy-/Return-Robustness

src/risk/monte_carlo.py
→ VaR/CVaR-Risk-Domain
```

Kein Zwang zur technischen Zusammenlegung, aber klare Owner-Dokumentation.

## 25.3 Stress

Bestehende Stress-Owner wiederverwenden.

Ergänzend erforderlich:

```text
fee_multiplier_stress
slippage_multiplier_stress
funding_stress
spread_expansion_stress
fill_quality_stress
latency_stress
trade_omission_stress
```

---


## 25.4 Linear Diagnostics ergänzend zu Walk-Forward, Monte Carlo und Stress

OLS-/Linear-Diagnostics sind ergänzende Erklärungs- und Robustness-Artefakte. Sie ersetzen keine Walk-Forward-, Monte-Carlo- oder Stress-Evidence.

### Signal-Orthogonalität

Zweck:

```text
SIGNAL_ORTHOGONALITY_DIAGNOSTICS_CAN_REPORT_REDUNDANCY=true
SIGNAL_ORTHOGONALITY_DOES_NOT_PROVE_PROFITABILITY=true
REDUNDANCY_DOES_NOT_DELETE_SIGNAL_AUTOMATICALLY=true
REDUNDANCY_CAN_DOWNWEIGHT_EVIDENCE_ONLY=true
CONFIRMATION_SIGNAL_ALLOWED_IF_EXPLICITLY_CLASSIFIED=true
DO_NOT_BIND_SIGNAL_ORTHOGONALITY_INTO_STRATEGY_SELECTION=true
```

Primäre Fleet-Anwendung:

```text
trend_following
bollinger_bands
momentum_1h
```

### Faktor-Exposure

Zweck:

```text
FACTOR_EXPOSURE_DIAGNOSTICS_CAN_REPORT_CLUSTER_RISK=true
FACTOR_EXPOSURE_DIAGNOSTICS_CAN_REPORT_BETA_STABILITY=true
FACTOR_EXPOSURE_DIAGNOSTICS_CAN_SUPPORT_PORTFOLIO_RESEARCH=true
FACTOR_EXPOSURE_DIAGNOSTICS_CAN_NOT_AUTHORIZE_MULTI_FUTURE_RUNTIME=true
```

### Parameter-Sensitivität

Zweck:

```text
PARAMETER_SENSITIVITY_DIAGNOSTICS_CAN_REPORT_FRAGILITY=true
BEST_PARAMETER_POINT_IS_NOT_EVIDENCE=true
ROBUST_REGION_REQUIRED_FOR_POSITIVE_INTERPRETATION=true
ROBUST_PLATEAU_CHECK_REPORTED=true
NO_PARAMETER_AUTO_OPTIMIZATION=true
NO_PARAMETER_DEFAULT_CHANGE_IN_V0=true
```

### Rolling Linear Drift

Zweck:

```text
ROLLING_LINEAR_DRIFT_DIAGNOSTICS_CAN_WARN=true
ROLLING_LINEAR_DRIFT_DIAGNOSTICS_CAN_BLOCK_ECONOMIC_EVIDENCE_BY_POLICY=true
ROLLING_LINEAR_DRIFT_DIAGNOSTICS_CAN_NOT_TRIGGER_RUNTIME_ACTION=true
ROLLING_LINEAR_DRIFT_DIAGNOSTICS_CAN_NOT_ARM_OR_DISARM=true
ROLLING_LINEAR_DRIFT_DIAGNOSTICS_CAN_NOT_CANCEL_OR_SUBMIT_ORDERS=true
```

# 26. Portfolio, Single-Future-Initialphase und Multi-Future-Zielmodell

Die vorhandene Multi-Strategy-/Multi-Asset-Infrastruktur bleibt zunächst Research-Capability.

Für die kanonische Initialphase gilt bewusst:

```text
SINGLE_SELECTED_FUTURE=true
MAX_POSITIONS=1
MAX_ACTIVE_DIRECTIONAL_SIDE=1
SIMULTANEOUS_LONG_SHORT_EXPOSURE_ALLOWED=false
```

Diese Begrenzung dient ausschließlich dazu, Safety, Stabilität, Reconciliation, Recovery, Fencing, Unknown-Outcome-Behandlung und Economic-to-Runtime-Gating unter minimaler Positionskomplexität nachzuweisen. Sie ist keine finale Produktgrenze.

## 26.1 Langfristiges Multi-Future-Zielmodell

Das langfristige Ziel bleibt ein futures-only Multi-Instrument-Portfolio-System, das aus einem Top20-Futures-Universum mehrere robuste, economic-validierte Futures selektieren und parallel verwalten kann.

```text
TOP20_FUTURES_UNIVERSE_TARGET=true
MULTI_SELECTED_FUTURES_PORTFOLIO_RUNTIME_TARGET=true
MULTIPLE_PROMISING_FUTURES_CAN_BE_SELECTED_AFTER_SEPARATE_GATES=true
MULTI_FUTURE_RUNTIME_AUTHORIZED=false
```

Zielkette:

```text
Top20 Futures Universe
→ Ranking / Candidate Selection
→ Portfolio Allocation
→ Per-Instrument Double Play
→ Per-Instrument Risk / Sizing
→ Global Portfolio Risk Gate
→ Safety / Runtime Authority
→ Execution / Reconciliation
```

Das Ziel ist nicht, alle guten Signale blind zu handeln. Ranking erzeugt keine Runtime-Authority. Portfolio-Auswahl erzeugt keine Order-Authority. Economic Evidence erzeugt keine Runtime-Authority.

## 26.2 Portfolio-Flächen in der Initialphase

Portfolio-Flächen dürfen bereits jetzt:

- Strategien vergleichen,
- Robustness aggregieren,
- Kandidaten ranken,
- Portfolio-Beiträge in Research und Economic Validation auswerten,
- spätere Allokationsfragen offline vorbereiten.

Sie dürfen nicht:

- die Double-Play-Authority umgehen,
- die Single-Side-Regel pro Instrument umgehen,
- Safety Kernel, Reconciliation oder Runtime Eligibility überschreiben,
- MAX_POSITIONS oder Exposure-Limits erhöhen,
- Orders, Cancels, Submissions oder Adapter-Kompatibilität erzeugen.

## 26.3 Per-Instrument-Invarianten bei späterer Multi-Future-Runtime

Auch wenn später mehrere Futures parallel erlaubt werden, bleiben pro Instrument unverändert:

```text
ONE_ACTIVE_DIRECTIONAL_SIDE_PER_INSTRUMENT=true
SIMULTANEOUS_LONG_SHORT_PER_INSTRUMENT_ALLOWED=false
REVERSAL_REQUIRES_RECONCILED_FLAT_PER_INSTRUMENT=true
NO_POSITION_INCREASE_DURING_UNRESOLVED_RECONCILIATION=true
NO_ORDER_WITHOUT_SINGLE_USE_PERMISSION=true
```

Multi-Future erweitert die Anzahl parallel verwalteter Instrumente, nicht die Authority eines einzelnen Instruments.

## 26.4 Zusätzliche Gates vor Multi-Future-Runtime

Multi-Future-Runtime ist erst nach separater Ratifikation und zusätzlicher Evidence zulässig. Mindestbedingungen:

```text
MULTI_FUTURE_GOVERNANCE_RATIFIED=true
PORTFOLIO_RISK_BINDING_PASS=true
PER_INSTRUMENT_CAPS_BOUND=true
GLOBAL_EXPOSURE_CAPS_BOUND=true
CORRELATION_CLUSTER_CAPS_BOUND=true
PORTFOLIO_DRAWDOWN_LOSS_CAPS_BOUND=true
MULTI_INSTRUMENT_RECONCILIATION_PASS=true
MULTI_INSTRUMENT_UNKNOWN_OUTCOME_RECOVERY_PASS=true
ZERO_ORDER_RUNTIME_EVIDENCE_PASS=true
SHADOW_EVIDENCE_PASS=true
PAPER_EVIDENCE_PASS=true
TESTNET_EVIDENCE_PASS=true
OPERATOR_MULTI_FUTURE_RUNTIME_GO=true
```

Bis alle diese Gates erfüllt und separat ratifiziert sind:

```text
MULTI_FUTURE_RUNTIME_AUTHORIZED=false
MAX_POSITIONS=1
```

## 26.5 Portfolio Authority Boundary

Ein späterer Portfolio Allocator darf auswählen und budgetieren. Er darf nicht:

- Safety Kernel überschreiben,
- Reconciliation überschreiben,
- Double Play pro Instrument umgehen,
- per-Instrument Reversal-/Flat-Invarianten schwächen,
- Orders direkt senden,
- Runtime Authority aus Ranking, Confidence oder Economic Evidence ableiten.

Die finale Authority bleibt Safety-/Runtime-gated.

---


## 26.6 Linear Factor Exposure und Active-Set-Replacement-Schutz

Faktor-Exposure, Ranking oder Orthogonalität dürfen spätere Portfolio-Kandidaten markieren, aber keine aktive Position, kein aktives Instrument und keinen Active-Set-Slot ersetzen.

```text
FACTOR_EXPOSURE_CAN_MARK_REPLACEMENT_CANDIDATE=true
FACTOR_EXPOSURE_CAN_NOT_FORCE_ACTIVE_SET_REPLACEMENT=true
RANKING_CAN_MARK_REPLACEMENT_ONLY=true
OLS_CAN_NOT_FORCE_ACTIVE_SET_REPLACEMENT=true
FLAT_RECONCILED_BEFORE_REPLACEMENT_REQUIRED=true
MULTI_FUTURE_RUNTIME_AUTHORIZED=false
```

Auch in einer späteren Multi-Future-Runtime gilt: Ein besser gerankter oder linear besser erklärter Kandidat darf einen aktiven Future nicht direkt verdrängen. Replacement bleibt an Exit-, Safety-, Reconciliation- und Authority-Policy gebunden.

# 27. Profitabilitäts- und Promotion-Gates

Aktuell bestätigtes Gap:

```text
PROMOTION_ECONOMIC_GATES=DOCUMENTATION_ONLY
```

Verboten:

```text
eligible_for_live=true
based_only_on_confidence_score
```

Künftig:

```text
eligible_for_promotion_candidate =
economic_validity_pass
AND robustness_pass
AND evidence_admissible
AND safety_policy_pass
```

Live- oder Runtime-Authority entsteht dadurch nicht.

---


## 27.1 Linear Evidence in Promotion Gates

Linear Evidence darf in Promotion-Gates nur als referenzierte Support-Evidence verwendet werden. Sie darf kein Promotion-Pass-Flag setzen.

```text
PROMOTION_GATE_MAY_READ_LINEAR_DIAGNOSTICS=true
PROMOTION_GATE_MAY_NOT_ACCEPT_LINEAR_DIAGNOSTICS_AS_SOLE_PASS=true
OLS_PROMOTION_PASS_AUTHORITY=false
MISSING_LINEAR_DIAGNOSTICS_FAIL_CLOSED_OR_WARN_BY_POLICY=true
```

Zulässige Promotion-Nutzung:

```text
cost_model_calibration_ref present
signal_orthogonality_ref present
factor_exposure_ref present
parameter_sensitivity_ref present
linear_diagnostics_status reviewed
linear_diagnostics_reason_codes reviewed
```

Nicht zulässig:

```text
eligible_for_promotion_candidate=true based_only_on_ols
eligible_for_shadow_candidate=true based_only_on_linear_diagnostics
runtime_rewire_admissible=true based_only_on_linear_diagnostics
```

# PART IV — RUNTIME SAFETY AND EXECUTION

# 28. Safety Kernel

Mandatory für jeden ausführungsrelevanten Intent.

Prüft mindestens:

- Governance,
- Environment,
- Runtime Eligibility,
- KillSwitch,
- Data Quality,
- Clock Trust,
- Trading Epoch,
- Executor Epoch,
- Authority Lease,
- Execution Permission,
- Position State,
- Reconciliation State,
- Risk Limits,
- Venue Metadata,
- Single Writer,
- Duplicate Intent,
- Unknown Outcome.

Safety darf nur begrenzen oder ablehnen.

---

# 29. KillSwitch

Explizite Modi:

```text
KILL_MODE_BLOCK_NEW
KILL_MODE_CANCEL_PENDING
KILL_MODE_REDUCE_TO_FLAT
KILL_MODE_EMERGENCY_FLATTEN
```

Ohne eindeutige Policy:

```text
NO_NEW_POSITIONS
NO_POSITION_INCREASE
NO_NEW_TRADING_PERMISSION
RECONCILIATION_REQUIRED
```

Kein automatischer Resume.

---

# 30. Runtime Eligibility, Lease und Permissions

Getrennte Permission-Typen:

```text
TradingExecutionPermissionV1
SafetyExitPermissionV1
CancelPermissionV1
ReconciliationQueryPermissionV1
```

Authority-Bindung:

```text
venue_id
account_id
subaccount_id
instrument_id
position_mode
margin_mode
execution_owner_id
writer_lease_id
fencing_token
executor_epoch
```

---

# 31. Durable-before-submit und Single Writer

Vor möglichem Netzwerk-Byte durable persistieren:

```text
intent_id
client_order_id
permission_id
lease_id
venue_id
account_id
instrument_id
submission_attempt_number
executor_epoch
authority_epoch
revocation_epoch
writer_lease_id
fencing_token
policy_digest
config_digest
implementation_digest
```

```text
NO_SUBMISSION_BEFORE_DURABLE_INTENT_PERSISTENCE=true
NO_STALE_WRITER_MAY_SUBMIT=true
PROCESS_ID_IS_NOT_A_FENCING_TOKEN=true
```

---

# 32. Unknown Outcomes und Reconciliation

Bei Timeout nach möglicher Übertragung:

```text
kein automatischer Resubmit
→ Query by Client Order ID
→ Open Orders
→ Recent Orders
→ Fills
→ Position
→ Reconciliation
```

Delivery-Semantik:

```text
at-least-once communication
+
idempotent intent processing
+
reconciliation-based effect resolution
```

---

# PART V — IMPLEMENTATION AND VALIDATION LADDER

# 33. Reuse-First-Regel

Vor jedem neuen Modul:

```text
REUSE_AS_IS
→ REUSE_WITH_NARROW_ADAPTER
→ REWIRE_EXISTING_COMPONENT
→ CONSOLIDATE_TO_EXISTING_OWNER
→ DEPRECATE_LEGACY_PATH
→ NEW_IMPLEMENTATION_JUSTIFIED
```

Ein neuer Owner ist nur zulässig bei:

```text
DISTINCT_AUTHORITY_SEMANTICS
OR DISTINCT_PERSISTENCE_LIFECYCLE
OR DISTINCT_VALIDATION_BOUNDARY
OR CONSUMER_CONTRACT_INCOMPATIBLE
```

---


# 33.1 Post-Merge Main-Sync und Evidence-Manifest-Guard

Nach jedem PR-Merge ist ein expliziter Merge-Closeout-Guard zwingend. Dieser Guard ist kein optionaler Hygiene-Schritt, sondern Teil der reproduzierbaren Peak-Trade-Evidence-Kette.

```text
POST_MERGE_MAIN_SYNC_REQUIRED=true
POST_MERGE_HEAD_EQUALS_ORIGIN_MAIN_REQUIRED=true
SOURCE_EVIDENCE_MANIFEST_REVERIFY_REQUIRED_WHEN_REFERENCED=true
SOURCE_EVIDENCE_ABSENCE_MUST_BE_EXPLICITLY_REPORTED=true
CLOSEOUT_EVIDENCE_MANIFEST_REQUIRED=true
CLOSEOUT_EVIDENCE_MANIFEST_VERIFY_RC_REQUIRED=0
MERGE_CLOSEOUT_WITHOUT_MANIFEST_VERIFY_ALLOWED=false
```

Pflichtreihenfolge nach jedem Merge:

```text
git fetch origin --prune
git checkout main
git reset --hard origin/main
POST_MERGE_HEAD="$(git rev-parse HEAD)"
POST_MERGE_ORIGIN_MAIN="$(git rev-parse origin/main)"
POST_MERGE_HEAD == POST_MERGE_ORIGIN_MAIN
```

Pre-Merge-PR-Checks müssen über den von `gh pr checks` gelieferten `state` validiert werden. `conclusion` ist kein verpflichtendes CLI-Ausgabefeld und darf nicht als Closeout-Abhängigkeit verwendet werden. Zulässige terminale Check-States sind ausschließlich:

```text
SUCCESS
SKIPPED
NEUTRAL
```

Danach müssen alle im PR, Operator-Go, Final Report oder Closeout referenzierten Source-Evidence-Bundles erneut verifiziert werden. Ein referenziertes Source-Evidence-Bundle ohne `MANIFEST.sha256` ist ein Blocker. Wenn ein Merge-Closeout fachlich kein Source-Evidence-Bundle referenziert, muss das explizit dokumentiert werden; dieser Fall darf nicht als erfolgreiche Source-Manifest-Verifikation ausgegeben werden:

```text
SOURCE_EVIDENCE_REFERENCED=true|false
SOURCE_MANIFEST_VERIFY_RC=0|NOT_APPLICABLE_NO_SOURCE_EVIDENCE_REFERENCED
SOURCE_EVIDENCE_NOT_REFERENCED=true|false
```

Für das neue Merge-Closeout-Bundle muss anschließend ein eigenes `MANIFEST.sha256` erzeugt und unmittelbar verifiziert werden:

```text
CLOSEOUT_MANIFEST_VERIFY_RC=0
```

Der Final Report eines Merge-Closeouts muss mindestens dokumentieren:

```text
PRE_MERGE_ORIGIN_MAIN
PR_HEAD
POST_MERGE_HEAD
POST_MERGE_ORIGIN_MAIN
HEAD_EQUALS_ORIGIN_MAIN=true
SOURCE_EVIDENCE_REFERENCED=true|false
SOURCE_MANIFEST_VERIFY_RC=0|NOT_APPLICABLE_NO_SOURCE_EVIDENCE_REFERENCED
SOURCE_EVIDENCE_NOT_REFERENCED=true|false
CLOSEOUT_MANIFEST_VERIFY_RC=0
DURABLE_EVIDENCE_DIR
```

Blocker-Regel:

```text
IF POST_MERGE_HEAD != POST_MERGE_ORIGIN_MAIN
THEN MERGE_CLOSEOUT_VERDICT=BLOCKED

IF SOURCE_EVIDENCE_REFERENCED == true AND SOURCE_MANIFEST_VERIFY_RC != 0
THEN MERGE_CLOSEOUT_VERDICT=BLOCKED

IF SOURCE_EVIDENCE_REFERENCED == true AND SOURCE_MANIFEST_SHA256_MISSING == true
THEN MERGE_CLOSEOUT_VERDICT=BLOCKED

IF SOURCE_EVIDENCE_REFERENCED == false AND SOURCE_EVIDENCE_NOT_REFERENCED != true
THEN MERGE_CLOSEOUT_VERDICT=BLOCKED

IF CLOSEOUT_MANIFEST_VERIFY_RC != 0
THEN MERGE_CLOSEOUT_VERDICT=BLOCKED
```

Diese Regel gilt für alle Merge-Closeouts, unabhängig davon, ob der PR nur Dokumentation, Tests, Offline-Research, Governance, Parity-Rewire oder Runtime-nahe Artefakte betrifft.

Sie erzeugt keine Runtime-Authority und darf keine bestehenden Safety-, Economic- oder Promotion-Gates überschreiben.

```text
NO_RUNTIME_AUTHORITY_FROM_MERGE_CLOSEOUT=true
NO_ECONOMIC_CLAIM_FROM_MANIFEST_VERIFY_ALONE=true
MANIFEST_VERIFY_PROVES_EVIDENCE_INTEGRITY_NOT_PROFITABILITY=true
```

---


# PART V-A — KANONISCHER IMPLEMENTIERUNGS-, PROVENANCE- UND REPAIR-VERTRAG

Dieser Teil ergänzt die bestehende Governance-, Safety-, Trading-, Risk-/Sizing-, Evidence- und Authority-Struktur. Er verändert keine bestehende Handelslogik und erzeugt keine Runtime-, Order-, Promotion- oder Economic-Pass-Authority.

```text
IMPLEMENTATION_CONTRACT_ADDITIVE_ONLY=true
CORE_TRADING_SEMANTICS_CHANGED=false
CANONICAL_TRADING_LOGIC_CHANGED=false
MASTER_V2_SEMANTICS_CHANGED=false
DOUBLE_PLAY_SEMANTICS_CHANGED=false
SCOPE_ENTRY_EXIT_REVERSAL_SEMANTICS_CHANGED=false
RISK_SIZING_SEMANTICS_CHANGED=false
SAFETY_SEMANTICS_CHANGED=false
KILLSWITCH_SEMANTICS_CHANGED=false
RECONCILIATION_SEMANTICS_CHANGED=false
AUTHORITY_SEMANTICS_CHANGED=false
PROMOTION_GATE_SEMANTICS_CHANGED=false
ECONOMIC_VALIDITY_GATE_CHANGED=false
```

Zweck dieses Teils ist, den bisher zwischen Runbook, Repo-Code, Tests und Beispiel-Slices verteilten technischen Vertrag so weit zu normieren, dass Cursor bei Digest-, Binding-, Materializer-, Binder-, Ratification-, Runner-, Repair- und Reevaluation-Arbeit nicht interpretieren oder raten muss.

## 33A.1 Grundregel: keine technischen Vermutungen

```text
NO_GUESSING_ABOUT_REPO_OWNERS=true
NO_GUESSING_ABOUT_DIGEST_PAYLOADS=true
NO_GUESSING_ABOUT_SERIALIZATION=true
NO_GUESSING_ABOUT_BINDING_IDENTITY=true
NO_GUESSING_ABOUT_RUNNER_REQUIREMENT=true
NO_GUESSING_ABOUT_SUPERSESSION=true
UNKNOWN_MUST_BE_REPORTED_EXPLICITLY=true
```

Ist ein technischer Sachverhalt nicht aus diesem Runbook, manifest-verifizierter Evidence oder dem aktuellen Repo eindeutig ableitbar, gilt:

```text
UNKNOWN_REQUIRES_REPO_EVIDENCE
→ READ_ONLY_OWNER_AND_CONTRACT_DISCOVERY
→ NO_MUTATION
→ STRUCTURED_FINDINGS
→ OPERATOR_OR_SEPARATE_RATIFICATION_IF_NORMATIVE_DECISION_REQUIRED
```

Zulässige Unknown-Klassen:

```text
UNKNOWN_CANONICAL_OWNER
UNKNOWN_DIGEST_INPUT_PAYLOAD
UNKNOWN_DIGEST_EXCLUDED_FIELDS
UNKNOWN_SERIALIZATION_CONTRACT
UNKNOWN_BINDING_IDENTITY_SEMANTICS
UNKNOWN_RATIFICATION_SUPERSESSION_SEMANTICS
UNKNOWN_RUNNER_OWNERSHIP
UNKNOWN_REEVALUATION_ENTRY_POINT
UNKNOWN_GENERATED_VS_AUTHORED_FIELD
UNKNOWN_TRANSITIVE_DIGEST_DEPENDENCY
UNKNOWN_TEST_OWNER
```

Ein Unknown darf nicht durch Kopieren eines ähnlichen Strategy-Slices als Wahrheit ersetzt werden. Ähnliche Slices sind Evidence für ein mögliches Pattern, nicht automatisch der kanonische Vertrag.

## 33A.2 Owner-Auflösung vor Mutation

Vor jeder Änderung an Configs, Bindings, Ratifications, Materializern, Digest-Funktionen, Runnern oder Evaluation-Entry-Points muss Cursor read-only inventarisieren:

```text
semantic_source_owner
materializer_owner
binder_or_validator_owner
digest_owner_per_digest_type
serialization_owner
binding_identity_owner
ratification_owner
runner_or_entry_point_owner
registry_owner
test_owner
evidence_owner
```

Für jeden Owner ist zu dokumentieren:

```text
owner_type
repo_path
symbol_or_schema
input_contract
output_contract
consumers
existing_tests
existing_call_sites
whether_single_canonical_owner
reuse_decision
confidence
unresolved_questions
```

Reuse-Reihenfolge bleibt zwingend:

```text
REUSE_AS_IS
→ REUSE_WITH_NARROW_ADAPTER
→ REWIRE_EXISTING_COMPONENT
→ CONSOLIDATE_TO_EXISTING_OWNER
→ NEW_IMPLEMENTATION_JUSTIFIED
```

Ein neuer Digest-, Materializer-, Binder-, Runner- oder Registry-Owner ist blockiert, solange nicht nachgewiesen ist, dass kein bestehender Owner den Contract erfüllen kann.

## 33A.3 Authored-, observed- und derived-Felder

Jedes relevante Feld muss genau einer Klasse zugeordnet werden:

```text
AUTHORED_SEMANTIC_FIELD
OBSERVED_EXTERNAL_BINDING_FIELD
DERIVED_DIGEST_FIELD
DERIVED_PROVENANCE_FIELD
DERIVED_REPORTING_FIELD
RUNTIME_STATE_FIELD
UNKNOWN_FIELD_CLASSIFICATION
```

Regeln:

```text
AUTHORED_SEMANTIC_FIELD_MAY_CHANGE_ONLY_IN_EXPLICITLY_AUTHORIZED_SEMANTIC_SLICE=true
OBSERVED_EXTERNAL_BINDING_FIELD_REQUIRES_POINT_IN_TIME_EVIDENCE=true
DERIVED_DIGEST_FIELD_MUST_BE_COMPUTED_BY_CANONICAL_OWNER=true
DERIVED_PROVENANCE_FIELD_MUST_BE_REGENERATABLE=true
DERIVED_FIELD_MUST_NOT_BE_HAND_EDITED_WHEN_CANONICAL_MATERIALIZER_EXISTS=true
UNKNOWN_FIELD_CLASSIFICATION_BLOCKS_MUTATION=true
```

Ein Repair darf derived metadata korrigieren, aber keine semantischen Felder stillschweigend verändern. Jede Änderung ist in einem maschinenlesbaren Feld-Diff zu klassifizieren.

## 33A.4 Kanonischer Digest-Contract

Für jeden Digest-Typ muss der aktuelle Repo-Contract read-only aufgelöst und dokumentiert werden. Mindestangaben:

```text
digest_name
canonical_owner
canonical_input_payload
included_fields
excluded_fields
normalization_rules
serialization_format
field_ordering
numeric_normalization
null_and_missing_semantics
encoding
hash_algorithm
self_reference_excluded
transitive_dependencies
consumers
validation_owner
```

Zwingende Invarianten:

```text
CANONICAL_DIGEST_OWNER_SINGLE_OR_EXPLICITLY_CONSOLIDATED=true
DIGEST_INPUT_MUST_BE_CANONICAL_PAYLOAD=true
DIGEST_SELF_INCLUSION_ALLOWED=false
DIGEST_OF_REPORTING_WRAPPER_INSTEAD_OF_SEMANTIC_PAYLOAD_ALLOWED=false
MANUAL_HASH_REIMPLEMENTATION_ALLOWED=false
NONDETERMINISTIC_FIELDS_IN_DIGEST_ALLOWED=false
TIMESTAMP_IN_SEMANTIC_DIGEST_ALLOWED=false unless explicitly ratified
FILESYSTEM_PATH_IN_SEMANTIC_DIGEST_ALLOWED=false unless explicitly ratified
DICT_OR_MAP_ORDER_MUST_BE_CANONICAL=true
FLOAT_NORMALIZATION_MUST_BE_EXPLICIT=true
REPEATED_COMPUTATION_MUST_BE_IDENTICAL=true
```

Dieses Runbook legt ohne Repo-Evidence nicht fest, welche konkrete Funktion welchen Digest berechnet. Cursor muss den tatsächlichen kanonischen Owner aus dem aktuellen Repo belegen. Fehlt ein eindeutiger Owner, ist das ein eigener Defect-/Governance-Scope und kein Anlass, einen neuen Algorithmus zu erfinden.

## 33A.5 Transitive Digest-Dependency-Graph

Vor jeder Digest-Reparatur oder Binding-Materialisierung muss ein gerichteter Dependency-Graph erzeugt werden:

```text
semantic_or_observed_source_fields
→ component_contract_digests
→ evaluation_or_composite_config_digest
→ binding_digest
→ ratification_or_registry_digest
→ evidence_references
```

Der konkrete Graph ist repo-abgeleitet und muss mindestens dokumentieren:

```text
node_name
node_type
canonical_owner
input_nodes
output_consumers
old_value
new_value
change_reason
semantic_change
cryptographic_identity_change
```

Regeln:

```text
TRANSITIVE_DIGEST_UPDATE_MUST_BE_COMPLETE=true
PARTIAL_DIGEST_CHAIN_UPDATE_ALLOWED=false
CIRCULAR_DIGEST_DEPENDENCY_ALLOWED=false
SELF_REFERENTIAL_MATERIALIZATION_ALLOWED=false
STALE_DESCENDANT_DIGEST_ALLOWED=false
UNEXPLAINED_DIGEST_CHANGE_ALLOWED=false
```

Eine Änderung eines upstream derived digest kann downstream digests kanonisch verändern. Das ist vollständig auszuweisen und darf nicht als „nur ein Feld geändert“ verkürzt werden.

## 33A.6 Semantische und kryptografische Binding-Identität

Jeder Binding-Bericht muss zwei Identitätsebenen getrennt ausweisen:

```text
SEMANTIC_BINDING_IDENTITY
CRYPTOGRAPHIC_BINDING_IDENTITY
```

Semantische Binding-Identität umfasst die fachlich wirksamen, authored oder observed Bindings, insbesondere soweit für den Scope relevant:

```text
strategy_id_and_version
research_scope_and_hypothesis
instrument_or_universe
dataset_identity_and_digest
signal_and_parameter_binding
ranking_rotation_or_selection_semantics
cost_execution_and_funding_binding
capital_risk_and_sizing_semantics
economic_policy_binding
validation_contract
```

Kryptografische Binding-Identität ist der tatsächlich kanonisch berechnete Binding-Digest.

Zwingende Berichtsregeln:

```text
IF SEMANTIC_FIELDS_UNCHANGED AND BINDING_DIGEST_UNCHANGED
THEN BINDING_CLASSIFICATION=SAME_SEMANTIC_AND_CRYPTOGRAPHIC_BINDING

IF SEMANTIC_FIELDS_UNCHANGED AND BINDING_DIGEST_CHANGED
THEN BINDING_CLASSIFICATION=SAME_SEMANTIC_BINDING_NEW_CRYPTOGRAPHIC_IDENTITY

IF SEMANTIC_FIELDS_CHANGED
THEN BINDING_CLASSIFICATION=MATERIAL_BINDING_CHANGE
```

```text
BINDING_DIGEST_CHANGED_MAY_NOT_BE_REPORTED_AS_CRYPTOGRAPHIC_IDENTITY_UNCHANGED=true
SEMANTIC_IDENTITY_UNCHANGED_MAY_NOT_HIDE_DIGEST_CHANGE=true
SAME_BINDING_TERM_REQUIRES_QUALIFICATION=true
```

Der unqualifizierte Ausdruck `same binding` ist nur zulässig, wenn semantische und kryptografische Identität unverändert sind. Andernfalls muss mindestens `same semantic binding, corrected/new cryptographic binding identity` verwendet werden.

Ob eine korrigierte kryptografische Identität eine neue versionierte Binding-ID, eine Supersession oder eine in-place repair record erfordert, darf nicht geraten werden. Diese Entscheidung muss aus dem aktuellen Ratification-/Registry-Contract belegt oder als Unknown separat ratifiziert werden.

## 33A.7 Defective Binding und Supersession

Ein bereits ratifiziertes oder referenziertes Binding mit technisch fehlerhafter derived metadata darf nicht stillschweigend historisch umgeschrieben werden, wenn dadurch Evidence-Referenzen, Digest-Wahrheiten oder Auditierbarkeit verloren gehen.

Zulässige Klassifikationen:

```text
DEFECTIVE_BINDING_REPAIRED_IN_PLACE
DEFECTIVE_BINDING_SUPERSEDED_BY_CORRECTED_BINDING
DEFECTIVE_DERIVED_METADATA_REGENERATED
MATERIAL_BINDING_CHANGE_REQUIRES_NEW_RATIFICATION
UNKNOWN_SUPERSESSION_CONTRACT
```

Pflichtfelder:

```text
old_binding_digest
new_binding_digest
semantic_fields_changed
cryptographic_identity_changed
defect_class
defect_owner
supersession_mode
supersedes_ref
superseded_by_ref
historical_evidence_preserved
negative_or_failed_evidence_preserved
retry_policy
```

Regeln:

```text
HISTORICAL_EVIDENCE_MUST_NOT_BE_REWRITTEN=true
FAILED_OR_NEGATIVE_EVIDENCE_MUST_NOT_BE_ERASED=true
DEFECTIVE_EXECUTION_ATTEMPT_REMAINS_AUDITABLE=true
CORRECTED_BINDING_MUST_REFERENCE_DEFECTIVE_PREDECESSOR_WHEN_IDENTITY_CHANGED=true
MATERIAL_CHANGE_REQUIRES_SEPARATE_RATIFICATION=true
```

Ist die Repo-Policy für Supersession nicht eindeutig, muss Cursor einen read-only Contract-Discovery-Bericht erstellen und darf die Ratification nicht nach eigenem Ermessen neu klassifizieren.

## 33A.8 Materializer-/Binder-Vertrag

Ein Materializer transformiert authored/observed Inputs in eine vollständig deterministische, validierbare Config oder Binding-Repräsentation. Ein Binder oder Validator prüft dieselbe kanonische Semantik über die kanonischen Digest-Owner.

Zwingende Invarianten:

```text
MATERIALIZER_MUST_USE_CANONICAL_DIGEST_OWNERS=true
MATERIALIZER_MUST_NOT_EMBED_WRONG_LAYER_DIGEST=true
MATERIALIZER_OUTPUT_MUST_BE_BINDER_ACCEPTED=true
MATERIALIZER_AND_BINDER_MUST_SHARE_CANONICAL_PAYLOAD_SEMANTICS=true
MATERIALIZER_MUST_NOT_DUPLICATE_DIGEST_ALGORITHM=true
MATERIALIZER_MUST_NOT_MUTATE_SOURCE_SEMANTICS=true
REPEATED_MATERIALIZATION_MUST_BE_BYTE_IDENTICAL=true
MATERIALIZATION_MUST_BE_IDEMPOTENT=true
ROUNDTRIP_MATERIALIZER_TO_BINDER_REQUIRED=true
```

Pflicht-Roundtrip:

```text
canonical authored/observed source
→ materializer
→ materialized artifact
→ binder/validator
→ PASS
```

Zusätzlicher deterministischer Nachweis:

```text
materialize(input, temp_dir_A)
materialize(input, temp_dir_B)
byte_compare(outputs_A, outputs_B)
→ DIFF_EMPTY
```

Falls byte-identische Outputs wegen ausdrücklich ratifizierter nicht-semantischer Provenance-Felder nicht möglich sind, müssen diese Felder außerhalb aller semantischen Digests liegen und ein normalisierter semantischer Vergleich muss identisch sein. Ein solcher Ausnahmecontract muss im Repo belegt sein; Cursor darf ihn nicht erfinden.

## 33A.9 Repair-Slice-Vertrag

Ein technischer Repair-Slice muss eng begrenzt sein und darf fachliche Evaluation und Defect-Repair nicht vermischen.

```text
REPAIR_SLICE_MUST_IDENTIFY_ROOT_CAUSE=true
REPAIR_SLICE_MUST_FIX_CANONICAL_OWNER=true
CONFIG_ONLY_PATCH_WHEN_GENERATOR_IS_DEFECTIVE_ALLOWED=false
REPAIR_SLICE_MUST_PRESERVE_UNRELATED_SEMANTICS=true
REPAIR_SLICE_MUST_REPORT_TRANSITIVE_DIGEST_CHANGES=true
REPAIR_SLICE_MUST_NOT_EXECUTE_ECONOMIC_EVALUATION=true unless explicitly separately authorized
REPAIR_SLICE_MUST_NOT_CLAIM_BASELINE_RESULT=true
REPAIR_SLICE_RUNTIME_EFFECT=NONE
REPAIR_SLICE_AUTHORITY_EFFECT=NONE
```

Ein Repair umfasst höchstens:

```text
canonical owner fix
required deterministic regeneration of derived artifacts
required registry/ratification metadata synchronization
focused regression tests
evidence and manifest
```

Nicht zulässig ohne separaten Scope:

```text
strategy_parameter_change
signal_change
cost_policy_change
risk_or_sizing_semantic_change
dataset_or_universe_change
threshold_relaxation
post_result_selection
economic_evaluation
robustness_execution
runtime_or_authority_change
```

## 33A.10 Repair und Reevaluation sind getrennte Authority-Slices

Standardsequenz:

```text
1. failed or blocked evaluation evidence
2. read-only defect classification
3. separately authorized repair PR
4. repair PR checks
5. repair merge-closeout with source and closeout manifests RC=0
6. separately authorized reevaluation
7. reevaluation binds repaired main HEAD and repair closeout as source evidence
```

```text
REPAIR_GO_DOES_NOT_AUTHORIZE_REEVALUATION=true
REEVALUATION_GO_DOES_NOT_RETROACTIVELY_AUTHORIZE_REPAIR=true
NO_EVALUATION_IN_REPAIR_PR_BY_DEFAULT=true
NO_MERGE_AND_REEVALUATE_IN_ONE_UNREVIEWED_SLICE=true
```

Die Reevaluation muss explizit ausweisen:

```text
previous_failed_attempt_ref
repair_pr_closeout_ref
old_binding_digest
new_binding_digest
semantic_binding_identity_relation
cryptographic_binding_identity_relation
same_dataset
same_universe
same_strategy_parameters
same_cost_policy
same_risk_sizing_semantics
```

Ein unveränderter semantischer Scope mit korrigiertem Binding-Digest ist keine unveränderte kryptografische Wiederholung und muss entsprechend benannt werden.

## 33A.11 Runner- und Entry-Point-Contract

Vor jeder Evaluation muss genau ein kanonischer Entry Point feststehen.

Mögliche, aber repo-seitig zu belegende Klassen:

```text
REUSE_EXISTING_GENERIC_RUNNER
REUSE_EXISTING_DIRECT_INVOCATION
REUSE_EXISTING_STRATEGY_SPECIFIC_RUNNER
ADD_THIN_CANONICAL_ADAPTER
RUNNER_NOT_REQUIRED_BY_REPO_CONTRACT
UNKNOWN_RUNNER_CONTRACT
```

Pflichtinventar:

```text
how_prior_attempt_was_invoked
canonical_generic_runner_if_any
strategy_specific_runner_if_any
direct_callable_entry_point
config_binding_method
go_token_enforcement
offline_boundary_enforcement
evidence_output_owner
existing_runner_tests
```

Ein dünner Adapter darf ausschließlich:

```text
reference_the_versioned_config
invoke_existing_canonical_owner
pass_go_and_offline_gates
bind_output_and_evidence_locations
exit_fail_closed
```

Er darf nicht:

```text
duplicate_strategy_logic
duplicate_sizing_logic
duplicate_cost_logic
duplicate_digest_logic
duplicate_dataset_or_universe_logic
create_runtime_authority
```

Regeln:

```text
RUNNER_REQUIRED_FALSE_REQUIRES_NAMED_ALTERNATIVE_ENTRY_POINT=true
RUNNER_ACTION_NOT_APPLICABLE_REQUIRES_REPO_CONTRACT_PROOF=true
NO_GENERIC_RUNNER_FOUND_DOES_NOT_IMPLY_RUNNER_NOT_REQUIRED=true
NEW_STRATEGY_SPECIFIC_RUNNER_REQUIRES_REUSE_DECISION=true
```

Wenn unklar ist, ob ein Runner Pflicht ist, ist `UNKNOWN_RUNNER_CONTRACT` auszugeben und vor Evaluation read-only zu klären.

## 33A.12 Pflicht-Testmatrix für Digests, Bindings und Materializer

Für jeden betroffenen Contract sind folgende Testaussagen zu bewerten:

```text
stale_or_wrong_layer_digest_rejected
correct_digest_accepted_by_real_binder
canonical_digest_owner_used
materializer_to_binder_roundtrip_pass
repeated_materialization_deterministic
second_materialization_diff_empty
semantic_payload_unchanged_when_repair_claims_no_semantic_change
dataset_digest_unchanged_when_claimed
universe_digest_unchanged_when_claimed
strategy_parameters_unchanged_when_claimed
cost_policy_unchanged_when_claimed
risk_sizing_semantics_unchanged_when_claimed
transitive_digest_chain_complete
old_evidence_preserved
supersession_or_repair_relation_valid
no_runtime_effect
no_authority_effect
```

Jede Aussage muss klassifiziert werden:

```text
DIRECTLY_PROVEN
INDIRECTLY_PROVEN
NOT_PROVEN
NOT_APPLICABLE_WITH_REASON
```

Merge-Admissibility verlangt für alle materiellen Aussagen `DIRECTLY_PROVEN`, außer das Runbook oder ein repo-kanonischer Contract erlaubt ausdrücklich einen indirekten Nachweis.

Nur statische Gleichheitsprüfungen gegen bereits geschriebene JSON-Werte reichen nicht aus, wenn der produktive Materializer oder Binder betroffen ist. Mindestens ein Test muss den realen Produktionspfad aufrufen.

## 33A.13 Config-, Binding- und Ratification-Änderungsdiff

Jeder entsprechende PR muss ein maschinenlesbares Vorher-/Nachher-Diff erzeugen:

```text
field_path
old_value
new_value
field_class
canonical_owner
change_type
semantic_effect
cryptographic_effect
reason
```

Zulässige `change_type`-Werte:

```text
SEMANTIC_AUTHORIZED_CHANGE
OBSERVED_BINDING_REFRESH
DERIVED_DIGEST_RECOMPUTATION
DERIVED_PROVENANCE_REFRESH
TRANSITIVE_DIGEST_UPDATE
UNEXPECTED_CHANGE
```

```text
UNEXPECTED_CHANGE_COUNT_MUST_BE_ZERO=true
UNCLASSIFIED_CHANGED_FIELD_COUNT_MUST_BE_ZERO=true
```

## 33A.14 Final-Report-Wahrheitsvertrag

Final Reports dürfen keine widersprüchlichen Wahrheiten enthalten. Pflichtfelder für Digest-/Binding-/Repair-Slices:

```text
ROOT_CAUSE_CONFIRMED
CANONICAL_OWNER
OLD_COMPONENT_DIGESTS
NEW_COMPONENT_DIGESTS
OLD_EVALUATION_CONFIG_DIGEST
NEW_EVALUATION_CONFIG_DIGEST
OLD_BINDING_DIGEST
NEW_BINDING_DIGEST
SEMANTIC_BINDING_FIELDS_CHANGED
CRYPTOGRAPHIC_BINDING_IDENTITY_CHANGED
BINDING_CLASSIFICATION
SUPERSESSION_MODE
MATERIALIZER_TO_BINDER_ROUNDTRIP_PASS
DETERMINISTIC_MATERIALIZATION
SECOND_MATERIALIZATION_DIFF_EMPTY
RUNNER_REQUIRED
RUNNER_ACTION
CANONICAL_ENTRY_POINT
ECONOMIC_EVALUATION_EXECUTED
RUNTIME_EFFECT
AUTHORITY_EFFECT
SOURCE_MANIFEST_VERIFY_RC
MANIFEST_VERIFY_RC
UNRESOLVED_UNKNOWNS
```

Blocker:

```text
IF OLD_BINDING_DIGEST != NEW_BINDING_DIGEST
AND CRYPTOGRAPHIC_BINDING_IDENTITY_CHANGED != true
THEN REPORT_CONTRADICTION=true

IF SEMANTIC_BINDING_FIELDS_CHANGED == true
AND BINDING_CLASSIFICATION CLAIMS SAME_SEMANTIC_BINDING
THEN REPORT_CONTRADICTION=true

IF RUNNER_REQUIRED == false
AND CANONICAL_ENTRY_POINT IS EMPTY
AND RUNNER_ACTION != RUNNER_NOT_REQUIRED_BY_REPO_CONTRACT
THEN REPORT_CONTRADICTION=true

IF REPORT_CONTRADICTION == true
THEN MERGE_ADMISSIBLE=false
```

## 33A.15 Evidence-Pflicht für Implementation-Contract-Slices

Mindestens:

```text
preflight.txt
source_manifest_verification.txt
owner_inventory.json
reuse_decision.json
field_classification.json
digest_contracts.json
digest_dependency_graph.json
before_after_field_diff.json
semantic_identity_comparison.json
cryptographic_identity_comparison.json
materializer_roundtrip.txt
deterministic_materialization.txt
runner_decision.json
test_assertion_matrix.json
test_results.txt
final_report.txt
MANIFEST.sha256
```

Nicht vorhandene oder nicht anwendbare Artefakte müssen als explizite `NOT_APPLICABLE_WITH_REASON`-Records erscheinen; sie dürfen nicht stillschweigend fehlen.

## 33A.16 CI- und PR-Grenzen

```text
FOCUSED_CI_PREFERRED=true
FULL_CI_REQUIRES_EXPLICIT_TRIGGER_PROOF=true
NO_POLLING=true
ONE_TERMINAL_CHECK_SNAPSHOT=true
NO_RERUN=true
NO_WORKFLOW_DISPATCH=true
```

FULL CI ist nur erforderlich, wenn zentrale Framework-, Dependency-, Infrastruktur- oder breit konsumierte Contract-Änderungen vorliegen oder der Impact nicht sicher begrenzt werden kann. Die Entscheidung ist vor CI zu dokumentieren.

Ein Repair-PR darf nicht gemergt werden, wenn:

```text
canonical_owner_unknown
materializer_roundtrip_not_proven
digest_dependency_graph_incomplete
unexpected_change_count_nonzero
report_contradiction_true
binding_classification_unknown_and_material
runner_contract_required_for_next_step_but_unresolved
source_or_closeout_manifest_rc_nonzero
```

## 33A.17 Cursor-Arbeitsregel für neue oder unklare Slices

Cursor muss vor Umsetzung in dieser Reihenfolge arbeiten:

```text
1. reconcile current state
2. verify source manifests
3. inventory canonical owners
4. classify fields
5. resolve digest contracts
6. build dependency graph
7. resolve identity and supersession semantics
8. resolve runner/entry-point contract
9. list knowns, unknowns and blockers
10. only then implement the smallest admissible slice
11. execute focused proof matrix
12. create durable evidence
13. open exactly one bounded PR
14. stop before merge unless operator explicitly signals checks green
```

Wenn Schritt 3 bis 8 keine eindeutige Antwort liefert:

```text
DO_NOT_IMPLEMENT
CREATE_READ_ONLY_DISCOVERY_REPORT
STATE_EXACT_INFORMATION_NEEDED
```

Das ist kein Projektstopp. Es ist ein fail-closed Diagnose-Slice, aus dem der nächste sichere Implementierungsauftrag abgeleitet wird.

## 33A.18 Repo-seitige kurze Navigations-SSOT

Zusätzlich zu diesem vollständigen Runbook soll im Repo eine kurze, stabile Navigationsdatei geführt werden. Empfohlener Pfad, sofern kein bestehender näherer Owner existiert:

```text
docs/governance/PEAK_TRADE_IMPLEMENTATION_CONTRACT.md
```

Diese Datei ist kein zweites Runbook. Sie muss:

```text
reference_the_full_canonical_runbook
summarize_non_negotiable_boundaries
state_the_owner_discovery_sequence
state_digest_binding_materializer_runner_rules
state_repair_vs_reevaluation_separation
state_unknown_no_guessing_rule
point_to_repo_canonical_owners_and_tests
```

Sie darf nicht:

```text
redefine_trading_logic
redefine_safety
redefine_risk_or_sizing
redefine_authority
embed_mutable_project_progress_as_normative_truth
become_parallel_ssot
```

Vor Erstellung muss Cursor prüfen, ob bereits ein kanonischer Repo-Owner für diese Implementierungsverträge existiert. Falls ja, ist dieser zu erweitern statt eine parallele Datei anzulegen.

---

# 34. Korrigierte kanonische Implementierungsreihenfolge

## STEP 29A — Constitutional and Semantic Contract Freeze

- v4.3 als Zielsemantik binden,
- bestehende Owner und Reuse Decisions ratifizieren,
- keine Runtime-Wirkung.

## STEP 29B — Canonical Market Context Binding

Reuse:

```text
src/trading/master_v2/double_play_futures_input.py
FuturesInputSnapshot
evaluate_futures_input_snapshot
```

Ziel:

```text
CanonicalMarketContextV1
```

Pflicht:

- finalisierte Trading Epoch,
- Warmup,
- Clock Trust,
- Mark/Index/Bid/Ask,
- Data Integrity,
- Input Digest,
- Idempotenz,
- Out-of-Order-Block.

## STEP 29C — Canonical Scope Initialization

- Scope Lifecycle,
- Initialisierung,
- Reinitialisierung,
- keine impliziten Defaults,
- keine freie Reinitialisierung bei offener oder unbekannter Position.

## STEP 29D — Deterministic Scope Event Generator

Erst nach 29B und 29C.

Reuse:

- `transition_state()`,
- `DynamicScopeRules`,
- `RuntimeScopeState`,
- bestehende Test-Harness-Fixtures.

Kein isolierter Preis-gegen-Grenze-Shortcut.

## STEP 29E — Bull/Bear Directional Assessment Completion

- ein gemeinsamer Contract,
- Symmetrie,
- Candidate/Confirmed,
- keine Authority-Wirkung.

## STEP 29F — Survival and Suitability Binding

Reuse vorhandener Module.

Ergänzen:

- Kostenmodell,
- Regime-Owner,
- deterministische Strategy-Auswahl.

## STEP 29G — Double Play Composition Matrix Completion

- vollständige Matrix,
- Konfliktregel,
- kein implizites Scoring-Override.

## STEP 29H — Entry, Position Management and Exit Policy

- Entry Preconditions,
- Exit-Klassen,
- Profit Protection,
- Reversal Preparation,
- Partial-Fill-Semantik.

## STEP 29I — Integrated Offline Trading Logic Replay

Kette:

```text
CanonicalMarketContextV1
→ Scope Initialization
→ Scope Event
→ Bull/Bear
→ State Switch
→ Survival
→ Suitability
→ Double Play
→ CanonicalTradingDecisionEvidenceV1
→ MANIFEST.sha256
```

Keine Runtime, keine Orders.

## STEP 29J — Default Backtest Economic Realism Binding

Reuse:

```text
scripts/run_backtest.py
src/backtest/engine.py
config.toml
```

Pflicht:

- keine impliziten Nullkosten,
- Fees/Slippage aus versionierter Config,
- Tests für Default-Binding,
- bestehende CLI-Kompatibilität.

## STEP 29K — Strategy Registry Consolidation

Zielowner:

```text
src/strategies/registry.py
```

Legacy-Keys nur über explizite Aliase und Deprecation.

## STEP 29L — MV2 Research Wiring

Kette:

```text
Canonical MV2 Decision Path
→ Backtest
→ Walk-Forward
→ Monte Carlo
→ Stress
→ Metrics
→ Evidence Chain
```

Keine duplizierte Signal- oder Strategy-Logik.

## STEP 29L.1 — Full Canonical System Backtest Parity Gate

Dieser Schritt ist eine explizite Sperre vor entscheidungsrelevanter System-Economic-Evidence.

Ziel:

```text
FULL_CANONICAL_CHAIN_WIRED=true
BACKTEST_RUNTIME_DECISION_PARITY_PASS=true
```

Pflichtumfang:

```text
Bull/Bear State Switch
Scope adverse exit
Reversal preparation
Flat-before-opposite-side
Survival and Suitability
Double Play composition
Entry / Position / Exit Policy
Capital / Risk / Sizing
Canonical Order Intent boundary
Safety Kernel semantics
KillSwitch boundary semantics
Reconciliation and Unknown Outcome semantics
Promotion Gate boundary
AI / Observability / Explainability boundary
Feedback / Learning boundary
```

Nicht erforderlich in diesem Schritt:

```text
NO_RUNTIME_AUTHORITY_REQUIRED
NO_SHADOW_REQUIRED
NO_PAPER_REQUIRED
NO_TESTNET_REQUIRED
NO_ORDER_SUBMISSION_REQUIRED
NO_CREDENTIALS_REQUIRED
```

Blocker-Regel:

```text
IF FULL_CANONICAL_CHAIN_WIRED != true
THEN SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE=false
```


## STEP 29L.2 — Offline Linear Evidence Scaffolding and Diagnostics Boundary

Dieser Schritt bindet den OLS-/Offline-Linear-Evidence-Layer als unterstützende Diagnoseinfrastruktur. Er darf vor produktiver Economic-Evidence als Scaffolding umgesetzt werden, bleibt aber diagnostic-only.

Ziel:

```text
LINEAR_EVIDENCE_LAYER_REUSE_DECISION_DOCUMENTED=true
LINEAR_MODEL_EVIDENCE_V1_BOUND=true
FEATURE_MATRIX_BINDING_PASS=true
OLS_BASELINE_FITTER_PASS=true
COST_MODEL_DIAGNOSTICS_PASS_OR_FAIL_CLOSED=true
```

Pflichtumfang v0:

```text
Contracts
Deterministic Fixture Truth Pack
Feature Matrix Builder
Lookahead / time-order guards
numpy.linalg.lstsq baseline fitter
Diagnostics: rank, condition_number, residuals, MAE, RMSE, R2 train/validation
Import-boundary tests
Failure Taxonomy
Manifest-verified report
```

Pflichtgrenzen:

```text
OFFLINE_ONLY=true
NO_CONFIG_DEFAULT_CHANGE_FOR_BACKTEST_COSTS_IN_V0=true
DO_NOT_BIND_COST_MODEL_INTO_STRATEGY_SELECTION=true
VALIDATION_SPLIT_MUST_BE_TIME_ORDERED=true
CALIBRATED_COST_POLICY=CONSERVATIVE_NOT_MEAN
NO_IMPORT_FROM_RUNTIME_EXECUTION_PATH=true
NO_IMPORT_FROM_ORDER_ADAPTERS=true
NO_IMPORT_FROM_SCHEDULER=true
OLS_RUNTIME_AUTHORITY=false
OLS_ORDER_AUTHORITY=false
OLS_ENTRY_EXIT_AUTHORITY=false
SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE=false
RUNTIME_REWIRE_ADMISSIBLE=false
```

Sequenzentscheidung:

```text
IF FULL_CANONICAL_CHAIN_WIRED != true OR BACKTEST_RUNTIME_DECISION_PARITY_PASS != true
THEN OLS_ALLOWED_SCOPE=SCAFFOLDING_AND_FAIL_CLOSED_DIAGNOSTIC_GAP_ASSESSMENT_ONLY

IF FULL_CANONICAL_CHAIN_WIRED == true AND BACKTEST_RUNTIME_DECISION_PARITY_PASS == true
THEN OLS_ALLOWED_SCOPE=PRODUCTIVE_OFFLINE_DIAGNOSTICS_FOR_STEP29M_SUPPORT
```

Recommended first PR:

```text
OFFLINE_LINEAR_COST_MODEL_DIAGNOSTICS_V0
```

## STEP 29M — Economic Viability Evidence

Erzeuge persistierte, manifest-verifizierte Netto-Evidence. OLS-/Linear-Diagnostics dürfen hier als unterstützende, referenzierte Evidence eingebunden werden, sofern sie manifest-verifiziert, time-ordered validiert und authority-neutral sind.

```text
ECONOMIC_VIABILITY_EVIDENCE_MAY_REFERENCE_LINEAR_DIAGNOSTICS=true
LINEAR_DIAGNOSTICS_SUPPORT_ONLY=true
OLS_CAN_NOT_SET_ECONOMICALLY_VIABLE_OFFLINE=true
OLS_CAN_NOT_REPLACE_WALK_FORWARD_MC_STRESS=true
```

## STEP 29N — Promotion Economic Gate Binding

Bindung an:

- EconomicViabilityEvidenceV1,
- Strategy Profiles,
- Robustness,
- Evidence Admissibility.

Kein Live-GO.

## STEP 29O — Intent Compatibility Firewall

Konsolidierung der parallelen Intent-Typen.

## STEP 29P — Capital / Risk / Sizing Mathematics

Monotone Quantity-Kette.

## STEP 29Q — Canonical Order Intent

Keine Adapter-Kompatibilität ohne explizite Transformation.

## STEP 29R — Runtime Rewire

Erst nach:

```text
TRADING_LOGIC_COMPLETION_GATE_PASS
ECONOMIC_VALIDITY_OFFLINE_GATE_PASS
INTENT_COMPATIBILITY_FIREWALL_PASS
```

`PRE_ECONOMIC_ZERO_ORDER_EVIDENCE` ersetzt diese Voraussetzungen nicht.

## STEP 29S — Fenced Writer and Restart Contract

## STEP 29T — Zero-Order Runtime

Erfordert weiterhin `ECONOMIC_VALIDITY_OFFLINE_GATE_PASS=true`. Die Pre-Economic
Zero-Order Evidence-Stufe ist **nicht** STEP 29T und autorisiert STEP 29T nicht.

## STEP 29U — Shadow

STEP 29U ist die zukünftige kanonische Ladder-Stufe **Shadow**. Sie liegt nach
STEP 29T (Zero-Order Runtime) und vor STEP 29V (Paper).

Diese Ratifikation definiert ausschließlich Repository-Semantik, Grenzen,
Ownership-Anforderungen und verbotene Äquivalenzen. Die offline Composition
ist in den kanonischen OKX-Futures Shadow no-order Pfad gebunden; Aktivierung
bleibt unautorisiert.

```text
STEP29U_SEMANTICS_RATIFIED=true
STEP29U_OPERATIONAL_STATUS=OFFLINE_COMPOSITION_BOUND_INTO_CANONICAL_SHADOW_NO_ORDER_NOT_ACTIVATED
CANONICAL_STEP_29U_BOUND=true
CANONICAL_SHADOW_MODE_EXISTS=true
STEP_29U_IMPLEMENTED=true
STEP_29U_ACTIVATED=false
CANONICAL_STEP_29U_ABSENT=CLEARED_COMPOSITION_BOUND_ACTIVATION_STILL_UNAUTHORIZED
NON_ACTIVATING=true
AUTHORITY_EFFECT=NONE
SHADOW_ACTIVATION_AUTHORIZED=false
```

### Nicht enthalten (verbindlich)

Diese Semantik-Ratifikation stellt **nicht** bereit und autorisiert **nicht**:

- eine lauffähige Shadow-Session,
- ein Scheduler-Job oder Worker,
- einen persistenten Prozess,
- kontinuierlichen Live-Marktdaten-Konsum,
- kontinuierliche simulierte Order-Intents,
- Fill-Execution,
- Position-/Account-Projektion,
- Restart/Resume,
- Runtime-Bridge-Aktivierung,
- Shadow-/Paper-/Testnet-/Live-Authority.

### Zukünftiges Mindestkontrakt (nicht implementiert)

Eine spätere STEP-29U-Implementation darf nur nach separater, bounded
Ratifikation mindestens dieser Komponenten existieren:

- canonical mode identity,
- lifecycle owner,
- session state machine,
- canonical decision consumption,
- execution-simulation boundary,
- fill/cost model ownership,
- position/account projection ownership,
- durable state and restart/resume,
- failure handling,
- audit evidence,
- activation boundary,
- explicit Operator GO requirements.

Dies sind zukünftige Voraussetzungen, keine implementierten Komponenten und
keine durch dieses Dokument freigegebenen Dateipfade.

### Authority

STEP 29U darf niemals eine zweite Decision-, Risk-, Safety-, Execution-,
Promotion- oder Runtime-Authority werden.

Bestehende Sole Authorities bleiben unverändert:

- Master V2 / Double Play für kanonische Decision-Semantik,
- bestehende Risk/Sizing-Authority,
- unabhängige Safety/Veto-Authority,
- bestehende Execution-/Reconciliation-Boundaries,
- externes Operator GO für Aktivierung.

```text
NO_SECOND_DECISION_AUTHORITY=true
NO_SECOND_RISK_AUTHORITY=true
NO_SECOND_SAFETY_AUTHORITY=true
NO_SECOND_EXECUTION_AUTHORITY=true
NO_SECOND_PROMOTION_AUTHORITY=true
NO_SECOND_RUNTIME_AUTHORITY=true
```

### Verbotene Äquivalenz

Keines der folgenden Surfaces ist kanonisches STEP 29U:

- Phase 24 `ShadowOrderExecutor` (`src/orders/shadow.py`),
- `scripts/run_shadow_execution.py`,
- Phase 31 `ShadowPaperSession` (`src/live/shadow_session.py`),
- `scripts/run_shadow_paper_session.py`,
- Shadow-247 Charter, Wrapper oder Preflight,
- Shadow Preparation Readiness Gate
  (`ops.shadow_preparation_readiness_gate_v0`),
- Dashboard-/WebUI-Readmodels,
- bloße Existenz von Config- oder Job-Definitionen.

```text
HISTORICAL_SHADOW_SURFACES_NON_EQUIVALENT_TO_STEP_29U=true
READINESS_GATE_IS_NOT_STEP_29U=true
CONFIG_OR_JOB_PRESENCE_IS_NOT_ACTIVATION=true
```

### Historische Reuse-Regel

Historische Komponenten dürfen nur als **nicht-autoritative**
Implementierungs-Inputs nach einer späteren, expliziten bounded Ratifikation
betrachtet werden. Ihre aktuelle Existenz:

- bindet STEP 29U nicht,
- autorisiert keine Aktivierung,
- etabliert keine Ownership,
- beweist keine Readiness,
- gewährt keine semantische Äquivalenz.

### Economic- und Activation-Locks

```text
ECONOMIC_VALIDITY_OFFLINE_GATE_PASS=false
SHADOW_PREPARATION_COMPLETE=false
SHADOW_ACTIVATION_AUTHORIZED=false
PAPER_ACTIVATION_AUTHORIZED=false
TESTNET_ACTIVATION_AUTHORIZED=false
SCHEDULER_ACTIVATION_AUTHORIZED=false
RUNTIME_ACTIVATION_AUTHORIZED=false
LIVE_AUTHORIZED=false
ORDERS=false
RUNTIME_BRIDGE_STATE=BOUND_NOT_ACTIVATED
```

### Dashboard-Blocker

**HISTORICAL (at STEP-29U docs ratification time):**
`MARKET_DASHBOARD_VISIBLE_INTRABAR_CONTINUITY=OPEN` was recorded as an open
Dashboard preparation blocker. That historical OPEN claim must not be treated
as current Market Dashboard product truth.

**CURRENT (repository-proven after PR #5548):** Market Dashboard Landscape V2
visible intrabar continuity is `PASS` / resolved on the sealed Landscape V2
consumer surface. Canonical current-state owner:
`docs/ops/market_dashboard/PEAK_TRADE_MARKET_DASHBOARD_LANDSCAPE_MASTER_RUNBOOK_V2.md`
(`INTRABAR_CAPABILITY=PASS`). This supersession does **not** authorize Shadow,
Paper, Testnet, Scheduler, Runtime, Orders, Capital, or Live.

```text
DASHBOARD_BLOCKER_ID=MARKET_DASHBOARD_VISIBLE_INTRABAR_CONTINUITY
# HISTORICAL_AT_STEP_29U_RATIFICATION (superseded as current product truth):
# MARKET_DASHBOARD_VISIBLE_INTRABAR_CONTINUITY=OPEN
# DASHBOARD_BLOCKER_STATE=OPEN
# DASHBOARD_BLOCKER_RESOLVED=false
# CURRENT_POST_PR_5548 (Landscape V2 consumer surface):
MARKET_DASHBOARD_VISIBLE_INTRABAR_CONTINUITY=PASS
DASHBOARD_BLOCKER_STATE=RESOLVED_ON_LANDSCAPE_V2
DASHBOARD_BLOCKER_RESOLVED=true
DASHBOARD_BLOCKER_WAIVED=false
RESOLVED_BY_PR=5548
CANONICAL_DASHBOARD_CLOSEOUT_OWNER=docs/ops/market_dashboard/PEAK_TRADE_MARKET_DASHBOARD_LANDSCAPE_MASTER_RUNBOOK_V2.md
```

Dieser Docs-only Semantik-Slice wurde durch den (damals offenen) Dashboard-Blocker
**nicht** blockiert. Der historische OPEN-Zustand darf durch diesen Slice weder
als weiterhin aktuell dargestellt noch als Runtime-/Activation-Freigabe gelesen
werden.

### Next-Step Boundary

Nach dieser Ratifikation ist als nächste Repository-Aktion nur ein
separat autorisierter, bounded, non-activating Preparation-Slice zulässig.
Keine STEP-29U-Implementation ist durch diese Dokumentänderung autorisiert.

```text
NEXT_PERMITTED_CLASS=OFFLINE_NON_ACTIVATING_PREPARATION_ONLY
STEP_29U_IMPLEMENTATION_AUTHORIZED_BY_THIS_RATIFICATION=false
```

### Separate Operator GO

Separates Operator GO ist verpflichtend vor:

- kanonischer STEP-29U-Implementation,
- persistenter Shadow-Session,
- Scheduler- oder Worker-Start,
- kontinuierlichem Live-Marktdaten-Job,
- kontinuierlichen simulierten Order-Intents,
- Paper / Testnet / Runtime / Live / Orders / Capital / Promotion.

```text
SEPARATE_OPERATOR_GO_REQUIRED_FOR_STEP29U_IMPLEMENTATION=true
SEPARATE_OPERATOR_GO_REQUIRED_FOR_ANY_ACTIVATION_STAGE=true
```

## STEP 29V — Paper

## STEP 29W — Testnet

## STEP 29X — Measured SLO Evidence

## STEP 29Y — Bounded Canary

## STEP 29Z — Full Autonomous Production

---

# 35. Aktuell autorisierter nächster Schritt

Der letzte dokumentierte Abschlussstand ist der manifest-verifizierte Merge-Closeout von PR #5078.

```text
POST_MERGE_HEAD=5a5ab570022cae47ec5442638ab0180f66caa1e4
HEAD_EQUALS_ORIGIN_MAIN=true
WORKTREE_CLEAN=true
PR5078_MERGED=true
RESEARCH_SCOPE=cross_sectional_ma_crossover_panel_rank_rotation/v0
DATASET_MATERIALIZED=true
DATASET_ID=pit_okx_linear_usdt_non_bitcoin_pt1h_panel
DATASET_SCHEMA=pit_okx_pt1h_panel_ohlcv_dataset_manifest_v1
INSTRUMENT_COUNT=399
BITCOIN_PRESENT=false
BAR_INTERVAL=PT1H
ROW_COUNT_TOTAL=37905
DATASET_DIGEST=c753c5795ab40d26237a066702cb72a06065bfce0143440ec0ccadfe249cc0e0
ECONOMIC_EVALUATION_EXECUTED=false
RUNTIME_EFFECT=NONE
AUTHORITY_EFFECT=NONE
```

`ma_crossover/v1` bleibt in seiner früheren Single-Instrument-Bindung terminal negativ. Der neue Scope ist nur deshalb admissibel, weil er eine sachlich eigenständige Cross-sectional-Multi-Instrument-Panel-Rank-Rotation mit neuem Dataset und neuer Portfolio-/Ranking-Semantik darstellt.

```text
PRIOR_SINGLE_INSTRUMENT_EVIDENCE=TERMINAL_NEGATIVE
UNCHANGED_SINGLE_INSTRUMENT_RETRY_BLOCKED=true
PANEL_ARCHETYPE_EVIDENCE=NOT_PREVIOUSLY_EXECUTED
MATERIAL_DIFFERENCE_PROVEN=true
```

Der aktuell autorisierte nächste Schritt lautet ausschließlich nach separatem Operator-GO:

```text
NEXT_STEP=VERSIONED_CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_BINDING_RATIFICATION
```

Dieser Schritt darf ausschließlich die bereits ratifizierte Research-Hypothese unveränderlich und reproduzierbar binden:

```text
research scope and version
underlying ma_crossover/v1 signal without signal mutation
dataset ID, schema and digest
exact instrument universe and universe digest
point-in-time and survivorship semantics
ranking formula and deterministic tie-break
selection, hold, exit and rotation semantics
rebalance cadence
missing/stale instrument handling
portfolio weighting and exposure constraints
realistic cost and execution bindings
economic policy binding
walk-forward, Monte-Carlo and stress contracts
implementation, config, data and universe digests
```

Nicht zulässig:

```text
NO_ECONOMIC_EVALUATION
NO_PARAMETER_OPTIMIZATION
NO_POST_RESULT_PARAMETER_SELECTION
NO_THRESHOLD_REDUCTION
NO_POLICY_RESCUE
NO_SIGNAL_LOGIC_CHANGE
NO_CORE_SYSTEM_CHANGE
NO_MASTER_V2_CHANGE
NO_DOUBLE_PLAY_CHANGE
NO_RISK_SIZING_CHANGE
NO_SAFETY_RUNTIME_CHANGE
NO_RUNTIME_REWIRE
NO_RUNTIME_EVIDENCE
NO_SHADOW
NO_PAPER
NO_TESTNET
NO_SCHEDULER
NO_ADAPTER_SUBMISSION
NO_ORDERS
NO_CREDENTIALS
NO_ARMING
NO_CANARY
NO_LIVE
```

Nach erfolgreicher Binding-Ratifikation bleibt eine Economic Evaluation erneut separat gegatet.

Neuere manifest-verifizierte Abschlussberichte ersetzen diesen Abschnitt nur als Fortschrittsstand. Sie ändern weder die kanonische Reihenfolge noch die Sicherheits-, Trading-, Risk-, Evidence- oder Authority-Regeln dieses Runbooks.

---

# 36. Testleiter

## LEVEL 0 — Unit und Contract

- Schemas,
- State Transitions,
- Digests,
- Futures-only,
- Bitcoin-Verbot,
- negative Tests.

## LEVEL 1 — Integrated Offline Replay

- vollständige MV2-Handelslogik,
- kein Runtime-/Adapter-Zugriff,
- MANIFEST-verifizierte Evidence.

## LEVEL 2 — Canonical System Backtest Parity

- vollständige kanonische Entscheidungskette,
- Bull/Bear State Switch,
- Scope adverse exit und Reversal Preparation,
- Capital/Risk/Sizing,
- Safety-/KillSwitch-/Reconciliation-Boundary,
- AI-/Observability-/Feedback-Boundary,
- gleiche Decision-Semantik wie Offline Replay und spätere Runtime.

## LEVEL 2.1 — Economic Backtest

- realistische Kosten,
- gleiche Trading Logic,
- persistierte Resultate,
- nur als System-Economic-Evidence zulässig, wenn LEVEL 2 PASS ist.


## LEVEL 2.2 — Offline Linear Evidence Diagnostics

- Contracts,
- Feature Matrix Builder,
- deterministic Fixture Truth Pack,
- OLS baseline fitter,
- Cost-/Slippage-Diagnostics,
- Signal-Orthogonality-Diagnostics,
- Factor-Exposure-Diagnostics,
- Parameter-Sensitivity-Diagnostics,
- Rolling-Drift-Diagnostics,
- Import-boundary tests,
- no authority effects,
- MANIFEST-verifizierte Evidence.

LEVEL 2.2 darf LEVEL 2 nicht ersetzen. Für System-Economic-Evidence gilt LEVEL 2 PASS als Voraussetzung.

## LEVEL 3 — Walk-Forward / Monte Carlo / Stress

- OOS,
- Parameterstabilität,
- Sequenzrobustheit,
- Kostenstress.

## LEVEL 3.5 — Pre-Economic Zero-Order Evidence (governed)

- vollständig passiv,
- Zero-Order only,
- max. 21600 Sekunden,
- explizites Operator-GO,
- keine Economic-/Shadow-/Runtime-Authority,
- Contract: `PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_SESSION_V1`.

Diese Stufe ersetzt weder Economic Validity noch LEVEL 4 Zero-Order Runtime
(STEP 29T) noch LEVEL 5 Shadow (STEP 29U).

## LEVEL 4 — Zero-Order Runtime

## LEVEL 5 — Shadow

## LEVEL 6 — Paper

## LEVEL 7 — Testnet

## LEVEL 8 — Measured SLO Evidence

## LEVEL 9 — Bounded Canary

## LEVEL 10 — Full Autonomous Production

Keine Stufe darf übersprungen werden.

---


---

# 36A. Canonical End-to-End System Smoke Run

Dieser Abschnitt dokumentiert den dauerhaft verpflichtenden kanonischen End-to-End-System-Smoke-Test als Integritätsnachweis der vollständigen Offline-Decision-Chain. Er ergänzt das Runbook ausschließlich additiv.

```text
CANONICAL_END_TO_END_SYSTEM_SMOKE_RUN_REQUIRED=true
OFFLINE_ONLY=true
NETWORK_ACCESS=false
LIVE_AUTHORIZED=false
ORDERS_ALLOWED=false
SHADOW_ALLOWED=false
PAPER_ALLOWED=false
TESTNET_ALLOWED=false
```

Zweck:

```text
Canonical Replay Input Builder
→ Canonical Offline Orchestrator
→ vollständige Decision Chain
→ CanonicalTradingDecisionEvidence
→ manifest-verifizierter Abschluss
```

Pflichtinvarianten:

```text
CANONICAL_REPLAY_INPUT_BUILDER_SINGLE_OWNER=true
CANONICAL_ORCHESTRATOR_SINGLE_DECISION_OWNER=true
STRATEGY_LAYER_FEEDS_CANONICAL_CHAIN=true
STRATEGY_SUITABILITY_CONSUMER_CANONICAL=true
BACKTEST_RUNTIME_DECISION_PARITY=true
LEGACY_BYPASS_DETECTED=false
PARALLEL_PIPELINE_CREATED=false
TRADING_SEMANTICS_CHANGED=false
RISK_SIZING_SEMANTICS_CHANGED=false
EXECUTION_SEMANTICS_CHANGED=false
```

Der Smoke-Test dient ausschließlich dem Nachweis der technischen Integrität der vollständigen Offline-Systemkette. Er erzeugt keine Runtime-, Promotion-, Economic- oder Order-Authority.

# 37. Definition of Done — Trading Logic

```text
CANONICAL_MARKET_CONTEXT_BOUND=true
FINALIZED_TRADING_EPOCH_BOUND=true
WARMUP_POLICY_BOUND=true
SCOPE_INITIALIZATION_BOUND=true
SCOPE_EVENT_FORMULAS_BOUND=true
BULL_ASSESSMENT_BOUND=true
BEAR_ASSESSMENT_BOUND=true
SURVIVAL_FORMULAS_BOUND=true
SUITABILITY_SELECTION_BOUND=true
DOUBLE_PLAY_MATRIX_COMPLETE=true
DECISION_PRECEDENCE_BOUND=true
ENTRY_POLICY_BOUND=true
POSITION_MANAGEMENT_POLICY_BOUND=true
EXIT_POLICY_BOUND=true
PARTIAL_FILL_SEMANTICS_BOUND=true
RISK_SIZING_FORMULAS_BOUND=true
INSTRUMENT_SELECTION_BOUNDARY_ENFORCED=true
DETERMINISTIC_REPLAY_PASS=true
CANONICAL_END_TO_END_SYSTEM_SMOKE_RUN_PASS=true
CANONICAL_END_TO_END_SYSTEM_SMOKE_RUN_OFFLINE_ONLY=true
FULL_CANONICAL_CHAIN_WIRED=true
BACKTEST_RUNTIME_DECISION_PARITY_PASS=true
BULL_BEAR_STATE_SWITCH_BACKTEST_PARITY_PASS=true
SCOPE_EXIT_REVERSAL_BACKTEST_PARITY_PASS=true
SAFETY_RECONCILIATION_BOUNDARY_BACKTEST_PARITY_PASS=true
AI_OBSERVABILITY_FEEDBACK_BOUNDARY_DOCUMENTED=true
```

---

# 38. Definition of Done — Economic Validity

```text
DEFAULT_BACKTEST_COSTS_BOUND=true
NO_IMPLICIT_ZERO_COST_PATH=true
MV2_BACKTEST_WIRING_PASS=true
MV2_WALK_FORWARD_WIRING_PASS=true
MV2_MONTE_CARLO_WIRING_PASS=true
MV2_STRESS_WIRING_PASS=true
PARAMETER_SENSITIVITY_COMPUTED=true
NET_PERFORMANCE_EVIDENCE_PERSISTED=true
ECONOMIC_VIABILITY_EVIDENCE_VALID=true
PROMOTION_ECONOMIC_GATE_ENFORCED=true
SYSTEM_ECONOMIC_EVIDENCE_REQUIRES_FULL_CANONICAL_CHAIN=true
RAW_SIGNAL_EVIDENCE_NOT_PROMOTION_ADMISSIBLE=true
LINEAR_MODEL_EVIDENCE_V1_BOUND=true
FEATURE_MATRIX_BINDING_PASS=true
OLS_BASELINE_FITTER_PASS=true
COST_MODEL_DIAGNOSTICS_PASS_OR_FAIL_CLOSED=true
VALIDATION_SPLIT_MUST_BE_TIME_ORDERED=true
NO_CONFIG_DEFAULT_CHANGE_FOR_BACKTEST_COSTS_IN_V0=true
CALIBRATED_COST_POLICY=CONSERVATIVE_NOT_MEAN
SIGNAL_ORTHOGONALITY_OPTIONAL_BOUND=false initially
FACTOR_EXPOSURE_OPTIONAL_BOUND=false initially
PARAMETER_SENSITIVITY_OPTIONAL_BOUND=false initially
NO_RUNTIME_AUTHORITY_FROM_LINEAR_EVIDENCE=true
```

---

# 39. Definition of Done — Safety and Runtime

```text
SAFETY_KERNEL_MANDATORY=true
KILL_SWITCH_RUNTIME_DRILL_PASS=true
RECONCILIATION_PASS=true
UNKNOWN_OUTCOME_RECOVERY_PASS=true
CLOCK_TRUST_PASS=true
SINGLE_WRITER_PASS=true
FENCING_TOKEN_ENFORCED=true
DURABLE_BEFORE_SUBMIT_PASS=true
RESTART_RECONCILIATION_PASS=true
```

Zusätzliche Definition of Done für eine spätere Multi-Future-Runtime:

```text
MULTI_FUTURE_GOVERNANCE_RATIFIED=true
PORTFOLIO_ALLOCATOR_AUTHORITY_BOUND=true
GLOBAL_PORTFOLIO_RISK_GATE_PASS=true
PER_INSTRUMENT_RECONCILIATION_PASS=true
MULTI_INSTRUMENT_RECONCILIATION_PASS=true
MULTI_INSTRUMENT_UNKNOWN_OUTCOME_RECOVERY_PASS=true
CORRELATION_CLUSTER_CAPS_ENFORCED=true
GLOBAL_EXPOSURE_CAPS_ENFORCED=true
PER_INSTRUMENT_CAPS_ENFORCED=true
MAX_POSITIONS_INCREASE_OPERATOR_RATIFIED=true
```

---

# 40. Kanonische Sicherheitsinvarianten

```text
FAVORABLE_EXTREME_MOVE_ALONE_DOES_NOT_TRIGGER_KILLSWITCH=true
ADVERSE_MOVE_USES_RISK_EXIT_STATE_SWITCH_FIRST=true
OPPOSITE_SIDE_CANNOT_OPEN_BEFORE_RECONCILED_FLAT=true
RECONCILIATION_FAILURE_BLOCKS_NEW_EXPOSURE=true
UNKNOWN_OUTCOME_NEVER_AUTO_RESUBMITS=true
DYNAMIC_SCOPE_CANNOT_EXPAND_BEYOND_HARD_LIMITS=true
CURRENT_SCOPE_IS_IMMUTABLE_WITHIN_DECISION_CYCLE=true
NO_ORDER_WITHOUT_QUANTITY_PROVENANCE=true
NO_ADAPTER_WITHOUT_SINGLE_USE_PERMISSION=true
NO_RUNTIME_AUTHORITY_FROM_EVIDENCE=true
NO_ENTRY_FROM_UNFINALIZED_MARKET_DATA=true
NO_DYNAMIC_SCOPE_UPDATE_FROM_UNTRUSTED_DATA=true
NO_IMPLICIT_STRATEGY_SELECTION=true
NO_IMPLICIT_ENTRY_OR_EXIT_ORDER_TYPE=true
ROUNDING_MUST_NOT_INCREASE_RISK=true
NO_RUNTIME_REWIRE_BEFORE_TRADING_LOGIC_COMPLETION_GATE=true
NO_ECONOMIC_CLAIM_WITHOUT_REALISTIC_COSTS=true
NO_PROMOTION_ELIGIBILITY_FROM_CONFIDENCE_ONLY=true
NO_MULTI_FUTURE_RUNTIME_FROM_RANKING_ONLY=true
NO_MULTI_FUTURE_RUNTIME_FROM_ECONOMIC_EVIDENCE_ONLY=true
NO_PORTFOLIO_ALLOCATOR_MAY_OVERRIDE_SAFETY=true
NO_PORTFOLIO_ALLOCATOR_MAY_OVERRIDE_RECONCILIATION=true
NO_MAX_POSITIONS_INCREASE_WITHOUT_OPERATOR_RATIFICATION=true
NO_RUNTIME_EVIDENCE_BEFORE_FULL_CORE_COMPLETION=true
POST_MERGE_MAIN_SYNC_AND_MANIFEST_VERIFY_REQUIRED=true
REFERENCED_SOURCE_EVIDENCE_MANIFEST_VERIFY_REQUIRED=true
SOURCE_EVIDENCE_ABSENCE_MUST_BE_EXPLICITLY_REPORTED=true
LINEAR_MODEL_OUTPUT_IS_NOT_TRADING_DECISION=true
LINEAR_MODEL_OUTPUT_IS_NOT_PROMOTION_PASS=true
LINEAR_MODEL_OUTPUT_IS_NOT_RUNTIME_AUTHORITY=true
LINEAR_MODEL_OUTPUT_IS_NOT_MULTI_FUTURE_AUTHORITY=true
NO_IMPORT_FROM_RUNTIME_EXECUTION_PATH=true
NO_IMPORT_FROM_ORDER_ADAPTERS=true
NO_IMPORT_FROM_SCHEDULER=true
OLS_CAN_NOT_FORCE_ACTIVE_SET_REPLACEMENT=true
```

---

# 41. Audit-bestätigte Reuse Decisions

## REUSE_AS_IS

```text
src/trading/master_v2/*
src/execution/pipeline.py
src/live/safety.py
src/ops/gates/risk_gate.py
src/backtest/walkforward.py
src/experiments/monte_carlo.py
src/experiments/stress_tests.py
scripts/ops/ci_test_selection_v1.py
scripts/ops/primary_evidence_retention_v0.py
src/webui/market_instrument_eligibility_v0.py
```

## REUSE_WITH_NARROW_ADAPTER

```text
scripts/run_backtest.py
src/experiments/strategy_profiles.py
src/experiments/stress_tests.py
src/execution/paper/futures_accounting.py
src/research/linear_evidence/* if existing Research/Evidence owner selected
```

## REWIRE_EXISTING_COMPONENT

```text
Master V2 → Offline Replay
Master V2 → Backtest
Promotion Loop → Economic Gates
Live Gates → Governed Session Start
```

## CONSOLIDATE_TO_EXISTING_OWNER

```text
Strategy Registry → src/strategies/registry.py
Portfolio Backtest → src/backtest/engine.py
Regime Owner → canonical MV2-bound path
```

## DEPRECATE_LEGACY_PATH

```text
legacy load_strategy path after alias migration
src/portfolio/manager.py after parity
execution_simple after decoupling
ShadowPaperSession after LiveSessionRunner parity
```

---

# 42. Nicht zulässige Fehlinterpretationen

```text
TECHNICAL_CAPABILITY_PRESENT
!= ECONOMIC_VALIDITY_PROVEN
```

```text
NEGATIVE_COMMITTED_PROFILE
!= WHOLE_SYSTEM_UNPROFITABLE
```

```text
MISSING_EVIDENCE
!= MISSING_IMPLEMENTATION
```

```text
RUNBOOK_TARGET_STATE
!= CURRENT_REPO_STATE
```

```text
AUDIT_RANKING
!= AUTOMATIC_IMPLEMENTATION_ORDER
```

```text
MAX_POSITIONS=1
!= FINAL_PRODUCT_LIMIT
```

```text
TOP20_RANKING
!= TOP20_RUNTIME_TRADING
```

```text
MULTI_FUTURE_TARGET_MODEL
!= MULTI_FUTURE_RUNTIME_AUTHORITY
```

```text
PORTFOLIO_BACKTEST_CAPABILITY
!= PORTFOLIO_RUNTIME_AUTHORITY
```

```text
RAW_SIGNAL_BACKTEST_PASS
!= SYSTEM_ECONOMIC_VALIDITY_PASS
```

```text
OLS_DIAGNOSTIC_PASS
!= ECONOMIC_VALIDITY_PASS
```

```text
LINEAR_COST_CALIBRATION_PASS
!= BACKTEST_COST_DEFAULT_CHANGE_AUTHORITY
```

```text
SIGNAL_ORTHOGONALITY_PASS
!= STRATEGY_SELECTION_AUTHORITY
```

```text
FACTOR_EXPOSURE_MARKS_REPLACEMENT
!= ACTIVE_SET_REPLACEMENT_AUTHORITY
```

```text
STRATEGY_ARCHETYPE_FAIL
!= CANONICAL_PEAK_TRADE_SYSTEM_FAIL
```

```text
FULL_CANONICAL_CHAIN_NOT_WIRED
!= ECONOMIC_VALIDITY_PROVEN
```

```text
RUNTIME_EVIDENCE
!= CORE_SYSTEM_COMPLETION_BYPASS
```

Die endgültige Reihenfolge folgt der semantischen Abhängigkeit des kanonischen Kernsystems.

---

# 43. Abschlussgrundsatz

Peak Trade ist erst dann fachlich und wirtschaftlich bereit, wenn:

```text
das vollständige kanonische System fertig verdrahtet ist,
die Handelslogik konsistent und deterministisch ist,
Bull und Bear symmetrisch und konfliktfrei koordiniert werden,
Dynamic Scope, Exit und Reversal getrennt sind,
die gleiche Logik in Research und Runtime verwendet wird,
Backtests realistische Kosten enthalten,
Offline Linear Evidence / OLS Diagnostics Kosten-, Signal-, Faktor-, Parameter- und Drift-Fragen erklärbar unterstützen,
Walk-Forward, Monte Carlo und Stress auf der kanonischen Logik laufen,
Netto-Performance-Evidence reproduzierbar persistiert wird,
Promotion technisch auf Economic Validity und Safety blockiert,
Runtime Safety unabhängig bleibt,
und keine Authority aus Readiness oder Evidence abgeleitet wird.
```

Der kanonische Weg lautet:

```text
Canonical Market Context
→ Scope Initialization
→ Scope Event Generator
→ Bull/Bear Assessments
→ Survival and Suitability
→ Double Play
→ Entry/Position/Exit Policy
→ Capital/Risk/Sizing
→ Canonical Order Intent Boundary
→ Safety / KillSwitch / Reconciliation Boundary
→ Promotion / Observability / Feedback Boundary
→ Manifest-Verified Full Canonical System Parity
→ Integrated Offline Replay
→ Realistic Backtest
→ Offline Linear Evidence / OLS Diagnostics
→ Walk-Forward / Monte Carlo / Stress
→ Pre-Economic Zero-Order Evidence (optional, governed; non-activating)
→ Economic Viability Evidence
→ Promotion Gates
→ Zero-Order Runtime
→ Shadow
→ Paper
→ Testnet
→ Measured SLO Evidence
→ Bounded Canary
→ Full Autonomous Production
```

Keine Activation-Stufe darf übersprungen werden. Die Pre-Economic Zero-Order
Evidence-Stufe ist optional und non-activating; sie ersetzt weder Economic
Validity noch Zero-Order Runtime noch Shadow.

---

# 43.1 Operativer Current-State-Anhang vom 2. Juli 2026

```text
CANONICAL_REVALIDATION_HEAD=cc19aedc57886d706a2db623aa7fcc23e7f90a39
HEAD_EQUALS_ORIGIN_MAIN=true
WORKTREE_CLEAN=true
PRIMARY_WORKTREE_MUTATED=false
REPO_MUTATION=false
```

Manifest-verifizierte Planning-Bundles:

```text
bounded_post_step30a_economic_validity_recovery_governance_matrix_canonical_revalidation_read_only_v0_20260702T212800Z
bounded_multi_candidate_futures_research_fleet_inventory_and_archetype_mapping_read_only_v0_20260702T234800Z
bounded_multi_candidate_futures_research_fleet_final_convergence_and_binding_readiness_read_only_v0_20260702T235500Z
```

Für alle drei gilt:

```text
MANIFEST_VERIFY_RC=0
```

Dieser Current-State-Anhang ist Fortschritts- und Governance-Evidence. Er ersetzt keine versionierten Repo-Owner, keine Strategy-Bindings und keine EconomicViabilityEvidenceV1.

---

# 44. v4.4.11 Änderungsprotokoll

Gegenüber v4.4.10 wurde ausschließlich der additive Governance-Abschnitt §0.1A ergänzt. Die bestehende Handelslogik, Safety-, Risk-/Sizing-, KillSwitch-, Reconciliation-, Promotion-, Evidence- und Authority-Semantik bleibt unverändert.

Ergänzt wurden:

1. §0.1A — Vollständige kanonische Systemparität vor System-Economic-Evidence,
2. maschinenlesbare Flags für Parity-, Wiring- und Backtest-/Runtime-Decision-Parity-Anforderungen,
3. explizite Abgrenzung: Raw-Signal-, Partial-Pipeline- und isolierte Research-Evidence sind keine kanonische System-Economic-Evidence,
4. verbindliche Reihenfolge: bei negativen oder schwachen Economic-Ergebnissen zuerst read-only Paritäts- und Verdrahtungsprüfung, dann reuse-first Wiring-Closure, erst danach fachliche Interpretation.

```text
IMPLEMENTATION_CONTRACT_ADDITIVE_ONLY=true
CORE_TRADING_SEMANTICS_CHANGED=false
CANONICAL_TRADING_LOGIC_CHANGED=false
MASTER_V2_SEMANTICS_CHANGED=false
DOUBLE_PLAY_SEMANTICS_CHANGED=false
SCOPE_ENTRY_EXIT_REVERSAL_SEMANTICS_CHANGED=false
RISK_SIZING_SEMANTICS_CHANGED=false
SAFETY_SEMANTICS_CHANGED=false
KILLSWITCH_SEMANTICS_CHANGED=false
RECONCILIATION_SEMANTICS_CHANGED=false
AUTHORITY_SEMANTICS_CHANGED=false
PROMOTION_GATE_SEMANTICS_CHANGED=false
ECONOMIC_VALIDITY_GATE_CHANGED=false
```

---


# 44.0 v4.4.12 Änderungsprotokoll

Gegenüber v4.4.11 wurde ausschließlich ein additiver Governance-Abschnitt für den kanonischen Offline-End-to-End-System-Smoke-Run ergänzt.

Ergänzt wurden:

1. Canonical End-to-End System Smoke Run als verpflichtender Offline-Integritätsnachweis,
2. Dokumentation der Architektur-Invarianten (Single Replay Builder Owner, Single Decision Owner, keine Legacy-Bypässe, keine parallele Pipeline),
3. ausdrückliche Offline-Only- und No-Authority-Abgrenzung,
4. Ergänzung der Definition of Done um den erfolgreichen End-to-End-System-Smoke-Test.

Nicht geändert wurden:

```text
CORE_TRADING_SEMANTICS_CHANGED=false
CANONICAL_TRADING_LOGIC_CHANGED=false
MASTER_V2_SEMANTICS_CHANGED=false
DOUBLE_PLAY_SEMANTICS_CHANGED=false
RISK_SIZING_SEMANTICS_CHANGED=false
SAFETY_SEMANTICS_CHANGED=false
AUTHORITY_SEMANTICS_CHANGED=false
PROMOTION_GATE_SEMANTICS_CHANGED=false
ECONOMIC_VALIDITY_GATE_CHANGED=false
```

# 44. v4.4.10 Änderungsprotokoll

Gegenüber v4.4.9 wurde ausschließlich ein additiver kanonischer Implementierungs-, Provenance- und Repair-Vertrag ergänzt. Die bestehende Handelslogik, Safety-, Risk-/Sizing-, KillSwitch-, Reconciliation-, Promotion-, Evidence- und Authority-Semantik bleibt unverändert.

Ergänzt wurden:

1. verbindliche No-Guessing- und Unknown-Regeln für nicht belegte Repo-Contracts,
2. read-only Owner-Auflösung vor jeder Mutation,
3. Klassifikation von authored, observed und derived Feldern,
4. kanonische Digest- und Serialisierungsanforderungen,
5. transitive Digest-Dependency-Graphen,
6. getrennte semantische und kryptografische Binding-Identität,
7. Repair-/Supersession-Regeln für technisch defekte Bindings,
8. Materializer-/Binder-Roundtrip und deterministische Rematerialisierung,
9. strikte Trennung von Defect-Repair und Reevaluation,
10. expliziter Runner-/Entry-Point-Contract,
11. verpflichtende Test- und Assertion-Matrix,
12. maschinenlesbare Vorher-/Nachher-Felddiffs,
13. widerspruchsfreie Final-Report-Regeln,
14. eine kurze repo-seitige Navigations-SSOT ohne paralleles Runbook.

```text
IMPLEMENTATION_CONTRACT_ADDITIVE_ONLY=true
CORE_TRADING_SEMANTICS_CHANGED=false
CANONICAL_TRADING_LOGIC_CHANGED=false
MASTER_V2_SEMANTICS_CHANGED=false
DOUBLE_PLAY_SEMANTICS_CHANGED=false
SCOPE_ENTRY_EXIT_REVERSAL_SEMANTICS_CHANGED=false
RISK_SIZING_SEMANTICS_CHANGED=false
SAFETY_SEMANTICS_CHANGED=false
KILLSWITCH_SEMANTICS_CHANGED=false
RECONCILIATION_SEMANTICS_CHANGED=false
AUTHORITY_SEMANTICS_CHANGED=false
PROMOTION_GATE_SEMANTICS_CHANGED=false
ECONOMIC_VALIDITY_GATE_CHANGED=false
```

---

# 44. v4.4.9 Änderungsprotokoll

Gegenüber der vorherigen v4.4.9-Fassung wurde ausschließlich die Arbeitsweise für neue Chats und fortlaufenden Projektfortschritt korrigiert.

Geändert wurden:

1. Das Runbook bleibt eine stabile kanonische SSOT und muss nach Merges nicht mehr von Cursor überschrieben werden.
2. Fortschritt wird über manifest-verifizierte Final Reports, Merge-Closeouts, Repo-Progress-Owner und Evidence-Bundles fortgeführt.
3. Ein neuer Chat darf das Runbook ohne widersprechende neuere Evidence nicht pauschal als veraltet oder unbrauchbar zurückweisen.
4. Ein neuerer belegter Abschlussstand supersediert ausschließlich Progress-Metadaten und `NEXT_STEP`, niemals kanonische Normen.
5. Der verpflichtende Desktop-Sync und der verpflichtende Runbook-Rewrite nach jedem State Change wurden entfernt.
6. Der Fallback-Checkpoint wurde auf den Merge-Closeout von PR #5078 aktualisiert.
7. Der nächste separate Schritt ist die versionierte Binding-Ratifikation des Cross-sectional-MA-Crossover-Panel-Rank-Rotation-v0-Scopes.

Nicht geändert wurden:

```text
CORE_TRADING_SEMANTICS_CHANGED=false
CANONICAL_TRADING_LOGIC_CHANGED=false
MASTER_V2_SEMANTICS_CHANGED=false
DOUBLE_PLAY_SEMANTICS_CHANGED=false
SCOPE_ENTRY_EXIT_REVERSAL_SEMANTICS_CHANGED=false
RISK_SIZING_SEMANTICS_CHANGED=false
SAFETY_SEMANTICS_CHANGED=false
KILLSWITCH_SEMANTICS_CHANGED=false
RECONCILIATION_SEMANTICS_CHANGED=false
AUTHORITY_SEMANTICS_CHANGED=false
PROMOTION_GATE_SEMANTICS_CHANGED=false
ECONOMIC_VALIDITY_GATE_CHANGED=false
IMPLEMENTATION_SEQUENCE_CHANGED=false
```

```text
RUNBOOK_REWRITE_AFTER_MERGE_REQUIRED=false
CURSOR_MAY_NOT_REWRITE_RUNBOOK_FOR_PROGRESS_TRACKING=true
LATEST_VERIFIED_EXTERNAL_EVIDENCE_OVERRIDES_EMBEDDED_PROGRESS_ONLY=true
LATEST_VERIFIED_EXTERNAL_EVIDENCE_MAY_NOT_OVERRIDE_CANONICAL_NORMS=true
```

---

# 44. v4.4.8 Änderungsprotokoll

Gegenüber v4.4.7 wurden ausschließlich Session-Bootstrap-, Current-State- und Fortschrittsregeln ergänzt beziehungsweise aktualisiert. Die kanonische Handelslogik, Safety-Semantik, Authority-Grenzen, Risk-/Sizing-Verträge und Implementierungsreihenfolge wurden nicht verändert.

Ergänzt wurden:

1. ein verpflichtender `CURRENT_STATE_RECONCILIATION_AND_RUNBOOK_REFRESH_READ_ONLY_V0` beim Einsatz in einem neuen Chat oder einer neuen Arbeitssitzung,
2. die ausdrückliche Einstufung eingebetteter Current-State-Angaben als potenziell veraltet und bis zum Repo-Abgleich nicht autoritativ,
3. eine fail-closed Sperre gegen Implementierung, Evaluation oder Runtime-Arbeit vor abgeschlossenem Current-State-Abgleich,
4. eine klare Trennung zwischen stabilen kanonischen Normen und veränderlichem Projektfortschritt,
5. die Empfehlung eines repo-abgeleiteten `PEAK_TRADE_CURRENT_STATE_V1.md`-Sidecars, ohne diesen bereits als vorhandenen Owner zu behaupten,
6. der terminal negative Abschluss der vollständigen kanonischen STEP29M-Baseline-Generation,
7. das Wiederholungsverbot unveränderter fehlgeschlagener Bindings und das Verbot eines Policy-Rescues,
8. der neue nächste read-only Schritt `NEW_DISTINCT_RESEARCH_GENERATION_HYPOTHESIS_AND_CANDIDATE_RANKING_READ_ONLY_V0`.

```text
CORE_TRADING_SEMANTICS_CHANGED=false
SAFETY_SEMANTICS_CHANGED=false
AUTHORITY_SEMANTICS_CHANGED=false
RISK_SIZING_SEMANTICS_CHANGED=false
SESSION_BOOTSTRAP_ADDED=true
CURRENT_STATE_REFRESH_REQUIRED=true
```

---

# 44. v4.4.7 Änderungsprotokoll

Die in v4.4.6 vollständig eingebettete Parameter-MD wurde bewusst zurückgebaut. Maßgeblich bleibt das kanonische Handelslogik-Runbook. Übernommen wurden nur Point-in-Time-Datenbindung, realistische Kosten, Gross/Cost/Net-Attribution, Reproduzierbarkeit, time-ordered Validation, OOS-Schutz und eine schlanke Klassifikation ausdrücklich kalibrierbarer Parameter.

Entfernt oder entschärft wurden insbesondere:

1. ein eigenständiger gleichrangiger Parameter-Governance-Layer,
2. zusätzliche Gate-Klassen als operative Pflichtstruktur,
3. standardmäßige vollständige Filter-Interaktionsmatrizen,
4. umfangreiche Pflichtinventare für jede Referenz und jeden konstanten Wert,
5. vollständige Final-Evidence-Pakete für frühe Baseline- und Diagnoseläufe,
6. jede Möglichkeit, Diagnostik als zusätzlichen Entry-, Survival-, Suitability-, Chop-, Ranking- oder Promotion-Filter zu verwenden.

```text
CANONICAL_TRADING_LOGIC_IS_PRIMARY_SSOT=true
PARAMETER_GOVERNANCE_IS_SUBORDINATE=true
NO_SECOND_PARAMETER_DRIVEN_TRADING_SYSTEM=true
SAFETY_SEMANTICS_CHANGED=false
CORE_TRADING_SEMANTICS_CHANGED=false
```

---

# 44.1 v4.4.5 Änderungsprotokoll

## 44.1.1 v4.4.5 Offline-Linear-Evidence-Integration

Diese integrierte Fassung ergänzt OLS / Offline Linear Evidence v1.1 als Teil der Economic-Validation-Domäne. Geändert wird ausschließlich die diagnostische Economic-Support-Schicht. Nicht geändert werden Core-System, kanonische Handelslogik, Master V2, Double Play, Scope-, Entry-, Exit- oder Reversal-Semantik, Risk-/Sizing-Verträge, Safety Kernel, Reconciliation oder Runtime-Authority.

Ergänzt wurden:

1. OLS als `OFFLINE_EVIDENCE_DIAGNOSTIC_AND_CALIBRATION_LAYER`,
2. `LinearModelEvidenceV1` und optionale Referenzen in `EconomicViabilityEvidenceV1`,
3. Cost-/Slippage-Diagnostics mit konservativer Cost-Policy,
4. Signal-Orthogonalität, Faktor-Exposure, Parameter-Sensitivität und Rolling-Drift als Support-Diagnostics,
5. Import- und Runtime-Boundary-Guards,
6. Active-Set-Replacement-Schutz für spätere Multi-Future-Portfolio-Fragen,
7. STEP 29L.2 als Scaffolding-/Diagnostics-Boundary zwischen Full-Canonical-Parity und Economic-Viability-Evidence.

```text
OLS_RUNTIME_AUTHORITY=false
OLS_ORDER_AUTHORITY=false
OLS_ENTRY_EXIT_AUTHORITY=false
OLS_SIZING_AUTHORITY=false
OLS_PROMOTION_PASS_AUTHORITY=false
OLS_CAN_NOT_SET_ECONOMICALLY_VIABLE_OFFLINE=true
OLS_CAN_NOT_REPLACE_WALK_FORWARD_MC_STRESS=true
```

Gegenüber v4.4.4 wurde ausschließlich eine operative Sequenzklarstellung ergänzt:

1. Das vollständige Core-System muss zuerst kanonisch fertiggestellt, verdrahtet und manifest-verifiziert werden.
2. Vor dieser Core-System-Completion ist keine Runtime-, Shadow-, Paper-, Testnet-, Canary-, Live-, Zero-Order- oder sonstige ausführungsnahe Evidence-Erzeugung als nächster Arbeitsstrom zulässig.
3. Zulässig vor vollständiger Core-Completion bleiben ausschließlich Core-System-Completion, Offline-Parity-Assessment und narrow Reuse-First-Rewire fehlender kanonischer Pfade.
4. Diese Klarstellung ändert keine Safety-, Runtime-, Order-, Credential-, Economic-, Promotion-, Shadow-, Paper-, Testnet-, Canary- oder Live-Authority.
5. `FULL_CANONICAL_CHAIN_WIRED=false` und `BACKTEST_RUNTIME_DECISION_PARITY_PASS=false` blockieren weiterhin jede System-Economic-Evidence und jede ausführungsnahe Evidence-Stufe.

## 44.2 v4.4.4 Änderungsprotokoll

Gegenüber v4.4.3 wurde ausschließlich die Source-Evidence-Formulierung des Post-Merge-Guards präzisiert:

1. Referenzierte Source-Evidence-Bundles müssen nach dem Merge erneut per `MANIFEST.sha256` verifiziert werden.
2. Ein referenziertes Source-Evidence-Bundle ohne `MANIFEST.sha256` blockiert den Closeout.
3. Falls ein Closeout fachlich kein Source-Evidence-Bundle referenziert, muss `SOURCE_EVIDENCE_NOT_REFERENCED=true` explizit dokumentiert werden.
4. Ein fehlender Source-Evidence-Bezug darf nicht stillschweigend als `SOURCE_MANIFEST_VERIFY_RC=0` ausgegeben werden.
5. Diese Präzisierung erzeugt keine Runtime-, Economic-, Promotion-, Shadow-, Paper-, Testnet-, Canary- oder Live-Authority und lockert keine Safety-Grenze.

## 44.3 v4.4.3 Änderungsprotokoll

Gegenüber v4.4.2 wurde eine explizite Post-Merge-Evidence-Guard-Regel ergänzt:

1. Jeder Merge-Closeout muss nach dem Merge `main` hart gegen `origin/main` synchronisieren.
2. `POST_MERGE_HEAD` und `POST_MERGE_ORIGIN_MAIN` müssen identisch sein.
3. Referenzierte Source-Evidence-Bundles müssen, sofern vorhanden, nach dem Merge erneut per `MANIFEST.sha256` verifiziert werden.
4. Das neue Closeout-Bundle muss ein eigenes `MANIFEST.sha256` erzeugen und unmittelbar mit `RC=0` verifizieren.
5. Ein Merge-Closeout ohne `HEAD_EQUALS_ORIGIN_MAIN=true`, `SOURCE_MANIFEST_VERIFY_RC=0` und `CLOSEOUT_MANIFEST_VERIFY_RC=0` ist nicht vollständig und muss als blockiert oder unvollständig dokumentiert werden.
6. Diese Regel erzeugt keine Runtime-, Economic-, Promotion-, Shadow-, Paper-, Testnet-, Canary- oder Live-Authority.

## 44.4 v4.4.2 Änderungsprotokoll

Gegenüber v4.4.1 wurde eine explizite Full-System-Completion-Klarstellung ergänzt:

1. Vollständige System-Economic-Evidence ist erst zulässig, wenn die vollständige kanonische Peak-Trade-Kette implementiert, verdrahtet und manifest-verifiziert ist.
2. Rohsignal-, Ranking-, Slot- oder isolierte Research-Kandidaten-Backtests dürfen nur als Explorations- oder Negative-Evidence gelten, nicht als vollständige System-Evidence.
3. Bull/Bear State Switch, Scope adverse exit, Reversal Preparation, Flat-before-opposite-side, Capital/Risk/Sizing, Safety/KillSwitch/Reconciliation, Promotion Gates, AI-/Observability- und Feedback-Boundaries müssen vor entscheidungsrelevanter Economic Validation als Backtest-/Runtime-paritär nachgewiesen werden.
4. Der aktuelle nächste Schritt wird auf `FULL_CANONICAL_SYSTEM_BACKTEST_PARITY_GAP_ASSESSMENT_AND_REWIRE_SCOPE` korrigiert.
5. Sicherheits-, Runtime-, Order-, Credential-, Shadow-, Paper-, Testnet-, Canary- und Live-Grenzen bleiben unverändert blockiert.

## 44.5 v4.4.1 Änderungsprotokoll

Gegenüber v4.4 wurde zusätzlich eine Governance-Klarstellung ergänzt:

1. `MAX_POSITIONS=1` und `SINGLE_SELECTED_FUTURE=true` sind ausdrücklich als initiale Safety-/Stability-Phase definiert, nicht als finale Produktgrenze.
2. Das langfristige Zielmodell bleibt ein futures-only Multi-Instrument-Portfolio-System aus einem Top20-Futures-Universum.
3. Multi-Future-Runtime bleibt bis zu separater Governance-Ratifikation, Portfolio-Risk-Binding, Multi-Instrument-Reconciliation, Unknown-Outcome-Recovery und Zero-Order-/Shadow-/Paper-/Testnet-Evidence ausdrücklich nicht autorisiert.
4. Ein späterer Portfolio Allocator darf auswählen und budgetieren, aber weder Safety Kernel noch Reconciliation noch per-Instrument Double Play umgehen.

## 44.6 v4.4 Änderungsprotokoll

Gegenüber v4.3 wurden ausschließlich Governance-, Fortschritts- und Economic-Evidence-Aktualisierungen vorgenommen.

Nicht geändert wurden:

- Core-System,
- kanonische Handelslogik,
- Master V2,
- Double Play,
- Scope-, Entry-, Exit- oder Reversal-Semantik,
- Risk-/Sizing-Verträge,
- Safety Kernel,
- Reconciliation,
- Runtime-Authority-Semantik.

Ergänzt oder aktualisiert wurden:

1. realer Abschlussstand STEP29M, STEP30A, STEP29N, STEP29O und STEP29R,
2. terminale negative Evidence für fünf abgeschlossene Bindings,
3. Klarstellung, dass historische Economic Failures durch Operator-Policy nicht verändert werden,
4. Aufhebung des `NO_NEW_CANDIDATE_HOLD`,
5. Autorisierung eines bounded Multi-Candidate-Futures-Research-Fleet-Modells,
6. ausdrücklicher Schutz des Core-Systems vor Research-bedingten Mutationen,
7. Wiederholungsverbot unveränderter fehlgeschlagener Bindings,
8. Final-Convergence der neuen Fleet auf:
   - `trend_following`,
   - `bollinger_bands`,
   - `momentum_1h`,
9. Ausschluss von:
   - unveränderten Negativbindungen,
   - near-duplicate Breakout-Varianten,
   - redundanten Mean-Reversion-Slots,
   - R&D-Skeletons ohne vollständige Daten- und Evaluation-Capability,
10. neuer nächster kanonischer Schritt: versionierte Fleet-Bindings und separate Offline-Evaluationsratifikation,
11. Bestätigung, dass Economic-Validity-, Promotion-, Safety- und Runtime-Gates unverändert bleiben.

---

# 45. Kanonische Gesamtentscheidung

```text
V4_4_9_IS_CANONICAL_TARGET=true
RUNBOOK_CANONICAL_NORMS_ARE_STATE_INDEPENDENT=true
RUNBOOK_REWRITE_AFTER_MERGE_REQUIRED=false
CURSOR_MAY_NOT_REWRITE_RUNBOOK_FOR_PROGRESS_TRACKING=true
DESKTOP_RUNBOOK_SYNC_REQUIRED=false

LATEST_VERIFIED_EXTERNAL_EVIDENCE_OVERRIDES_EMBEDDED_PROGRESS_ONLY=true
LATEST_VERIFIED_EXTERNAL_EVIDENCE_MAY_NOT_OVERRIDE_CANONICAL_NORMS=true
RUNBOOK_MAY_NOT_BE_REJECTED_AS_STALE_WITHOUT_CONTRADICTORY_NEWER_EVIDENCE=true

POST_MERGE_MAIN_SYNC_REQUIRED=true
POST_MERGE_EVIDENCE_MANIFEST_VERIFY_REQUIRED=true
REFERENCED_SOURCE_EVIDENCE_MANIFEST_VERIFY_REQUIRED=true
SOURCE_EVIDENCE_ABSENCE_MUST_BE_EXPLICITLY_REPORTED=true

CORE_SYSTEM_MUTATION_ALLOWED=false
CANONICAL_TRADING_LOGIC_MUTATION_ALLOWED=false
MASTER_V2_MUTATION_ALLOWED=false
DOUBLE_PLAY_MUTATION_ALLOWED=false
RISK_SIZING_MUTATION_ALLOWED=false
SAFETY_RUNTIME_MUTATION_ALLOWED=false

FULL_CANONICAL_CHAIN_WIRED=true
BACKTEST_RUNTIME_DECISION_PARITY_PASS=true
ECONOMIC_VALIDITY_OFFLINE_GATE_PASS=false
RUNTIME_REWIRE_DEFERRED=true
RUNTIME_REWIRE_ADMISSIBLE=false
LIVE_AUTHORIZED=false

FALLBACK_CURRENT_STATE_HEAD=5a5ab570022cae47ec5442638ab0180f66caa1e4
LATEST_MERGED_PR=5078
RESEARCH_SCOPE=cross_sectional_ma_crossover_panel_rank_rotation/v0
DATASET_MATERIALIZED=true
DATASET_ID=pit_okx_linear_usdt_non_bitcoin_pt1h_panel
INSTRUMENT_COUNT=399
BITCOIN_PRESENT=false
DATASET_DIGEST=c753c5795ab40d26237a066702cb72a06065bfce0143440ec0ccadfe249cc0e0
ECONOMIC_EVALUATION_EXECUTED=false
RUNTIME_EFFECT=NONE
AUTHORITY_EFFECT=NONE

NEXT_STEP=VERSIONED_CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_BINDING_RATIFICATION
NEXT_STEP_REQUIRES_SEPARATE_OPERATOR_GO=true
```

Der kanonische Fortschrittspfad lautet ab dem dokumentierten Fallback-Checkpoint:

```text
Manifest-verifizierter PR #5078 Dataset-Materialization-Closeout
→ separate versionierte Binding-Ratifikation
→ unveränderliche Candidate-/Signal-/Dataset-/Universe-/Ranking-/Rotation-/Kosten-/Policy-Bindings
→ separate Offline-Economic-Evaluation-Ratifikation
→ Full-Canonical Panel Baseline
→ nur nach policy-konformer Baseline und nach festgelegtem Contract: Walk-Forward / Monte Carlo / Stress
→ Manifest-Verified EconomicViabilityEvidenceV1
→ PASS / FAIL / INCONCLUSIVE
→ nur bei vollständigem PASS: Promotion-Candidate
→ Runtime-Rewire weiterhin separat gegatet
```

Spätere Multi-Future-Runtime folgt unverändert einem zusätzlichen, separat zu ratifizierenden Pfad:

```text
Single-Future Runtime Proof
→ Portfolio Risk Binding
→ Multi-Instrument Reconciliation Evidence
→ Multi-Instrument Unknown Outcome Recovery Evidence
→ Portfolio Allocator Authority Boundary
→ Zero-Order Multi-Future Evidence
→ Shadow / Paper / Testnet Multi-Future Evidence
→ separate Operator Multi-Future Runtime Ratification
```

Neue Chats arbeiten nach diesem Runbook und dem jeweils jüngsten belegten Abschlussstand weiter. Das Runbook selbst bleibt unverändert, solange keine bewusst ratifizierte Änderung seiner kanonischen Normen beschlossen wird.

Keine Research-, Progress-, Bootstrap- oder Operator-Entscheidung darf negative Evidence überschreiben, Safety lockern oder Runtime Authority erzeugen.
