# Peak Trade — Canonical Chain Wiring Repair Master Runbook v2.2

## 0. Dokumentstatus

```text
DOCUMENT_TYPE=IMPLEMENTATION_CONTRACT_AND_HANDOFF_RUNBOOK
DOCUMENT_VERSION=2.2
STATUS=TECHNICAL_IMPLEMENTATION_COMPLETE
IMPLEMENTATION_COMPLETE=true
CLOSEOUT_COMPLETE=true
TECHNICAL_CANONICAL_CHAIN_WIRING_COMPLETE=true
FULL_CANONICAL_CHAIN_WIRED=true
BACKTEST_RUNTIME_DECISION_PARITY=true
FINAL_CLOSEOUT_COMPLETE=true
FINAL_CLOSEOUT_HEAD=a1890a3402f7686ba43309f00b0e5998245dafea
FINAL_IMPLEMENTATION_PR=5233
FINAL_IMPLEMENTATION_SQUASH_COMMIT=81222f4e4227a98f93d0456d28db28aa075d4f80
FINAL_DURABLE_STATIC_GUARD_PR=5235
FINAL_DURABLE_STATIC_GUARD_SQUASH_COMMIT=a1890a3402f7686ba43309f00b0e5998245dafea
DISCOVERY_COMPLETE=true
SEMANTIC_AUTHORITY_RESOLVED=true
BUILDER_OWNERSHIP_RESOLVED=true
SLICE_1_COMPLETE=true
SLICE_2_COMPLETE=true
SLICE_3_COMPLETE=true
SLICE_4_COMPLETE=true
SLICE_1_REOPENED=false
ARCHITECTURE_REMAINS_BINDING=true
SAFETY_BOUNDARIES_REMAIN_BINDING=true
ARCHITECTURE_AUTHORIZATION_DECISION=C
ARCHITECTURE_DECISION_D_NAME=
FAMILY_SCOPED_STRATEGY_AGREEMENT_INTO_EXISTING_SUITABILITY_V1
ARCHITECTURE_DECISION_D_RATIFIED=true
CANONICAL_RUNTIME_ENTRYPOINT_STATUS=BOUND_NOT_ACTIVATED
RUNTIME_EFFECT=NONE
AUTHORITY_EFFECT=NONE
ORDER_EFFECT=NONE
ECONOMIC_EFFECT=NONE
NEXT_ACTION=NONE_FOR_CANONICAL_CHAIN_WIRING_REPAIR
MISSION_STATUS=TECHNICALLY_COMPLETE
CANONICAL_CHAIN_WIRING_REPAIR_MISSION_STATUS=COMPLETE
FURTHER_CHAIN_WIRING_MUTATION_REQUIRED=false
FURTHER_MUTATION_REQUIRES_SEPARATE_NEW_SCOPE=true
NEW_SCOPE_REQUIRES_NEW_UNCERTAINTY_OR_SEPARATE_AUTHORIZATION=true
READ_ONLY_CHAINING_WITHOUT_NEW_UNCERTAINTY=false
READ_ONLY_CHAINING_REQUIRED=false
MISSION_COMPLETE=false
ECONOMIC_VALIDITY_PASS=false
ECONOMIC_VALIDITY_CLAIMED=false
PROMOTION_ELIGIBLE=false
PROMOTION_CLAIMED=false
RUNTIME_AUTHORIZED=false
LIVE_AUTHORIZED=false
ORDERS_ALLOWED=false
REPO=/Users/frnkhrz/Peak_Trade
```

Hinweis: `MISSION_COMPLETE=false` bleibt bewusst gesetzt — Economic Validity,
Promotion und Runtime-/Live-Authority sind **nicht** Teil dieses Closeouts.
`MISSION_STATUS=TECHNICALLY_COMPLETE` und
`STATUS=TECHNICAL_IMPLEMENTATION_COMPLETE` beziehen sich ausschließlich auf die
technische Canonical-Chain-Wiring-Reparatur und den Durable-Static-Guard-Closeout
durch PRs bis einschließlich #5235.

### 0.1 Historischer Discovery-/Slice-1-Startzustand (superseded als aktueller Repo-Ist)

Die folgenden Felder beschreiben den **historischen Discovery-Baseline** zum Slice-1-Start und sind **nicht** der aktuelle Post-Closeout-Repo-Ist. Inhalt bleibt als Audit-Trail erhalten und wird **nicht** mit `FINAL_CLOSEOUT_HEAD` überschrieben.

```text
HISTORICAL_DISCOVERY_BASELINE=true
DISCOVERY_BASELINE_HEAD=6e8c5889bbc20b762dc0f846776a8bbc70e4376f
DISCOVERY_BASELINE_ORIGIN_MAIN=6e8c5889bbc20b762dc0f846776a8bbc70e4376f
DISCOVERY_BASELINE_WORKTREE_CLEAN=true
STATUS_AT_DISCOVERY=IMPLEMENTATION_READY
```

### 0.2 HISTORICAL CANONICAL STATE (Post-Slice-1 / pre-final-closeout; superseded)

> **HISTORICAL / SUPERSEDED AS CURRENT REPO STATE.** Post-Slice-1-Baseline nach
> PR #5226. Der aktuelle Endzustand steht in §0 Dokumentstatus und in
> `CANONICAL_CHAIN_WIRING_REPAIR_FINAL_CLOSEOUT_V1`. Die SHA
> `6a37df8ab433b4d99a0a12d4c7c3c43d45774ea7` bleibt als historische
> Post-Slice-1-Baseline erhalten.

```text
CURRENT_CANONICAL_BASELINE_HEAD=
6a37df8ab433b4d99a0a12d4c7c3c43d45774ea7

SLICE_1_COMPLETE=true
PR5226_SQUASH_MERGED=true
CANONICAL_REPLAY_INPUT_BUILDER_SINGLE_OWNER=true
CANONICAL_REPLAY_INPUT_BUILDER_SYMBOL=build_integrated_offline_replay_input_v1
PRODUCTIVE_DIRECT_REPLAY_INPUT_CONSTRUCTOR_COUNT=1
MV2_THIN_ADAPTER=true
RUNTIME_BRIDGE_THIN_ADAPTER=true
PARITY_HARNESS_THIN_ADAPTER=true

CORE_SEMANTICS_CHANGED=false
RISK_SIZING_SEMANTICS_CHANGED=false
SAFETY_SEMANTICS_CHANGED=false
RUNTIME_EFFECT=NONE
AUTHORITY_EFFECT=NONE
ORDER_EFFECT=NONE

SLICE_2_IMPLEMENTATION_READY=true
SLICE_2_IMPLEMENTATION_BLOCKED=false
ARCHITECTURE_RATIFICATION_SELECTION=D
STRATEGY_SIGNAL_VALUE_CANONICAL_CONSUMER_STATUS=
FAMILY_SCOPED_STRATEGY_AGREEMENT_INTO_EXISTING_SUITABILITY_V1
PREVIOUS_SELECTION=D
PREVIOUS_IMPLEMENTATION_BLOCKED=true
ARCHITECTURE_AUTHORIZATION_DECISION=C
ARCHITECTURE_DECISION_D_NAME=
FAMILY_SCOPED_STRATEGY_AGREEMENT_INTO_EXISTING_SUITABILITY_V1
ARCHITECTURE_DECISION_D_RATIFIED=true
GO_TOKEN=GO_DECISION_D_STRATEGY_SIGNAL_CANONICAL_CONSUMER_BINDING_V1
AUTHORIZED_CANONICAL_CONSUMER_STAGE=evaluate_suitability_binding_v1
AUTHORIZED_CONSUMER_OWNER_FILE=
src/trading/master_v2/suitability_binding_v1.py
AUTHORIZED_CONSUMER_OWNER_SYMBOL=evaluate_suitability_binding_v1
EXACT_CONSUMER_PATH=
StrategySignalBindingResultV1
→ normalize_strategy_signal_to_suitability_agreement_material_v1
→ build_integrated_offline_replay_input_v1
→ run_integrated_offline_trading_logic_replay_v1
→ _suitability_input_for_assessment
→ evaluate_suitability_binding_v1
STRATEGY_VALUE_SEMANTICS_RESOLVED=true
CMC_CONSISTENCY_BINDING_RESOLVED=true
FAIL_CLOSED_RULES_RESOLVED=true
REAL_CANONICAL_EFFECT_PROVEN=true
RAW_SIGNAL_DIRECT_AUTHORITY=false
PROVENANCE_ONLY_BINDING=false
NEW_PARALLEL_DECISION_STAGE=false
NEW_TOTAL_DECISION_OWNER=false
SLICE_2_IMPLEMENTATION_AUTHORIZED=true
NEXT_AUTOMATIC_IMPLEMENTATION_SCOPE=
FAMILY_SCOPED_STRATEGY_AGREEMENT_INTO_EXISTING_SUITABILITY_V1
SEPARATE_FUTURE_ARCHITECTURE_AUTHORIZATION_REQUIRED=false
SEPARATE_ARCHITECTURE_AUTHORIZATION_EXECUTED=true
CORE_CODE_EFFECT=SUITABILITY_AGREEMENT_BINDING_ONLY
READ_ONLY_CHAINING_REQUIRED=false
MISSION_COMPLETE=false
ECONOMIC_VALIDITY_CLAIMED=false
PROMOTION_CLAIMED=false
```

### 0.3 PR #5229 — Architecture Authorization Decision C Closeout (ratified)

```text
PR_NUMBER=5229
PR_HEAD_SHA=bc441e0020ba221936e903658f3c564536042a62
PR_SQUASH_COMMIT=cab3fa2c231492714ab8c446390f22d35ae6ce54
MERGED_AT=2026-07-15T20:55:07Z
RATIFICATION_STATUS=COMPLETE
ARCHITECTURE_AUTHORIZATION_DECISION=C
AUTHORIZED_CANONICAL_CONSUMER_STAGE=none
AUTHORIZED_CONSUMER_OWNER_FILE=none
AUTHORIZED_CONSUMER_OWNER_SYMBOL=none
SLICE_1_REOPENED=false
SLICE_2_STATUS=BLOCKED_BY_ARCHITECTURE_DECISION_C
SLICE_2_IMPLEMENTATION_AUTHORIZED=false
NEXT_AUTOMATIC_SCOPE=NONE
NEXT_AUTOMATIC_IMPLEMENTATION_SCOPE=NONE
READ_ONLY_CHAINING_REQUIRED=false
CORE_CODE_EFFECT=NONE
RUNTIME_EFFECT=NONE
AUTHORITY_EFFECT=NONE
ORDER_EFFECT=NONE
```

**Historische Fortsetzungsregel nach PR #5229 (Decision C Ist-Befund):**

- PR #5229 hat Architekturentscheidung **C** ratifiziert (`NO_SAFE_ARCHITECTURE_AUTHORIZABLE`) als negativen historischen Ist-Befund.
- Decision C wird **nicht** überschrieben und bleibt als Audit-Baseline erhalten.
- Slice 1 bleibt abgeschlossen und darf nicht erneut geöffnet werden (`SLICE_1_REOPENED=false`).
- Keine Provenance-only-Verdrahtung.
- Keine Direct-Signal-Authority.
- Keine neue parallele Decision Stage.
- Kein neuer Total Decision Owner.

**Decision-D-Ratifikation (bindend unter GO_TOKEN):**

```text
GO_TOKEN=GO_DECISION_D_STRATEGY_SIGNAL_CANONICAL_CONSUMER_BINDING_V1
ARCHITECTURE_DECISION_D_NAME=
FAMILY_SCOPED_STRATEGY_AGREEMENT_INTO_EXISTING_SUITABILITY_V1
ARCHITECTURE_DECISION_D_RATIFIED=true
SLICE_2_IMPLEMENTATION_AUTHORIZED=true
SLICE_2_IMPLEMENTATION_BLOCKED=false
SELECTED_EXISTING_CANONICAL_STAGE=evaluate_suitability_binding_v1
EXACT_CONSUMER_PATH=
StrategySignalBindingResultV1
→ normalize_strategy_signal_to_suitability_agreement_material_v1
→ build_integrated_offline_replay_input_v1
→ run_integrated_offline_trading_logic_replay_v1
→ _suitability_input_for_assessment
→ evaluate_suitability_binding_v1
```

Kanonisches Architecture-Ratification-Closeout (Selection D, negativ historisch):
[`docs/governance/STRATEGY_SIGNAL_CANONICAL_ARCHITECTURE_RATIFICATION_CLOSEOUT_V1.md`](STRATEGY_SIGNAL_CANONICAL_ARCHITECTURE_RATIFICATION_CLOSEOUT_V1.md).

Separate Architecture Authorization (GO v1, Decision **C** — historical negative Ist; squash-merged as PR #5229):
[`docs/governance/STRATEGY_SIGNAL_CANONICAL_CONSUMER_ARCHITECTURE_AUTHORIZATION_V1.md`](STRATEGY_SIGNAL_CANONICAL_CONSUMER_ARCHITECTURE_AUTHORIZATION_V1.md).

Positive Architecture Decision **D** (family-scoped suitability agreement; Slice-2 authorized under GO_TOKEN):
[`docs/governance/STRATEGY_SIGNAL_CANONICAL_CONSUMER_ARCHITECTURE_DECISION_D_V1.md`](STRATEGY_SIGNAL_CANONICAL_CONSUMER_ARCHITECTURE_DECISION_D_V1.md).

### 0.4 CANONICAL_CHAIN_WIRING_REPAIR_FINAL_CLOSEOUT_V1

> **HISTORICAL IMPLEMENTATION CLOSEOUT (PR #5233) — superseded as absolute final
> repo head by PRs through #5235.** Technical Canonical Chain Wiring Repair
> implementation landed via squash-merge of PR #5233. Durable static-guard
> closeout and current technical baseline are recorded in
> `# Final Technical Closeout — PRs through #5235`. No Economic Evaluation, no
> runtime activation, no orders, no authority expansion.
>
> ```text
> HISTORICAL_EXECUTED_SCOPE=true
> NO_LONGER_CURRENT_NEXT_ACTION=true
> HISTORICAL_IMPLEMENTATION_PR=5233
> SUPERSEDED_AS_ABSOLUTE_FINAL_HEAD_BY_PR=5235
> ```

```text
PR_NUMBER=5233
PR_STATE=MERGED
MERGE_METHOD=SQUASH
PR_HEAD_SHA=9685f88a86f90fb4e571b58ab73b2f8bada7e470
PR_BASE_OID=b6d1988739b529b01e8ed226fbb890a300783c0b
PR_SQUASH_COMMIT=81222f4e4227a98f93d0456d28db28aa075d4f80
POST_MERGE_FOCUSED_TESTS=37 passed

FINAL_DIFF_SHA256=fc83d89b5e59ab28baa737ce16f332f8394f6ab7beb71a0e3ab057435f9d1376

FINAL_IMPLEMENTATION_FILES=
* config/governance/technical_canonical_wiring_authorization_v1.json
* src/ops/double_play/specialists.py
* src/trading/master_v2/evaluate_double_play_authority_boundary_v0.py
* src/trading/master_v2/offline_double_play_scenario_replay_v0.py
* tests/governance/test_technical_canonical_wiring_authorization_bound_to_boundary_guard_v1.py
* tests/trading/master_v2/test_runtime_backtest_parity_and_legacy_boundary_closeout_v1.py

CANONICAL_REPLAY_INPUT_BUILDER_SINGLE_OWNER=true
PRODUCTIVE_DIRECT_REPLAY_INPUT_CONSTRUCTOR_COUNT=1
CANONICAL_TOTAL_DECISION_OWNER_UNCHANGED=true
DECISION_D_BINDING_UNCHANGED=true
MASTER_V2_IMPORTS_BACKTEST_TYPES=false

BACKTEST_CANONICAL_BUILDER_BOUND=true
RUNTIME_BRIDGE_CANONICAL_BUILDER_BOUND=true
BACKTEST_CANONICAL_ORCHESTRATOR_BOUND=true
RUNTIME_BRIDGE_CANONICAL_ORCHESTRATOR_BOUND=true
RUNTIME_BRIDGE_DUPLICATES_DECISION_LOGIC=false

BACKTEST_RUNTIME_DECISION_EVIDENCE_MATCH=true
BACKTEST_RUNTIME_SEMANTIC_DIGEST_MATCH=true

OFFLINE_SCENARIO_REPLAY_NON_AUTHORITATIVE=true
OPS_DOUBLE_PLAY_NON_AUTHORITATIVE=true
LEGACY_SYSTEM_ECONOMIC_EVIDENCE_BLOCKED=true
LEGACY_RUNTIME_GUARD_UNCHANGED=true

DIRECT_STRATEGY_TO_POSITION_PATH_COUNT=0
SYSTEM_RELEVANT_DIRECT_STRATEGY_TO_TRADE_PATH_COUNT=0
CLASSIC_ENGINE_DECISION_AUTHORITY_BYPASS_COUNT=0

CORE_DECISION_SEMANTICS_CHANGED=false
RISK_SIZING_SEMANTICS_CHANGED=false
FILL_SEMANTICS_CHANGED=false
PORTFOLIO_SEMANTICS_CHANGED=false
SAFETY_SEMANTICS_CHANGED=false

CANONICAL_RUNTIME_ENTRYPOINT_STATUS=BOUND_NOT_ACTIVATED
RUNTIME_EFFECT=NONE
AUTHORITY_EFFECT=NONE
ORDER_EFFECT=NONE

TECHNICAL_WIRING_AUTHORIZATION_VALID_JSON=true
TECHNICAL_WIRING_AUTHORIZATION_SCOPE_BOUNDED=true
ECONOMIC_BOUNDARY_GUARD_PASS=true
LINT_GATE_PASS=true
LINT_GATE_ALWAYS_RUN_SUCCESS=true

TECHNICAL_CANONICAL_CHAIN_WIRING_COMPLETE=true
FULL_CANONICAL_CHAIN_WIRED=true
BACKTEST_RUNTIME_DECISION_PARITY=true
STRATEGY_LAYER_FEEDS_CANONICAL_CORE=true
FINAL_CLOSEOUT_COMPLETE=true
FINAL_CLOSEOUT_HEAD=81222f4e4227a98f93d0456d28db28aa075d4f80
FINAL_IMPLEMENTATION_PR=5233
FINAL_IMPLEMENTATION_SQUASH_COMMIT=81222f4e4227a98f93d0456d28db28aa075d4f80

NEXT_ACTION=NONE_FOR_CANONICAL_CHAIN_WIRING_REPAIR
MISSION_STATUS=TECHNICALLY_COMPLETE
FURTHER_MUTATION_REQUIRES_SEPARATE_NEW_SCOPE=true
NEW_READ_ONLY_CHAIN_CREATED=false
```

# Final Technical Closeout — PRs through #5235

> **BINDING CURRENT TECHNICAL CLOSEOUT.** Append-only final technical closeout
> after squash-merge of durable static-guard PR #5235 on top of implementation
> PR #5233. Documentation-only recognition of already-merged repo truth.
> Not an Economic Evaluation, promotion, runtime, order, or live authorization.

```text
STATUS=TECHNICAL_IMPLEMENTATION_COMPLETE
IMPLEMENTATION_COMPLETE=true
CLOSEOUT_COMPLETE=true

FINAL_BASELINE_HEAD=
a1890a3402f7686ba43309f00b0e5998245dafea

FINAL_MERGED_PR=5235
FINAL_MERGED_PR_HEAD=
ff4569b62eb9b4192c893e3d218665ab7910469f
FINAL_SQUASH_COMMIT=
a1890a3402f7686ba43309f00b0e5998245dafea

PR5235_FINAL_DIFF_SHA256=
a1002cd41cf4cb26736a0e4d806cf08a0321df4bd27c227182e49f0768467a30

PR5235_FILES=
tests/trading/master_v2/test_canonical_replay_input_builder_ssot_contract_v1.py
tests/trading/master_v2/test_runtime_backtest_parity_and_legacy_boundary_closeout_v1.py
tests/trading/master_v2/test_strategy_suitability_agreement_static_contract_v1.py

SRC_FILES_CHANGED_BY_PR5235=false
DURABLE_STATIC_GUARDS_PRESENT=true

TECHNICAL_CANONICAL_CHAIN_WIRING_COMPLETE=true
FULL_CANONICAL_CHAIN_WIRED=true
BACKTEST_RUNTIME_DECISION_PARITY=true

CANONICAL_REPLAY_INPUT_BUILDER_SINGLE_OWNER=true
PRODUCTIVE_DIRECT_REPLAY_INPUT_CONSTRUCTOR_COUNT=1

CANONICAL_ORCHESTRATOR_SINGLE_DECISION_OWNER=true
CANONICAL_TOTAL_DECISION_OWNER_COUNT=1

STRATEGY_LAYER_FEEDS_CANONICAL_CORE=true
STRATEGY_SIGNAL_IS_EFFECTIVE_CANONICAL_INPUT=true
STRATEGY_SIGNAL_PROVENANCE_BOUND=true
STRATEGY_SIGNAL_DIGEST_BOUND=true
STRATEGY_USES_CANONICAL_MARKET_CONTEXT=true
STRATEGY_SIGNAL_HAS_REAL_CANONICAL_CONSUMER=true
STRATEGY_SIGNAL_IS_PROVENANCE_ONLY=false

DIRECT_STRATEGY_TO_POSITION_PATH_COUNT=0
DIRECT_STRATEGY_TO_ORDER_INTENT_PATH_COUNT=0
SYSTEM_RELEVANT_DIRECT_STRATEGY_TO_TRADE_PATH_COUNT=0
CLASSIC_ENGINE_BYPASS_COUNT=0

BACKTEST_ENGINE_DECISION_AUTHORITY=false
RUNTIME_BRIDGE_DECISION_AUTHORITY=false
CLASSIC_ENGINE_CANONICAL_ORCHESTRATOR_BOUND=true
RUNTIME_BRIDGE_CANONICAL_ORCHESTRATOR_BOUND=true

CORE_SEMANTICS_CHANGED=false
RISK_SIZING_SEMANTICS_CHANGED=false
SAFETY_SEMANTICS_CHANGED=false

RUNTIME_EFFECT=NONE
AUTHORITY_EFFECT=NONE
ORDER_EFFECT=NONE
ECONOMIC_EFFECT=NONE

ECONOMIC_VALIDITY_PASS=false
PROMOTION_ELIGIBLE=false
RUNTIME_AUTHORIZED=false
LIVE_AUTHORIZED=false
ORDERS_ALLOWED=false

CANONICAL_CHAIN_WIRING_REPAIR_MISSION_STATUS=COMPLETE
FURTHER_CHAIN_WIRING_MUTATION_REQUIRED=false
NEW_SCOPE_REQUIRES_NEW_UNCERTAINTY_OR_SEPARATE_AUTHORIZATION=true
READ_ONLY_CHAINING_WITHOUT_NEW_UNCERTAINTY=false
```

Der technische Wiring-Abschluss (PRs durch #5235) ist **keine** Economic-
oder Promotion-Freigabe und **keine** Runtime-/Live-/Order-Freigabe.

**Zweck:** Dieses Runbook ist der vollständige technische Implementierungsvertrag (jetzt final closed) für die Reparatur der bestätigten Chain-Wiring-Defekte zwischen Strategy Layer, kanonischem Master-V2-Core, Backtest, Offline Replay und Runtime-Parity-Bridge.

Es ist so aufgebaut, dass es:

1. direkt an Cursor übergeben werden kann,
2. in einem neuen Chat als vollständiger Projektkontext dient,
3. Discovery-Ergebnisse, Architekturwahrheiten, Grenzen, Umsetzungsslices, Tests und Closeout-Felder in einem Dokument bündelt,
4. keine erfundenen Repo-Symbole als bestehende Implementierung ausgibt,
5. die Strategy-Schicht verbindlich in den Core einspeist,
6. den Core als einzige fachliche Gesamtwahrheit erhält,
7. keine Runtime-, Order- oder Live-Authority aktiviert.

**Bindend weiterhin:** Operator-Absicht (§1), Safety-Grenzen (§2), kanonische Architektur (§4), Single-Truth-Regel, Strategy-Signal-Authoritätsgrenzen, die PR-#5229-Decision-C-Historie (§0.3), die Decision-D-Ratifikation unter `GO_DECISION_D_STRATEGY_SIGNAL_CANONICAL_CONSUMER_BINDING_V1` mit Consumer-Pfad `evaluate_suitability_binding_v1`, und der finale technische Closeout `# Final Technical Closeout — PRs through #5235`. **Historisch / superseded als aktueller Ist:** Discovery-Baseline-HEAD `6e8c5889…`, Post-Slice-1-Baseline `6a37df8a…` (§0.2), Implementation-Closeout PR #5233 (§0.4), Multiple-Builder-Discovery-Befund, §8.1 Builder-Defekt als aktueller Defekt, §8.3 Builder nur als Implementierungsziel, offene Slice-2-/Slice-3-/Slice-4-Aufträge, früherer „Nächster Cursor-Auftrag“-Text, sowie der frühere automatische Read-Only-Consumer-Design-Gate vor Slice 2.

---

# 1. Operator-Absicht — unverhandelbar

```text
STRATEGY_LAYER_MUST_FEED_CANONICAL_CORE=true
STRATEGY_LAYER_MAY_NOT_BYPASS_CANONICAL_CORE=true
CANONICAL_CORE_IS_SINGLE_TRADING_TRUTH=true
BACKTEST_MAY_NOT_OWN_TRADING_DECISIONS=true
RUNTIME_BRIDGE_MAY_NOT_DUPLICATE_TRADING_LOGIC=true
CLASSIC_ENGINE_MAY_ONLY_SIMULATE_CANONICAL_DECISIONS=true
```

Die Strategy-Schicht darf nicht entfernt, ignoriert oder lediglich als irrelevante Provenance nebenher berechnet werden.

Sie muss fachlich wirksam in die kanonische Decision Chain eingehen.

Gleichzeitig gilt:

```text
STRATEGY_SIGNAL_IS_INPUT_MATERIAL=true
STRATEGY_SIGNAL_IS_COMPLETE_DECISION=false
STRATEGY_SIGNAL_HAS_POSITION_AUTHORITY=false
STRATEGY_SIGNAL_HAS_EXIT_AUTHORITY=false
STRATEGY_SIGNAL_HAS_REVERSAL_AUTHORITY=false
STRATEGY_SIGNAL_HAS_SIZING_AUTHORITY=false
STRATEGY_SIGNAL_HAS_ORDER_AUTHORITY=false
```

Die Strategy liefert eine gebundene, versionierte und digestierte fachliche Aussage. Der Master-V2-Core entscheidet unter Einbeziehung von Marktvertrauen, Scope, Directional Assessment, Survival, Suitability, Double Play, Entry/Exit/Reversal, Capital/Risk/Sizing sowie Safety-/KillSwitch-/Reconciliation-Grenzen.

---

# 2. Scope und harte Sicherheitsgrenzen

## 2.1 Autorisierter Scope

```text
AUTHORIZED:
- read-only repo inspection
- bounded offline implementation
- focused unit and contract tests
- static call-path verification
- offline parity verification
- manifest generation and verification
- feature branch, commit, push and PR only after explicit implementation GO
```

## 2.2 Nicht autorisiert

```text
LIVE_AUTHORIZED=false
ORDERS_ALLOWED=false
SHADOW_ALLOWED=false
PAPER_ALLOWED=false
TESTNET_ALLOWED=false
SCHEDULER_ALLOWED=false
ARMING_ALLOWED=false
CANARY_ALLOWED=false
CREDENTIALS_ALLOWED=false
RUNTIME_ACTIVATION_ALLOWED=false
ECONOMIC_EVALUATION_ALLOWED=false
PARAMETER_OPTIMIZATION_ALLOWED=false
THRESHOLD_RELAXATION_ALLOWED=false
```

`CANONICAL_RUNTIME_ENTRYPOINT_STATUS="BOUND_NOT_ACTIVATED"` bleibt unverändert.

Das Schließen der Offline-Wiring- und Parity-Lücken ist **keine** Runtime-Aktivierung.

---

# 3. Repo-Wahrheiten aus abgeschlossener Discovery

## 3.1 Nicht im Repo vorhandene Platzhalter

Folgende Namen aus dem ursprünglichen Architekturentwurf existieren nicht als Repo-Symbole und dürfen nicht als vorhandene Implementierung behandelt werden:

```text
StrategySignalV1=DOES_NOT_EXIST
CanonicalDecisionRequestV1=DOES_NOT_EXIST
CanonicalDecisionOrchestratorV1=DOES_NOT_EXIST_AS_CLASS
```

Repo-äquivalente reale Contracts:

```text
STRATEGY_SIGNAL_RESULT=
src/backtest/strategy_signal_binding_v1.py:
StrategySignalBindingResultV1

STRATEGY_SIGNAL_PROVENANCE=
src/backtest/strategy_signal_binding_v1.py:
StrategySignalProvenanceV1

FIRST_COMPLETE_CANONICAL_DECISION_INPUT=
src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py:
IntegratedOfflineReplayInputV1

CANONICAL_TOTAL_DECISION_OWNER=
src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py:
run_integrated_offline_trading_logic_replay_v1

CANONICAL_DECISION_EVIDENCE=
src/trading/master_v2/canonical_trading_decision_evidence_v1.py:
CanonicalTradingDecisionEvidenceV1
```

## 3.2 Bestätigter Ausgangszustand

> **HISTORICAL / SUPERSEDED AS CURRENT REPO STATE.** Discovery-Baseline zum Slice-1-Start
> (`DISCOVERY_BASELINE_HEAD=6e8c5889bbc20b762dc0f846776a8bbc70e4376f`).
> Post-Slice-1-Ist siehe §0.2 (`CURRENT_CANONICAL_BASELINE_HEAD=6a37df8a…`,
> `PRODUCTIVE_DIRECT_REPLAY_INPUT_CONSTRUCTOR_COUNT=1`). Architektur- und Safety-Grenzen bleiben bindend.

```text
HISTORICAL_DISCOVERY_BASELINE=true
CORE_COMPONENTS_PRESENT=true
CORE_COMPONENTS_INDIVIDUALLY_WIRED_MOSTLY=true

FULL_CANONICAL_CHAIN_WIRED=false
BACKTEST_RUNTIME_DECISION_PARITY_OBSERVED=false
STRATEGY_LAYER_FEEDS_CANONICAL_CORE_OBSERVED=false

SEMANTIC_SINGLE_DECISION_OWNER_RESOLVED=true
FIRST_CANONICAL_DECISION_INPUT_RESOLVED=true
STRATEGY_SIGNAL_IS_COMPLETE_DECISION_INPUT=false
EXISTING_STRATEGY_TO_REPLAY_INPUT_ADAPTER_FOUND=false

MULTIPLE_REPLAY_INPUT_BUILDERS_FOUND=true
CANONICAL_REPLAY_INPUT_BUILDER_EXISTS_TODAY=false
DESIGNATED_CANONICAL_REPLAY_INPUT_BUILDER_OWNER=
src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py

TOTAL_CONFIRMED_BYPASS_PATHS=9
BYPASS_TECHNICAL_ONLY=2
BYPASS_DECISION_AUTHORITY=7
```

---

# 4. Kanonische Architektur — Zielbild

## 4.1 Vollständiger Daten- und Entscheidungsfluss

```text
Strategy Registry / Strategy Identity
→ Strategy Signal Execution
→ StrategySignalBindingResultV1
→ MV2 Strategy-to-Replay-Input Adapter
→ Single Canonical Replay Input Builder
→ IntegratedOfflineReplayInputV1
→ run_integrated_offline_trading_logic_replay_v1
   → CanonicalMarketContextV1 validation/binding
   → Canonical Scope Initialization
   → Deterministic Scope Event Generation
   → Bull/Bear Directional Assessment
   → Bull/Bear State Transition
   → Survival Assessment
   → Suitability Binding
   → Double Play Composition
   → Entry / Position / Exit / Reversal Policy
   → Canonical Trading Decision Evidence
   → Capital / Risk / Sizing boundary
   → Canonical Order Intent boundary
   → Safety / KillSwitch / Reconciliation boundary
→ canonical decision-to-position mapping
→ BacktestEngine as execution/fill simulator only
→ BacktestResult / parity evidence
```

## 4.2 Single-Truth-Regel

```text
CANONICAL_TRADING_LOGIC_SINGLE_SSOT=true
CANONICAL_TOTAL_DECISION_OWNER=
run_integrated_offline_trading_logic_replay_v1

STRATEGY_DECISION_OWNER=false
CLASSIC_ENGINE_DECISION_OWNER=false
RUNTIME_BRIDGE_DECISION_OWNER=false
PARITY_HARNESS_DECISION_OWNER=false
OPS_DOUBLE_PLAY_DECISION_OWNER=false
```

Teilkomponenten besitzen fachliche Teilsemantik, aber keine Gesamt-Authority:

```text
Directional Assessment=PARTIAL_DECISION_COMPONENT
State Switch=PARTIAL_DECISION_COMPONENT
Survival=PARTIAL_DECISION_COMPONENT
Suitability=PARTIAL_DECISION_COMPONENT
Composition=PARTIAL_DECISION_COMPONENT
EntryExitReversal=PARTIAL_DECISION_COMPONENT
CapitalRiskSizing=PARTIAL_DECISION_COMPONENT
KillSwitch=SAFETY_VETO_COMPONENT
```

Nur der integrierte Orchestrator komponiert die vollständige fachliche Entscheidung.

---

# 5. Reale Owner- und Contract-Matrix

| Stufe | Reeller Owner | Reeller Input | Reeller Output | Kanonisch | Darf umgangen werden |
|---|---|---|---|---|---|
| Strategy Identity | `src/strategies/registry.py` | Strategy-ID/Config | Registry Snapshot/Spec | Ja | Nein |
| Strategy Signal | `src/backtest/strategy_signal_binding_v1.py` | Bars, Config, Registry | `StrategySignalBindingResultV1` | Als Input-Contract ja | Nicht für systemrelevante Evaluation |
| Market Context | `src/trading/master_v2/canonical_market_context_v1.py` | Bar/Futures-Marktmaterial | `CanonicalMarketContextV1` | Ja | Nein |
| Scope Init | `canonical_scope_initialization_v1.py` | CMC + Policy + Prereqs | `CanonicalScopeSnapshotV1` | Ja | Nein |
| Scope Event | `deterministic_scope_event_generator_v1.py` | Scope + CMC | `ScopeEventEvidenceV1` | Ja | Nein |
| Directional | `directional_assessment_v1.py` | `DirectionalAssessmentInputV1` | `DirectionalAssessmentV1` | Ja | Nein |
| State Switch | `double_play_state.py:transition_state` | Side State + Event | Next State/Transition | Ja | Nein |
| Survival | `survival_assessment_v1.py` | DA + Costs/Metrics | `SurvivalResultV1` | Ja | Nein |
| Suitability | `suitability_binding_v1.py` | DA + Survival + Regime + Registry | `SuitabilityResultV1` | Ja | Nein |
| Composition | `double_play_composition_matrix_v1.py` | Bull/Bear Results + Position Context | `DoublePlayCompositionResultV1` | Ja | Nein |
| Entry/Exit/Reversal | `double_play_entry_exit_policy_v0.py` | Composition + Gates + Safety/Recon | `EntryExitPolicyDecisionV0` | Ja | Nein |
| Capital/Risk/Sizing | `src/governance/capital_risk_sizing_v1.py` | Evidence + Capital Context | `CapitalRiskSizingDecisionV1` | Ja | Nein |
| Decision Evidence | `canonical_trading_decision_evidence_v1.py` | Stage References/Outcome | `CanonicalTradingDecisionEvidenceV1` | Ja | Nein |
| Gesamtentscheidung | `integrated_offline_trading_logic_replay_v1.py` | `IntegratedOfflineReplayInputV1` | `IntegratedOfflineReplayResultV1` | Ja | Nein |
| Fill Simulation | `src/backtest/engine.py` | Canonical Position Series/Decision Projection | `BacktestResult` | Nur Ausführungsschicht | Darf keine Entscheidung ersetzen |
| Runtime Parity Bridge | `canonical_core_runtime_integration_bridge_v0.py` | Harness/normalized input | Canonical Core Result | Delegation | Darf keine Logik duplizieren |

---

# 6. Wesentliche semantische Wahrheit: Strategy-Signal allein reicht nicht

`StrategySignalBindingResultV1` enthält im Kern:

```text
- Signalserie mit Werten aus {-1, 0, 1}
- Strategy Identity
- Strategy Version
- Provenance
- Strategy Signal Digest
```

Es enthält nicht die vollständigen Informationen für eine kanonische Entscheidung.

Fehlende kanonische Informationen umfassen insbesondere:

```text
- Canonical Market Context trust state
- data_integrity_status
- clock_trust_status
- bar_finality_status
- trusted_data
- mark/reference prices under canonical contract
- feature contract and context identity
- scope snapshot
- deterministic scope event
- prior side state
- position context
- bull/bear dual assessments
- survival inputs/results
- suitability registry and regime state
- composition state
- safety state
- reconciliation state
- policy bindings
- implementation/config/input digests
- component version bindings
```

Daraus folgt:

```text
STRATEGY_SIGNAL_DIRECT_TO_DIRECTIONAL_ASSESSMENT=INVALID
STRATEGY_SIGNAL_DIRECT_TO_POSITION=INVALID
STRATEGY_SIGNAL_DIRECT_TO_TRADE=INVALID
STRATEGY_SIGNAL_DIRECT_TO_ORDER_INTENT=INVALID
```

Die korrekte Lösung ist nicht, Strategy-Signale zu ignorieren. Die korrekte Lösung ist, sie zusammen mit CMC, State, Registry, Policies und Digests in die vollständige kanonische Input Unit einzubinden.

---

# 7. Erste vollständige kanonische Decision Unit

```text
FIRST_CANONICAL_DECISION_INPUT=IntegratedOfflineReplayInputV1
OWNER=
src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py
```

`CanonicalMarketContextV1` ist notwendig, aber nicht vollständig.

`StrategySignalBindingResultV1` ist fachlich relevant, aber nicht vollständig.

`IntegratedOfflineReplayInputV1` ist der erste Contract, der die vollständige orchestrierbare Decision-Unit darstellt.

Daher lautet die verbindliche Adapter-Kette:

```text
StrategySignalBindingResultV1
+
CanonicalMarketContextV1
+
Sequence / Prior State
+
Strategy Registry Snapshot
+
Policy Bindings
+
Position / Safety / Reconciliation Inputs
+
Version and Digest Bindings
→ Single Canonical Replay Input Builder
→ IntegratedOfflineReplayInputV1
```

---

# 8. Single Canonical Replay Input Builder

## 8.1 Historischer Defekt (Discovery-/Slice-1-Start; superseded)

> **HISTORICAL / SUPERSEDED AS CURRENT DEFECT.** Beschreibt den Discovery-/Slice-1-Startzustand.
> Nach PR #5226 / final PR #5233 gilt:
> `CANONICAL_REPLAY_INPUT_BUILDER_SINGLE_OWNER=true`,
> `PRODUCTIVE_DIRECT_REPLAY_INPUT_CONSTRUCTOR_COUNT=1`, Thin Adapters für MV2 / Runtime Bridge / Parity Harness.
> Der technische Inhalt bleibt als Audit-Trail erhalten und ist **nicht** der aktuelle Ist.

Zum Discovery-Zeitpunkt existierten mindestens drei produktive Konstruktionsstellen für `IntegratedOfflineReplayInputV1`:

| Historische Stelle | Damaliger Status |
|---|---|
| `src&#47;backtest&#47;mv2_research_wiring_v1.py#_build_replay_input` | MV2-spezifischer privater Builder |
| `canonical_core_runtime_integration_bridge_v0.py:build_integrated_offline_replay_input_from_harness_v0` | Bridge-spezifischer Builder |
| `integrated_vs_scenario_replay_full_system_parity_harness_v0.py` inline | Fixture-/Parity-spezifische Konstruktion |

Zusätzlich:

```text
mv2_research_wiring_v1.py:
_coerce_replay_input_enums_for_integrated_replay_v1
```

ist eine Enum-Rekonstruktion/Coercion und keine eigenständige fachliche Builder-Authority, muss aber nach der Konsolidierung geprüft und möglichst in die kanonische Normalisierung einbezogen werden.

## 8.2 Warum mehrere Builder unzulässig sind

Die bestehenden Builder unterscheiden sich unter anderem bei:

```text
- price_path construction
- up/adverse/reversal distances
- sequence and state material
- strategy registry material
- context_reference
- digests
- component version mappings
- source-specific defaults
```

Diese Unterschiede erzeugen Drift vor dem Single Decision Owner.

Daher:

```text
SINGLE_CANONICAL_REPLAY_INPUT_BUILDER_REQUIRED=true
SECOND_CANONICAL_BUILDER_ALLOWED=false
DIRECT_DATACLASS_CONSTRUCTION_IN_PRODUCTIVE_ADAPTERS_ALLOWED=false
```

## 8.3 Designierter Owner

> **HISTORICAL AS IMPLEMENTATION TARGET — NOW REALIZED.** Unter Discovery war
> `build_integrated_offline_replay_input_v1` ein Implementierungsziel.
> Post-Slice-1 (PR #5226) existiert das Symbol als kanonischer Single Owner (§0.2).

Der öffentliche Builder muss im Schema-/Orchestrator-Modul liegen:

```text
FILE=
src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py

DESIGNATED_SYMBOL=
build_integrated_offline_replay_input_v1
```

Der Symbolname war unter Discovery ein **Implementierungsziel**, kein bereits existierender Repo-Symbolbeleg (historisch). Nach Slice 1 ist er der kanonische öffentliche Builder-Owner.

Vor Mutation ist zu prüfen, dass der Name nicht kollidiert. Bei Kollision ist ein semantisch gleichwertiger eindeutiger Name zu wählen und im Manifest festzuhalten.



## 8.3a Reuse-First-Präzisierung

```text
EXISTING_PUBLIC_CANONICAL_BUILDER_REUSE_REQUIRED=true
NEW_PUBLIC_BUILDER_ONLY_IF_NO_SEMANTICALLY_EQUIVALENT_OWNER_EXISTS=true
```

Vor Einführung eines neuen öffentlichen Builders ist nachzuweisen, dass kein bestehender semantisch gleichwertiger öffentlicher Entry-Point existiert. Die Wiederverwendung eines bestehenden Owners hat Vorrang.

## 8.4 Verantwortlichkeit des Builders

Der Builder darf:

```text
- vollständig normalisierte Source-Felder entgegennehmen
- Pflichtfelder validieren
- Enums normalisieren
- Identitäten und Versionen binden
- Digests binden oder deterministisch ableiten, soweit bestehende Contracts dies verlangen
- IntegratedOfflineReplayInputV1 exakt einmal konstruieren
- fehlende oder inkonsistente Felder fail-closed ablehnen
```

Der Builder darf nicht:

```text
- Strategy-Logik ausführen
- Strategy-Parameter interpretieren
- Directional Assessment vorwegnehmen
- Survival/Suitability/Composition berechnen
- Entry/Exit/Reversal entscheiden
- Risk/Sizing ändern
- Safety-/KillSwitch-/Recon-Semantik ändern
- Runtime-Authority erzeugen
- source-spezifische willkürliche Defaults verstecken
```

Source-spezifische Defaults müssen entweder:

1. explizit als Input geliefert werden, oder
2. aus einem bestehenden kanonischen Policy-/Config-Contract stammen.

---

# 9. Strategy-to-Core Adapter

## 9.1 Einzig zulässiger produktiver Einspeisepunkt

```text
FILE=
src/backtest/mv2_research_wiring_v1.py
```

Begründung:

- Dort treffen `StrategySignalBindingResultV1`, CMC, Bar-Sequenz und Replay-Assembly bereits zusammen.
- `master_v2` darf nicht von Backtest-spezifischen Strategy-Signal-Typen abhängig gemacht werden.
- Die Dependency-Richtung bleibt sauber:
  - Backtest-/Research-Adapter kennt Strategy-Signal-Contract und Core-Builder.
  - Core-Builder kennt nur normalisierte kanonische Felder.
  - Core importiert keinen Backtest-Signal-Typ.

## 9.2 Adapter-Verantwortlichkeit

Der Adapter muss:

```text
- StrategySignalBindingResultV1 für den konkreten Epoch/Bar korrekt ausrichten
- Strategy Identity und Version gegen Registry Snapshot prüfen
- Signal-Provenance und Digest binden
- Signalwert/Side-Hint nicht direkt als Position ausführen
- Strategy-Material in dafür vorgesehene normalisierte Replay-Input-Felder überführen
- dieselbe CanonicalMarketContextV1-Instanz bzw. deren kanonische Identity/Digest verwenden
- Sequence/Prior-State korrekt weiterreichen
- den Single Canonical Replay Input Builder aufrufen
- bei fehlender Ausrichtung, fehlender Provenance oder Digest-Mismatch fail-closed abbrechen
```

Der Adapter darf nicht:

```text
- IntegratedOfflineReplayInputV1 direkt selbst konstruieren
- einen zweiten Replay Input Builder erzeugen
- Directional/Survival/Suitability/Composition duplizieren
- Engine-Positionen erzeugen
- Engine-Sizing auslösen
- Order Intents erzeugen
```

## 9.3 Strategy-Einfluss muss nachweisbar sein

Die Umsetzung darf nicht lediglich Provenance an Evidence anhängen, ohne die Core-Entscheidung fachlich beeinflussen zu können.

Pflichtnachweise:

```text
STRATEGY_SIGNAL_BOUND_TO_REPLAY_INPUT=true
STRATEGY_SIGNAL_DIGEST_BOUND=true
STRATEGY_IDENTITY_BOUND=true
STRATEGY_VERSION_BOUND=true
STRATEGY_INPUT_REACHES_CANONICAL_ORCHESTRATOR=true
STRATEGY_INPUT_IS_VISIBLE_IN_DECISION_EVIDENCE_OR_REFERENCED_INPUT_DIGEST=true
```

Zusätzlich ist ein kontrollierter Fixture-Test erforderlich:

```text
SAME_CMC_SAME_STATE_DIFFERENT_VALID_STRATEGY_INPUT
→ canonical input digest changes
→ strategy binding/provenance reference changes
→ expected canonical stage influenced according to existing contract
→ no direct position mapping from raw ±1
```

Wichtig: Welche konkrete Stage den Strategy-Input konsumiert, muss aus den bestehenden Contracts reuse-first abgeleitet werden. Es ist verboten, ohne Repo-Beleg eine neue parallele Directional- oder Suitability-Semantik zu erfinden.



### Zusätzliche Readiness-Regel

Vor jeder Implementierung ist nachzuweisen:

```text
EXISTING_CANONICAL_CONSUMER_IDENTIFIED=true
NO_ARTIFICIAL_CONSUMER_INTRODUCED=true
```

Es muss dokumentiert werden, welche **bereits existierende** kanonische Stage den Strategy-Input fachlich konsumiert. Existiert kein nachweisbarer Consumer, ist dies als separater bounded Scope auszuweisen und darf nicht implizit innerhalb des Wiring-PR eingeführt werden.

---


## 9.4 Bestätigter Readiness-Befund: kein bestehender Consumer für Strategy-Signalwerte

Der Read-Only Implementation-Readiness-Report gegen
`main@6e8c5889bbc20b762dc0f846776a8bbc70e4376f` hat folgenden Befund bestätigt:

```text
EXISTING_CANONICAL_CONSUMER_IDENTIFIED_FOR_STRATEGY_SIGNAL_VALUES=false
EXISTING_CANONICAL_CONSUMER_FOR_STRATEGY_REGISTRY_IDENTITY=true
NO_ARTIFICIAL_CONSUMER_INTRODUCED=true
SLICE_2_SIGNAL_VALUE_EFFECTIVENESS_REQUIRES_SEPARATE_FUTURE_SCOPE=true
FUTURE_SCOPE_ID=STRATEGY_SIGNAL_VALUE_CANONICAL_CONSUMER_BINDING_V1
```

Historische Consumer-Lage zum Readiness-Zeitpunkt (Baseline `6e8c5889…`;
**nicht** der aktuelle Post-Closeout-Ist):

| Kanonische Stage | Damaliger Input | Bewertung für `StrategySignalBindingResultV1.signals` |
|---|---|---|
| Directional Assessment | `price_path`, Reference Price, CMC Trust | Kein bestehender Consumer; Signalstärke wird aus Marktmaterial abgeleitet |
| Suitability Binding | Strategy Registry, Ranking, Regime | Konsumiert Identity/Registry-Material, aber keine Strategy-Signalwerte oder deren Provenance |
| Entry/Exit/Reversal Policy | Boolean Policy Signals | Kein Consumer des Strategy-Binding-Contracts |
| Composition / Survival / State Switch | kanonische Vorstufen | Kein Strategy-Signalwert-Input |

Daraus folgte damals verbindlich (historischer Readiness-Befund; durch PR #5229 Decision **C** ratifiziert als negativer Audit-Ist; später durch Decision **D** und Slices 2–4 supersediert):

```text
HISTORICAL_READINESS_BASELINE=true
SLICE_1_MAY_PROCEED_WITHOUT_STRATEGY_VALUE_BINDING=true
SLICE_1_MUST_NOT_ADD_DORMANT_STRATEGY_FIELDS=true
SLICE_2_IMPLEMENTATION_READY=false
SLICE_2_IMPLEMENTATION_AUTHORIZED=false
STRATEGY_PROVENANCE_ONLY_WIRING_FORBIDDEN=true
RAW_STRATEGY_SIGNAL_TO_POSITION_MAPPING_FORBIDDEN=true
ARCHITECTURE_AUTHORIZATION_DECISION=C
AUTHORIZED_CANONICAL_CONSUMER_STAGE=none
NEXT_AUTOMATIC_IMPLEMENTATION_SCOPE=NONE
READ_ONLY_CHAINING_REQUIRED=false
```

Slice 1 bleibt eine reine Konsolidierung der Replay-Input-Construction-Authority und ist abgeschlossen (`SLICE_1_COMPLETE=true`, `SLICE_1_REOPENED=false`). Er darf weder neue Strategy-Felder noch einen neuen Strategy-Consumer einführen und darf nicht erneut geöffnet werden.

**Superseded als aktueller Ist:** Der frühere Auftrag, vor Slice 2 automatisch
`READ_ONLY_STRATEGY_SIGNAL_VALUE_CANONICAL_CONSUMER_BINDING_V1` erneut
auszuführen bzw. einen weiteren Consumer-Design-Report zu starten, ist
**aufgehoben**. PR #5229 hat Decision **C** als historischen negativen Ist
ratifiziert. Decision **D** und die späteren Slice-2–4-Implementierungen
(final PR #5233) haben die technische Chain-Wiring-Mission danach
abgeschlossen. Ohne neue Unsicherheit darf kein weiterer Read-Only-Report
verkettet werden.

```text
HISTORICAL_DECISION_C_CLOSEOUT=true
STATUS=RATIFIED_NEGATIVE_CLOSEOUT
SLICE_2_IMPLEMENTATION_BLOCKED=true
SLICE_2_STATUS=BLOCKED_BY_ARCHITECTURE_DECISION_C
NEW_PARALLEL_DECISION_STAGE_ALLOWED=false
SEPARATE_ARCHITECTURE_AUTHORIZATION_EXECUTED=true
SEPARATE_FUTURE_ARCHITECTURE_AUTHORIZATION_REQUIRED=false
NEXT_AUTOMATIC_IMPLEMENTATION_SCOPE=NONE
```

# 10. Canonical Market Context Binding

## 10.1 Verbindliche Regel

```text
ONE_CANONICAL_MARKET_CONTEXT_PER_DECISION_CYCLE=true
STRATEGY_LOCAL_MARKET_CONTEXT_ALLOWED=false
BACKTEST_LOCAL_DECISION_MARKET_CONTEXT_ALLOWED=false
RUNTIME_BRIDGE_LOCAL_DECISION_MARKET_CONTEXT_ALLOWED=false
```

Strategy-Ausführung darf weiterhin Bars/Features für die Signalberechnung konsumieren. Für die kanonische Gesamtentscheidung muss die Signal-Provenance jedoch an denselben Marktzyklus gebunden sein wie `CanonicalMarketContextV1`.

Zu beweisen:

```text
- instrument identity match
- trading epoch match
- bar finality match
- source/input digest linkage
- no out-of-order strategy signal
- no unfinalized-bar decision
```

## 10.2 Keine falsche Lösung

Nicht ausreichend:

```text
Strategy signal merely copied into arbitrary CMC feature map
```

Der Discovery-Report hat bestätigt, dass Directional Assessment seine Signalstärke aus `price_path` und `reference_price` ableitet und Trust-Gates aus CMC bezieht. Ein beliebiges Einfügen der ±1-Serie in CMC-Features würde die kanonische Entscheidung nicht notwendigerweise beeinflussen und könnte eine tote Verdrahtung erzeugen.

Die korrekte Lösung ist:

```text
Strategy Signal + CMC + State + Registry + Policies
→ normalized replay input material
→ canonical orchestrator
```

Nicht:

```text
Strategy Signal
→ fake CMC feature
→ no actual consumer
```

---

# 11. Classic Backtest Engine — Zielrolle

## 11.1 Historischer Defekt (pre-Slice-3; superseded)

> **HISTORICAL / SUPERSEDED AS CURRENT DEFECT.** Discovery-/pre-Slice-3-Befund.
> Finaler Closeout bestätigt:
> `DIRECT_STRATEGY_TO_POSITION_PATH_COUNT=0`,
> `SYSTEM_RELEVANT_DIRECT_STRATEGY_TO_TRADE_PATH_COUNT=0`,
> `CLASSIC_ENGINE_DECISION_AUTHORITY_BYPASS_COUNT=0`.

Zum Discovery-Zeitpunkt existierten direkte Strategy-to-Trade-Pfade:

```text
src/backtest/registry_engine.py
→ BacktestEngine.run_realistic

src/backtest/engine.py:run_single_strategy_from_registry
→ BacktestEngine.run_realistic

src/backtest/walkforward.py
→ BacktestEngine.run_realistic

src/sweeps/engine.py
→ BacktestEngine.run_realistic

src/portfolio/manager.py
→ BacktestEngine.run_realistic

src/backtest/mv2_research_wiring_v1.py
with ENGINE_SIGNAL_SOURCE_CONFIGURED_STRATEGY
→ BacktestEngine.run_realistic
```

Diese Pfade gaben der Strategy-Serie de facto Positions-/Trade-Authority.

## 11.2 Zielrolle

```text
BACKTEST_ENGINE_ROLE=FILL_AND_EXECUTION_SIMULATOR_ONLY
BACKTEST_ENGINE_TRADING_DECISION_AUTHORITY=false
BACKTEST_ENGINE_STRATEGY_SIGNAL_AUTHORITY=false
```

Der Engine-Input für systemrelevante kanonische Evaluationspfade muss aus dem kanonischen Decision Replay stammen:

```text
ENGINE_SIGNAL_SOURCE=mv2_decision_replay_series
```

oder einem semantisch identischen kanonischen Decision-to-Position-Mapper.

## 11.3 Umgang mit klassischen Callern

Jeder produktive Caller muss einzeln klassifiziert werden:

```text
A. CANONICALIZE
   Caller wird auf run_mv2_research_backtest_wiring_v1 oder einen
   gleichwertigen kanonischen Adapter umgeleitet.

B. FAIL_CLOSED_FOR_SYSTEM_ECONOMIC_EVIDENCE
   Legacy-Pfad darf für klar gekennzeichnete isolierte Unit-/Legacy-Zwecke
   bestehen, darf aber keine systemrelevante Economic Evidence erzeugen.

C. REMOVE_AS_DEAD_PATH
   Nur wenn durch Call-Graph und Tests eindeutig belegt.
```

Es ist nicht zwingend sicher, alle Caller in einem einzigen unbounded Patch umzuleiten. Die Umsetzung soll bounded erfolgen, aber der Endzustand muss die neun Bypass-Pfade vollständig klassifizieren und Decision-Authority-BYPASS auf null bringen.

---

# 12. Runtime Bridge — Parity ja, Aktivierung nein

## 12.1 Aktueller Status

```text
CANONICAL_RUNTIME_ENTRYPOINT_STATUS=BOUND_NOT_ACTIVATED
RUNTIME_AUTHORITY_EFFECT=NONE
ORDER_AUTHORITY_EFFECT=NONE
```

## 12.2 Ziel

Die Runtime Bridge soll denselben Single Canonical Replay Input Builder und denselben Integrated Orchestrator verwenden.

```text
RUNTIME_BRIDGE_CANONICAL_ORCHESTRATOR_BOUND=true
RUNTIME_BRIDGE_DUPLICATES_DECISION_LOGIC=false
RUNTIME_BRIDGE_REPLAY_INPUT_BUILDER_DUPLICATE=false
RUNTIME_BRIDGE_AUTHORITY_EFFECT=NONE
RUNTIME_BRIDGE_ORDER_EFFECT=NONE
```

Der bestehende Harness-Builder:

```text
build_integrated_offline_replay_input_from_harness_v0
```

darf als dünner Source-Adapter bestehen bleiben, aber nicht mehr selbst `IntegratedOfflineReplayInputV1` mit eigener Semantik konstruieren. Er muss den Single Canonical Builder aufrufen.

Kein Guard-Flip.

Keine Runtime-Aktivierung.

Keine Orders.

---

# 13. Parity Harness — Zielrolle

Die Inline-Konstruktion in:

```text
integrated_vs_scenario_replay_full_system_parity_harness_v0.py
```

muss auf den Single Canonical Replay Input Builder migriert werden.

Fixture-spezifische Werte dürfen weiter als explizite Inputs existieren.

Nicht zulässig:

```text
fixture-specific hidden construction semantics
direct IntegratedOfflineReplayInputV1(...) in productive parity path
separate component-version defaults
separate digest semantics
```

Test-only Helper dürfen für kompakte Fixture-Erzeugung bestehen, sollen aber möglichst ebenfalls den öffentlichen Builder verwenden, damit der Builder-Contract selbst getestet wird.

---

# 14. Bypass- und Duplicate-Authority-Inventar

## 14.1 Bestätigte Bypass-Pfade

| # | Pfad | Klassifikation |
|---|---|---|
| 1 | `registry_engine → run_realistic` | Echte zweite Decision Authority |
| 2 | `engine.run_single_strategy_from_registry` | Echte zweite Decision Authority |
| 3 | `walkforward → run_realistic` | Echte zweite Decision Authority |
| 4 | `sweeps&#47;engine → run_realistic` | Echte zweite Decision Authority |
| 5 | `portfolio&#47;manager → run_realistic` | Echte zweite Decision Authority |
| 6 | MV2 `configured_strategy_signal → engine` | Echte zweite Decision Authority |
| 7 | `offline_double_play_scenario_replay_v0` | Technischer paralleler Orchestrierungspfad; kanonische Komponenten reused |
| 8 | `ops.double_play.evaluate_double_play` | Legacy Duplicate Decision Logic |
| 9 | Engine `PositionSizer` vs Canonical CRS | Technische/semantische Sizing-Duplikation |

## 14.2 Endzustand

```text
DIRECT_STRATEGY_TO_POSITION_PATH_COUNT=0
DIRECT_STRATEGY_TO_ORDER_INTENT_PATH_COUNT=0
SYSTEM_RELEVANT_DIRECT_STRATEGY_TO_TRADE_PATH_COUNT=0
CLASSIC_ENGINE_DECISION_AUTHORITY_BYPASS_COUNT=0
REPLAY_INPUT_PRODUCTIVE_CONSTRUCTOR_COUNT=1
CANONICAL_TOTAL_DECISION_OWNER_COUNT=1
```

Legacy-Code darf nur bestehen, wenn:

```text
LEGACY_NON_AUTHORITATIVE=true
SYSTEM_ECONOMIC_EVIDENCE_BLOCKED=true
RUNTIME_ENTRY_BLOCKED=true
STATIC_CONTRACT_TEST_ENFORCES_BOUNDARY=true
```

---

# 15. Duplicate Risk/Sizing — Grenze dieses Repairs

Bestätigte aktuelle Owner:

```text
src/risk PositionSizer via BacktestEngine
src/governance/capital_risk_sizing_v1.py
src/backtest/offline_evaluation_sizing_contract_v1
```

Dieses Repair darf keine Risk-/Sizing-Semantik verändern.

Ziel innerhalb dieses Scopes:

```text
- Engine PositionSizer darf nicht als zweite kanonische Sizing-Authority
  für systemrelevante Core-Evidence wirken.
- Existing canonical CRS decisions and references remain unchanged.
- Backtest fill simulation may consume already-canonicalized position/size
  material according to existing contracts.
```

Wenn die vollständige Entfernung der Sizing-Duplikation eine Semantikänderung erfordert:

```text
FAIL_CLOSED
SEPARATE_BOUNDED_RISK_SIZING_RECONCILIATION_SCOPE_REQUIRED=true
```

Nicht im Chain-Wiring-PR improvisieren.

---

# 16. Empfohlene bounded Implementierungssequenz

> **HISTORICALLY COMPLETE.** Die Slice-Sequenz 1–4 ist durch die Implementation
> PRs und final PR #5233 (`81222f4e…`) technisch abgeschlossen; Durable Static
> Guards landed in PR #5235. Die Slice-Texte bleiben als auditierbarer Vertrag
> erhalten und sind **keine** offenen Aufträge.
>
> ```text
> HISTORICAL_EXECUTED_SCOPE=true
> NO_LONGER_CURRENT_NEXT_ACTION=true
> ```

Ein einzelner großer Rewire über Builder, MV2, Bridge, Parity, fünf Classic Caller und Legacy Guards wäre risikoreich. Die technische Gesamtmission wurde deshalb in überprüfbare Slices geteilt.

## Slice 1 — Canonical Replay Input Builder Consolidation

> **HISTORICALLY COMPLETE — SLICE_1_COMPLETE=true** (PR #5226 squash-merged).
> Ziele und Acceptance unten sind erfüllt. Historischer Auftragstext bleibt als
> Vertrag auditierbar. Keine erneute Slice-1-Implementierung.
>
> ```text
> HISTORICAL_EXECUTED_SCOPE=true
> NO_LONGER_CURRENT_NEXT_ACTION=true
> ```

### Ziel

```text
- public single builder in integrated_offline_trading_logic_replay_v1.py
- MV2 private builder delegates to it
- Runtime harness builder delegates to it
- Parity inline construction delegates to it
- productive direct constructor count becomes 1
- no decision semantics change
```

### Erwartete Dateien

```text
src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py
src/backtest/mv2_research_wiring_v1.py
src/trading/master_v2/canonical_core_runtime_integration_bridge_v0.py
src/trading/master_v2/integrated_vs_scenario_replay_full_system_parity_harness_v0.py
focused tests
```

### Acceptance

```text
CANONICAL_REPLAY_INPUT_BUILDER_SINGLE_OWNER=true
```

Für die vorgelagerte Read-Only-Readiness gilt:

```text
PRODUCTIVE_DIRECT_REPLAY_INPUT_CONSTRUCTOR_COUNT_MUST_BE_DISCOVERED=true
NO_FIXED_CONSTRUCTOR_COUNT_ASSUMPTION=true
```

```text
CANONICAL_REPLAY_INPUT_BUILDER_SINGLE_OWNER=true
PRODUCTIVE_DIRECT_REPLAY_INPUT_CONSTRUCTOR_COUNT=1
MV2_BUILDER_IS_THIN_ADAPTER=true
RUNTIME_BUILDER_IS_THIN_ADAPTER=true
PARITY_BUILDER_IS_THIN_ADAPTER=true
CORE_DECISION_SEMANTICS_CHANGED=false
```

## Slice 2 — Strategy Signal to Canonical Replay Input Binding

> **HISTORICALLY COMPLETE — SLICE_2_COMPLETE=true.**
> Autorisiert unter `GO_DECISION_D_STRATEGY_SIGNAL_CANONICAL_CONSUMER_BINDING_V1`.
> Decision **C** bleibt historischer negativer Ist-Befund.
> Decision **D** ratifiziert
> `FAMILY_SCOPED_STRATEGY_AGREEMENT_INTO_EXISTING_SUITABILITY_V1`.
> `AUTHORIZED_CANONICAL_CONSUMER_STAGE=evaluate_suitability_binding_v1`.
> Technical Chain Wiring Mission closed via PRs through #5235
> (implementation PR #5233; durable static guards PR #5235).
>
> ```text
> HISTORICAL_EXECUTED_SCOPE=true
> NO_LONGER_CURRENT_NEXT_ACTION=true
> ```

### Ziel

```text
- StrategySignalBindingResultV1 is aligned per decision cycle
- strategy identity/version/provenance/digest are bound
- signal becomes effective canonical input material
- no raw signal-to-position mapping remains in MV2 canonical path
- engine signal source is canonical replay series
```

### Erwartete Dateien

```text
src/backtest/mv2_research_wiring_v1.py
src/backtest/strategy_signal_suitability_agreement_adapter_v1.py
src/trading/master_v2/strategy_suitability_agreement_material_v1.py
src/trading/master_v2/suitability_binding_v1.py
src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py
focused tests
```

### Vorbedingung (Decision D unter GO_TOKEN)

```text
ARCHITECTURE_AUTHORIZATION_DECISION=C
ARCHITECTURE_DECISION_D_RATIFIED=true
ARCHITECTURE_DECISION_D_NAME=
FAMILY_SCOPED_STRATEGY_AGREEMENT_INTO_EXISTING_SUITABILITY_V1
GO_TOKEN=GO_DECISION_D_STRATEGY_SIGNAL_CANONICAL_CONSUMER_BINDING_V1
AUTHORIZED_CANONICAL_CONSUMER_STAGE=evaluate_suitability_binding_v1
AUTHORIZED_CONSUMER_OWNER_FILE=
src/trading/master_v2/suitability_binding_v1.py
AUTHORIZED_CONSUMER_OWNER_SYMBOL=evaluate_suitability_binding_v1
SLICE_2_IMPLEMENTATION_AUTHORIZED=true
SLICE_2_STATUS=AUTHORIZED_UNDER_DECISION_D
NEXT_AUTOMATIC_IMPLEMENTATION_SCOPE=
FAMILY_SCOPED_STRATEGY_AGREEMENT_INTO_EXISTING_SUITABILITY_V1
STRATEGY_VALUE_SEMANTICS_RESOLVED=true
CMC_CONSISTENCY_BINDING_RESOLVED=true
FAIL_CLOSED_RULES_RESOLVED=true
REAL_CANONICAL_EFFECT_PROVEN=true
RAW_SIGNAL_DIRECT_AUTHORITY=false
PROVENANCE_ONLY_BINDING=false
NEW_PARALLEL_DECISION_STAGE=false
NEW_TOTAL_DECISION_OWNER=false
EXACT_CONSUMER_PATH=
StrategySignalBindingResultV1
→ normalize_strategy_signal_to_suitability_agreement_material_v1
→ build_integrated_offline_replay_input_v1
→ run_integrated_offline_trading_logic_replay_v1
→ _suitability_input_for_assessment
→ evaluate_suitability_binding_v1
```

### Acceptance

```text
STRATEGY_LAYER_FEEDS_CANONICAL_CORE=true
STRATEGY_SIGNAL_BINDING_REACHES_INTEGRATED_REPLAY=true
STRATEGY_SIGNAL_PROVENANCE_BOUND=true
STRATEGY_SIGNAL_DIGEST_BOUND=true
STRATEGY_SIGNAL_HAS_REAL_CANONICAL_CONSUMER=true
STRATEGY_SIGNAL_IS_NOT_PROVENANCE_ONLY=true
STRATEGY_SIGNAL_CAN_AFFECT_CANONICAL_DECISION=true
SELECTED_EXISTING_CANONICAL_STAGE=evaluate_suitability_binding_v1
MV2_CONFIGURED_STRATEGY_ENGINE_BYPASS=false
ENGINE_SIGNAL_SOURCE=mv2_decision_replay_series
RAW_STRATEGY_SIGNAL_DIRECT_POSITION_AUTHORITY=false
NEW_PARALLEL_DECISION_STAGE_REQUIRED=false
CANONICAL_TOTAL_DECISION_OWNER_UNCHANGED=true
```

## Slice 3 — Classic Caller Canonicalization / Fail-Closed Guarding

> **HISTORICALLY COMPLETE — SLICE_3_COMPLETE=true.** Acceptance unten ist
> im finalen Closeout bestätigt
> (`CLASSIC_ENGINE_DECISION_AUTHORITY_BYPASS_COUNT=0`). Kein offener Auftrag.
>
> ```text
> HISTORICAL_EXECUTED_SCOPE=true
> NO_LONGER_CURRENT_NEXT_ACTION=true
> ```

### Ziel

Alle fünf klassischen produktiven Caller und der Engine convenience entry point klassifizieren und entweder kanonisch umleiten oder für systemrelevante Evidence fail-closed blockieren.

### Erwartete Dateien

```text
src/backtest/registry_engine.py
src/backtest/engine.py
src/backtest/walkforward.py
src/sweeps/engine.py
src/portfolio/manager.py
src/backtest/mv2_research_wiring_v1.py
focused boundary tests
```

### Acceptance

```text
DIRECT_STRATEGY_TO_POSITION_PATH_COUNT=0
SYSTEM_RELEVANT_DIRECT_STRATEGY_TO_TRADE_PATH_COUNT=0
CLASSIC_ENGINE_DECISION_AUTHORITY_BYPASS_COUNT=0
```

## Slice 4 — Runtime/Backtest Parity and Legacy Boundary Closeout

> **HISTORICALLY COMPLETE — SLICE_4_COMPLETE=true** (final implementation PR #5233
> squash-merged as `81222f4e4227a98f93d0456d28db28aa075d4f80`; durable static
> guards PR #5235 as `a1890a3402f7686ba43309f00b0e5998245dafea`).
> `BACKTEST_RUNTIME_DECISION_PARITY=true`;
> `CANONICAL_RUNTIME_ENTRYPOINT_STATUS=BOUND_NOT_ACTIVATED`.
> Kein offener Auftrag.
>
> ```text
> HISTORICAL_EXECUTED_SCOPE=true
> NO_LONGER_CURRENT_NEXT_ACTION=true
> ```

### Ziel

```text
- Runtime Bridge and Backtest consume same canonical builder/orchestrator
- same normalized fixture produces same canonical decision evidence
- runtime remains BOUND_NOT_ACTIVATED
- legacy duplicate decision paths explicitly non-authoritative or blocked
```

### Acceptance

```text
BACKTEST_RUNTIME_DECISION_PARITY=true
RUNTIME_EFFECT=NONE
AUTHORITY_EFFECT=NONE
LEGACY_RUNTIME_GUARD_UNCHANGED=true
```

---

# 17. Implementierungsregeln

## 17.1 Reuse-first

```text
REUSE_WITH_NARROW_ADAPTER=true
NEW_TOTAL_DECISION_OWNER_ALLOWED=false
NEW_PARALLEL_REPLAY_INPUT_SCHEMA_ALLOWED=false
NEW_STRATEGY_SIGNAL_SCHEMA_ALLOWED=false
```

## 17.2 Keine versteckten Defaults

Jeder bisher builder-spezifische Wert muss klassifiziert werden:

```text
- canonical policy value
- source fixture value
- MV2 sequence state value
- legacy arbitrary default
```

Arbitrary Defaults dürfen nicht unbesehen in den Single Builder übernommen werden.

Der Builder muss source-neutrale Inputs akzeptieren.

## 17.3 Fail-closed

Beispiele:

```text
strategy_id mismatch
strategy_version mismatch
signal epoch mismatch
instrument mismatch
missing provenance
signal digest mismatch
CMC untrusted
bar non-final
out-of-order sequence
missing component version
missing required policy binding
invalid enum normalization
```

müssen deterministisch blockieren.

Keine stille Coercion, sofern der bestehende Contract sie nicht explizit vorsieht.

## 17.4 Dependency-Richtung

```text
master_v2 must not import backtest StrategySignalBindingResultV1
backtest adapter may import master_v2 public builder
runtime bridge may import master_v2 public builder
parity harness may import master_v2 public builder
```

---

# 18. Fokussierte Testmatrix

## 18.1 Builder-SSOT

```python
def test_productive_paths_use_single_canonical_replay_input_builder() -> None:
    ...

def test_mv2_source_adapter_does_not_construct_replay_input_directly() -> None:
    ...

def test_runtime_bridge_source_adapter_does_not_construct_replay_input_directly() -> None:
    ...

def test_parity_harness_does_not_construct_replay_input_directly() -> None:
    ...
```

## 18.2 Strategy Binding

```python
def test_strategy_signal_binding_reaches_integrated_orchestrator() -> None:
    ...

def test_strategy_identity_and_version_are_bound_to_replay_input() -> None:
    ...

def test_strategy_signal_provenance_and_digest_are_bound() -> None:
    ...

def test_strategy_signal_epoch_must_match_canonical_market_context_epoch() -> None:
    ...

def test_strategy_signal_instrument_must_match_canonical_market_context() -> None:
    ...

def test_missing_or_mismatched_strategy_binding_fails_closed() -> None:
    ...

def test_raw_strategy_signal_cannot_directly_drive_engine_position() -> None:
    ...
```

## 18.3 CMC Identity und Trust

```python
def test_strategy_binding_uses_exact_canonical_market_context_identity() -> None:
    ...

def test_untrusted_cmc_blocks_strategy_driven_decision() -> None:
    ...

def test_unfinalized_bar_cannot_create_canonical_decision() -> None:
    ...

def test_out_of_order_strategy_signal_is_rejected() -> None:
    ...
```

## 18.4 Core-Semantik bleibt erhalten

```python
def test_flat_before_opposite_side_remains_enforced() -> None:
    ...

def test_directional_assessment_contract_is_unchanged() -> None:
    ...

def test_survival_suitability_composition_sequence_is_unchanged() -> None:
    ...

def test_entry_exit_reversal_policy_contract_is_unchanged() -> None:
    ...

def test_risk_sizing_boundary_remains_downstream() -> None:
    ...

def test_safety_killswitch_reconciliation_boundaries_remain_downstream() -> None:
    ...
```

## 18.5 Classic No-Bypass

```python
def test_registry_engine_cannot_produce_system_evidence_via_raw_strategy_signal() -> None:
    ...

def test_engine_registry_convenience_path_is_canonical_or_fail_closed() -> None:
    ...

def test_walkforward_is_canonical_or_fail_closed_for_system_evidence() -> None:
    ...

def test_sweep_engine_is_canonical_or_fail_closed_for_system_evidence() -> None:
    ...

def test_portfolio_manager_is_canonical_or_fail_closed_for_system_evidence() -> None:
    ...

def test_mv2_configured_strategy_signal_cannot_override_replay_decision_series() -> None:
    ...
```

## 18.6 Backtest/Runtime Parity

```python
def test_backtest_and_runtime_bridge_use_same_replay_input_builder() -> None:
    ...

def test_backtest_and_runtime_bridge_emit_same_decision_for_same_normalized_fixture() -> None:
    ...

def test_backtest_and_runtime_decision_semantic_digest_match() -> None:
    ...

def test_runtime_bridge_remains_bound_not_activated() -> None:
    ...

def test_runtime_bridge_has_zero_order_and_authority_effect() -> None:
    ...
```

## 18.7 Strategy-Wirksamkeit ohne Direct Authority

```python
def test_valid_strategy_input_changes_bound_input_digest_or_strategy_reference() -> None:
    ...

def test_strategy_input_is_not_dead_provenance_only() -> None:
    ...

def test_opposite_raw_strategy_signal_does_not_bypass_core_gates() -> None:
    ...

def test_strategy_signal_cannot_override_untrusted_market_context() -> None:
    ...
```

---

# 19. Statische Call-Path-Prüfungen

Zusätzlich zu Unit-Tests sind statische Contract-Tests erforderlich.

Zu verbieten bzw. zu kontrollieren:

```text
- productive IntegratedOfflineReplayInputV1(...) outside canonical builder
- direct configured strategy signal passed as system-relevant engine source
- direct strategy function output mapped to position/trade
- runtime bridge calling partial decision components directly
- classic callers producing canonical/system economic evidence without MV2/Core path
```

Die Prüfung darf AST-basiert oder über bereits im Repo etablierte Contract-Test-Patterns erfolgen.

Fragile reine String-Grep-Tests nur ergänzend.

---

# 20. Manifest- und Evidence-Anforderungen

Jeder Slice muss ein manifest-verifiziertes Evidence-Bundle erzeugen, entsprechend den bestehenden Repo-Konventionen.

Mindestens:

```text
- preflight state
- source manifest verification
- exact changed files
- exact focused tests
- exact test return codes
- call-path inventory before/after
- direct constructor inventory before/after
- bypass inventory before/after
- semantic invariants
- runtime/authority effects
- final diff digest
- commit SHA
```

Finale Felder:

```text
ROOT_CAUSE_CONFIRMED=true

CANONICAL_REPLAY_INPUT_BUILDER_SINGLE_OWNER=true|false
PRODUCTIVE_DIRECT_REPLAY_INPUT_CONSTRUCTOR_COUNT=<n>

STRATEGY_LAYER_FEEDS_CANONICAL_CORE=true|false
STRATEGY_SIGNAL_PROVENANCE_BOUND=true|false
STRATEGY_SIGNAL_DIGEST_BOUND=true|false
STRATEGY_USES_CANONICAL_MARKET_CONTEXT=true|false
STRATEGY_SIGNAL_HAS_REAL_CANONICAL_CONSUMER=true|false
STRATEGY_SIGNAL_IS_PROVENANCE_ONLY=true|false
SLICE_2_IMPLEMENTATION_READY=true|false

CANONICAL_ORCHESTRATOR_SINGLE_DECISION_OWNER=true|false
FULL_CANONICAL_CHAIN_WIRED=true|false
BACKTEST_RUNTIME_DECISION_PARITY=true|false

CLASSIC_ENGINE_BYPASS_COUNT=<n>
DIRECT_STRATEGY_TO_POSITION_PATH_COUNT=<n>
DIRECT_STRATEGY_TO_ORDER_INTENT_PATH_COUNT=<n>
SYSTEM_RELEVANT_DIRECT_STRATEGY_TO_TRADE_PATH_COUNT=<n>

CORE_SEMANTICS_CHANGED=false
RISK_SIZING_SEMANTICS_CHANGED=false
SAFETY_SEMANTICS_CHANGED=false

RUNTIME_EFFECT=NONE
AUTHORITY_EFFECT=NONE
ORDER_EFFECT=NONE

FOCUSED_TESTS_PASS=true|false
STATIC_CONTRACT_TESTS_PASS=true|false
MANIFEST_VERIFY_RC=0|nonzero
```

---

# 21. Blocker und Stop-Bedingungen

Sofort fail-closed stoppen bei:

```text
WORKTREE_CLEAN=false before authorized mutation
HEAD!=ORIGIN_MAIN at required clean baseline
unexpected existing feature branch state
canonical owner ambiguity
new total decision owner required
master_v2 must import backtest strategy types
core decision semantics must change
risk/sizing semantics must change
safety/killswitch/reconciliation semantics must change
runtime guard must be activated
orders or credentials required
economic evaluation requested implicitly
unmanifested builder defaults
strategy input has no real canonical consumer when Slice 2 is requested
focused parity cannot be established
```

Zusätzlich — als **historische Fail-Closed-Bedingungen** während der Implementation
(nicht als aktueller Post-Closeout-Ist; final bestätigt sind die positiven Gegenstücke
in §0.4):

```text
CANONICAL_REPLAY_INPUT_BUILDER_SINGLE_OWNER=false
PRODUCTIVE_DIRECT_REPLAY_INPUT_CONSTRUCTOR_COUNT>1
STRATEGY_LAYER_FEEDS_CANONICAL_CORE=false
DIRECT_STRATEGY_TO_POSITION_PATH_COUNT>0
BACKTEST_RUNTIME_DECISION_PARITY=false
```

waren Closeout-Blocker, falls sie während der Umsetzung erneut beobachtet worden wären.

---

# 22. Definition of Done

> **SATISFIED / FINAL CLOSEOUT.** Die unten stehenden Felder sind nach PR #5233
> (`81222f4e4227a98f93d0456d28db28aa075d4f80`) technisch erfüllt. Siehe
> `CANONICAL_CHAIN_WIRING_REPAIR_FINAL_CLOSEOUT_V1` (§0.4).

Die technische Gesamtmission gilt als abgeschlossen, weil:

```text
STRATEGY_LAYER_FEEDS_CANONICAL_CORE=true
STRATEGY_SIGNAL_IS_EFFECTIVE_CANONICAL_INPUT=true
STRATEGY_SIGNAL_PROVENANCE_BOUND=true
STRATEGY_SIGNAL_DIGEST_BOUND=true
STRATEGY_USES_CANONICAL_MARKET_CONTEXT=true

CANONICAL_REPLAY_INPUT_BUILDER_SINGLE_OWNER=true
PRODUCTIVE_DIRECT_REPLAY_INPUT_CONSTRUCTOR_COUNT=1

CANONICAL_ORCHESTRATOR_SINGLE_DECISION_OWNER=true
BACKTEST_ENGINE_DECISION_AUTHORITY=false
RUNTIME_BRIDGE_DECISION_AUTHORITY=false

CLASSIC_ENGINE_CANONICAL_ORCHESTRATOR_BOUND=true
RUNTIME_BRIDGE_CANONICAL_ORCHESTRATOR_BOUND=true

DIRECT_STRATEGY_TO_POSITION_PATH_COUNT=0
DIRECT_STRATEGY_TO_ORDER_INTENT_PATH_COUNT=0
SYSTEM_RELEVANT_DIRECT_STRATEGY_TO_TRADE_PATH_COUNT=0
CLASSIC_ENGINE_BYPASS_COUNT=0
CLASSIC_ENGINE_DECISION_AUTHORITY_BYPASS_COUNT=0

FULL_CANONICAL_CHAIN_WIRED=true
BACKTEST_RUNTIME_DECISION_PARITY=true

CORE_SEMANTICS_CHANGED=false
RISK_SIZING_SEMANTICS_CHANGED=false
SAFETY_SEMANTICS_CHANGED=false

RUNTIME_EFFECT=NONE
AUTHORITY_EFFECT=NONE
ORDER_EFFECT=NONE
CANONICAL_RUNTIME_ENTRYPOINT_STATUS=BOUND_NOT_ACTIVATED
```

Das Ergebnis bedeutet ausschließlich:

```text
TECHNICAL_CANONICAL_CHAIN_WIRING_COMPLETE=true
STATUS=TECHNICAL_IMPLEMENTATION_COMPLETE
MISSION_STATUS=TECHNICALLY_COMPLETE
```

Es bedeutet **nicht** Economic-/Promotion-/Runtime-/Live-Freigabe. Explizite
Nicht-Aussagen bleiben:

```text
ECONOMIC_VALIDITY_PASS=false
PROMOTION_ELIGIBLE=false
RUNTIME_AUTHORIZED=false
LIVE_AUTHORIZED=false
ORDERS_ALLOWED=false
MISSION_COMPLETE=false
```

---

# 23. Übergabe an einen neuen Chat

## 23.1 Kontextblock

Diesen Block zusammen mit dem Runbook in einen neuen Chat geben:

```text
Wir arbeiten im Repo /Users/frnkhrz/Peak_Trade.

Das beigefügte Dokument
"Peak_Trade_Canonical_Chain_Wiring_Repair_Master_Runbook_v2.2.md"
ist der verbindliche Implementierungsvertrag.

STATUS=TECHNICAL_IMPLEMENTATION_COMPLETE
IMPLEMENTATION_COMPLETE=true
CLOSEOUT_COMPLETE=true
TECHNICAL_CANONICAL_CHAIN_WIRING_COMPLETE=true
FULL_CANONICAL_CHAIN_WIRED=true
BACKTEST_RUNTIME_DECISION_PARITY=true
FINAL_CLOSEOUT_COMPLETE=true
FINAL_IMPLEMENTATION_PR=5233
FINAL_IMPLEMENTATION_SQUASH_COMMIT=81222f4e4227a98f93d0456d28db28aa075d4f80
FINAL_DURABLE_STATIC_GUARD_PR=5235
FINAL_CLOSEOUT_HEAD=a1890a3402f7686ba43309f00b0e5998245dafea
CANONICAL_RUNTIME_ENTRYPOINT_STATUS=BOUND_NOT_ACTIVATED
NEXT_ACTION=NONE_FOR_CANONICAL_CHAIN_WIRING_REPAIR
MISSION_STATUS=TECHNICALLY_COMPLETE
CANONICAL_CHAIN_WIRING_REPAIR_MISSION_STATUS=COMPLETE
FURTHER_CHAIN_WIRING_MUTATION_REQUIRED=false
FURTHER_MUTATION_REQUIRES_SEPARATE_NEW_SCOPE=true
NEW_SCOPE_REQUIRES_NEW_UNCERTAINTY_OR_SEPARATE_AUTHORIZATION=true
READ_ONLY_CHAINING_WITHOUT_NEW_UNCERTAINTY=false
MISSION_COMPLETE=false
ECONOMIC_VALIDITY_PASS=false
PROMOTION_ELIGIBLE=false
RUNTIME_AUTHORIZED=false
LIVE_AUTHORIZED=false
ORDERS_ALLOWED=false

Bestätigte Wahrheiten (aktueller Post-Closeout-Ist):

- Core ist die einzige fachliche Trading-Gesamtwahrheit.
- Strategy Layer speist den kanonischen Core wirksam
  (`STRATEGY_LAYER_FEEDS_CANONICAL_CORE=true`).
- Reeller Strategy-Contract: StrategySignalBindingResultV1.
- Erste vollständige kanonische Decision Unit: IntegratedOfflineReplayInputV1.
- Single Decision Owner: run_integrated_offline_trading_logic_replay_v1.
- Canonical Replay Input Builder ist Single-Owner
  (`PRODUCTIVE_DIRECT_REPLAY_INPUT_CONSTRUCTOR_COUNT=1`).
- Classic-Engine Decision-Authority-Bypass-Count ist 0.
- Durable Static Guards vorhanden (PR #5235).
- BacktestEngine bleibt Fill-/Execution-Simulator.
- Runtime bleibt BOUND_NOT_ACTIVATED.
- Keine Economic Evaluation, keine Runtime-Aktivierung, keine Orders.
- Slice 1–4 historisch abgeschlossen; Implementierungs-Merge PR #5233;
  Durable-Static-Guard-Closeout PR #5235.
- Discovery-/Decision-C-/Post-Slice-1-/PR-#5233-Baselines bleiben historische
  Audit-Info und sind nicht der absolute aktuelle HEAD-Ist.

Keine neue Discovery. Keine neue Read-Only-Kette. Keine Mutation ohne
separaten neuen Scope und neues Operator-GO.
```

## 23.2 Fortsetzungsregel

Ein neuer Chat darf nicht wieder bei hypothetischen Klassen wie `StrategySignalV1` oder `CanonicalDecisionRequestV1` beginnen.

Er muss die realen Repo-Symbole verwenden.

**Nach Final Technical Closeout (PRs through #5235) gilt verbindlich:**

```text
FINAL_CLOSEOUT_COMPLETE=true
CLOSEOUT_COMPLETE=true
FINAL_IMPLEMENTATION_PR=5233
FINAL_DURABLE_STATIC_GUARD_PR=5235
FINAL_CLOSEOUT_HEAD=a1890a3402f7686ba43309f00b0e5998245dafea
TECHNICAL_CANONICAL_CHAIN_WIRING_COMPLETE=true
FULL_CANONICAL_CHAIN_WIRED=true
BACKTEST_RUNTIME_DECISION_PARITY=true
DURABLE_STATIC_GUARDS_PRESENT=true
CANONICAL_RUNTIME_ENTRYPOINT_STATUS=BOUND_NOT_ACTIVATED
NEXT_ACTION=NONE_FOR_CANONICAL_CHAIN_WIRING_REPAIR
MISSION_STATUS=TECHNICALLY_COMPLETE
CANONICAL_CHAIN_WIRING_REPAIR_MISSION_STATUS=COMPLETE
FURTHER_CHAIN_WIRING_MUTATION_REQUIRED=false
FURTHER_MUTATION_REQUIRES_SEPARATE_NEW_SCOPE=true
NEW_SCOPE_REQUIRES_NEW_UNCERTAINTY_OR_SEPARATE_AUTHORIZATION=true
READ_ONLY_CHAINING_WITHOUT_NEW_UNCERTAINTY=false
READ_ONLY_CHAINING_REQUIRED=false
NEW_READ_ONLY_CHAIN_CREATED=false
MISSION_COMPLETE=false
ECONOMIC_VALIDITY_PASS=false
PROMOTION_ELIGIBLE=false
RUNTIME_AUTHORIZED=false
LIVE_AUTHORIZED=false
ORDERS_ALLOWED=false
RUNTIME_EFFECT=NONE
AUTHORITY_EFFECT=NONE
ORDER_EFFECT=NONE
ECONOMIC_EFFECT=NONE
```

**Historische Decision-D-/Decision-C-Audit-Felder (nicht aktueller offener Auftrag):**

```text
HISTORICAL_DECISION_AND_SLICE_AUTHORIZATION_TRAIL=true
PR5229_RATIFICATION_STATUS=COMPLETE
ARCHITECTURE_AUTHORIZATION_DECISION=C
ARCHITECTURE_DECISION_D_RATIFIED=true
ARCHITECTURE_DECISION_D_NAME=
FAMILY_SCOPED_STRATEGY_AGREEMENT_INTO_EXISTING_SUITABILITY_V1
GO_TOKEN=GO_DECISION_D_STRATEGY_SIGNAL_CANONICAL_CONSUMER_BINDING_V1
AUTHORIZED_CANONICAL_CONSUMER_STAGE=evaluate_suitability_binding_v1
SLICE_1_REOPENED=false
SLICE_2_IMPLEMENTATION_AUTHORIZED=true
SLICE_2_STATUS=AUTHORIZED_UNDER_DECISION_D
EXACT_CONSUMER_PATH=
StrategySignalBindingResultV1
→ normalize_strategy_signal_to_suitability_agreement_material_v1
→ build_integrated_offline_replay_input_v1
→ run_integrated_offline_trading_logic_replay_v1
→ _suitability_input_for_assessment
→ evaluate_suitability_binding_v1
```

Verboten als automatische Fortsetzung: erneuter Consumer-Design-Report,
erneuter Read-Only-Scope, erneute Slice-1–4-Implementierung ohne neuen
separaten Operator-Scope, Runtime-Aktivierung, Economic Evaluation, Orders.

---

# 24. NEXT_ACTION — Canonical Chain Wiring Repair Closed

```text
NEXT_ACTION=NONE_FOR_CANONICAL_CHAIN_WIRING_REPAIR
MISSION_STATUS=TECHNICALLY_COMPLETE
CANONICAL_CHAIN_WIRING_REPAIR_MISSION_STATUS=COMPLETE
FURTHER_CHAIN_WIRING_MUTATION_REQUIRED=false
FURTHER_MUTATION_REQUIRES_SEPARATE_NEW_SCOPE=true
NEW_SCOPE_REQUIRES_NEW_UNCERTAINTY_OR_SEPARATE_AUTHORIZATION=true
READ_ONLY_CHAINING_WITHOUT_NEW_UNCERTAINTY=false
NEW_READ_ONLY_CHAIN_CREATED=false
ECONOMIC_VALIDITY_PASS=false
PROMOTION_ELIGIBLE=false
RUNTIME_AUTHORIZED=false
LIVE_AUTHORIZED=false
ORDERS_ALLOWED=false
```

Keine neue Read-Only-Kette. Kein weiterer automatischer Cursor-Auftrag für
diese Mission. Weitere Änderungen erfordern einen separaten neuen Scope und
ein neues Operator-GO.

### 24.1 HISTORICAL / SUPERSEDED — früherer Slice-1 Readiness-Auftrag

> **HISTORICAL / SUPERSEDED — SLICE 1 ALREADY COMPLETED.** Dieser §24.1-Auftragstext war der
> Slice-1-Readiness-Auftrag zum Discovery-Baseline `6e8c5889…`. Slice 1 ist per PR #5226
> abgeschlossen (`SLICE_1_COMPLETE=true`). Nicht erneut ausführen. Inhalt bleibt als
> historischer Vertrag erhalten.
>
> ```text
> HISTORICAL_EXECUTED_SCOPE=true
> NO_LONGER_CURRENT_NEXT_ACTION=true
> ```

Dieser Auftrag war read-only. Er prüfte nur Drift seit dem Discovery-Baseline-Commit und erzeugte den exakten bounded Implementierungsvertrag für Slice 1.

```text
AUSFÜHRUNGSART: READ_ONLY_CANONICAL_REPLAY_INPUT_BUILDER_IMPLEMENTATION_READINESS_V1

REPO: /Users/frnkhrz/Peak_Trade
WORKTREE: primary
BRANCH: main

DISCOVERY_BASELINE_HEAD:
6e8c5889bbc20b762dc0f846776a8bbc70e4376f

Keine Mutation.
Keine Tests.
Keine Background-Terminals.
Keine Evidence-Verzeichnisse.
Keine PR.
Keine Economic Evaluation.

PHASE 0 — PREFLIGHT

Ermittle:

HEAD
ORIGIN_MAIN
HEAD_EQUALS_ORIGIN_MAIN
WORKTREE_CLEAN
REPO_DIFF_EMPTY

Falls HEAD oder origin/main seit Discovery verändert sind:
kein automatischer Blocker.
Prüfe gezielt, ob sich die manifestierten Owner, Builder,
Call-Sites oder Contracts geändert haben.

PHASE 1 — SYMBOL AND CONTRACT DRIFT CHECK

Verifiziere gegen den aktuellen Repo-Stand:

1.
IntegratedOfflineReplayInputV1 existiert weiterhin in:
src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py

2.
run_integrated_offline_trading_logic_replay_v1 bleibt der
Single Total Decision Owner.

3.
StrategySignalBindingResultV1 und StrategySignalProvenanceV1
bleiben die realen Strategy-Signal-Contracts.

4.
Die produktiven ReplayInput-Konstruktionsstellen sind weiterhin:

- mv2_research_wiring_v1.py:_build_replay_input
- canonical_core_runtime_integration_bridge_v0.py:
  build_integrated_offline_replay_input_from_harness_v0
- integrated_vs_scenario_replay_full_system_parity_harness_v0.py
  inline construction

5.
Prüfe alle weiteren produktiven direkten Konstruktionen von:
IntegratedOfflineReplayInputV1(...)

Gib die vollständige aktuelle Liste aus.

PHASE 2 — FIELD-BY-FIELD CONSOLIDATION CONTRACT

Erzeuge für jedes Feld von IntegratedOfflineReplayInputV1 eine Matrix:

FIELD
TYPE
REQUIRED
CURRENT_MV2_SOURCE
CURRENT_RUNTIME_BRIDGE_SOURCE
CURRENT_PARITY_SOURCE
CANONICAL_SOURCE_CLASSIFICATION
NORMALIZATION_REQUIRED
DEFAULT_ALLOWED
FAIL_CLOSED_RULE

CANONICAL_SOURCE_CLASSIFICATION darf nur sein:

- MARKET_CONTEXT
- STRATEGY_BINDING
- SEQUENCE_STATE
- REGISTRY
- POLICY
- POSITION_CONTEXT
- SAFETY_RECON
- VERSION_BINDING
- DIGEST_BINDING
- FIXTURE_ONLY
- UNKNOWN

UNKNOWN → Slice 1 nicht implementierungsbereit.

PHASE 3 — BUILDER API DESIGN FROM EXISTING CONTRACTS

Leite reuse-first die kleinste public Builder-Signatur ab.

Keine neue Schema-Klasse erfinden, außer bestehende Feldanzahl oder
Dependency-Grenzen machen eine bereits im Repo übliche Params-Dataclass
zwingend erforderlich.

Ausgeben:

PROPOSED_BUILDER_FILE
PROPOSED_BUILDER_SYMBOL
PROPOSED_PARAMETERS
PROPOSED_RETURN_TYPE
VALIDATION_RULES
ENUM_NORMALIZATION_OWNER
DIGEST_BINDING_OWNER
VERSION_BINDING_OWNER

Prüfe Namenskollisionen.

PHASE 4 — THIN ADAPTER MIGRATION PLAN

Für jede Source:

- MV2
- Runtime Bridge
- Parity Harness

ausgeben:

CURRENT_CONSTRUCTION_SYMBOL
FIELDS_PREPARED_BY_SOURCE
FIELDS_NORMALIZED_BY_CANONICAL_BUILDER
DIRECT_CONSTRUCTOR_REMOVED=true|false
THIN_ADAPTER_SURVIVES=true|false
EXPECTED_CHANGED_FILES
EXPECTED_TEST_FILES

PHASE 5 — STRATEGY-BINDING FORWARD COMPATIBILITY

Ohne Slice 2 zu implementieren:

Prüfe, wie der Single Builder so gestaltet werden muss, dass
mv2_research_wiring_v1 später StrategySignalBindingResultV1-Material
einspeisen kann, ohne dass master_v2 Backtest-Typen importiert.

Ausgeben:

NORMALIZED_STRATEGY_FIELDS_AVAILABLE_TODAY
NORMALIZED_STRATEGY_FIELDS_MISSING
BUILDER_EXTENSION_NEEDED_IN_SLICE_1=true|false
MASTER_V2_IMPORTS_BACKTEST_TYPES_REQUIRED=false

Keine hypothetische tote Provenance-Lösung akzeptieren.
Der spätere Strategy-Input muss fachlich konsumierbar und digestgebunden
sein, ohne Direct Position Authority zu erhalten.

PHASE 6 — EXACT SLICE-1 MUTATION MANIFEST

Erzeuge den exakten bounded Scope:

FILES_TO_MODIFY
FILES_TO_ADD
SYMBOLS_TO_ADD
SYMBOLS_TO_CHANGE
DIRECT_CONSTRUCTORS_TO_REMOVE
FOCUSED_TESTS_TO_RUN
STATIC_CONTRACT_TESTS_TO_ADD
OUT_OF_SCOPE_FILES
RISKS
ROLLBACK_BOUNDARY

Keine Implementierung.

FINAL REPORT

STATUS=PASS|FAIL_CLOSED
VERDICT=CANONICAL_REPLAY_INPUT_BUILDER_IMPLEMENTATION_READY|NOT_READY

HEAD=<sha>
ORIGIN_MAIN=<sha>
HEAD_EQUALS_ORIGIN_MAIN=true|false
WORKTREE_CLEAN=true|false

DISCOVERY_CONTRACT_DRIFTED=true|false
SINGLE_DECISION_OWNER_STILL_CONFIRMED=true|false
PRODUCTIVE_DIRECT_REPLAY_INPUT_CONSTRUCTOR_COUNT=<n>
ALL_REPLAY_INPUT_FIELDS_CLASSIFIED=true|false
UNKNOWN_FIELDS=<list>
BUILDER_API_RESOLVED=true|false
ENUM_NORMALIZATION_OWNER_RESOLVED=true|false
DIGEST_BINDING_OWNER_RESOLVED=true|false
VERSION_BINDING_OWNER_RESOLVED=true|false
STRATEGY_FORWARD_COMPATIBILITY_RESOLVED=true|false
MASTER_V2_IMPORTS_BACKTEST_TYPES_REQUIRED=false
SLICE_1_MINIMAL_MUTATION_MANIFEST_RESOLVED=true|false
CORE_SEMANTICS_CHANGE_REQUIRED=false
RISK_SIZING_SEMANTICS_CHANGE_REQUIRED=false
SAFETY_SEMANTICS_CHANGE_REQUIRED=false
RUNTIME_EFFECT=NONE
AUTHORITY_EFFECT=NONE

Stop nach dem Report.
```

---

# 25. Bounded Implementation Template — Slice 1

> **HISTORICAL / SUPERSEDED — ALREADY EXECUTED.** Dieses Template wurde im Slice-1-Pfad
> (PR #5226) vollzogen. Nicht erneut als offener Implementierungsauftrag behandeln.
> Post-Slice-1-Ist: §0.2. Inhalt bleibt als historisches Template erhalten.
>
> ```text
> HISTORICAL_EXECUTED_SCOPE=true
> NO_LONGER_CURRENT_NEXT_ACTION=true
> ```

Nur nach erfolgreichem Readiness-Report und separatem Operator-GO verwenden.

```text
AUSFÜHRUNGSART: BOUNDED_CANONICAL_REPLAY_INPUT_BUILDER_CONSOLIDATION_V1

REPO: /Users/frnkhrz/Peak_Trade
WORKTREE: primary
BRANCH: new bounded feature branch

EXPECTED_HEAD:
aus aktuellem autorisiertem Preflight

EXPECTED_ORIGIN_MAIN:
aus aktuellem autorisiertem Preflight

GO_TOKEN:
vom Operator separat bereitstellen

Implementiere ausschließlich den manifestierten Slice-1-Scope aus dem
unmittelbar vorherigen Readiness-Report.

Pflichtziele:

- genau ein public canonical Replay Input Builder
- produktive direkte Konstruktionen von IntegratedOfflineReplayInputV1
  nur innerhalb dieses Builders
- MV2, Runtime Bridge und Parity Harness werden Thin Source Adapters
- bestehende Source-Materialien bleiben explizit
- keine Strategy-Semantikänderung
- keine neuen Strategy-Signal-Felder oder dormant Provenance-Felder
- kein Strategy-Signalwert-Consumer in Slice 1
- keine Core-Decision-Semantikänderung
- keine Risk-/Sizing-Semantikänderung
- keine Safety-/Recon-Semantikänderung
- keine Runtime-Aktivierung
- keine Economic Evaluation

Fail-closed bei unerwartetem Contract-Drift.

Führe nur manifestierte fokussierte Tests und Static Contract Tests aus.

Erzeuge Evidence und Manifest nach Repo-Konvention.

Stop vor Merge.

FINAL REPORT:

STATUS=PASS|FAIL_CLOSED
VERDICT=CANONICAL_REPLAY_INPUT_BUILDER_CONSOLIDATION_COMPLETE|FAILED

CANONICAL_REPLAY_INPUT_BUILDER_SINGLE_OWNER=true|false
PRODUCTIVE_DIRECT_REPLAY_INPUT_CONSTRUCTOR_COUNT=<n>
MV2_THIN_ADAPTER=true|false
RUNTIME_BRIDGE_THIN_ADAPTER=true|false
PARITY_HARNESS_THIN_ADAPTER=true|false
CORE_SEMANTICS_CHANGED=false
RISK_SIZING_SEMANTICS_CHANGED=false
SAFETY_SEMANTICS_CHANGED=false
RUNTIME_EFFECT=NONE
AUTHORITY_EFFECT=NONE
ORDER_EFFECT=NONE
FOCUSED_TESTS_PASS=true|false
STATIC_CONTRACT_TESTS_PASS=true|false
MANIFEST_VERIFY_RC=0|nonzero

Stop vor Merge.
```

---

# 26. Abschließende Architekturformel

```text
Strategy Layer contributes signal truth.
Canonical Market Context contributes market truth.
Canonical Core composes the only trading decision truth.
Capital/Risk/Sizing contributes canonical quantity truth.
Safety/KillSwitch/Reconciliation may veto or constrain.
Backtest simulates fills.
Runtime Bridge proves parity but has no authority.
```

Oder formal:

```text
StrategySignalBindingResultV1
≠ Trading Decision

CanonicalMarketContextV1
≠ Complete Trading Decision

IntegratedOfflineReplayInputV1
= Complete Canonical Decision Input

run_integrated_offline_trading_logic_replay_v1
= Single Canonical Total Decision Owner

CanonicalTradingDecisionEvidenceV1
= Immutable Canonical Decision Evidence

BacktestEngine
= Downstream Simulation Consumer
```

Diese Formel ist bei jeder Implementierungsentscheidung anzuwenden.
