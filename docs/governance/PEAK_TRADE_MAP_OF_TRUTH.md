# Peak Trade — Map of Truth

```text
DOCUMENT_CLASS=CURRENT_RUNTIME_TRUTH
DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS
```

**Rolle:** Zentraler Navigations-Einstieg (Discovery-Only).  
**Authority:** Keine. Dieses Dokument definiert keine Semantik.

```text
THIS_DOCUMENT_DEFINES_NO_SEMANTICS=true
THIS_DOCUMENT_POINTS_ONLY_TO_CANONICAL_OWNERS=true
THIS_DOCUMENT_IS_NOT_A_SECOND_RUNBOOK=true
THIS_DOCUMENT_IS_NOT_A_SECOND_SSOT=true
PARALLEL_SSOT_CREATED=false
LIVE_AUTHORIZED=false
ORDERS_ALLOWED=false
SCHEDULER_RUNTIME_ALLOWED=false
```

**Dieses Dokument definiert keine Semantik. Es verweist ausschließlich auf die kanonischen Owner.**

**Aktuelle Runtime-Ist-Wahrheit (nicht Zielbild):** [`PEAK_TRADE_CANONICAL_RUNTIME_TRUTH_MAP_V1.md`](PEAK_TRADE_CANONICAL_RUNTIME_TRUTH_MAP_V1.md)

**Capability-Closure-Arbeitsrunbook:** [`Peak_Trade_Canonical_Capability_Closure_Runtime_Recovery_Trading_Path_Runbook_V1_2_Trading_First.md`](Peak_Trade_Canonical_Capability_Closure_Runtime_Recovery_Trading_Path_Runbook_V1_2_Trading_First.md)

---

## 1. Systemzweck

Peak Trade ist ein **futures-only** Handelssystem. Das **Zielprogramm** ist vollautonome Runtime-Closure; das ist **nicht** der aktuelle Runtime-Ist-Zustand.

Aktuell verbindlich (siehe Canonical Runtime Truth Map):

```text
CANONICAL_RUNTIME_ENTRYPOINT_STATUS=FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE
FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE=true
SIMULATED_EXECUTION_ACTIVE=true
RUNTIME_ACTIVATED_SCOPE=CAP72_INTERNAL_STATEFUL_NO_ORDER_ONLY
PUBLIC_MD_RUNTIME_CAPABLE=true
PUBLIC_MD_NETWORK_SESSION_OBSERVED=false
LIVE_TRADING=FAIL_CLOSED
DASHBOARD=READ_ONLY_CONSUMER
PHASE_1_SELECTION=SINGLE_SELECTED_FUTURE
SELECTION_OWNER=CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1
PHASE_1_MAX_POSITIONS=1
MULTI_FUTURE_RUNTIME_AUTHORIZED=false
```

Das Zielprogramm umfasst u. a.:

- deterministische, auditierbare Handelslogik,
- realistische Profitabilitätsvalidierung,
- unabhängige Safety Authority,
- gefencete Single-Writer-Runtime,
- vollständige Reconciliation und sichere Restart-/Recovery-Semantik,
- durchgängige Research → Validation → Promotion → Runtime → Feedback-Kette,
- Phase-1 Single-Future-Safety vor späterer Multi-Future-Portfolio-Runtime (nur nach separaten Gates).

Keine Anlageberatung. Keine Live-/Order-/Scheduler-Freigabe allein durch Lektüre.

---

## 2. Kanonische semantische Autorität (Master Runbook V2.3)

Ab sofort und bis zur vollständigen Systemautonomie ist die **einzige** aktuelle Architektur-, Governance- und Implementierungsautorität:

| Rolle | Pfad |
|-------|------|
| **Canonical Master Runbook (aktuell)** | [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) |
| **Historische Vorgängerautorität (SUPERSEDED)** | [`Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md`](Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md) |

```text
CANONICAL_MASTER_RUNBOOK_PATH=docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md
CANONICAL_WORKING_AUTHORITY=docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md
CURSOR_MUST_READ_CANONICAL_RUNBOOK_FIRST=true
NO_PARALLEL_SEMANTIC_MODEL=true
RUNTIME_AUTHORIZATION_EFFECT=NONE
LIVE_AUTHORIZED=false
TESTNET_AUTHORIZED=false
ORDERS_ALLOWED=false
```

Historische Vorgängerfelder (nicht aktuell; nur für bestehende Contract-/Progress-Marker und Supersession-Nachweis):

```text
CANONICAL_VOLLAUTONOMIE_RUNBOOK_VERSION=v4.4.12
CANONICAL_VOLLAUTONOMIE_RUNBOOK_PATH=docs/governance/Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md
CANONICAL_RUNBOOK_CONTENT_VERSION=4.4.12-full-canonical-system-parity-before-system-economic-evidence
HISTORICAL_ONLY=true
STATUS=SUPERSEDED
SUPERSEDED_BY=docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md
```

Ältere Runbook-Pfade (v4.4 / v4.4.1 / v4.4.10 Dateiname / v2.6 / v4.4.12) sind **historische Adoption-/Crosslink-Oberflächen**. Normative Semantik kommt ausschließlich aus dem Canonical Master Runbook über diese Map.

Kurz-Navigationsvertrag (keine zweite SSOT): [`PEAK_TRADE_IMPLEMENTATION_CONTRACT.md`](PEAK_TRADE_IMPLEMENTATION_CONTRACT.md).

Ops-Drift-Registry (kein Navigations-Ersatz): [`docs/ops/registry/DOCS_TRUTH_MAP.md`](../ops/registry/DOCS_TRUTH_MAP.md).

---

## 3. Wichtigste Architektur-Domänen

Aus der kanonischen SSOT (Authority-Grenzen dort, nicht hier):

| Domäne | Kurzbeschreibung |
|--------|------------------|
| `TRADING_DECISION_CORE` | Market Context → Scope → Assessment → Survival/Suitability → Double Play → Decision |
| `CAPITAL_RISK_AND_SIZING_CORE` | Envelope → Pre-/Post-Sizing Risk → Position Sizing → Order Intent |
| `ECONOMIC_VALIDATION_CORE` | Backtest/Kosten/OLS-Diagnostik → Walk-Forward/MC/Stress → Viability Evidence |
| `SAFETY_EXECUTION_RUNTIME_CORE` | Safety Kernel → Eligibility → Lease → Submission → Reconciliation → Recovery |
| `LEARNING_PROMOTION_CORE` | Admissible Evidence → Candidate → Validation → Promotion → Deploy Inactive |

Weitere Architektur-Landkarten (deep dives, keine parallele Trading-SSOT):

- [`docs/architecture/PEAK_TRADE_CANONICAL_UNIFIED_TRADING_SYSTEM_RUNBOOK_V2_6.md`](../architecture/PEAK_TRADE_CANONICAL_UNIFIED_TRADING_SYSTEM_RUNBOOK_V2_6.md) — historisches strategisches Zielbild v2.6
- [`docs/architecture/canonical/PEAK_TRADE_CANONICAL_END_STATE_WIRING_MAP.md`](../architecture/canonical/PEAK_TRADE_CANONICAL_END_STATE_WIRING_MAP.md) — derived end-state wiring map (non-SSOT; non-runtime-authorizing; forensic SHA-bound)
- [`docs/ARCHITECTURE_OVERVIEW.md`](../ARCHITECTURE_OVERVIEW.md)
- [`docs/PEAK_TRADE_OVERVIEW.md`](../PEAK_TRADE_OVERVIEW.md)

---

## 4. Wichtigste Governance-Dokumente

| Dokument | Rolle |
|----------|-------|
| [`README.md`](README.md) | Governance-Index |
| [`PEAK_TRADE_RUNBOOK_EXECUTION_GOVERNANCE_V1.md`](PEAK_TRADE_RUNBOOK_EXECUTION_GOVERNANCE_V1.md) | Ausführungssteuerung / Package-Sequenz |
| [`PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md`](PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md) | Progress-Registry (Soll ↔ Ist) |
| [`PEAK_TRADE_IMPLEMENTATION_CONTRACT.md`](PEAK_TRADE_IMPLEMENTATION_CONTRACT.md) | Cursor-Kurzvertrag (navigation only) |
| [`ECONOMIC_DIAGNOSTIC_OPTIMIZATION_BOUNDARY_AND_CANONICAL_TRADING_LOGIC_IMMUTABILITY_CONTRACT_V0.md`](ECONOMIC_DIAGNOSTIC_OPTIMIZATION_BOUNDARY_AND_CANONICAL_TRADING_LOGIC_IMMUTABILITY_CONTRACT_V0.md) | Zulässige Optimierungsflächen vs. unveränderliche Semantik |
| [`AI_AUTONOMY_GO_NO_GO_OVERVIEW.md`](AI_AUTONOMY_GO_NO_GO_OVERVIEW.md) | AI-Autonomie Guardrails |
| [`feature_state_map_v1.md`](feature_state_map_v1.md) | Feature-Klassifikation A–D |

---

## 5. Wichtigste Runtime-Dokumente

| Dokument | Rolle |
|----------|-------|
| [`PEAK_TRADE_CANONICAL_RUNTIME_TRUTH_MAP_V1.md`](PEAK_TRADE_CANONICAL_RUNTIME_TRUTH_MAP_V1.md) | Canonical Runtime Ist-Zustand (CURRENT_RUNTIME_TRUTH; non-authorizing) |
| [`PEAK_TRADE_DEFERRED_WORK_RECOVERY_REGISTER_V1.md`](PEAK_TRADE_DEFERRED_WORK_RECOVERY_REGISTER_V1.md) | Deferred-Work Recovery Register (Capability 0.4; Rotation-Policy Wiedervorlage; non-activating) |
| [`docs/ops/specs/REAL_MARKET_247_RUNTIME_ARCHITECTURE_V1.md`](../ops/specs/REAL_MARKET_247_RUNTIME_ARCHITECTURE_V1.md) | Runtime-Architektur |
| [`docs/runbooks/canonical/PEAK_TRADE_CANONICAL_RUNTIME_OPERATIONS_DASHBOARD_AND_PROCESS_SUPERVISION_RUNBOOK_V2_4.md`](../runbooks/canonical/PEAK_TRADE_CANONICAL_RUNTIME_OPERATIONS_DASHBOARD_AND_PROCESS_SUPERVISION_RUNBOOK_V2_4.md) | Canonical Runtime Operations / Dashboard / Process Supervision V2.4 (`DERIVED_DOMAIN_AUTHORITY_ONLY`; **nicht** SSOT; Master Runbook bleibt einzige SSOT mit absoluter Precedence; Manifest: [`…_V2_4_RATIFICATION.json`](../runbooks/canonical/PEAK_TRADE_CANONICAL_RUNTIME_OPERATIONS_DASHBOARD_AND_PROCESS_SUPERVISION_RUNBOOK_V2_4_RATIFICATION.json); **kein** Runtime-/Trading-/Testnet-/Live-/Order-/Credential-Authorization-Effekt) |
| [`docs/ops/runbooks/README.md`](../ops/runbooks/README.md) | Ops-Runbooks-Index |
| [`docs/ops/RUNBOOK_INDEX.md`](../ops/RUNBOOK_INDEX.md) | Runbook-Index |
| [`docs/ops/README.md`](../ops/README.md) | Ops Operator Center |
| [`docs/LIVE_OPERATIONAL_RUNBOOKS.md`](../LIVE_OPERATIONAL_RUNBOOKS.md) | Live-Ops-Übersicht (non-authorizing) |
| [`docs/architecture/TREND_FOLLOWING_V2_CANONICAL_WIRING.md`](../architecture/TREND_FOLLOWING_V2_CANONICAL_WIRING.md) | Canonical Wiring-Hinweis (keine zweite Trading-SSOT) |
| [`docs/architecture/canonical/PEAK_TRADE_CANONICAL_END_STATE_WIRING_MAP.md`](../architecture/canonical/PEAK_TRADE_CANONICAL_END_STATE_WIRING_MAP.md) | Canonical End-State Wiring Map (derived; `RUNTIME_AUTHORITY_EFFECT=NONE`; keine zweite Trading-SSOT) |
| [`docs/ops/specs/FULL_CORE_LIVE_PATH_COMPOSITION_ROOT_V1.md`](../ops/specs/FULL_CORE_LIVE_PATH_COMPOSITION_ROOT_V1.md) | Navigation-only Core→Live composition-root spec (non-SSOT; offline halt-before-wire; canary venue-proof remains distinct; no Live GET/POST) |
| [`docs/ops/specs/FULL_CORE_LIVE_PATH_IDENTITY_AND_ADMISSION_GAP_V1.md`](../ops/specs/FULL_CORE_LIVE_PATH_IDENTITY_AND_ADMISSION_GAP_V1.md) | Navigation-only Full-Core path-identity and live-admission gap DAG spec (non-SSOT; `FUTURE_PRODUCTIVE_LIVE_EXECUTION_PATH=FULL_CORE_LIVE_PATH`; canary / §11.14 not a second productive Live authority; no GET; no POST) |
| [`docs/ops/specs/PRE_LIVE_CAPITAL_ADMISSION_CONTRACT_V1.md`](../ops/specs/PRE_LIVE_CAPITAL_ADMISSION_CONTRACT_V1.md) | Navigation-only Pre-Live Capital Admission spec (non-SSOT; typed admission seam; Treasury HTTP isolation preserved; no GET; no POST) |

---

## 6. Wichtigste Safety-Dokumente

| Dokument | Rolle |
|----------|-------|
| [`docs/GOVERNANCE_AND_SAFETY_OVERVIEW.md`](../GOVERNANCE_AND_SAFETY_OVERVIEW.md) | Safety-/Governance-Übersicht |
| [`docs/SAFETY_POLICY_TESTNET_AND_LIVE.md`](../SAFETY_POLICY_TESTNET_AND_LIVE.md) | Testnet-/Live-Safety-Policy |
| [`docs/risk/KILL_SWITCH_ARCHITECTURE.md`](../risk/KILL_SWITCH_ARCHITECTURE.md) | Kill-Switch-Architektur |
| [`docs/ops/KILL_SWITCH_RUNBOOK.md`](../ops/KILL_SWITCH_RUNBOOK.md) | Kill-Switch-Betrieb |
| [`docs/ops/runbooks/CANARY_LIVE_ENTRY_CRITERIA.md`](../ops/runbooks/CANARY_LIVE_ENTRY_CRITERIA.md) | Canary-Entry-Kriterien (non-authorizing) |
| [`docs/PEAK_TRADE_V1_KNOWN_LIMITATIONS.md`](../PEAK_TRADE_V1_KNOWN_LIMITATIONS.md) | Bekannte Grenzen |

---

## 7. Wichtigste Trading-Logik-Dokumente

Normative Semantik: **nur** das Canonical Master Runbook (`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`). Historisch: v4.4.12 (SUPERSEDED).

Ergänzende Owner-/Wiring-Hinweise (keine parallele Trading-SSOT):

| Dokument | Rolle |
|----------|-------|
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) | Master-V2 / Double-Play / Scope / Entry-Exit-Reversal (aktuell) |
| [`Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md`](Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md) | Historische Vorgängerreferenz (SUPERSEDED) |
| [`Peak_Trade_Canonical_Chain_Wiring_Repair_Master_Runbook_v2.2.md`](Peak_Trade_Canonical_Chain_Wiring_Repair_Master_Runbook_v2.2.md) | Chain-Wiring-Repair-Vertrag |
| [`STRATEGY_SIGNAL_CANONICAL_ARCHITECTURE_RATIFICATION_CLOSEOUT_V1.md`](STRATEGY_SIGNAL_CANONICAL_ARCHITECTURE_RATIFICATION_CLOSEOUT_V1.md) | Negative Architecture Ratification |
| [`docs/ops/specs/MASTER_V2_DECISION_AUTHORITY_MAP_V1.md`](../ops/specs/MASTER_V2_DECISION_AUTHORITY_MAP_V1.md) | Decision-Authority-Map (`NAVIGATION_ONLY`; not selection authority; 2026-06-15 Universe Selection row is HISTORICAL_TRUE / pre-Cap-2.3; current Selection Owner = Cap 2.3) |
| [`docs/ops/specs/MASTER_V2_CAPABILITY_2_1_GOVERNED_FUTURES_UNIVERSE_PRODUCER_V1.md`](../ops/specs/MASTER_V2_CAPABILITY_2_1_GOVERNED_FUTURES_UNIVERSE_PRODUCER_V1.md) | Cap 2.1 GFU (`UNIVERSE_MEMBERSHIP_INPUT_AUTHORITY`; not selection) |
| [`docs/ops/specs/MASTER_V2_CAPABILITY_2_2_PRODUCTIVE_FUTURES_RANKING_PRODUCER_V1.md`](../ops/specs/MASTER_V2_CAPABILITY_2_2_PRODUCTIVE_FUTURES_RANKING_PRODUCER_V1.md) | Cap 2.2 ranking (`CANDIDATE_CONTEXT_ONLY`; not selection) |
| [`docs/ops/specs/MASTER_V2_CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1.md`](../ops/specs/MASTER_V2_CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1.md) | Cap 2.3 sole Selection Owner (`SELECTION_AUTHORITY_OWNER_SINGLE`; `ACTIVATED=false`) |
| [`docs/ops/specs/MASTER_V2_CAPABILITY_2_4_SINGLE_SELECTED_FUTURE_RUNTIME_BINDING_V1.md`](../ops/specs/MASTER_V2_CAPABILITY_2_4_SINGLE_SELECTED_FUTURE_RUNTIME_BINDING_V1.md) | Cap 2.4 runtime binding consumer (`CAP24_ROLE=RUNTIME_BINDING_CONSUMER`; does not own selection) |
| [`docs/ops/specs/PEAK_TRADE_POST_RESTORATION_BASELINE_PRESERVATION_AND_COMPATIBILITY_CONTRACT_V1.md`](../ops/specs/PEAK_TRADE_POST_RESTORATION_BASELINE_PRESERVATION_AND_COMPATIBILITY_CONTRACT_V1.md) | Post-Restoration Preservation / Compatibility (navigation only) |
| [`docs/ops/specs/PEAK_TRADE_POST_RESTORATION_PARALLEL_OWNER_AND_SKIP_SAFETY_PATH_QUARANTINE_V1.md`](../ops/specs/PEAK_TRADE_POST_RESTORATION_PARALLEL_OWNER_AND_SKIP_SAFETY_PATH_QUARANTINE_V1.md) | Post-Restoration Parallel-Owner / Skip-Safety Quarantine (navigation only) |
| [`docs/ops/specs/PEAK_TRADE_POST_RESTORATION_REMAINING_P0_QUARANTINE_V1.md`](../ops/specs/PEAK_TRADE_POST_RESTORATION_REMAINING_P0_QUARANTINE_V1.md) | Post-Restoration Remaining P0 Quarantine (navigation only) |
| [`docs/ops/specs/PEAK_TRADE_POST_RESTORATION_ACCOUNTING_PORTFOLIO_ALIGNMENT_ADJUDICATION_V1.md`](../ops/specs/PEAK_TRADE_POST_RESTORATION_ACCOUNTING_PORTFOLIO_ALIGNMENT_ADJUDICATION_V1.md) | Post-Restoration Accounting / Portfolio Alignment Adjudication (navigation only) |
| [`docs/ops/specs/PEAK_TRADE_POST_RESTORATION_SIMULATED_EXECUTION_PIPELINE_ADJUDICATION_V1.md`](../ops/specs/PEAK_TRADE_POST_RESTORATION_SIMULATED_EXECUTION_PIPELINE_ADJUDICATION_V1.md) | Post-Restoration Simulated Execution Pipeline Adjudication (navigation only) |
| [`docs/ops/specs/PEAK_TRADE_POST_RESTORATION_LIVE_SAFETY_GATES_ADJUDICATION_V1.md`](../ops/specs/PEAK_TRADE_POST_RESTORATION_LIVE_SAFETY_GATES_ADJUDICATION_V1.md) | Post-Restoration Live Safety Gates Adjudication (navigation only) |
| [`docs/ops/specs/PEAK_TRADE_POST_RESTORATION_VENUE_PRETRADE_LIMIT_GATES_ADJUDICATION_V1.md`](../ops/specs/PEAK_TRADE_POST_RESTORATION_VENUE_PRETRADE_LIMIT_GATES_ADJUDICATION_V1.md) | Post-Restoration Venue Pretrade Limit Gates Adjudication (navigation only) |
| [`docs/ops/specs/PEAK_TRADE_POST_RESTORATION_VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_ADJUDICATION_V1.md`](../ops/specs/PEAK_TRADE_POST_RESTORATION_VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_ADJUDICATION_V1.md) | Post-Restoration Venue Pretrade Metadata Binding Alignment Adjudication (navigation only) |
| [`docs/ops/specs/PEAK_TRADE_EXACT_VENUE_METADATA_GET_CURRENT_SUI_PRETRADE_MAX_SIZE_V1.md`](../ops/specs/PEAK_TRADE_EXACT_VENUE_METADATA_GET_CURRENT_SUI_PRETRADE_MAX_SIZE_V1.md) | Exact Venue Metadata GET Current SUI Pretrade MAX_SIZE (navigation only) |
| [`docs/ops/specs/PEAK_TRADE_POST_6148_MAX_SIZE_UNIT_ADJUDICATION_V1.md`](../ops/specs/PEAK_TRADE_POST_6148_MAX_SIZE_UNIT_ADJUDICATION_V1.md) | Post-6148 MAX_SIZE Unit Adjudication (navigation only) |
| [`docs/ops/specs/PEAK_TRADE_POST_6149_MAX_SIZE_NORMALIZATION_ADJUDICATION_V1.md`](../ops/specs/PEAK_TRADE_POST_6149_MAX_SIZE_NORMALIZATION_ADJUDICATION_V1.md) | Post-6149 MAX_SIZE Normalization Adjudication (navigation only) |
| [`docs/ops/specs/PEAK_TRADE_ORDER_PLAN_TYPED_CONTRACT_COUNT_DOMAIN_CLOSURE_V1.md`](../ops/specs/PEAK_TRADE_ORDER_PLAN_TYPED_CONTRACT_COUNT_DOMAIN_CLOSURE_V1.md) | Order Plan Typed Contract Count Domain Closure (navigation only) |
| [`docs/ops/specs/PEAK_TRADE_MAX_SIZE_FRESHNESS_OWNER_POLICY_DECISION_V1.md`](../ops/specs/PEAK_TRADE_MAX_SIZE_FRESHNESS_OWNER_POLICY_DECISION_V1.md) | MAX_SIZE Freshness Owner Policy Decision (navigation only) |
| [`docs/ops/specs/PEAK_TRADE_MAX_SIZE_FRESH_OBSERVATION_AND_CONSUMER_WIRING_V1.md`](../ops/specs/PEAK_TRADE_MAX_SIZE_FRESH_OBSERVATION_AND_CONSUMER_WIRING_V1.md) | MAX_SIZE Fresh Observation and Consumer Wiring (navigation only) |
| [`docs/ops/specs/PEAK_TRADE_MAX_AVAILABLE_OWNER_POLICY_ADJUDICATION_AND_CLOSURE_V1.md`](../ops/specs/PEAK_TRADE_MAX_AVAILABLE_OWNER_POLICY_ADJUDICATION_AND_CLOSURE_V1.md) | MAX_AVAILABLE Owner Policy Adjudication and Closure (navigation only) |
| [`docs/ops/specs/PEAK_TRADE_PRICE_BAND_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1.md`](../ops/specs/PEAK_TRADE_PRICE_BAND_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1.md) | PRICE_BAND Forensic Binding Implementation and Closure (navigation only) |
| [`docs/ops/specs/PEAK_TRADE_LEVERAGE_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1.md`](../ops/specs/PEAK_TRADE_LEVERAGE_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1.md) | LEVERAGE Forensic Binding Implementation and Closure (navigation only) |
| [`docs/ops/specs/PEAK_TRADE_POS_MODE_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1.md`](../ops/specs/PEAK_TRADE_POS_MODE_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1.md) | POS_MODE Forensic Binding Implementation and Closure (navigation only) |
| [`docs/ops/specs/PEAK_TRADE_MARGIN_MODE_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1.md`](../ops/specs/PEAK_TRADE_MARGIN_MODE_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1.md) | MARGIN_MODE Forensic Binding Implementation and Closure (navigation only) |
| [`docs/ops/specs/PEAK_TRADE_AVAILABLE_MARGIN_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1.md`](../ops/specs/PEAK_TRADE_AVAILABLE_MARGIN_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1.md) | AVAILABLE_MARGIN Forensic Binding Implementation and Closure (navigation only) |
| [`docs/ops/specs/PEAK_TRADE_INSTRUMENT_STATE_FORENSIC_BINDING_AND_CLOSURE_V1.md`](../ops/specs/PEAK_TRADE_INSTRUMENT_STATE_FORENSIC_BINDING_AND_CLOSURE_V1.md) | INSTRUMENT_STATE Forensic Binding and Closure (navigation only) |
| [`docs/ops/specs/PEAK_TRADE_ACCOUNT_MODE_FORENSIC_BINDING_AND_CLOSURE_V1.md`](../ops/specs/PEAK_TRADE_ACCOUNT_MODE_FORENSIC_BINDING_AND_CLOSURE_V1.md) | ACCOUNT_MODE Forensic Binding and Closure (navigation only) |
| [`docs/ops/specs/PEAK_TRADE_VENUE_PRETRADE_LIMIT_GATES_FORENSIC_BINDING_AND_CLOSURE_V1.md`](../ops/specs/PEAK_TRADE_VENUE_PRETRADE_LIMIT_GATES_FORENSIC_BINDING_AND_CLOSURE_V1.md) | VENUE_PRETRADE_LIMIT_GATES Forensic Binding and Closure (navigation only) |
| [`docs/ops/specs/PEAK_TRADE_CANARY_SUBMIT_AUTHORIZATION_CONTRACT_V1.md`](../ops/specs/PEAK_TRADE_CANARY_SUBMIT_AUTHORIZATION_CONTRACT_V1.md) | CANARY_SUBMIT_AUTHORIZATION Contract (navigation only) |
| [`docs/ops/specs/PEAK_TRADE_BIND_CURRENT_SUI_L4_FAIL_CLOSED_MAX_AVAILABLE_ZERO_END_STATE_NO_REPAIR_V1.md`](../ops/specs/PEAK_TRADE_BIND_CURRENT_SUI_L4_FAIL_CLOSED_MAX_AVAILABLE_ZERO_END_STATE_NO_REPAIR_V1.md) | Current-SUI L4 fail-closed MAX_AVAILABLE zero end-state bind (navigation only; no repair) |
| [`docs/ops/specs/MODEL_C_DYNAMIC_SCOPE_DERIVED_SWITCH_EVENT_THRESHOLDS_CONTRACT_V1.md`](../ops/specs/MODEL_C_DYNAMIC_SCOPE_DERIVED_SWITCH_EVENT_THRESHOLDS_CONTRACT_V1.md) | MODEL_C docs-only target: derive switch-event distances from Dynamic Scope SSOT (formula recorded docs-only, not runtime-bound; non-authorizing; MODEL_B remains productive baseline; navigation only) |
| [`docs/ops/specs/MODEL_C_FORMULA_AND_POLICY_ADJUDICATION_V1.md`](../ops/specs/MODEL_C_FORMULA_AND_POLICY_ADJUDICATION_V1.md) | MODEL_C formula and policy adjudication (OQ-C1..C6 docs-only; runtime bind unauthorized; freeze exception unauthorized; MODEL_B remains productive baseline; navigation only) |
| [`docs/ops/specs/MODEL_C_UP_DISTANCE_SWITCH_VS_PROFIT_PROTECTION_AUTHORITY_SPLIT_V1.md`](../ops/specs/MODEL_C_UP_DISTANCE_SWITCH_VS_PROFIT_PROTECTION_AUTHORITY_SPLIT_V1.md) | MODEL_C dual-use identity split: Cap 6.5 profit-protection `200.0` is not Cap 6.3 switch-event `up_distance` (numeric coincidence preserved; navigation only) |
| [`docs/ops/specs/DIRECTIONAL_MAPPING_CONTRACT_REPAIR_V1.md`](../ops/specs/DIRECTIONAL_MAPPING_CONTRACT_REPAIR_V1.md) | Directional mapping core contract (runtime-bound for SHORT reversal polarity + PENDING departing-side generator orientation; Wallclock/Hardening Entry/Exit cursor consumes Replay mapping owner after §14 / §11.2.1.H; PENDING rows not re-adjudicated; freeze exception unauthorized; MODEL_C runtime unauthorized; no last_active_side; navigation only) |

---

## 8.0 Phase 11 §11.12.8 bounded campaign evidence (navigation only)

| Pfad | Rolle |
|------|-------|
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.8.2 | SSOT forensic campaign-run status |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.8.3 | SSOT OKX EEA Demo BTC-USDT-SWAP productive-order path closeout (`CLOSED_DEPRECATED_HISTORICAL_EVIDENCE_ONLY`) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.8.4 | SSOT historical OKX Global Demo binding package (NO_ORDER; not activated; superseded by §11.12.8.5) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.8.5 | SSOT active OKX EEA Demo XPerp binding package (NO_ORDER package default; write path in §11.12.8.6) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.8.6 | SSOT OKX EEA Demo XPerp ephemeral campaign private-write path (armable; no auto-execute) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.8.7 | SSOT OKX EEA Demo XPerp bounded campaign forensic closeout package (no section close; superseded next-step by §11.12.8.8) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.8.8 | SSOT OKX EEA Demo XPerp clOrdId alphanumeric fix + bounded ACK proof (no section close; superseded next-step by §11.12.8.9) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.8.9 | SSOT OKX EEA Demo XPerp cancel-instId fix + bounded clean closeout proof (closeout recommended; superseded next-step by §11.12.8.10) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.8.10 | SSOT OKX EEA Demo XPerp §11.12.8 Owner closeout package (`SECTION_11_12_8_CLOSED=true`; Cap 11.12 Testnet progression program not closed) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.9 | SSOT Pre-Live Cybersecurity Acceptance Gate contract (mandatory; gate `NOT_PASSED`) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.9.1 | SSOT evidence-bound Pre-Live gate evaluation (`SECTION_11_12_9_EVALUATION_COMPLETED=true`; gate remains `NOT_PASSED`) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.9.2 | SSOT Cap 11.12 Testnet progression program nomenclature reconcile (docs-only; legacy tokens aliased&#47;retired) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.9.3 | SSOT Cap 11.12 Testnet progression residual proof §11.12.1 (fixture bind; no order&#47;network) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.9.4 | SSOT Cap 11.12 Testnet progression residual proof §11.12.2 (fixture dry-run bind; no order&#47;network) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.9.5 | SSOT Cap 11.12 Testnet progression residual proof §11.12.3 (fixture lifecycle bind; no order&#47;network) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.9.6 | SSOT Cap 11.12 Testnet progression residual proof §11.12.4 (fixture lifecycle bind; no order&#47;network) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.9.7 | SSOT Cap 11.12 Testnet progression residual proof §11.12.5 (fixture recovery bind; no order&#47;network) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.9.8 | SSOT Cap 11.12 Testnet progression residual proof §11.12.6 (fixture restart bind; no order&#47;network) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.9.9 | SSOT Cap 11.12 Testnet progression residual proof §11.12.7 (fixture kill-switch bind; no order&#47;network) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.9.10 | SSOT Cap 11.12 Testnet progression residual proof §11.12.8 (fixture campaign-evidence bind; no order&#47;network) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.9.11 | SSOT Cap 11.12 OPEN_TESTNET_PROVEN_FIELDS reporting reconcile residual (no proven-field closure; no order&#47;network) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.9.12 | SSOT Cap 11.12 productive `TESTNET_ORDER_LIFECYCLE_PROVEN` (bounded Demo XPerp lifecycle; hard stop) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.9.13 | SSOT Cap 11.12 productive `TESTNET_RECONCILIATION_PROVEN` (Demo XPerp account&#47;order snapshot vs local; `ORDER_EFFECT=NONE`; hard stop) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.9.14 | SSOT Cap 11.12 productive `TESTNET_RESTART_PROVEN` (Demo XPerp restart with open order + open position; hard stop) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.9.15 | SSOT Cap 11.12 productive `TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN` (Demo XPerp unknown-submit query-before-retry + reconnect; hard stop) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.9.16 | SSOT Cap 11.12 productive `TESTNET_DUPLICATE_ORDER_PREVENTION_PROVEN` (Demo XPerp duplicate&#47;replay&#47;retry client_order_id prevention; hard stop) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.9.17 | SSOT Cap 11.12 productive `TESTNET_KILL_SWITCH_PROVEN` (Demo XPerp kill-switch&#47;emergency-control trip&#47;halt&#47;cancel-all; hard stop) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.9.18 | SSOT Cap 11.12 productive `TESTNET_AUTONOMOUS_RECOVERY_PROVEN` (Demo XPerp autonomous recovery&#47;degradation; hard stop) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.9.19 | SSOT Cap 11.12 productive `TESTNET_EVIDENCE_VERIFIED` (independent sealed-chain verifier; Cap program closed; hard stop; Pre-Live&#47;§11.13 not started) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.9.20 | SSOT Pre-Live Cybersecurity Gate post Cap 11.12 close re-evaluation (`TESTNET_LIFECYCLE_PROVEN` bound; gate remains `NOT_PASSED`; hard stop) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.9.21 | SSOT LONG_RUNNING_TESTNET_PROVEN prep/eval package (pre-run; `PROVEN=false`; §11.12.8 not reopened; separate EXECUTE GO required) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.9.22 | SSOT Pre-Live Cybersecurity Gate post-LONG_RUNNING re-evaluation (`LONG_RUNNING_TESTNET_PROVEN=true` bound; gate remains `NOT_PASSED`; hard stop) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.9.23 | SSOT Pre-Live Cybersecurity Architecture Review (`CYBERSECURITY_ARCHITECTURE_REVIEW=PASS`; gate remains `NOT_PASSED`; hard stop) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.9.24 | SSOT Pre-Live Threat Model Current (`THREAT_MODEL_CURRENT=true`; gate remains `NOT_PASSED`; hard stop) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.9.25 | SSOT Pre-Live Secrets Review (`SECRETS_REVIEW=PASS`; gate remains `NOT_PASSED`; hard stop) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.9.26 | SSOT Pre-Live Dependency Audit (`DEPENDENCY_AUDIT=FAIL`; `DEPENDENCY_AUDIT_PROVEN=false`; gate remains `NOT_PASSED`; hard stop) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.9.27 | SSOT post-Dependency-Audit forensic gap &#47; remediation review (review-only; `FULL_SECURITY_COVERAGE_REVIEW_PROVEN=false`; PR `#5862` `MERGED`; gate remains `NOT_PASSED`; hard stop) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.9.28 | SSOT Dependency Audit RB-01&#47;RB-02 remediation + re-run (`DEPENDENCY_AUDIT=PASS`; `DEPENDENCY_AUDIT_PROVEN=true`; gate remains `NOT_PASSED`; hard stop) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.9.29 | SSOT Pre-Live SBOM_PRESENT (`SBOM_PRESENT=true`; gate remains `NOT_PASSED`; hard stop) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.9.30 | SSOT Pre-Live Static Security Analysis (`STATIC_SECURITY_ANALYSIS=FAIL`; `STATIC_SECURITY_ANALYSIS_PROVEN=false`; `HIGH_FINDINGS_OPEN=5`; gate remains `NOT_PASSED`; hard stop) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.9.31 | SSOT Static Security Analysis HIGH remediation + re-run (`STATIC_SECURITY_ANALYSIS=PASS`; `STATIC_SECURITY_ANALYSIS_PROVEN=true`; `HIGH_FINDINGS_OPEN=0`; gate remains `NOT_PASSED`; hard stop) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.9.32 | SSOT Pre-Live Security Regression (`SECURITY_REGRESSION=PASS`; gate remains `NOT_PASSED`; hard stop) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.9.33 | SSOT Pre-Live Penetration Program (`PENETRATION_PROGRAM=PASS`; gate remains `NOT_PASSED`; hard stop) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.12.9.34 | SSOT Pre-Live Credential Leakage Test (`CREDENTIAL_LEAKAGE_TEST=PASS`; gate remains `NOT_PASSED`; hard stop) |
| [`docs/ops/specs/CAPABILITY_11_LONG_RUNNING_TESTNET_PROVEN_PREP_EVAL_V1.md`](../ops/specs/CAPABILITY_11_LONG_RUNNING_TESTNET_PROVEN_PREP_EVAL_V1.md) | Capability spec for LONG_RUNNING_TESTNET_PROVEN prep/eval (no execute) |
| [`docs/ops/specs/CAPABILITY_11_SECTION_11_12_8_OKX_EEA_DEMO_XPERP_VENUE_HOST_ACCOUNT_INSTRUMENT_BINDING_V1.md`](../ops/specs/CAPABILITY_11_SECTION_11_12_8_OKX_EEA_DEMO_XPERP_VENUE_HOST_ACCOUNT_INSTRUMENT_BINDING_V1.md) | Capability spec for active EEA Demo XPerp binding |
| [`docs/ops/specs/CAPABILITY_11_SECTION_11_12_8_OKX_EEA_DEMO_XPERP_CAMPAIGN_PRIVATE_WRITE_GATE_V1.md`](../ops/specs/CAPABILITY_11_SECTION_11_12_8_OKX_EEA_DEMO_XPERP_CAMPAIGN_PRIVATE_WRITE_GATE_V1.md) | Capability spec for ephemeral XPerp campaign private-write gate |
| [`docs/ops/specs/CAPABILITY_11_SECTION_11_12_8_OKX_GLOBAL_DEMO_VENUE_HOST_ACCOUNT_INSTRUMENT_BINDING_V1.md`](../ops/specs/CAPABILITY_11_SECTION_11_12_8_OKX_GLOBAL_DEMO_VENUE_HOST_ACCOUNT_INSTRUMENT_BINDING_V1.md) | Historical Global Demo binding capability (not active) |
| [`evidence/ops/section_11_12_8_bounded_long_running_productive_testnet_campaign_now/20260808T181528Z/`](../../evidence/ops/section_11_12_8_bounded_long_running_productive_testnet_campaign_now/20260808T181528Z/) | Historical primary sealed run evidence (immutable; HTTP 403 era) |
| [`…&#47;20260808T181528Z&#47;derived_forensic_closeout_v1&#47;`](../../evidence/ops/section_11_12_8_bounded_long_running_productive_testnet_campaign_now/20260808T181528Z/derived_forensic_closeout_v1/) | Derived HTTP-403 forensic closeout (non-SSOT) |
| [`evidence&#47;ops&#47;section_11_12_8_bounded_okx_eea_demo_xperp_campaign_execute_v1&#47;20260810T181703Z&#47;`](../../evidence/ops/section_11_12_8_bounded_okx_eea_demo_xperp_campaign_execute_v1/20260810T181703Z/) | Primary sealed OKX EEA Demo XPerp bounded campaign evidence (immutable) |
| [`…&#47;20260810T181703Z&#47;derived_forensic_closeout_v1&#47;`](../../evidence/ops/section_11_12_8_bounded_okx_eea_demo_xperp_campaign_execute_v1/20260810T181703Z/derived_forensic_closeout_v1/) | Derived XPerp campaign forensic closeout (clOrdId 51000; non-SSOT) |
| [`evidence&#47;ops&#47;section_11_12_8_retry_bounded_okx_eea_demo_xperp_ack_proof_after_clordid_fix_v1&#47;20260810T194806Z&#47;`](../../evidence/ops/section_11_12_8_retry_bounded_okx_eea_demo_xperp_ack_proof_after_clordid_fix_v1/20260810T194806Z/) | Bounded XPerp ACK proof after alphanumeric clOrdId fix (immutable evidence; non-SSOT) |
| [`evidence&#47;ops&#47;section_11_12_8_retry_bounded_okx_eea_demo_xperp_clean_closeout_after_cancel_instid_fix_v1&#47;20260810T200151Z&#47;`](../../evidence/ops/section_11_12_8_retry_bounded_okx_eea_demo_xperp_clean_closeout_after_cancel_instid_fix_v1/20260810T200151Z/) | Bounded XPerp clean closeout after cancel-instId fix (immutable evidence; non-SSOT) |
| [`evidence&#47;ops&#47;section_11_12_8_closeout_package_v1&#47;20260810T201332Z&#47;`](../../evidence/ops/section_11_12_8_closeout_package_v1/20260810T201332Z/) | Owner §11.12.8 closeout package (derived; non-SSOT; section closed) |
| [`evidence&#47;ops&#47;section_11_12_9_pre_live_cybersecurity_acceptance_gate_evidence_bound_evaluation_v1&#47;20260810T202800Z&#47;`](../../evidence/ops/section_11_12_9_pre_live_cybersecurity_acceptance_gate_evidence_bound_evaluation_v1/20260810T202800Z/) | Owner §11.12.9.1 Pre-Live Cybersecurity Acceptance Gate evidence-bound evaluation (derived; non-SSOT; historical; superseded as current acceptance matrix by §11.12.9.20; gate remains `NOT_PASSED`) |
| [`evidence&#47;ops&#47;section_11_12_9_20_pre_live_cybersecurity_gate_post_cap_11_12_close_reevaluation_v1&#47;20260811T001530Z&#47;`](../../evidence/ops/section_11_12_9_20_pre_live_cybersecurity_gate_post_cap_11_12_close_reevaluation_v1/20260811T001530Z/) | Owner §11.12.9.20 Pre-Live Cybersecurity Gate post Cap 11.12 close re-evaluation (derived; non-SSOT; `TESTNET_LIFECYCLE_PROVEN` bound; gate remains `NOT_PASSED`) |
| [`docs&#47;evidence&#47;capability_11_long_running_testnet_proven_prep_eval_v1&#47;`](../../docs/evidence/capability_11_long_running_testnet_proven_prep_eval_v1/) | §11.12.9.21 LONG_RUNNING_TESTNET_PROVEN prep/eval package evidence (`PROVEN=false`; no campaign execute) |
| [`evidence&#47;ops&#47;section_11_12_9_21_execute_bounded_long_running_productive_testnet_campaign_now&#47;20260811T005425Z&#47;`](../../evidence/ops/section_11_12_9_21_execute_bounded_long_running_productive_testnet_campaign_now/20260811T005425Z/) | Owner-executed bounded long-running productive Testnet campaign (sealed; `LONG_RUNNING_TESTNET_PROVEN` source) |
| [`evidence&#47;ops&#47;section_11_12_9_22_pre_live_cybersecurity_gate_post_long_running_reevaluation_v1&#47;20260811T020006Z&#47;`](../../evidence/ops/section_11_12_9_22_pre_live_cybersecurity_gate_post_long_running_reevaluation_v1/20260811T020006Z/) | Owner §11.12.9.22 Pre-Live gate post-LONG_RUNNING re-evaluation (derived; non-SSOT; gate remains `NOT_PASSED`) |
| [`evidence&#47;ops&#47;section_11_12_9_23_pre_live_cybersecurity_architecture_review_v1&#47;20260811T021353Z&#47;`](../../evidence/ops/section_11_12_9_23_pre_live_cybersecurity_architecture_review_v1/20260811T021353Z/) | Owner §11.12.9.23 Pre-Live Cybersecurity Architecture Review (derived; non-SSOT; `CYBERSECURITY_ARCHITECTURE_REVIEW=PASS`; gate remains `NOT_PASSED`) |
| [`evidence&#47;ops&#47;section_11_12_9_24_pre_live_threat_model_current_v1&#47;20260811T023114Z&#47;`](../../evidence/ops/section_11_12_9_24_pre_live_threat_model_current_v1/20260811T023114Z/) | Owner §11.12.9.24 Pre-Live Threat Model Current package (derived; non-SSOT; `THREAT_MODEL_CURRENT=true`; gate remains `NOT_PASSED`) |
| [`evidence&#47;ops&#47;section_11_12_9_25_pre_live_credential_hygiene_review_v1&#47;20260811T025933Z&#47;`](../../evidence/ops/section_11_12_9_25_pre_live_credential_hygiene_review_v1/20260811T025933Z/) | Owner §11.12.9.25 Pre-Live Secrets Review package (derived; non-SSOT; `SECRETS_REVIEW=PASS`; gate remains `NOT_PASSED`) |
| [`evidence&#47;ops&#47;section_11_12_9_26_pre_live_dependency_audit_v1&#47;20260811T031527Z&#47;`](../../evidence/ops/section_11_12_9_26_pre_live_dependency_audit_v1/20260811T031527Z/) | Owner §11.12.9.26 Pre-Live Dependency Audit package (derived; non-SSOT; `DEPENDENCY_AUDIT=FAIL`; `DEPENDENCY_AUDIT_PROVEN=false`; gate remains `NOT_PASSED`) |
| [`evidence&#47;ops&#47;section_11_12_9_26_post_dependency_audit_forensic_gap_and_remediation_review_v1&#47;20260811T033939Z&#47;`](../../evidence/ops/section_11_12_9_26_post_dependency_audit_forensic_gap_and_remediation_review_v1/20260811T033939Z/) | Owner §11.12.9.27 post-Dependency-Audit forensic gap &#47; remediation review (derived; non-SSOT; review-only; PR `#5862` `MERGED`; gate remains `NOT_PASSED`) |
| [`evidence&#47;ops&#47;section_11_12_9_27_dependency_audit_rb01_rb02_remediation_and_rerun_v1&#47;20260811T035809Z&#47;`](../../evidence/ops/section_11_12_9_27_dependency_audit_rb01_rb02_remediation_and_rerun_v1/20260811T035809Z/) | Owner §11.12.9.28 RB-01&#47;RB-02 remediation + DEPENDENCY_AUDIT re-run (derived; non-SSOT; historical evidence path name retained; `DEPENDENCY_AUDIT=PASS`; gate remains `NOT_PASSED`) |
| [`evidence&#47;ops&#47;section_11_12_9_27_pr_5862_squash_merge_closeout_v1&#47;20260811T040810Z&#47;`](../../evidence/ops/section_11_12_9_27_pr_5862_squash_merge_closeout_v1/20260811T040810Z/) | PR `#5862` squash-merge closeout (derived; non-SSOT; `PR_STATE=MERGED`; merge `6530fc9e652e9c0c3c6c77bee0cac120bdafc5d8`) |
| [`evidence&#47;ops&#47;section_11_12_9_28_pr_5863_squash_merge_closeout_v1&#47;20260811T041913Z&#47;`](../../evidence/ops/section_11_12_9_28_pr_5863_squash_merge_closeout_v1/20260811T041913Z/) | PR `#5863` squash-merge closeout (derived; non-SSOT; `PR_STATE=MERGED`; merge `b1ebe0f93d88ab22bb147c48fb27e1863b829e5e`; historical `SBOM_AUTHORIZED=false` at closeout) |
| [`evidence&#47;ops&#47;section_11_12_9_29_pre_live_sbom_present_v1&#47;20260811T042745Z&#47;`](../../evidence/ops/section_11_12_9_29_pre_live_sbom_present_v1/20260811T042745Z/) | Owner §11.12.9.29 Pre-Live SBOM_PRESENT package (derived; non-SSOT; `SBOM_PRESENT=true`; gate remains `NOT_PASSED`) |
| [`evidence&#47;ops&#47;section_11_12_9_30_pre_live_static_security_analysis_v1&#47;20260811T043159Z&#47;`](../../evidence/ops/section_11_12_9_30_pre_live_static_security_analysis_v1/20260811T043159Z/) | Owner §11.12.9.30 Pre-Live Static Security Analysis (derived; non-SSOT; `STATIC_SECURITY_ANALYSIS=FAIL`; `HIGH_FINDINGS_OPEN=5`; gate remains `NOT_PASSED`) |
| [`evidence&#47;ops&#47;section_11_12_9_31_static_security_analysis_high_remediation_and_rerun_v1&#47;20260811T043722Z&#47;`](../../evidence/ops/section_11_12_9_31_static_security_analysis_high_remediation_and_rerun_v1/20260811T043722Z/) | Owner §11.12.9.31 HIGH remediation + Bandit re-run (derived; non-SSOT; `STATIC_SECURITY_ANALYSIS=PASS`; `HIGH_FINDINGS_OPEN=0`; gate remains `NOT_PASSED`) |
| [`evidence&#47;ops&#47;section_11_12_9_32_pre_live_security_regression_v1&#47;20260811T044255Z&#47;`](../../evidence/ops/section_11_12_9_32_pre_live_security_regression_v1/20260811T044255Z/) | Owner §11.12.9.32 Pre-Live Security Regression (derived; non-SSOT; `SECURITY_REGRESSION=PASS`; gate remains `NOT_PASSED`) |
| [`evidence&#47;ops&#47;section_11_12_9_33_pre_live_penetration_program_v1&#47;20260811T044900Z&#47;`](../../evidence/ops/section_11_12_9_33_pre_live_penetration_program_v1/20260811T044900Z/) | Owner §11.12.9.33 Pre-Live Penetration Program (derived; non-SSOT; `PENETRATION_PROGRAM=PASS`; gate remains `NOT_PASSED`) |
| [`evidence&#47;ops&#47;section_11_12_9_34_pre_live_credential_leakage_test_v1&#47;20260811T045537Z&#47;`](../../evidence/ops/section_11_12_9_34_pre_live_credential_leakage_test_v1/20260811T045537Z/) | Owner §11.12.9.34 Pre-Live Credential Leakage Test (derived; non-SSOT; `CREDENTIAL_LEAKAGE_TEST=PASS`; gate remains `NOT_PASSED`) |
| [`evidence&#47;ops&#47;section_11_12_9_35_pre_live_authority_replay_test_v1&#47;20260811T050403Z&#47;`](../../evidence/ops/section_11_12_9_35_pre_live_authority_replay_test_v1/20260811T050403Z/) | Owner §11.12.9.35 Pre-Live Authority Replay Test (derived; non-SSOT; `AUTHORITY_REPLAY_TEST=PASS`; gate remains `NOT_PASSED`) |
| [`evidence&#47;ops&#47;section_11_12_9_36_pre_live_recovery_security_test_v1&#47;20260811T050823Z&#47;`](../../evidence/ops/section_11_12_9_36_pre_live_recovery_security_test_v1/20260811T050823Z/) | Owner §11.12.9.36 Pre-Live Recovery Security Test (derived; non-SSOT; `RECOVERY_SECURITY_TEST=PASS`; gate remains `NOT_PASSED`) |
| [`evidence&#47;ops&#47;section_11_12_9_37_pre_live_critical_findings_open_v1&#47;20260811T052152Z&#47;`](../../evidence/ops/section_11_12_9_37_pre_live_critical_findings_open_v1/20260811T052152Z/) | Owner §11.12.9.37 Pre-Live Critical Findings Open (derived; non-SSOT; `CRITICAL_FINDINGS_OPEN=0` proven; gate remains `NOT_PASSED`) |
| [`evidence&#47;ops&#47;section_11_12_9_38_pre_live_high_findings_open_v1&#47;20260811T052547Z&#47;`](../../evidence/ops/section_11_12_9_38_pre_live_high_findings_open_v1/20260811T052547Z/) | Owner §11.12.9.38 Pre-Live High Findings Open (derived; non-SSOT; `HIGH_FINDINGS_OPEN=0` proven; gate remains `NOT_PASSED`) |
| [`evidence&#47;ops&#47;section_11_12_9_39_pre_live_live_testnet_isolation_proven_v1&#47;20260811T052914Z&#47;`](../../evidence/ops/section_11_12_9_39_pre_live_live_testnet_isolation_proven_v1/20260811T052914Z/) | Owner §11.12.9.39 Pre-Live Live&#47;Testnet Isolation Proven (derived; non-SSOT; `LIVE_TESTNET_ISOLATION_PROVEN=true`; gate remains `NOT_PASSED`) |
| [`evidence&#47;ops&#47;section_11_12_9_40_pre_live_live_default_block_proven_v1&#47;20260811T053222Z&#47;`](../../evidence/ops/section_11_12_9_40_pre_live_live_default_block_proven_v1/20260811T053222Z/) | Owner §11.12.9.40 Pre-Live Live Default Block Proven (derived; non-SSOT; `LIVE_DEFAULT_BLOCK_PROVEN=true`; gate remains `NOT_PASSED`) |
| [`evidence&#47;ops&#47;section_11_12_9_41_pre_live_live_arming_fail_closed_proven_v1&#47;20260811T060013Z&#47;`](../../evidence/ops/section_11_12_9_41_pre_live_live_arming_fail_closed_proven_v1/20260811T060013Z/) | Owner §11.12.9.41 Pre-Live Live Arming Fail-Closed Proven (derived; non-SSOT; `LIVE_ARMING_FAIL_CLOSED_PROVEN=true`; gate remains `NOT_PASSED`) |
| [`evidence&#47;ops&#47;section_11_12_9_42_pre_live_audit_evidence_verified_v1&#47;20260811T125657Z&#47;`](../../evidence/ops/section_11_12_9_42_pre_live_audit_evidence_verified_v1/20260811T125657Z/) | Owner §11.12.9.42 Pre-Live Audit Evidence Verified (derived; non-SSOT; `AUDIT_EVIDENCE_VERIFIED=true`; gate remains `NOT_PASSED`) |
| [`evidence&#47;ops&#47;section_11_12_9_43_pre_live_manifest_verify_rc_v1&#47;20260811T131157Z&#47;`](../../evidence/ops/section_11_12_9_43_pre_live_manifest_verify_rc_v1/20260811T131157Z/) | Owner §11.12.9.43 Pre-Live Manifest Verify RC (derived; non-SSOT; `MANIFEST_VERIFY_RC=0` gate criterion bound; gate remains `NOT_PASSED`) |
| [`evidence&#47;ops&#47;section_11_12_9_44_pre_live_cybersecurity_gate_pass_v1&#47;20260811T133046Z&#47;`](../../evidence/ops/section_11_12_9_44_pre_live_cybersecurity_gate_pass_v1/20260811T133046Z/) | Owner §11.12.9.44 Pre-Live Cybersecurity Gate PASS (derived; non-SSOT; `PRE_LIVE_CYBERSECURITY_GATE=PASS`; `ELIGIBLE_FOR_LIVE_READINESS_EVALUATION=true`; §11.13 unstarted; Live unauthorized) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.1 | SSOT Live Readiness Evaluation (`SECTION_11_13_LIVE_READINESS_EVALUATION_COMPLETED=true`; `FULLY_AUTONOMOUS_LIVE_TRADING_READY=false`; Live unauthorized) |
| [`evidence&#47;ops&#47;section_11_13_live_readiness_evaluation_v1&#47;20260811T134610Z&#47;`](../../evidence/ops/section_11_13_live_readiness_evaluation_v1/20260811T134610Z/) | Owner §11.13.1 Live Readiness Evaluation (derived; non-SSOT; `FULLY_AUTONOMOUS_LIVE_TRADING_READY=false`; Live unauthorized; historical earliest-open pointer superseded by §11.13.2 proven) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.2 | SSOT LIVE_PRIVATE_READ_ONLY proven (`LIVE_PRIVATE_READ_ONLY_EXECUTED=true`; `LIVE_PRIVATE_READ_ONLY_PROVEN=true`; `LIVE_AUTHORIZED=false`; Cap 11.7 contracts-only; Live Shadow not started) |
| [`evidence&#47;ops&#47;section_11_13_2_live_private_read_only_proven_v1&#47;20260811T170310Z&#47;`](../../evidence/ops/section_11_13_2_live_private_read_only_proven_v1/20260811T170310Z/) | Owner §11.13.2 productive LIVE private read-only proof (derived; non-SSOT; GET-only; writes&#47;orders=0; `MANIFEST_VERIFY_RC=0`; Live unauthorized) |
| [`docs/ops/specs/SECTION_11_13_2_LIVE_PRIVATE_READ_ONLY_V1.md`](../ops/specs/SECTION_11_13_2_LIVE_PRIVATE_READ_ONLY_V1.md) | Derived §11.13.2 package spec (non-SSOT) |
| [`docs/ops/specs/SECTION_11_13_2_OWNER_EXECUTE_INPUT_CONTRACT_V1.md`](../ops/specs/SECTION_11_13_2_OWNER_EXECUTE_INPUT_CONTRACT_V1.md) | Owner execute-time input checklist (non-SSOT; no invented values) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.3 | SSOT LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION proven (`LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_EXECUTED=true`; `LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_PROVEN=true`; `LIVE_RECONCILIATION_PROVEN=false`; `LIVE_AUTHORIZED=false`; Cap 11.7 contracts-only; historical next pointer superseded by §11.13.4) |
| [`evidence&#47;ops&#47;section_11_13_3_live_shadow_with_exchange_reconciliation_proven_v1&#47;20260811T211828Z&#47;`](../../evidence/ops/section_11_13_3_live_shadow_with_exchange_reconciliation_proven_v1/20260811T211828Z/) | Owner §11.13.3 productive LIVE shadow exchange-reconciliation proof (derived; non-SSOT; GET-only; writes&#47;orders=0; `MANIFEST_VERIFY_RC=0`; layer divergences reported; Live unauthorized) |
| [`docs/ops/specs/SECTION_11_13_3_LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_V1.md`](../ops/specs/SECTION_11_13_3_LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_V1.md) | Derived §11.13.3 package spec (non-SSOT) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.4 | SSOT LIVE_DRY_RUN_ORDER_PLAN proven (`LIVE_DRY_RUN_ORDER_PLAN_EXECUTED=true`; `LIVE_DRY_RUN_ORDER_PLAN_PROVEN=true`; `ORDER_PLAN_RESULT=BLOCKED_NO_EXECUTE`; `LIVE_RECONCILIATION_PROVEN=false`; `BLOCKS_NEW_ENTRY=true`; `LIVE_AUTHORIZED=false`; Cap 11.8 fixture-only; historical-at-§11.13.4 Canary not started; historical next pointer superseded as current-state by §11.13.5.I `CANARY_FIRST_SUBMIT_ATTEMPTED=true`) |
| [`evidence&#47;ops&#47;section_11_13_4_live_dry_run_order_plan_proven_v1&#47;20260811T230805Z&#47;`](../../evidence/ops/section_11_13_4_live_dry_run_order_plan_proven_v1/20260811T230805Z/) | Owner §11.13.4 productive LIVE dry-run order-plan proof (derived; non-SSOT; GET-only; writes&#47;orders=0; `MANIFEST_VERIFY_RC=0`; plan blocked by unresolved divergence; Live unauthorized) |
| [`docs/ops/specs/SECTION_11_13_4_LIVE_DRY_RUN_ORDER_PLAN_V1.md`](../ops/specs/SECTION_11_13_4_LIVE_DRY_RUN_ORDER_PLAN_V1.md) | Derived §11.13.4 package spec (non-SSOT) |
| [`docs/ops/specs/SECTION_11_13_4_OWNER_EXECUTE_INPUT_CONTRACT_V1.md`](../ops/specs/SECTION_11_13_4_OWNER_EXECUTE_INPUT_CONTRACT_V1.md) | Owner execute-time input checklist (non-SSOT; no invented values) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5 | SSOT LIVE_CANARY_MINIMUM_EXPOSURE productive surface authoring bound (`SECTION_11_13_5_PRODUCTIVE_SURFACE_AUTHORING_BOUND=true`; `LIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED=false`; `LIVE_CANARY_MINIMUM_EXPOSURE_PROVEN=false`; `LIVE_RECONCILIATION_PROVEN=false`; `BLOCKS_NEW_ENTRY=true`; `TRADE_ATTESTATION=true`; Cap 11.9 fixture-only; Canary not executed) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5 PRODUCTIVE_FLATTEN_POST_AND_RECONCILIATION | Navigation-only predecessor flatten-POST persist (`LIVE_FLATTEN_PROVABILITY_PROVEN=false`; `EMPTY_DATA_IS_ZERO=false`; `TARGET_POSITION_ZERO_PROVEN=false`; historical next `OWNER_MERGE_GO` superseded by PR `#6252` closeout; MOT not SSOT) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5 PR_6252_MERGE_CLOSEOUT | Navigation-only predecessor post-merge closeout (`PR_6252_STATUS=SQUASH_MERGED`; `G12_STATUS=OPEN`; `TARGET_POSITION_ZERO_PROVEN=false`; `LIVE_FLATTEN_PROVABILITY_PROVEN=false`; `RECOVERY_POSITION_SEMANTICS=CASE_C_EMPTY_DATA_NOT_ZERO`; `SECTION_11_14_AUTHORIZED=false`; historical next `SEPARATE_OWNER_GO_FOR_G12_POSITION_ZERO_PROOF` superseded by delayed posId-zero conjunction contract; MOT not SSOT) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5 G12_DELAYED_POSID_ZERO_ROW_FULL_CONJUNCTION_PROOF_CONTRACT | Navigation-only predecessor additive offline G12 delayed-zero conjunction contract (`G12_STATUS` historically OPEN at that persist; delayed zero does not imply live flatten; `posId` filter does not prove related completeness; `.ops_local` not canonical; MOT not SSOT) |
| [`docs/ops/specs/G12_DELAYED_POSID_ZERO_ROW_FULL_CONJUNCTION_PROOF_CONTRACT_V1.md`](../ops/specs/G12_DELAYED_POSID_ZERO_ROW_FULL_CONJUNCTION_PROOF_CONTRACT_V1.md) | Derived delayed G12 conjunction spec (non-SSOT; historical additive evaluator; G12 closeout is the successor persist) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5 G12_CANONICAL_DELAYED_ZERO_PERSIST_AND_PENDING_RELATED_OBSERVATIONS | Navigation-only current G12 delayed-zero persist plus P7/P9 read-only observations (`G12_STATUS=CLOSED_LIVE_FLATTEN_PROVABILITY_PROVEN`; `TARGET_POSITION_ZERO_PROVEN=true` from full conjunction not P5 isolation; `LIVE_FLATTEN_PROVABILITY_PROVEN=true`; P9 `data=[]` is not target-zero; `SECTION_11_14_AUTHORIZED=false`; next `SEPARATE_OWNER_GO_FOR_SECTION_11_14_LIVE_ORDER_AND_ECONOMIC_EVIDENCE_LADDER`; MOT not SSOT) |
| [`docs/ops/specs/G12_CANONICAL_DELAYED_ZERO_PERSIST_AND_PENDING_RELATED_OBSERVATIONS_V1.md`](../ops/specs/G12_CANONICAL_DELAYED_ZERO_PERSIST_AND_PENDING_RELATED_OBSERVATIONS_V1.md) | Derived delayed-zero persist and P7/P9 observation spec (non-SSOT; no POST; no merge; §11.14 unauthorized) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.14 OFFLINE_EVIDENCE_LADDER_SURFACE | Navigation-only historical §11.14 offline surface persist (`SECTION_11_14_OFFLINE_SURFACE_BOUND=true`; `SECTION_11_14_AUTHORIZED=false`; `SECTION_11_14_COMPLETE=false`; all 12 ladder fields false at that consumed GO; successor `11.14.LIVE_EXECUTION_CODE_EXISTS_ADJUDICATION`; MOT not SSOT) |
| [`docs/ops/specs/SECTION_11_14_LIVE_ORDER_AND_ECONOMIC_EVIDENCE_LADDER_OFFLINE_SURFACE_V1.md`](../ops/specs/SECTION_11_14_LIVE_ORDER_AND_ECONOMIC_EVIDENCE_LADDER_OFFLINE_SURFACE_V1.md) | Derived historical §11.14 offline-surface spec (non-SSOT; no GET; no POST; no Live evidence; section incomplete) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.14 LIVE_EXECUTION_CODE_EXISTS_ADJUDICATION | Navigation-only historical §11.14 first-field adjudication (`LIVE_EXECUTION_CODE_EXISTS=true`; `LIVE_EXECUTION_PATH_REACHABLE=false` at that consumed GO; later observed/proven fields false; `SECTION_11_14_AUTHORIZED=false`; successor `11.14.LIVE_EXECUTION_PATH_REACHABLE_ADJUDICATION`; MOT not SSOT) |
| [`docs/ops/specs/SECTION_11_14_LIVE_EXECUTION_CODE_EXISTS_ADJUDICATION_V1.md`](../ops/specs/SECTION_11_14_LIVE_EXECUTION_CODE_EXISTS_ADJUDICATION_V1.md) | Derived historical §11.14 LIVE_EXECUTION_CODE_EXISTS adjudication spec (non-SSOT; static/offline only; no GET; no POST; path-reachable remained false under that GO) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.14 LIVE_EXECUTION_PATH_REACHABLE_ADJUDICATION | Navigation-only historical §11.14 second-field adjudication (`LIVE_EXECUTION_PATH_REACHABLE=true`; `LIVE_PRIVATE_READ_ONLY_PROVEN=false` at that consumed GO; later observed/proven fields false; `SECTION_11_14_AUTHORIZED=false`; successor `11.14.LIVE_PRIVATE_READ_ONLY_PROVEN_ADJUDICATION`; MOT not SSOT) |
| [`docs/ops/specs/SECTION_11_14_LIVE_EXECUTION_PATH_REACHABLE_ADJUDICATION_V1.md`](../ops/specs/SECTION_11_14_LIVE_EXECUTION_PATH_REACHABLE_ADJUDICATION_V1.md) | Derived historical §11.14 LIVE_EXECUTION_PATH_REACHABLE adjudication spec (non-SSOT; pre-submit reachability; conditional private GET; no POST; later fields remained false under that GO) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.14 LIVE_PRIVATE_READ_ONLY_PROVEN_ADJUDICATION | Navigation-only historical §11.14 third-field adjudication (`LIVE_PRIVATE_READ_ONLY_PROVEN=true`; `LIVE_ORDER_PLAN_OBSERVED=false` at that consumed GO; later observed/proven fields false; `SECTION_11_14_AUTHORIZED=false`; successor `11.14.LIVE_ORDER_PLAN_OBSERVED_ADJUDICATION`; MOT not SSOT) |
| [`docs/ops/specs/SECTION_11_14_LIVE_PRIVATE_READ_ONLY_PROVEN_ADJUDICATION_V1.md`](../ops/specs/SECTION_11_14_LIVE_PRIVATE_READ_ONLY_PROVEN_ADJUDICATION_V1.md) | Derived historical §11.14 LIVE_PRIVATE_READ_ONLY_PROVEN adjudication spec (non-SSOT; current config+balance private GET; no POST; later fields remained false under that GO) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.14 LIVE_ORDER_PLAN_OBSERVED_ADJUDICATION | Navigation-only historical §11.14 fourth-field adjudication (`LIVE_ORDER_PLAN_OBSERVED=true`; `LIVE_SUBMIT_ACK_OBSERVED=false`; later observed/proven fields false; `SECTION_11_14_AUTHORIZED=false`; `SECTION_11_14_COMPLETE=false`; `POST_PERFORMED=false`; successor `11.14.LIVE_SUBMIT_ACK_CONTRACT_AND_MUTATION_BOUNDARY_FORENSIC_ADJUDICATION`; MOT not SSOT) |
| [`docs/ops/specs/SECTION_11_14_LIVE_ORDER_PLAN_OBSERVED_ADJUDICATION_V1.md`](../ops/specs/SECTION_11_14_LIVE_ORDER_PLAN_OBSERVED_ADJUDICATION_V1.md) | Derived historical §11.14 LIVE_ORDER_PLAN_OBSERVED adjudication spec (non-SSOT; gated submit-path observation; no POST; later fields remain false) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.14 LIVE_SUBMIT_ACK_CONTRACT_AND_MUTATION_BOUNDARY_FORENSIC_ADJUDICATION | Navigation-only historical §11.14 ACK-contract forensic adjudication (`LIVE_SUBMIT_ACK_OBSERVED=false`; `CASE_ADJUDICATION=CASE_C_CANONICAL_SEMANTIC_GAP` at that consumed GO; `AUTHORIZED_PRODUCTIVE_SUBMIT_COUNT_MAX=1`; `RETRY_DEFAULT=false`; `SECOND_SUBMIT_DEFAULT=false`; `POST_PERFORMED=false`; successor `11.14.LIVE_SUBMIT_ACK_OBSERVED_PROOF_CRITERION`; MOT not SSOT) |
| [`docs/ops/specs/SECTION_11_14_LIVE_SUBMIT_ACK_CONTRACT_AND_MUTATION_BOUNDARY_FORENSIC_ADJUDICATION_V1.md`](../ops/specs/SECTION_11_14_LIVE_SUBMIT_ACK_CONTRACT_AND_MUTATION_BOUNDARY_FORENSIC_ADJUDICATION_V1.md) | Derived historical §11.14 LIVE_SUBMIT_ACK forensic contract spec (non-SSOT; offline only; no GET; no POST; ACK remained false; CASE_C) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.14 LIVE_SUBMIT_ACK_OBSERVED_PROOF_CRITERION | Navigation-only historical §11.14 ACK proof-criterion bind (`LIVE_SUBMIT_ACK_OBSERVED=false`; `CASE_ADJUDICATION=CASE_A_READY_FOR_EXACT_SINGLE_POST_OWNER_GO` at that consumed GO; producer and criterion bound; successor `11.14.LIVE_SUBMIT_ACK_OBSERVED_ADJUDICATION`; MOT not SSOT) |
| [`docs/ops/specs/SECTION_11_14_LIVE_SUBMIT_ACK_OBSERVED_PROOF_CRITERION_V1.md`](../ops/specs/SECTION_11_14_LIVE_SUBMIT_ACK_OBSERVED_PROOF_CRITERION_V1.md) | Derived historical §11.14 LIVE_SUBMIT_ACK_OBSERVED proof-criterion spec (non-SSOT; offline only; ACK remained false under that GO; CASE_A) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.14 LIVE_SUBMIT_ACK_OBSERVED_ADJUDICATION | Navigation-only historical §11.14 ACK observation (`LIVE_SUBMIT_ACK_OBSERVED=true`; `CASE_ADJUDICATION=CASE_LIVE_SUBMIT_ACK_OBSERVED_FILL_INELIGIBLE` at that consumed GO; one POST; no retry; `LIVE_FILL_OBSERVED=false` under that GO; `POST_PERFORMED=true`; successor `11.14.LIVE_FILL_OBSERVED_ADJUDICATION`; MOT not SSOT) |
| [`docs/ops/specs/SECTION_11_14_LIVE_SUBMIT_ACK_OBSERVED_ADJUDICATION_V1.md`](../ops/specs/SECTION_11_14_LIVE_SUBMIT_ACK_OBSERVED_ADJUDICATION_V1.md) | Derived historical §11.14 LIVE_SUBMIT_ACK_OBSERVED adjudication spec (non-SSOT; exact single live POST; ACK true; fill ineligible under that GO) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.14 LIVE_FILL_OBSERVED_ADJUDICATION | Navigation-only historical §11.14 fill observation (`LIVE_FILL_OBSERVED=true`; `CASE_ADJUDICATION=CASE_LIVE_FILL_OBSERVED_FEE_INELIGIBLE` at that consumed GO; identity-bound fills GET; no POST; `LIVE_FEE_OBSERVED=false` under that GO; successor `11.14.LIVE_FEE_OBSERVED_ADJUDICATION`; MOT not SSOT) |
| [`docs/ops/specs/SECTION_11_14_LIVE_FILL_OBSERVED_ADJUDICATION_V1.md`](../ops/specs/SECTION_11_14_LIVE_FILL_OBSERVED_ADJUDICATION_V1.md) | Derived historical §11.14 LIVE_FILL_OBSERVED adjudication spec (non-SSOT; identity-bound private fills GET; fill true; fee ineligible under that GO) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.14 LIVE_FEE_OBSERVED_ADJUDICATION | Navigation-only historical §11.14 fee observation (`LIVE_FEE_OBSERVED=true`; `CASE_ADJUDICATION=CASE_LIVE_FEE_OBSERVED_POSITION_INELIGIBLE` at that consumed GO; identity-bound fills GET; no POST; `LIVE_POSITION_RECONCILED=false` under that GO; successor `11.14.LIVE_POSITION_RECONCILED_ADJUDICATION`; MOT not SSOT) |
| [`docs/ops/specs/SECTION_11_14_LIVE_FEE_OBSERVED_ADJUDICATION_V1.md`](../ops/specs/SECTION_11_14_LIVE_FEE_OBSERVED_ADJUDICATION_V1.md) | Derived historical §11.14 LIVE_FEE_OBSERVED adjudication spec (non-SSOT; identity-bound private fills GET; fee true; position ineligible under that GO) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.14 LIVE_POSITION_RECONCILED_ADJUDICATION | Navigation-only historical §11.14 position reconciliation (`LIVE_POSITION_RECONCILED=true`; `CASE_ADJUDICATION=CASE_LIVE_POSITION_RECONCILED_ACCOUNTING_INELIGIBLE` at that consumed GO; identity-bound positions GET; no POST; `LIVE_ACCOUNTING_RECONSTRUCTED=false` under that GO; successor `11.14.LIVE_ACCOUNTING_RECONSTRUCTED_ADJUDICATION`; MOT not SSOT) |
| [`docs/ops/specs/SECTION_11_14_LIVE_POSITION_RECONCILED_ADJUDICATION_V1.md`](../ops/specs/SECTION_11_14_LIVE_POSITION_RECONCILED_ADJUDICATION_V1.md) | Derived historical §11.14 LIVE_POSITION_RECONCILED adjudication spec (non-SSOT; identity-bound private positions GET; position true; accounting ineligible under that GO) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.14 LIVE_ACCOUNTING_RECONSTRUCTED_ADJUDICATION | Navigation-only historical §11.14 accounting reconstruction (`LIVE_ACCOUNTING_RECONSTRUCTED=true`; `CASE_ADJUDICATION=CASE_LIVE_ACCOUNTING_RECONSTRUCTED_RESTART_INELIGIBLE` at that consumed GO; persisted identity-bound fill/fee/position path; no GET; no POST; `LIVE_RESTART_RECONSTRUCTED=false` under that GO; successor `11.14.LIVE_RESTART_RECONSTRUCTED_ADJUDICATION`; MOT not SSOT) |
| [`docs/ops/specs/SECTION_11_14_LIVE_ACCOUNTING_RECONSTRUCTED_ADJUDICATION_V1.md`](../ops/specs/SECTION_11_14_LIVE_ACCOUNTING_RECONSTRUCTED_ADJUDICATION_V1.md) | Derived historical §11.14 LIVE_ACCOUNTING_RECONSTRUCTED adjudication spec (non-SSOT; offline reconstruction from persisted identity-bound path; accounting true; restart ineligible under that GO) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.14 LIVE_RESTART_RECONSTRUCTED_ADJUDICATION | Navigation-only historical §11.14 restart reconstruction (`LIVE_RESTART_RECONSTRUCTED=false`; `CASE_ADJUDICATION=CASE_LIVE_RESTART_RECONSTRUCTED_FAIL_CLOSED_MISSING_DURABLE_HANDOFF` at that consumed GO; criterion bound; no durable Live pre-restart handoff; no GET; no POST; no restart execution; successor `11.14.LIVE_RESTART_RECONSTRUCTED_EXHAUSTIVE_OFFLINE_CENSUS`; MOT not SSOT) |
| [`docs/ops/specs/SECTION_11_14_LIVE_RESTART_RECONSTRUCTED_ADJUDICATION_V1.md`](../ops/specs/SECTION_11_14_LIVE_RESTART_RECONSTRUCTED_ADJUDICATION_V1.md) | Derived historical §11.14 LIVE_RESTART_RECONSTRUCTED adjudication spec (non-SSOT; offline fail-closed census; criterion bound; restart false; recovery ineligible under that GO) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.14 LIVE_RESTART_RECONSTRUCTED_EXHAUSTIVE_OFFLINE_CENSUS | Navigation-only current §11.14 restart exhaustive census (`LIVE_RESTART_RECONSTRUCTED=false`; `CASE_ADJUDICATION=CASE_LIVE_RESTART_RECONSTRUCTED_FAIL_CLOSED_MISSING_DURABLE_HANDOFF`; `CASE_B_NOT_PROVEN_CONTRACT_CLOSED=true`; no identity-bound Live durable_state; future persist-first Owner-GO specified not executed; no GET; no POST; no restart execution; `OWNER_GO_FOR_LIVE_RESTART_RECONSTRUCTED` remains §11.14 evidence-domain only and is not the productive Live-execution next pointer; MOT not SSOT) |
| [`docs/ops/specs/SECTION_11_14_LIVE_RESTART_RECONSTRUCTED_EXHAUSTIVE_OFFLINE_CENSUS_V1.md`](../ops/specs/SECTION_11_14_LIVE_RESTART_RECONSTRUCTED_EXHAUSTIVE_OFFLINE_CENSUS_V1.md) | Derived §11.14 LIVE_RESTART_RECONSTRUCTED exhaustive offline census spec (non-SSOT; criterion bound; restart false; future GO specified not executed) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.2.1 FULL_CORE_LIVE_PATH_COMPOSITION_ROOT | Navigation-only Core→Live composition persist (`FULL_CORE_LIVE_PATH_BOUND=true` offline static; `CANARY_VENUE_PROOF_PATH != FULL_CORE_LIVE_PATH`; `CURRENT_LIVE_CORE_PATH_PROVEN=false`; `FULL_CORE_SYSTEM_E2E_PROVEN=false`; hard stop before wire; MOT not SSOT) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.2.1.A EXECUTION_ADMISSION_AND_TYPED_CONTRACT_HARDENING | Navigation-only pointer to typed Full-Core admission persist (`FULL_CORE_EXECUTION_ADMISSION_BOUNDARY=halt_at_live_execution_boundary_v1`; `DURABLE_FILEGATE_RUNTIME_JOIN_IMPLEMENTED=false`; `CURRENT_CAPITAL_RISK_MODE=OFFLINE_ALGEBRA`; `FROZEN_PRETRADE_LIVE_ADMISSION_ALLOWED=false`; `LIVE_ENABLED=false`; MOT not SSOT) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.2.1.C SCOPE_DIRECTION_STATE_MODEL_2_REBUILD | Navigation-only pointer to Model 2 ScopeDirectionState rebuild persist (`SCOPE_DIRECTION_STATE_RESTART_AUTHORITY=DERIVED_NOT_PERSISTED_INDEPENDENT_TRUTH`; `CAP62_SCOPE_DIRECTION_STATE_CLASSIFICATION=REBUILD_DETERMINISTICALLY`; SideState fail-closed unchanged; MOT not SSOT) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.2.1.D SCOPE_DIRECTION_OVERLAY_GENERATOR_INERT | Navigation-only pointer to overlay generator-inert persist (`COMPOSITION_SELECTED_SIDE_MAY_WRITE_SCOPE_DIRECTION_STATE=false`; `COMPOSITION_SELECTED_SIDE_CAN_MUTATE_GENERATOR_DIRECTION=false`; `CORE_LOGIC_CHANGE=true`; SideState fail-closed unchanged; MOT not SSOT) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.2.1.E HARDENING_V2_SCOPE_DIRECTION_OVERLAY_GENERATOR_INERT | Navigation-only pointer to Hardening-v2 overlay generator-inert persist (`HARDENING_V2_OVERLAY_SYNCHRONIZED=true`; `COMPOSITION_SELECTED_SIDE_MAY_WRITE_SCOPE_DIRECTION_STATE=false`; `CORE_LOGIC_CHANGE=true`; SideState fail-closed unchanged; MOT not SSOT) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.2.1.F SCOPE_DIRECTION_GENERATOR_FALLBACK_AND_SIXTH_ECONOMIC_GUARD_ADMISSION | Navigation-only pointer to generator-fallback persist (`MASTER_V2_GENERATOR_FALLBACK_SYNCHRONIZED=true`; `COMPOSITION_SELECTED_SIDE_MAY_WRITE_SCOPE_DIRECTION_STATE=false`; sixth Economic-Guard class slice-bound; `CORE_LOGIC_CHANGE=true`; SideState fail-closed unchanged; MOT not SSOT) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.2.1.G SIDESTATE_ARMED_IDENTITY_SPLIT_AND_SEVENTH_ECONOMIC_GUARD_ADMISSION | Navigation-only pointer to SideState ARMED identity-split persist (`NEUTRAL_START_AND_SWITCH_TERMINAL_ARE_DISTINCT=true`; `HISTORY_RECONSTRUCTED=false`; `LAST_ACTIVE_SIDE_BINDING_AUTHORIZED=false`; seventh Economic-Guard class slice-bound; `CORE_LOGIC_CHANGE=true`; MOT not SSOT) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.2.1.H SIDESTATE_PENDING_ENTRY_EXIT_MAPPING_SINGLE_OWNER_MINIMUM_ATOMIC_REPAIR | Navigation-only pointer to Wallclock/Hardening Entry/Exit single-owner persist (`ENTRY_EXIT_MAPPING_OWNER=_side_state_to_entry_exit_direction`; `LOCAL_WALLCLOCK_MAPPING_AUTHORITY_REMAINING=false`; `PENDING_TARGET_REWRITE_AUTHORIZED=false`; `NEW_ECONOMIC_GUARD_CLASS_COUNT=0`; `CORE_LOGIC_CHANGE=true`; MOT not SSOT) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.2.1.I FULL_CORE_LIVE_PATH_IDENTITY_AND_ADMISSION_GAP | Navigation-only pointer to Full-Core productive Live-path identity persist (`FUTURE_PRODUCTIVE_LIVE_EXECUTION_PATH=FULL_CORE_LIVE_PATH`; `CANARY_PATH_IS_PARALLEL_PRODUCTIVE_LIVE_AUTHORITY=false`; `FULL_CORE_SYSTEM_E2E_PROVEN=false`; `EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY=DURABLE_FILEGATE_RUNTIME_JOIN_IMPLEMENTED`; no GET; no POST; MOT not SSOT) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.2.1.J FULL_CORE_DURABLE_FILEGATE_JOIN_SEAM | Navigation-only pointer to Full-Core durable FILEGATE join persist (`DURABLE_FILEGATE_RUNTIME_JOIN_IMPLEMENTED=true`; `TRUSTED_FILEGATE_DOES_NOT_ADMIT_LIVE=true`; `LIVE_ENABLED=false`; `EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY=OWNER_ONE_SHOT_TYPED_LIVE_EXECUTION_PERMIT` at that consumed GO; successor `11.2.1.K`; no GET; no POST; MOT not SSOT) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.2.1.K FULL_CORE_OWNER_ONE_SHOT_TYPED_PERMIT_SEAM | Navigation-only pointer to Full-Core typed OWNER_ONE_SHOT permit persist (`OWNER_ONE_SHOT_TYPED_LIVE_EXECUTION_PERMIT_IMPLEMENTED=true`; `VALID_PERMIT_ALONE_CAN_ADMIT=false`; `FILEGATE_CAN_BE_OVERRIDDEN_BY_PERMIT=false`; `LIVE_ENABLED=false`; `EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY=FRESH_PRETRADE_RUNTIME_GET_IMPLEMENTED` at that consumed GO; successor `11.2.1.L`; no GET; no POST; MOT not SSOT) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.2.1.L FULL_CORE_FRESH_PRETRADE_RUNTIME_GET_SEAM | Navigation-only pointer to Full-Core Fresh Pretrade Runtime GET persist (`FRESH_PRETRADE_RUNTIME_GET_IMPLEMENTED=true`; `FRESH_GET_ALONE_CAN_ADMIT=false`; `FRESH_GET_CAN_OVERRIDE_OTHER_GATES=false`; `LIVE_ENABLED=false`; `EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY=LIVE_ACCOUNT_BOUND_IMPLEMENTED` at that consumed GO; successor `11.2.1.M`; no productive venue GET; no POST; MOT not SSOT) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.2.1.M FULL_CORE_REMAINING_ADMISSION_CHAIN_CLOSEOUT | Navigation-only pointer to Full-Core remaining admission-chain closeout (`LIVE_ACCOUNT_BOUND_IMPLEMENTED=true`; `FULL_CORE_OFFLINE_E2E_PROVEN=true`; `FULL_CORE_OFFLINE_E2E_EVIDENCE_CLASS=INJECTED_NON_PRODUCTIVE`; `FULL_CORE_SYSTEM_E2E_PROVEN=false`; `CURRENT_LIVE_CORE_PATH_PROVEN=false`; `LIVE_ACCOUNT_BOUND_ALONE_CAN_ADMIT=false`; `LIVE_ENABLED=false`; `EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY=LIVE_ENABLED`; successor `11.2.1.N`; no productive venue GET; no POST; MOT not SSOT) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.2.1.N PRE_LIVE_CAPITAL_ADMISSION_CONTRACT | Navigation-only pointer to Pre-Live Capital Admission persist (`CAPITAL_ADMISSION_IMPLEMENTED=true`; `OBSERVED_CAPITAL != RISK_ADMISSIBLE_CAPITAL`; `PL_TF_001_STATUS=CLOSED_TYPED_ADMISSION_SEAM`; `PL_TF_002_STATUS=FROZEN_PENDING_NETWORK_EVIDENCE`; `TREASURY_MUTATION_REACHABLE_FROM_TRADING=false`; `LIVE_ENABLED=false`; `EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY=LIVE_ENABLED`; no GET; no POST; MOT not SSOT) |
| [`docs/ops/specs/FULL_CORE_LIVE_PATH_COMPOSITION_ROOT_V1.md`](../ops/specs/FULL_CORE_LIVE_PATH_COMPOSITION_ROOT_V1.md) | Derived Core→Live composition-root spec (non-SSOT; offline only; no GET; no POST; LiveExecutionPort remains Cap-11.1 forbidden) |
| [`docs/ops/specs/FULL_CORE_LIVE_PATH_IDENTITY_AND_ADMISSION_GAP_V1.md`](../ops/specs/FULL_CORE_LIVE_PATH_IDENTITY_AND_ADMISSION_GAP_V1.md) | Derived Full-Core path-identity and live-admission gap DAG spec (non-SSOT; canary / §11.14 evidence domain retained; not a second productive Live authority; no GET; no POST) |
| [`docs/ops/specs/FULL_CORE_DURABLE_FILEGATE_JOIN_SEAM_V1.md`](../ops/specs/FULL_CORE_DURABLE_FILEGATE_JOIN_SEAM_V1.md) | Derived Full-Core durable FILEGATE join-seam spec (non-SSOT; typed admission evidence only; trusted FILEGATE does not admit Live; no GET; no POST) |
| [`docs/ops/specs/FULL_CORE_OWNER_ONE_SHOT_TYPED_PERMIT_SEAM_V1.md`](../ops/specs/FULL_CORE_OWNER_ONE_SHOT_TYPED_PERMIT_SEAM_V1.md) | Derived Full-Core typed OWNER_ONE_SHOT permit-seam spec (non-SSOT; exact token evidence only; trusted permit does not admit Live; does not override FILEGATE; no GET; no POST) |
| [`docs/ops/specs/FULL_CORE_FRESH_PRETRADE_RUNTIME_GET_SEAM_V1.md`](../ops/specs/FULL_CORE_FRESH_PRETRADE_RUNTIME_GET_SEAM_V1.md) | Derived Full-Core Fresh Pretrade Runtime GET-seam spec (non-SSOT; typed GET evidence only; trusted GET does not admit Live; injectable GET-only port; no productive venue GET; no POST) |
| [`docs/ops/specs/FULL_CORE_REMAINING_ADMISSION_CHAIN_CLOSEOUT_V1.md`](../ops/specs/FULL_CORE_REMAINING_ADMISSION_CHAIN_CLOSEOUT_V1.md) | Derived Full-Core remaining admission-chain closeout spec (non-SSOT; typed LIVE_ACCOUNT_BOUND join; injected offline E2E is not Current-Live proof; no productive venue GET; no POST) |
| [`docs/ops/specs/PRE_LIVE_CAPITAL_ADMISSION_CONTRACT_V1.md`](../ops/specs/PRE_LIVE_CAPITAL_ADMISSION_CONTRACT_V1.md) | Derived Pre-Live Capital Admission contract spec (non-SSOT; observed capital is not risk-admissible; PL-TF-002 frozen pending network evidence; no GET; no POST) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.B | SSOT PR `#5879` squash-merge + pre-Canary readiness fail-closed (`MERGE_COMMIT_SHA=b3dadd86d…`; `PRODUCTIVE_CANARY_SURFACE_MERGED_TO_ORIGIN_MAIN=true`; `TRADE_ATTESTATION=false`; `EXCHANGE_TRUTH_ADOPTION_STATUS=OWNER_POLICIES_REQUIRED_NOT_ADOPTED`; `LIVE_CANARY_CYBERSECURITY_GATE=NOT_PASSED`; `TERMINAL_STATE=FAIL_CLOSED_PRE_CANARY_BLOCKED`; Canary not executed) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.C | SSOT LIVE canary trade-key attestation proven (`OWNER_GO_LIVE_CANARY_TRADE_KEY_ATTESTATION=CONSUMED`; `SECRETREF_STATUS=RESOLVED`; `TRADE_ATTESTATION=true`; `WITHDRAW_ATTESTATION=false`; `CANARY_TRADE_KEY_BINDING=PROVEN`; `LIVE_CANARY_CYBERSECURITY_GATE=NOT_PASSED`; `TERMINAL_STATE=TRADE_KEY_ATTESTATION_PROVEN_AWAITING_EXCHANGE_TRUTH_ADOPTION`; Canary not executed) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.D | SSOT Exchange Truth Adoption for canary path (`OWNER_GO_EXCHANGE_TRUTH_ADOPTION=CONSUMED`; `EXCHANGE_TRUTH_ADOPTION_STATUS=ADOPTED_PROVEN`; `OKX_TEMP_SECURITY_RESTRICTION=24h_no_withdrawals_and_no_p2p_sell`; `LIVE_CANARY_CYBERSECURITY_GATE=NOT_PASSED`; historical next pointer superseded by §11.13.5.E) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.E | SSOT economic baseline + OKX clearance evidence (`OWNER_GO_ECONOMIC_BASELINE_AND_OKX_CLEARANCE_EVIDENCE=CONSUMED`; `LIVE_RECONCILIATION_PROVEN=true`; `BLOCKS_NEW_ENTRY=false`; `ECONOMIC_DIVERGENCE_STATUS=RESOLVED_NO_UNRESOLVED_DIVERGENCE`; `OKX_TEMP_SECURITY_CLEARANCE_EVIDENCE=ABSENT_OR_UNPROVEN`; `LIVE_CANARY_CYBERSECURITY_GATE=NOT_PASSED`; historical next pointer superseded by §11.13.5.E1) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.E1 | SSOT fresh OKX temp-security clearance evidence (`OWNER_GO=CAP11_OKX_TEMP_SECURITY_CLEARANCE_FRESH_EVIDENCE_CANONICAL_PERSISTENCE`; `OKX_TEMP_SECURITY_CLEARANCE_EVIDENCE=PRESENT_PROVEN`; `LIVE_CANARY_CYBERSECURITY_GATE=NOT_PASSED`; `LIVE_AUTHORIZED=false`; Canary not executed; historical next pointer superseded by §11.13.5.F) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.F | SSOT Live-Canary cybersecurity-gate PASS persist (`OWNER_GO=PERSIST_LIVE_CANARY_CYBERSECURITY_GATE_PASS`; `LIVE_CANARY_CYBERSECURITY_GATE=PASS`; `FORENSIC_GATE_REQUIREMENTS=21&#47;21_PROVEN`; `LIVE_AUTHORIZED=false`; Canary not executed; historical next pointer superseded by §11.13.5.G) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.G | SSOT Live-Canary submit-transport preparation (`OWNER_GO=OWNER_GO_CANARY_SUBMIT_TRANSPORT_PREPARATION`; `CANARY_SUBMIT_TRANSPORT_IMPLEMENTED=true`; `SUBMIT_UNLOCKED=false`; `LIVE_AUTHORIZED=false`; Canary not executed; historical next pointer superseded by §11.13.5.H) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.H | SSOT Live-Canary execution-plumbing remediation (`OWNER_GO=SECTION_11_13_5_CANARY_EXECUTION_PLUMBING_REMEDIATION_PREPARATION`; `CANARY_EXECUTION_PLUMBING_REMEDIATION_PREPARED=true`; historical `AUTH_GET_50110` at H time; historical next pointer superseded by §11.13.5.I) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.I | SSOT POST-HTTP-401 bounded transport remediation + incident persistence (`OWNER_GO=SECTION_11_13_5_POST_HTTP_401_BOUNDED_REMEDIATION_PREPARATION`; PR `#5902` squash-merged `4adb0af23`; `OWNER_MERGE_GO_FOR_BOUNDED_POST_401_REMEDIATION_PR_STATUS=DONE_MERGED`; `CANARY_FIRST_SUBMIT_HTTP_STATUS=401`; `POST_401_ROOT_CAUSE=UNPROVEN_FAIL_CLOSED`; `HISTORICAL_AUTH_50110_CLEARED_AT_11_13_5_I=true`; no retry; historical next pointer superseded by §11.13.5.J) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.J | SSOT one-shot trading-POST HTTP 401 &#47; OKX 50124 observed classification (`OWNER_GO` historical token contains `MARKET_PERMISSION` but `ROOT_CAUSE_PROVEN=false`; `LATEST_50124_CLASSIFICATION=OKX_50124_OBSERVED_ONESHOT_TRADING_POST`; `HTTP_50124_INSTRUMENT_SPECIFIC_PROVEN=false`; historical first 401 remains `UNPROVEN_FAIL_CLOSED`; `account&#47;instruments` not on submit path; no retry; historical next pointer superseded by §11.13.5.K) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.K | SSOT EEA XPerp 310404 canary rebind preparation (`CURRENT_PHASE=SECTION_11_13_5_EEA_XPERP_310404_REBIND_PREPARATION`; `NEW_CANARY_INSTRUMENT=BTC-USD_UM_XPERP-310404`; `NEW_CANARY_INST_TYPE=FUTURES`; `NEW_CANARY_RULE_TYPE=xperp`; `NEW_CANARY_SETTLEMENT_TRUTH=USDC`; `BTC_USDT_SWAP_STATUS=REJECTED_FOR_CURRENT_EEA_CANARY_PATH`; `DEMO_XPERP_310328_SEPARATED=true`; `REQUEST_BODY_OWNER=build_venue_native_order_body_v1`; `LIVE_AUTHORIZED=false`; not execute; not funded; not proven; historical next pointer superseded by §11.13.5.L; PR `#5905` merged `2caad4a2e`) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.L | SSOT post-K GET bind (`SET_ACCOUNT_LEVERAGE=3`; snapshot theoretical IM floor `2.101456666666666666666666667` USDC at `markPx=63043.7`; `CANARY_OPERATIONAL_MINIMUM_PROVEN=false`; `TDMODE_GET_SETTING_PROVEN=true`; `TDMODE_LIVE_POST_PROVEN=false`; `LIVE_AUTHORIZED=false`; not funded; not execute; historical next pointer superseded by §11.13.5.M; PR `#5906` squash-merged `bc59e1e33`) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.M | SSOT PR `#5906` persistence closeout + tracker retirement preparation (`PERSISTENCE_REMEDIATION_PR_MERGED=true`; `OWNER_MERGE_GO_FOR_POST_K_PERSISTENCE_REMEDIATION_PR_STATUS=CONSUMED_CLOSED`; tracker `RETIRED_CLOSED_NONAUTHORITATIVE` `AUTHORITY=NONE` retained; `CANARY_OPERATIONAL_MINIMUM_PROVEN=false`; `FUNDING_AMOUNT_PROVEN=false`; I44&#47;G16 `INSUFFICIENT_EVIDENCE`; `LIVE_AUTHORIZED=false`; not funded; not execute; historical next pointer superseded by §11.13.5.N; PR `#5907` squash-merged `27ceae911`) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.N | SSOT `OWNER_GO_FOR_NEW_FUNDING` evaluation fail-closed (`FUNDING_AMOUNT_PROVEN=false`; `RECOMMENDED_BOUNDED_CANARY_FUNDING_AMOUNT_PROVEN=false`; snapshot IM floor is not operational amount; I44&#47;G16 `INSUFFICIENT_EVIDENCE`; `LIVE_AUTHORIZED=false`; no money movement; not execute; historical next pointer superseded by §11.13.5.O; PR `#5908` squash-merged `2c55d81dd`) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.O | SSOT operational funding-amount evidence fail-closed (`AUTHORIZED_SCOPE=EVIDENCE_ONLY`; `FUNDING_AMOUNT_PROVEN=false`; no GET refresh; no max-avail-size; I44&#47;G16 `INSUFFICIENT_EVIDENCE`; `LIVE_AUTHORIZED=false`; no money movement; not execute; historical next pointer superseded by §11.13.5.P; PR `#5909` squash-merged `8c36b48bd`) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.P | SSOT operational funding-formula ratification fail-closed (`AUTHORIZED_SCOPE=RATIFICATION_ONLY`; `FORMULA_BODY_SUPPLIED_IN_GO=false`; `OWNER_RATIFIED_OPERATIONAL_FORMULA_PRESENT=false`; `FUNDING_AMOUNT_PROVEN=false`; I44&#47;G16 `INSUFFICIENT_EVIDENCE`; `LIVE_AUTHORIZED=false`; no money movement; not execute; historical next pointer superseded by §11.13.5.Q; PR `#5910` squash-merged `736e7e21e`) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.Q | SSOT operational funding-policy decision template (`AUTHORIZED_SCOPE=POLICY_SPEC_ONLY`; template unfilled; `FORMULA_BODY_STATUS=ABSENT`; `FUNDING_AMOUNT_PROVEN=false`; nine §11.13.5.N blockers remain open; GET evidence GO not granted; I44&#47;G16 `INSUFFICIENT_EVIDENCE`; `LIVE_AUTHORIZED=false`; no money movement; not execute; historical next pointer superseded by §11.13.5.R; PR `#5911` squash-merged `e0b3438ef`) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.R | SSOT Owner operational funding-policy decisions (`AUTHORIZED_SCOPE=POLICY_GRAMMAR_FILL_ONLY`; `OWNER_POLICY_DECISIONS_STATUS=PERSISTED_POLICY_GRAMMAR_NOT_FORMULA_RATIFICATION`; `FORMULA_BODY_STATUS=ABSENT`; `NUMERIC_COEFFICIENTS_ADDED=false`; `FUNDING_AMOUNT_PROVEN=false`; nine §11.13.5.N blockers remain open; GET evidence GO not granted; I44&#47;G16 `INSUFFICIENT_EVIDENCE`; `LIVE_AUTHORIZED=false`; no money movement; not execute; historical next pointer superseded by §11.13.5.S; PR `#5912` squash-merged `b4dc3f1a5`) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.S | SSOT bounded operational funding GET evidence (`AUTHORIZED_SCOPE=GET_ONLY_EVIDENCE`; fresh markPx `62986.2`; `FRESH_THEORETICAL_IM_FLOOR_USDC=2.09954` floor-only; `max-avail-size` `availBuy=0` `availSell=0`; `totalEq=0`; `FORMULA_BODY_STATUS=ABSENT`; `FUNDING_AMOUNT_PROVEN=false`; I44&#47;G16 `INSUFFICIENT_EVIDENCE`; `LIVE_AUTHORIZED=false`; no money movement; not execute; historical next pointer superseded by §11.13.5.T; PR `#5913` squash-merged `d96f8ec50`) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.T | SSOT operational formula instantiation fail-closed (`AUTHORIZED_SCOPE=FORMULA_INSTANTIATION_ONLY`; `FORMULA_BODY_SUPPLIED_IN_GO=false`; `INSTANTIATION_EFFECT=NONE`; `FULL_FORMULA_INSTANTIATION=false`; `FORMULA_BODY_STATUS=ABSENT`; `NUMERIC_COEFFICIENTS_ADDED=false`; fresh IM floor `2.09954` USDC not operational amount; I44&#47;G16 `INSUFFICIENT_EVIDENCE`; `LIVE_AUTHORIZED=false`; no money movement; not execute; historical next pointer superseded by §11.13.5.U; PR `#5914` squash-merged `3e1dd5c2b`) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.U | SSOT operational reserve policy-form ratification (`AUTHORIZED_SCOPE=POLICY_RATIFICATION_ONLY`; `RULE_FEE=FEE-WC-MAX-ABS-RT`; `RULE_DELIVERY=DLV-INCLUDE-ALWAYS`; `RULE_SLIPPAGE=SLP-TOB-FLOOR-TICK`; `RULE_MM_LIQ=MM-MMR-ADDEND`; `RULE_FX=FX-VENUE-CONVERT`; `RULE_OUTPUT_UNIT=FX-STATE-ALL-FINAL-FUNDS-IN-USDC`; `RULE_ROUNDING=RND-CEIL-VENUE-CCY-PRECISION-AFTER-COMPOSITION`; `FORMULA_BODY_STATUS=ABSENT`; `B08_EXACT_FORMULA_BODY_STATUS=NOT_RATIFIED`; `NUMERIC_COEFFICIENTS_ADDED=false`; `FUNDING_AMOUNT_PROVEN=false`; I44&#47;G16 `INSUFFICIENT_EVIDENCE`; `LIVE_AUTHORIZED=false`; no GET; no money movement; not execute; historical next pointer superseded by §11.13.5.V; PR `#5915` squash-merged `ddaa4e555`) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.V | SSOT XPerp trade-fee query grammar + taker&#47;maker field mapping (`AUTHORIZED_SCOPE=POLICY_RATIFICATION_ONLY`; `QUERY_GRAMMAR_RATIFIED=true`; `RATIFIED_QUERY=GET &#47;api&#47;v5&#47;account&#47;trade-fee?instType=FUTURES&instFamily=BTC-USD_UM_XPERP`; `TAKER_RATE=takerUSDC` when generic taker&#47;maker empty; `HISTORICAL_VALUES_NOT_CURRENT=true`; `NO_GET_EXECUTED_THIS_STEP=true`; `RULE_FEE` numeric instance unproven until fresh GET; `RULE_DELIVERY` remains unproven; `B08_EXACT_FORMULA_BODY_STATUS=NOT_RATIFIED`; `FUNDING_AMOUNT_PROVEN=false`; `LIVE_AUTHORIZED=false`; no GET; no money movement; not execute; historical next pointer superseded by §11.13.5.W; PR `#5916` squash-merged `0ff8f7307`) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.W | SSOT fresh XPerp trade-fee GET evidence persist (`AUTHORIZED_SCOPE=GET_EVIDENCE_PERSIST_ONLY`; `GET_COUNT=1`; `HTTP_STATUS=200`; `OKX_CODE=0`; `TAKER_RATE=-0.0005`; `MAKER_RATE=-0.0002`; `FEE_RATE_WC=0.0005`; `FEE_RATE_RT=0.0010`; `RULE_FEE_NUMERIC_INSTANCE_STATUS=FRESH_GET_RATES_PROVEN`; `RULE_DELIVERY` remains unproven; `B08_EXACT_FORMULA_BODY_STATUS=NOT_RATIFIED`; `FUNDING_AMOUNT_PROVEN=false`; `LIVE_AUTHORIZED=false`; no GET this persist; no money movement; not execute; historical next pointer superseded by §11.13.5.X; PR `#5917` squash-merged `23e0b1c86`) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.X | SSOT XPerp delivery-fee algebra ratification fail-closed (`AUTHORIZED_SCOPE=ALGEBRA_RATIFICATION_ONLY`; `ALGEBRA_BODY_SUPPLIED_IN_GO=false`; `DELIVERY_ALGEBRA_RATIFIED=false`; `RULE_DELIVERY_STATUS=UNPROVEN_PENDING_OWNER_SUPPLIED_ALGEBRA_BODY`; observed `delivery=0.0003` evidence-only; `B08_EXACT_FORMULA_BODY_STATUS=NOT_RATIFIED`; `FUNDING_AMOUNT_PROVEN=false`; `LIVE_AUTHORIZED=false`; no GET; no money movement; not execute; historical next pointer superseded by §11.13.5.Y; PR `#5918` squash-merged `fbb8e8509`) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.Y | SSOT XPerp delivery-fee algebra body persist (`AUTHORIZED_SCOPE=ALGEBRA_BODY_SUPPLY_ONLY`; `COMPLETE_DELIVERY_FEE_ALGEBRA_PROVEN=false`; `TAKER_VS_DELIVERY_FIELD_RESOLUTION=CONFLICT`; `DELIVERY_RATE_OPERAND_STATUS=UNPROVEN`; `POSITION_VALUE_ALGEBRA_STATUS=UNPROVEN`; partial sub-algebra persisted; W-pack `delivery=0.0003` not operative; `B08_EXACT_FORMULA_BODY_STATUS=NOT_RATIFIED`; `FUNDING_AMOUNT_PROVEN=false`; `LIVE_AUTHORIZED=false`; no GET; no money movement; not execute; historical next pointer superseded by §11.13.5.Z; PR `#5919` squash-merged `b4f84963c`) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.Z | SSOT XPerp expiration delivery-rate operand fail-closed (`AUTHORIZED_SCOPE=RATE_OPERAND_RESOLUTION_ONLY`; `DELIVERY_RATE_OPERAND_STATUS=UNPROVEN`; `TAKER_VS_DELIVERY_FIELD_RESOLUTION=DISTINCT_FIELDS_XPERP_EXPIRATION_OPERAND_UNPROVEN`; taker not proven as expiration rate; API `delivery` label without XPerp applicability; EEA XPerp fee overview omits delivery fee and is not proven absence; FAQ `0.01%` not identified with W-pack `delivery=0.0003`; no GET; `POSITION_VALUE_ALGEBRA_STATUS=UNPROVEN`; `COMPLETE_DELIVERY_FEE_ALGEBRA=UNPROVEN`; `B08_EXACT_FORMULA_BODY_STATUS=NOT_RATIFIED`; `FUNDING_AMOUNT_PROVEN=false`; `LIVE_AUTHORIZED=false`; no money movement; not execute; historical next pointer superseded by §11.13.5.Z1) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.Z1 | SSOT distinct EEA XPerp normal-expiry fee existence premise (`AUTHORIZED_SCOPE=PREMISE_REVIEW_ONLY`; `DISTINCT_XPERP_EXPIRY_DELIVERY_FEE_EXISTENCE_STATUS=UNPROVEN`; `RATE_OPERAND_QUESTION_CURRENTLY_WELL_POSED=false`; scheduled expiry and cash settlement proven; distinct expiry fee neither proven to apply nor proven not to apply; API `delivery=0.0003` non-operative; FAQ `0.01%` non-operative; silence is not zero; no GET; `POSITION_VALUE_ALGEBRA_STATUS=UNPROVEN`; `COMPLETE_DELIVERY_FEE_ALGEBRA=UNPROVEN`; `B08_EXACT_FORMULA_BODY_STATUS=NOT_RATIFIED`; `FUNDING_AMOUNT_PROVEN=false`; `LIVE_AUTHORIZED=false`; no money movement; not execute; historical next pointer superseded by §11.13.5.Z2) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.Z2 | SSOT exhausted EDGE_I &#47; EVENT_B applicability closeout (`AUTHORIZED_SCOPE=EDGE_I_CLOSEOUT_DOCS_ONLY`; historical snapshot `EDGE_I_STATUS=UNPROVEN`; `APPLICABILITY_VERDICT=C`; `TARGET_INSTFAMILY=BTC-USD_UM_XPERP`; `TARGET_FAMILY_SCOPE_PROVEN=true`; `TRADE_FEE_DELIVERY_FIELD_EVENT_B_APPLICABILITY=UNPROVEN`; observed `delivery=0.0003` is `OBSERVED_TARGET_FAMILY_FEE_API_VALUE` and `NON_OPERATIVE`; public&#47;taxonomy&#47;TARGET-exact fee-API&#47;delivery-semantics surfaces exhausted; `DELIVERY_RATE_OPERATIVE_VALUE=NONE`; `LIVE_AUTHORIZED=false`; no money movement; not execute; parallel unknown-none delivery-term contract persist at §11.13.5.Z2A; historical next pointer superseded by §11.13.5.Z2B) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.Z2A | SSOT fail-closed UNKNOWN&#47;NONE delivery term in operational reserve composition (`AUTHORIZED_SCOPE=UNKNOWN_NONE_DELIVERY_TERM_CONTRACT_DOCS_ONLY`; `PARALLEL_TO_SECTION_11_13_5_Z2=true`; historical snapshot `Z2_CANONICAL_POINTER_REPLACED=false`; `EDGE_I_READJUDICATED=false`; `EDGE_I_STATUS=UNPROVEN`; `APPLICABILITY_VERDICT=C`; `FINAL_VERDICT=C`; `APPLIES_PROVEN=false`; `DOES_NOT_APPLY_PROVEN=false`; `DELIVERY_RATE_OPERATIVE_VALUE=NONE`; `OPERATIVE_EXPIRY_FEE_RATE=NONE`; `DELIVERY_FEE_TERM_NUMERIC_STATUS=UNINSTANTIATED`; `FULL_OPERATIONAL_RESERVE_COMPOSITION_STATUS=BLOCKED`; `SILENT_ZERO_FORBIDDEN=true`; `SILENT_NA_FORBIDDEN=true`; `DLV_INCLUDE_ALWAYS_IS_NOT_APPLICABILITY_PROOF=true`; `LIVE_AUTHORIZED=false`; no money movement; not execute; historical next pointer superseded by §11.13.5.Z2B) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.Z2B | Historical snapshot OKX ticket `7823581` normal-expiry fee applicability and non-operative 0.01% rate (`AUTHORIZED_SCOPE=OKX_TICKET_7823581_SUPPORT_EVIDENCE_BIND_DOCS_ONLY`; current operative rate superseded by §11.13.5.Z2I; `SUPPORT_TICKET_7823581_STATUS=HISTORICAL_SUPERSEDED_FOR_RATE_ADJUDICATION`; `SUPPORT_RATE_0_0001_STATUS=HISTORICAL_SUPERSEDED`; `SUPPORT_RATE_0_0001_CAN_BLOCK_CURRENT_RATE=false`; historical tokens `NORMAL_EXPIRY_FEE_RATE_DECIMAL=0.0001`; `OPERATIVE_EXPIRY_FEE_RATE=NONE`; `LIVE_AUTHORIZED=false`; no money movement; not execute; historical next pointer superseded by §11.13.5.Z2C) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.Z2C | SSOT Peak_Trade-internal conservative expiry-fee economic-uncertainty bound for qty=1 minimum-exposure canary (`AUTHORIZED_SCOPE=INTERNAL_CONSERVATIVE_EXPIRY_FEE_ECONOMIC_UNCERTAINTY_BOUND_CONTRACT_ONLY`; `Z2B_APPLICABILITY_AND_RATE_REMAIN_BINDING=true`; `PROVEN_NORMAL_EXPIRY_RATE=0.0001`; `PEAK_TRADE_EXPIRY_RESERVE_RATE=0.0003`; `PEAK_TRADE_EXPIRY_RESERVE_RATE_IS_OKX_FEE_TRUTH=false`; `OEM_FEE_MONETARY_BASE_STATUS=UNPROVEN`; `ACTUAL_EXPIRY_FEE_AMOUNT_STATUS=UNPROVEN`; `OPERATIVE_EXPIRY_FEE_RATE=NONE`; `ABSOLUTE_BOUND_USES_UNPROVEN_EXCHANGE_FORMULA=false`; `QTY_LIMIT=1`; `SCALING_AUTHORIZED=false`; `MULTI_FUTURE_AUTHORIZED=false`; `POST_SETTLEMENT_RECONCILIATION_REQUIRED=true`; `LIVE_AUTHORIZED=false`; no money movement; not execute; historical next pointer superseded by §11.13.5.Z2D) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.Z2D | SSOT remaining UNPROVEN Position-Value &#47; FX &#47; Rounding chain for qty=1 operational reserve (`AUTHORIZED_SCOPE=POSITION_VALUE_FX_ROUNDING_CHAIN_CLASSIFICATION_AND_INTERNAL_QTY1_POLICY_CONTRACT_ONLY`; `Z2B_APPLICABILITY_AND_RATE_REMAIN_BINDING=true`; `Z2C_INTERNAL_EXPIRY_BOUND_REMAINS_BINDING=true`; `POSITION_VALUE_ALGEBRA_STATUS=UNPROVEN`; `PEAK_TRADE_INTERNAL_POSITION_VALUE_IS_OKX_POSITION_VALUE=false`; `RULE_FX_STATUS=UNPROVEN`; `USD_USDC_CONVERSION_APPLIED=false`; `RULE_ROUNDING_STATUS=UNPROVEN`; `ROUNDING_APPLIED=false`; `COVER_USDC_STATUS=UNINSTANTIATED`; `EXCHANGE_TRUTH_CHANGED=false`; `QTY_LIMIT=1`; `SCALING_AUTHORIZED=false`; `LIVE_AUTHORIZED=false`; no money movement; not execute; historical next pointer superseded by §11.13.5.Z2E) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.Z2E | SSOT B08 exact internal conservative qty=1 formula-body ratification (`AUTHORIZED_SCOPE=EXACT_FORMULA_BODY_RATIFICATION_CONTRACT_ONLY`; `B08_EXACT_FORMULA_BODY_KIND=INTERNAL_CONSERVATIVE_QTY1_COMPOSITION_NOT_EXCHANGE_TRUTH_NOT_COVER_USDC`; `B08_EXACT_FORMULA_BODY_STATUS=RATIFIED_INTERNAL_CONSERVATIVE_QTY1_NOT_COVER_USDC`; `PEAK_TRADE_EXPIRY_RESERVE_RATE=0.0003`; `PEAK_TRADE_EXPIRY_RESERVE_RATE_IS_OKX_FEE_TRUTH=false`; `NORMAL_EXPIRY_RATE=0.0001` non-operative; `MONETARY_BASE=UNPROVEN`; `EXACT_OKX_FEE_FORMULA=UNPROVEN`; `COVER_USDC_STATUS=UNINSTANTIATED`; `NUMERIC_FUNDING_AMOUNT=NONE`; `EXCHANGE_TRUTH_CHANGED=false`; `QTY_LIMIT=1`; `SCALING_AUTHORIZED=false`; `LIVE_AUTHORIZED=false`; no money movement; not execute; historical next pointer superseded by §11.13.5.Z2F) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.Z2F | SSOT fail-closed B08 term-instance &#47; FX &#47; rounding adjudication (`AUTHORIZED_SCOPE=FORMULA_TERM_INSTANCE_AND_FX_ROUNDING_BINDING_CONTRACT_ONLY`; `QTY_TERM_STATUS=PROVEN`; `CTVAL_TERM_STATUS=PROVEN` `0.0001 BTC` instrument metadata; `MARKPX_TERM_STATUS=UNINSTANTIATED`; `MONETARY_BASE_STATUS=UNPROVEN`; `FX_STATUS=UNPROVEN`; `ROUNDING_STATUS=UNPROVEN`; `CONSERVATIVE_RATE_0_0003_STATUS=INTERNAL_CONSERVATIVE_POLICY_NOT_EXCHANGE_TRUTH`; `B08_INTERNAL_ALGEBRA_STATUS=RATIFIED_INTERNAL_CONSERVATIVE_QTY1_NOT_COVER_USDC`; `COVER_USDC_STATUS=UNINSTANTIATED`; `NUMERIC_FUNDING_AMOUNT_PRODUCED=false`; `EXCHANGE_TRUTH_CHANGED=false`; `QTY_LIMIT=1`; `SCALING_AUTHORIZED=false`; `LIVE_AUTHORIZED=false`; no money movement; not execute; historical next pointer superseded by §11.13.5.Z2G) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.Z2G | SSOT current markPx public GET evidence (`AUTHORIZED_SCOPE=CURRENT_MARKPX_PUBLIC_GET_EVIDENCE_ONLY`; `GET` `&#47;api&#47;v5&#47;public&#47;mark-price`; `markPx=64495.3`; `MARKPX_TERM_STATUS=OBSERVED_NOT_NORMATIVELY_BOUND`; `MARKPX_OKX_DELIVERY_FEE_OPERAND_STATUS=UNPROVEN`; `MONETARY_BASE_STATUS=UNPROVEN`; `FX_STATUS=UNPROVEN`; `ROUNDING_STATUS=UNPROVEN`; `COVER_USDC_STATUS=UNINSTANTIATED`; `NUMERIC_FUNDING_AMOUNT_PRODUCED=false`; `EXCHANGE_TRUTH_CHANGED=false`; `QTY_LIMIT=1`; `SCALING_AUTHORIZED=false`; `LIVE_AUTHORIZED=false`; public GET-only; no credentials; no money movement; not execute; historical next pointer superseded by §11.13.5.Z2H) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.Z2H | SSOT current ticker bid&#47;ask public GET evidence (`AUTHORIZED_SCOPE=CURRENT_TICKER_BID_ASK_PUBLIC_GET_EVIDENCE_ONLY`; `GET` `&#47;api&#47;v5&#47;market&#47;ticker`; `bidPx=64529.9`; `askPx=64530`; `BID_ASK_TERM_STATUS=OBSERVED_NOT_NORMATIVELY_BOUND`; `SLIPPAGE_RESERVE_NUMERIC_STATUS=UNINSTANTIATED`; `MARKPX_TERM_STATUS=OBSERVED_NOT_NORMATIVELY_BOUND`; `MARKPX_OKX_DELIVERY_FEE_OPERAND_STATUS=UNPROVEN`; `MONETARY_BASE_STATUS=UNPROVEN`; `FX_STATUS=UNPROVEN`; `ROUNDING_STATUS=UNPROVEN`; `COVER_USDC_STATUS=UNINSTANTIATED`; `NUMERIC_FUNDING_AMOUNT_PRODUCED=false`; `EXCHANGE_TRUTH_CHANGED=false`; `QTY_LIMIT=1`; `SCALING_AUTHORIZED=false`; `LIVE_AUTHORIZED=false`; public GET-only; no credentials; no money movement; not execute; COVER_USDC current pointer unchanged; historical superseded 0.0003 vs 0.0001 persist at §11.13.5.Z2I-HIST; current rate persist at §11.13.5.Z2I) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.Z2I-HIST | Historical superseded PR `#5960` delivery `0.0003` versus expiry-settlement `0.0001` provenance adjudication (`PERSIST_STATUS=HISTORICAL_SUPERSEDED`; `PR_5960_SEMANTICS_STATUS=HISTORICAL_SUPERSEDED`; `CURRENT_NORMATIVE_AUTHORITY=false`; `SUPERSEDED_BY=SECTION_11_13_5_Z2I`; historical snapshot `DELIVERY_0003_EXPIRY_SETTLEMENT_RATE_AUTHORITY=NONE`; `EXPIRY_SETTLEMENT_RATE_NORMATIVE=0.0001`; `OPERATIVE_EXPIRY_SETTLEMENT_RATE=NONE`; `LIVE_AUTHORIZED=false`; no GET; no support; no money movement; not execute; not current Owner truth) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.Z2I | SSOT owner-ratified operative expiry-settlement rate from verified first-party OKX API `delivery` (`AUTHORIZED_SCOPE=OWNER_RATIFIED_EXPIRY_SETTLEMENT_RATE_ADJUDICATION_FROM_VERIFIED_API_DELIVERY`; `PARALLEL_TO_SECTION_11_13_5_Z2H=true`; `Z2H_CANONICAL_POINTER_REPLACED=false`; `DELIVERY_RATE_VALUE=0.0003`; `DELIVERY_RATE_VALUE_PROVENANCE=VERIFIED_FIRST_PARTY_OKX_API_ARTIFACT`; `DELIVERY_RATE_PEAK_TRADE_GENERATED=false`; `DELIVERY_RATE_OWNER_GENERATED=false`; `EXPIRY_SETTLEMENT_RATE=0.0003`; `EXPIRY_SETTLEMENT_RATE_PERCENT=0.03%`; `OPERATIVE_EXPIRY_SETTLEMENT_RATE=0.0003`; `EXPIRY_SETTLEMENT_RATE_ADJUDICATION=OWNER_RATIFIED_FROM_VERIFIED_FIRST_PARTY_OKX_DELIVERY_FIELD`; `OPERATIVE_EXPIRY_FEE_RATE=0.0003`; `SINGLE_CURRENT_RATE_TRUTH=true`; `EXPIRY_RATE_GATE=PASS`; `EXPIRY_RATE_BLOCKER=false`; `SUPPORT_REQUIRED_FOR_RATE_DECISION=false`; `SUPPORT_RATE_0_0001_STATUS=HISTORICAL_SUPERSEDED`; `PR_5960_SEMANTICS_STATUS=HISTORICAL_SUPERSEDED`; `PEAK_TRADE_EXPIRY_RESERVE_RATE=0.0003`; `PEAK_TRADE_EXPIRY_RESERVE_RATE_SOURCE=PEAK_TRADE_POLICY_REUSE_OF_SAME_NUMERIC_VALUE`; `PEAK_TRADE_EXPIRY_RESERVE_RATE_IS_OKX_FEE_TRUTH=false`; `COVER_USDC_STATUS=UNINSTANTIATED`; `LIVE_AUTHORIZED=false`; no money movement; not execute; semantic persist at §11.13.5.Z2J) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.Z2J | SSOT first-party USD-margined X-Perp settlement-semantics adjudication (`AUTHORIZED_SCOPE=USD_M_XPERP_SETTLEMENT_SEMANTIC_ADJUDICATION_DOCS_ONLY`; `PARALLEL_TO_SECTION_11_13_5_Z2I=true`; `Z2H_CANONICAL_POINTER_REPLACED=false`; `Z2I_OPERATIVE_EXPIRY_RATE_REMAINS_BINDING=true`; `SEMANTIC_PROPOSITION_VERDICT=PROVEN`; `NUMERIC_PROPOSITION_VERDICT=UNPROVEN`; `CLIENT_FX_PROPOSITION_VERDICT=UNPROVEN`; `ACCOUNT_SETTLE_CCY=USDC`; `PUBLIC_SETTLE_CCY=USD`; `VENUE_INTERNAL_CONVERSION_SEMANTIC_PROVEN=true`; `VENUE_NUMERIC_CONVERSION_OPERATOR_PROVEN=false`; `CLIENT_SIDE_FX_REQUIRED_PROVEN=false`; `MODEL_3_SEMANTICS_CANONICALIZED=true`; `MODEL_3_NUMERIC_COVER_CANONICALIZED=false`; `NAMED_REMAINING_COVER_USDC_TERM=FINITE_PHYSICAL_USDC_COVER_AMOUNT_ABSENT`; `COVER_USDC_STATUS=UNINSTANTIATED`; `LIVE_AUTHORIZED=false`; no money movement; not execute; funding&#47;Canary remain blocked; historical next pointer superseded by §11.13.5.Z2K) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.Z2K | SSOT current public-tier MMR public GET evidence (`AUTHORIZED_SCOPE=CURRENT_PUBLIC_TIER_MMR_PUBLIC_GET_EVIDENCE_ONLY`; `GET` `&#47;api&#47;v5&#47;public&#47;position-tiers`; `mmr=0.01` qty=1 tier 1; `MMR_TERM_STATUS=OBSERVED_NOT_NORMATIVELY_BOUND`; `MM_LIQ_BUFFER_NUMERIC_STATUS=UNINSTANTIATED`; `PUBLIC_MMR_CLASSIFICATION=PUBLIC_TIER_FACT_NOT_ACCOUNT_EFFECTIVE_MMR`; `FX_STATUS=UNPROVEN`; `ROUNDING_STATUS=UNPROVEN`; `VENUE_NUMERIC_CONVERSION_OPERATOR_PROVEN=false`; `PHYSICAL_USDC_COVER_AMOUNT_AVAILABLE=false`; `COVER_USDC_STATUS=UNINSTANTIATED`; `NUMERIC_FUNDING_AMOUNT_PRODUCED=false`; `EXCHANGE_TRUTH_CHANGED=false`; `QTY_LIMIT=1`; `SCALING_AUTHORIZED=false`; `LIVE_AUTHORIZED=false`; public GET-only; no credentials; no money movement; not execute; funding&#47;Canary remain blocked; historical `NEXT_CANONICAL_STEP_POINTER=OWNER_GO_REQUIRED_FOR_PRODUCTIVE_EVIDENCE_TO_RESOLVE_REMAINING_UNPROVEN_COVER_USDC_TERMS_AFTER_CURRENT_PUBLIC_TIER_MMR_BEFORE_FUNDING`; historical next pointer superseded by §11.13.5.Z2L) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.Z2L | SSOT fee-reserve rates rebind grammar after Z2K (`AUTHORIZED_SCOPE=FEE_RESERVE_RATES_REBIND_GRAMMAR_ONLY`; `GRAMMAR_ONLY=true`; `EVIDENCE_CALL_EXECUTED=false`; `GET` `&#47;api&#47;v5&#47;account&#47;trade-fee` grammar sealed not executed; `REQUEST_BINDING=instType=FUTURES;instFamily=BTC-USD_UM_XPERP`; `FRESHNESS_RULE=SAME_COVER_USDC_EVIDENCE_PACK_REEXECUTED_GET_NO_TTL`; `FREEZE_RULE=SAME_EVIDENCE_PACK_TAKER_MAKER_ONLY_AFTER_AUTHORIZED_REBIND_GET`; `FEE_RESERVE_RATES_GRAMMAR_STATUS=SEALED_NOT_GET_NOT_FROZEN`; `HISTORICAL_W_PACK_IS_NOT_EXECUTE_FRESH=true`; `COVER_USDC_STATUS=UNINSTANTIATED`; `LIVE_AUTHORIZED=false`; no GET; no credentials; no money movement; not execute; funding&#47;Canary remain blocked; historical next pointer superseded by §11.13.5.Z2M) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.Z2M | SSOT one-shot authenticated trade-fee GET execution-path ratification (`AUTHORIZED_SCOPE=FEE_RESERVE_RATES_REBIND_GET_EXECUTION_PATH_RATIFICATION_ONLY`; `THIS_GO_AUTHORIZES_HTTP_GET=false`; `EVIDENCE_CALL_EXECUTED=false`; `GET` `&#47;api&#47;v5&#47;account&#47;trade-fee` path ratified not executed; `REQUEST_HOST=eea.okx.com`; `REQUEST_QUERY=instType=FUTURES&instFamily=BTC-USD_UM_XPERP`; `SECRETREF_URI=secretref:&#47;&#47;vault&#47;peak-trade&#47;live-canary-minimum-exposure&#47;okx`; `RETRY_COUNT_ALLOWED=0`; `ONE_SHOT_REQUEST_LIMIT=1`; `GENERAL_CANARY_GET_ALLOWLIST_WIDENED=false`; `FEE_RESERVE_RATES_ADJUDICATION=UNPROVEN`; `EARLIEST_UNRESOLVED_DEPENDENCY=FEE_RESERVE_RATES_REBIND_GET_USING_SEALED_GRAMMAR_AND_SEALED_EXECUTION_PATH_NOT_EXECUTED`; `COVER_USDC_STATUS=UNINSTANTIATED`; `LIVE_AUTHORIZED=false`; no GET; no credentials; no money movement; not execute; funding&#47;Canary remain blocked; historical next pointer superseded by §11.13.5.Z2N) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.Z2N | SSOT bind of already persisted PR `#5966` authenticated fee-reserve rates rebind GET evidence (`AUTHORIZED_SCOPE=PERSIST_FRESH_FEE_RESERVE_RATES_REBIND_GET_EVIDENCE_TO_ORIGIN_MAIN_SSOT_ONLY`; `FEE_RESERVE_RATES_REBIND_GET_EVIDENCE_BOUND=true`; `EVIDENCE_SOURCE=ORIGIN_MAIN_PERSISTED_EVIDENCE_FROM_PR_5966`; `NETWORK_CALL_REQUIRED_FOR_BINDING=false`; `NETWORK_CALL_EXECUTED_DURING_BINDING=false`; `REQUEST_INST_TYPE=FUTURES`; `REQUEST_INST_FAMILY=BTC-USD_UM_XPERP`; `MARKET_DASHBOARD_FAMILY_TAXONOMY_USED=false`; `HTTP_STATUS=200`; `OKX_CODE=0`; `TAKER_USDC_RAW=-0.0005`; `MAKER_USDC_RAW=-0.0002`; `FEE_RESERVE_RATES_ADJUDICATION=PROVEN`; `NUMERIC_FEE_RESERVE_STATUS=UNINSTANTIATED`; `EARLIEST_UNRESOLVED_DEPENDENCY=COVER_USDC_UNINSTANTIATED_REMAINING_UNPROVEN_TERMS_AFTER_FEE_RESERVE_RATES_REBIND`; `COVER_USDC_STATUS=UNINSTANTIATED`; `LIVE_AUTHORIZED=false`; no GET this step; no credentials; no money movement; not execute; funding&#47;Canary remain blocked; historical next pointer superseded by §11.13.5.Z2O) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.Z2O | SSOT same-pack current markPx public GET and INTERNAL_NOTIONAL_ENVELOPE (`AUTHORIZED_SCOPE=SAME_PACK_CURRENT_MARKPX_PUBLIC_GET_AND_INTERNAL_NOTIONAL_ENVELOPE_ONLY`; `GET` `&#47;api&#47;v5&#47;public&#47;mark-price`; `markPx=64408.5`; `SAME_PACK_WITH_Z2N_FEE_FREEZE=true`; `Z2G_MARKPX_64495_3_NOT_USED=true`; `INTERNAL_NOTIONAL_ENVELOPE_NUMERIC=6.44085`; `INTERNAL_NOTIONAL_ENVELOPE_UNIT=PEAK_TRADE_INTERNAL_NOTIONAL_UNIT`; `NUMERIC_FEE_RESERVE=0.00644085`; `DELIVERY_COVER_INTERNAL_NUMERIC=0.001932255`; `SLIPPAGE_RESERVE_NUMERIC_STATUS=UNINSTANTIATED`; `MM_LIQ_BUFFER_NUMERIC_STATUS=UNINSTANTIATED`; `EARLIEST_UNRESOLVED_DEPENDENCY=COVER_USDC_UNINSTANTIATED_REMAINING_UNPROVEN_TERMS_AFTER_SAME_PACK_INTERNAL_NOTIONAL_ENVELOPE`; `FX_STATUS=UNPROVEN`; `ROUNDING_STATUS=UNPROVEN`; `COVER_USDC_STATUS=UNINSTANTIATED`; `NUMERIC_FUNDING_AMOUNT_PRODUCED=false`; `EXCHANGE_TRUTH_CHANGED=false`; `QTY_LIMIT=1`; `SCALING_AUTHORIZED=false`; `LIVE_AUTHORIZED=false`; public GET-only; no credentials; no money movement; not execute; funding&#47;Canary remain blocked; historical next pointer superseded by §11.13.5.Z2P) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.Z2P | SSOT same-pack current ticker bid&#47;ask public GET and SLIPPAGE_RESERVE_NUMERIC (`AUTHORIZED_SCOPE=SAME_PACK_CURRENT_TICKER_BID_ASK_PUBLIC_GET_AND_SLIPPAGE_RESERVE_NUMERIC_ONLY`; `GET` `&#47;api&#47;v5&#47;market&#47;ticker`; `bidPx=64805.6`; `askPx=64805.7`; `tickSz=0.1`; `SLIPPAGE_RESERVE_NUMERIC=0.00002`; `SAME_PACK_WITH_Z2N_FEE_FREEZE=true`; `Z2H_BID_ASK_NOT_USED=true`; `MM_LIQ_BUFFER_NUMERIC_STATUS=UNINSTANTIATED`; `FX_STATUS=UNPROVEN`; `ROUNDING_STATUS=UNPROVEN`; `COVER_USDC_STATUS=UNINSTANTIATED`; `NUMERIC_FUNDING_AMOUNT_PRODUCED=false`; `EXCHANGE_TRUTH_CHANGED=false`; `QTY_LIMIT=1`; `SCALING_AUTHORIZED=false`; `LIVE_AUTHORIZED=false`; public GET-only; no credentials; no money movement; not execute; funding&#47;Canary remain blocked; historical next pointer superseded by §11.13.5.Z2Q) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.Z2Q | SSOT same-pack current public-tier MMR public GET and MM_LIQ_BUFFER_NUMERIC (`AUTHORIZED_SCOPE=PERSIST_SAME_PACK_CURRENT_PUBLIC_TIER_MMR_AND_MM_LIQ_BUFFER_NUMERIC_TO_ORIGIN_MAIN_SSOT_ONLY`; `GET` `&#47;api&#47;v5&#47;public&#47;position-tiers`; `mmr=0.01` qty=1 tier 1 from this GET; `Z2K_HISTORICAL_MMR_NOT_USED_AS_OPERATIVE_INPUT=true`; `MM_LIQ_BUFFER_NUMERIC=0.0644085`; `MM_LIQ_BUFFER_NUMERIC_STATUS=PROVEN_INTERNAL_ALGEBRA_NOT_COVER_USDC`; `FEE_RESERVE_NUMERIC=NONE`; `DELIVERY_COVER_INTERNAL_NUMERIC=NONE`; `SUM_INTERNAL_NUMERIC=NONE`; `EARLIEST_UNRESOLVED_DEPENDENCY=COVER_USDC_UNINSTANTIATED_REMAINING_UNPROVEN_TERMS_AFTER_SAME_PACK_MM_LIQ_BUFFER`; `FX_STATUS=UNPROVEN`; `ROUNDING_STATUS=UNPROVEN`; `COVER_USDC_STATUS=UNINSTANTIATED`; `NUMERIC_FUNDING_AMOUNT_PRODUCED=false`; `EXCHANGE_TRUTH_CHANGED=false`; `QTY_LIMIT=1`; `SCALING_AUTHORIZED=false`; `LIVE_AUTHORIZED=false`; docs persist of one prior public GET; no GET this persist; no credentials; no money movement; not execute; funding&#47;Canary remain blocked; historical next pointer superseded by §11.13.5.Z2R) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.Z2R | SSOT one-shot public unauthenticated instruments GET for target `ctMult` (`AUTHORIZED_SCOPE=ONE_PUBLIC_UNAUTHENTICATED_READ_ONLY_TARGET_CTMULT_GET_ONLY`; `GET` `&#47;api&#47;v5&#47;public&#47;instruments?instType=FUTURES&instId=BTC-USD_UM_XPERP-310404`; `HOST=eea.okx.com`; `HTTP_STATUS=200`; `OKX_CODE=0`; `TARGET_BIND_VALID=true`; `RAW_CTMULT_FIELD_PRESENT=true`; `TARGET_INSTID_310404_CTMULT=1`; `TARGET_INSTID_310404_CTMULT_NUMERIC_PROVEN=true`; `CTVAL_BINDING_STILL_VALID=true`; `TARGET_CTVAL=0.0001`; `OEM_0.01_CONTRACT_SIZE_TARGET_BINDING_PROVEN=false`; `EXPIRATION_DELIVERY_POSITION_VALUE_FORMULA_PROVEN=false`; `POSITION_VALUE_ALGEBRA_STATUS=UNPROVEN`; `EARLIEST_UNPROVEN_TERM_AFTER=POSITION_VALUE_ALGEBRA`; `COVER_USDC_STATUS=UNINSTANTIATED`; `NUMERIC_FUNDING_AMOUNT_PRODUCED=false`; `EXCHANGE_TRUTH_CHANGED=false`; `QTY_LIMIT=1`; `LIVE_AUTHORIZED=false`; one public GET; no retry; no credentials; no money movement; not execute; funding&#47;Canary remain blocked; historical next pointer superseded by §11.13.5.Z2S) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.Z2S | SSOT deep first-party POSITION_VALUE_ALGEBRA adjudication (`AUTHORIZED_SCOPE=POSITION_VALUE_ALGEBRA_DEEP_ADJUDICATION_ONLY`; no GET; `GENERAL_LINEAR_NOTIONAL_ALGEBRA_STATUS=PROVEN`; `API_LINEAR_NOTIONAL_FORMULA=sz*ctVal*markPx`; `CTMULT_INCLUDED_IN_API_NOTIONAL_FORMULA=false`; `TARGET_FACE_VALUE_AUTHORITY_STATUS=CONFLICTED`; OEM spec `Contract Size=0.01 BTC` for `BTC-USD_UM XPERP` expiry 2031-04-04 vs API `ctVal=0.0001 BTC` and Guide example `0.0001 BTC`; `CONFLICT_FACTOR=100`; `REAL_FIRST_PARTY_NUMERIC_CONFLICT=true`; `PRODUCT_SCOPE_MATCH=true`; `EXPIRY_SCOPE_MATCH=true`; `GUIDE_EXACT_TARGET_MATCH=false`; `GUIDE_PRODUCT_CLASS_MATCH=true`; `INTERNAL_NOTIONAL_ENVELOPE_USED_AS_OEM_PROOF=false`; `FINAL_SETTLEMENT_PNL_FORMULA_STATUS=INFERRED_NOT_PROVEN`; `POSITION_VALUE_ALGEBRA_STATUS=UNPROVEN`; `UNPROVEN_REMAINDER=TARGET_CONTRACT_FACE_VALUE_CONFLICT_0.01_BTC_VS_0.0001_BTC`; `COVER_USDC_STATUS=UNINSTANTIATED`; `NUMERIC_FUNDING_AMOUNT_PRODUCED=false`; `EXCHANGE_TRUTH_CHANGED=false`; `QTY_LIMIT=1`; `LIVE_AUTHORIZED=false`; no GET; no support contact; no money movement; not execute; funding&#47;Canary remain blocked; historical next pointer superseded by §11.13.5.Z2T) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.Z2T | SSOT docs-only first-party source ingest and algebra-shape split (`AUTHORIZED_SCOPE=DOCS_ONLY_Z2S_FIRST_PARTY_SOURCE_INGEST_AND_ALGEBRA_SHAPE_SPLIT_NO_FACE_VALUE_RESOLUTION_NO_SUPPORT_CONTACT`; no GET; no support; `FORMULA_SHAPE_STATUS=PROVEN_FOR_LINEAR_CONTRACT_SHAPE`; `POSITION_VALUE_FORMULA_SHAPE=sz*ctVal*markPx`; `CTMULT_FACTOR_100_EXPLANATION=REJECTED`; `TARGET_PARAMETER_BINDING_STATUS=CONFLICTING_CURRENT_FIRST_PARTY_SOURCES`; `TARGET_FACE_VALUE_AUTHORITY=CONFLICTING_CURRENT_FIRST_PARTY_SOURCES`; `FACE_VALUE_CONFLICT_STATUS=UNRESOLVED`; Guide example `BTC-USD_UM_XPERP-040431` is not literal `BTC-USD_UM_XPERP-310404`; OEM spec `0.01 BTC` vs API&#47;Guide&#47;E3 `0.0001 BTC` remain concurrently current; `FINAL_DELIVERY_PRICE_METHOD_STATUS=PROVEN`; `FINAL_SETTLEMENT_PNL_FORMULA_STATUS=PARTIAL_CONDITIONAL_PENDING_EXPLICIT_NORMATIVE_INHERITANCE`; no USDC-futures-listing PnL inheritance; `ACCOUNT_SETTLE_CCY=USDC`; `FX_STATUS=UNPROVEN_FOR_PHYSICAL_USDC_COVER`; `ROUNDING_STATUS=UNPROVEN`; `VENUE_NUMERIC_CONVERSION_OPERATOR_STATUS=UNPROVEN`; `FINITE_PHYSICAL_USDC_COVER_AMOUNT=UNPROVEN`; `COVER_USDC_STATUS=UNINSTANTIATED`; `SUPPORT_CONTACT_AUTHORIZED=false`; `NUMERIC_FUNDING_AMOUNT_PRODUCED=false`; `EXCHANGE_TRUTH_CHANGED=false`; `QTY_LIMIT=1`; `LIVE_AUTHORIZED=false`; no GET; no support contact; no money movement; not execute; funding&#47;Canary remain blocked; historical next pointer superseded by §11.13.5.Z2U) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.Z2U | SSOT docs&#47;evidence-only operative algebra triangulation bind (`AUTHORIZED_SCOPE=Z2S_READ_ONLY_OPERATIVE_ALGEBRA_BIND_DOCS_EVIDENCE_ONLY`; no new GET; no support; dual-host public metadata `ctVal=0.0001` `ctValCcy=BTC` `ctMult=1` `settleCcy=USD` `lever=50` instrument-max not account leverage 3; `OPERATIVE_METADATA_VALUE=0.0001_BTC`; `OPERATIVE_RUNTIME_VALUE=UNPROVEN`; `OPERATIVE_CONTRACT_VALUE_PROVEN=false`; OEM spec last updated 20 August 2026 still `0.01 BTC` for `BTC-USD_UM XPERP` expiry 2031-04-04 16:00 HK; `DECLARED_OEM_SPEC_VALUE=0.01_BTC`; `OEM_SPEC_DIVERGENCE=PROVEN`; no claim OEM is wrong&#47;stale&#47;typo&#47;legacy; theoretical IM Long `2.1014567` Short `2.09954` USDC are Peak_Trade floors not OKX-account IM; `H1_SUPPORT=ALGEBRAIC_CONSISTENCY_ONLY`; `RULE_C_INDEPENDENT_RUNTIME_IM_SATISFIED=false`; `FACTOR_100_RECONCILIATION=NONE_PROVEN`; `FACE_VALUE_DOCUMENT_CONFLICT_RECONCILED=false`; `USD_USDC_USD_UM_SEMANTICS_STATUS=PARTIAL`; `Z2S_OPERATIVE_ALGEBRA_STATUS=PARTIALLY_PROVEN`; `POSITION_VALUE_ALGEBRA_STATUS=UNPROVEN`; `COVER_USDC_STATUS=UNINSTANTIATED`; `LIVE_AUTHORIZED=false`; no money movement; not execute; funding&#47;Canary remain blocked; historical next pointer superseded by §11.13.5.Z2V) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.Z2V | SSOT docs&#47;evidence-only bind of completed independent OKX EEA account-runtime probe (`AUTHORIZED_SCOPE=Z2U_NEGATIVE_INDEPENDENT_ACCOUNT_RUNTIME_PROBE_BIND_DOCS_EVIDENCE_ONLY`; prior GO GET-only; this persist no new GET; `HOST=eea.okx.com`; `GET` `&#47;api&#47;v5&#47;account&#47;positions` HTTP 200 `code=0` `data=[]`; `GET` `&#47;api&#47;v5&#47;account&#47;account-position-risk` `posData=[]`; `GET` `&#47;api&#47;v5&#47;account&#47;positions-history` `data=[]`; `GET` `&#47;api&#47;v5&#47;account&#47;balance` `totalEq=0` `imr=""` `notionalUsd=""` `upl=""`; `GET` `&#47;api&#47;v5&#47;account&#47;adjust-leverage-info` `estMgn=0` `estMaxAmt=0` `existOrd=false`; `GET` `&#47;api&#47;v5&#47;account&#47;max-size` `maxBuy=0` `maxSell=0`; Help Center UI only not a trading ticket; `TARGET_RUNTIME_RECORD_FOUND=false`; `RULE_C_INDEPENDENT_RUNTIME_IM_SATISFIED=false`; `OPERATIVE_RUNTIME_VALUE=UNPROVEN`; `OPERATIVE_CONTRACT_VALUE_PROVEN=false`; `OPERATIVE_CONTRACT_VALUE=UNPROVEN`; `FACE_VALUE_DOCUMENT_CONFLICT_RECONCILED=false`; `CANDIDATE_A_0_0001_BTC_COMPATIBLE=INCONCLUSIVE_ZERO_EQUITY_NOT_DISCRIMINATING`; `CANDIDATE_B_0_01_BTC_COMPATIBLE=INCONCLUSIVE_ZERO_EQUITY_NOT_DISCRIMINATING`; `INDEPENDENCE_FROM_PUBLIC_CTVAL_FORMULA=true_SURFACES_CHECKED_BUT_NO_DISCRIMINATING_VALUE`; `NO_USD_EQUALS_USDC=true`; `COVER_USDC_STATUS=UNINSTANTIATED`; `COVER_USDC_INSTANTIATED=false`; zero estimates are not Rule-C proof; repeat zero-equity GET has no discriminatory value; `LIVE_AUTHORIZED=false`; no money movement; not execute; funding&#47;Canary remain blocked; historical next pointer superseded by §11.13.5.Z2W) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.Z2W | SSOT docs&#47;evidence&#47;governance-only Evidence Boundary Reached bind (`AUTHORIZED_SCOPE=Z2V_PLUS_PR_5979_PATH_ADJUDICATION_EVIDENCE_BOUNDARY_REACHED_BIND_DOCS_EVIDENCE_ONLY`; no GET; no OKX API; PR `#5979` squash-merged documentary-only not a new Z-section; `DOES_ANY_CANONICAL_NO_SUBMIT_NO_POSITION_NO_FUNDING_DISCRIMINATOR_REMAIN=false`; `RECOMMENDED_BRANCH=EVIDENCE_BOUNDARY_REACHED`; `RULE_C_STATUS=UNPROVEN`; `RUNTIME_PROOF_OBTAINED=false`; `FACE_VALUE_CONFLICT_STATUS=UNRESOLVED`; `FACE_VALUE_CONFLICT_CLOSED=false`; `COVER_USDC_STATUS=UNINSTANTIATED`; `ACCOUNT_LEVEL_VALUE=2`; `ORDER_PRECHECK_ACCOUNT_LEVEL_2_STATUS=NOT_APPLICABLE`; `MINIMAL_NEW_STATE_CLASS_IF_REQUIRED=ORDER_DERIVED_OR_POSITION_DERIVED_IM_NOTIONALUSD_OR_UPL`; `NEW_RUNTIME_STATE_CLASS_AUTHORIZED=false`; `REPEAT_ZERO_EQUITY_NO_POSITION_GET_DISCRIMINATORY_VALUE=false`; `NO_CAPABILITY_ADVANCEMENT=true`; `LIVE_AUTHORIZED=false`; no money movement; not execute; funding&#47;Canary remain blocked; historical next pointer superseded by §11.13.5.Z2X) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.Z2X | SSOT docs&#47;governance-only fail-closed adjudication of the order-or-position state class (`AUTHORIZED_SCOPE=Z2W_ORDER_DERIVED_OR_POSITION_DERIVED_STATE_CLASS_FAIL_CLOSED_ADJUDICATION_DOCS_ONLY`; no GET; no order submit; `ADJUDICATION=B`; `UNFILLED_ORDER_DOES_NOT_PRODUCE_DISCRIMINATOR_POSITION_REQUIRED=true`; `MINIMAL_DISCRIMINATING_STATE_CLASS=FILLED_POSITION_DERIVED`; `UNFILLED_ORDER_SAFE_PROBE_PROVEN=false`; `PRODUCTIVE_ORDER_SUBMIT_PERFORMED=false`; `RULE_C_STATUS=UNPROVEN`; `FACE_VALUE_CONFLICT_STATUS=UNRESOLVED`; `COVER_USDC_STATUS=UNINSTANTIATED`; `POSITION_OPENING_AUTHORIZED=false`; `LIVE_AUTHORIZED=false`; no money movement; not execute; funding&#47;Canary remain blocked; historical next pointer superseded by §11.13.5.Z2Y) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.Z2Y | SSOT docs&#47;governance-only fail-closed authorizability adjudication of `FILLED_POSITION_DERIVED` (`AUTHORIZED_SCOPE=Z2X_FILLED_POSITION_DERIVED_AUTHORIZABILITY_ADJUDICATION_DOCS_ONLY`; no GET; no order submit; no funding; `ADJUDICATION=B`; `FILLED_POSITION_DERIVED_PROBE_NOT_PRESENTLY_AUTHORIZABLE=true`; `FUTURE_RUNTIME_PROTOCOL_DOCUMENTED=false`; `FLATTEN_GUARANTEE_STATUS=UNPROVEN_HARD_STOP`; `COVER_USDC_STATUS=UNINSTANTIATED`; `FACE_VALUE_CONFLICT_STATUS=UNRESOLVED`; `POSITION_OPENING_AUTHORIZED=false`; `LIVE_AUTHORIZED=false`; no money movement; not execute; funding&#47;Canary remain blocked; historical next pointer superseded by §11.13.5.Z2Z) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.Z2Z | SSOT docs-only evidence-model re-adjudication (`AUTHORIZED_SCOPE=Z2Y_EVIDENCE_MODEL_RE_ADJUDICATION_DOCS_ONLY`; no GET; no order; no funding; `POSITION_NOTIONAL_ALGEBRA_STATUS=FIRST_PARTY_DOCUMENTED`; `LINEAR_UPL_ALGEBRA_STATUS=FIRST_PARTY_DOCUMENTED`; `VENUE_CLOSE_POSITION_MARKET_CAPABILITY=FIRST_PARTY_DOCUMENTED`; `PEAK_TRADE_CLOSE_POSITION_ALLOWLISTED=false`; `LIVE_FLATTEN_PROVABILITY=UNPROVEN_HARD_STOP`; `CURRENT_FIRST_PARTY_OEM_LAST_UPDATED=20_AUGUST_2026`; `OEM_SPEC_12_AUG_2026_FIRST_PARTY_REPRODUCED=false`; `OEM_SPEC_METADATA_CORRECTION_REQUIRED=false`; `VENUE_HAS_NON_LIMIT_ONLY_EXECUTION_PRIMITIVES=true`; `CURRENT_PEAK_TRADE_LIFECYCLE=LIMIT_ONLY_NO_MARKET`; `COVER_USDC_EVIDENCE_CLASS=ALGEBRA_PROVEN_BUT_NUMERIC_INSTANTIATION_BLOCKED_BY_CTVAL_AUTHORITY_CONFLICT_AND_ACCOUNT_SETTLEMENT_CURRENCY_OPERATOR`; `ADJUDICATION=B`; `FACE_VALUE_CONFLICT_STATUS=UNRESOLVED`; `COVER_USDC_STATUS=UNINSTANTIATED`; `FILL_DETERMINISM_STATUS=UNPROVEN`; `FILLED_POSITION_DERIVED_RUNTIME_AUTHORIZED=false`; `LIVE_AUTHORIZED=false`; no money movement; not execute; funding&#47;Canary remain blocked; historical next pointer superseded by §11.13.5.Z2AA) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.Z2AA | SSOT docs-only earliest Z2Y safety-dependency adjudication (`AUTHORIZED_SCOPE=POST_Z2Z_NEXT_Z2Y_SAFETY_DEPENDENCY_WORK_DOCS_ONLY`; no GET; no order; no funding; `SAFETY_DEPENDENCY_STEP_ADJUDICATION=C`; `Z2Y_AUTHORIZABILITY_ADJUDICATION_REMAINS=B`; `EARLIEST_UNRESOLVED_DEPENDENCY=LIVE_FLATTEN_PROVABILITY`; `EARLIEST_NUMERIC_SAFETY_BLOCKER=FACE_VALUE_CONFLICT`; `LIVE_FLATTEN_STATICALLY_PROVABLE_UNDER_CURRENT_CONTRACT=false`; `VENUE_DOCUMENTED_CLOSE_INCOMPATIBLE_WITH_LIMIT_ONLY_NO_MARKET=true`; `FILL_STATE_MACHINE_STATUS=DOCUMENTED_NOT_ACTIVATED_UNPROVEN`; `WORST_CASE_LOSS_BOUND_STATUS=UNINSTANTIABLE`; `LIVE_FLATTEN_PROVABILITY=UNPROVEN_HARD_STOP`; `FILL_DETERMINISM=UNPROVEN`; `RULE_C_STATUS=UNPROVEN`; `FACE_VALUE_CONFLICT=UNRESOLVED`; `COVER_USDC=UNINSTANTIATED`; `USD_EQUALS_USDC_ASSUMED=false`; `FILLED_POSITION_DERIVED_RUNTIME_AUTHORIZED=false`; `LIVE_AUTHORIZED=false`; no money movement; not execute; funding&#47;Canary remain blocked; historical next pointer superseded by §11.13.5.Z2AB) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.Z2AB | SSOT docs-only productive runtime-proof admissibility adjudication (`AUTHORIZED_SCOPE=POST_Z2AA_PRODUCTIVE_RUNTIME_PROOF_ADMISSIBILITY_DOCS_ONLY`; no GET; no order; no funding; `ADJUDICATION=C`; `PRODUCTIVE_RUNTIME_PROOF_ADMISSIBLE=false`; `GATE_1_EXACT_INSTRUMENT_BINDING=PASS`; `GATE_2_MINIMUM_SIZE=PASS`; `GATE_3_ENTRY_ORDER_POLICY=PASS`; `GATE_4_FLATTEN_CAPABILITY=FAIL`; `GATE_5_PRICE_BOUND_FOR_ENTRY=FAIL`; `GATE_6_PRICE_BOUND_FOR_FLATTEN=FAIL`; `GATE_7_FILL_STATE_MACHINE=UNPROVEN`; `GATE_8_WORST_CASE_LOSS_BOUND=FAIL`; `GATE_9_FUNDING_INDEPENDENCE=PASS`; `GATE_10_RUNTIME_OBSERVABILITY=PASS`; `WORST_CASE_LOSS_BOUND=UNINSTANTIABLE`; `LIVE_FLATTEN_PROVABILITY=UNPROVEN_HARD_STOP`; `FILL_DETERMINISM=UNPROVEN`; `FACE_VALUE_CONFLICT=UNRESOLVED`; `COVER_USDC=UNINSTANTIATED`; `FUNDING_PREREQUISITE=UNSATISFIED`; `USD_EQUALS_USDC_ASSUMED=false`; `ORDER_SUBMIT_AUTHORIZED=false`; `FILLED_POSITION_DERIVED_RUNTIME_AUTHORIZED=false`; `LIVE_AUTHORIZED=false`; no money movement; not execute; funding&#47;Canary remain blocked; historical next pointer superseded by §11.13.5.Z2AC) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.Z2AC | SSOT docs-only persist of the already-completed LF-06 venue-semantics adjudication (`AUTHORIZED_SCOPE=LF_06_SSOT_PERSIST_ONLY`; no GET; no order; no funding; `LF_06_OVERALL_ADJUDICATION=NOT_PASS`; `CLAIM_LF06_01=PROVEN`; `CLAIM_LF06_02=PARTIALLY_PROVEN`; `CLAIM_LF06_03=PROVEN`; `CLAIM_LF06_04=PARTIALLY_PROVEN`; `CLAIM_LF06_05=PARTIALLY_PROVEN`; `CLAIM_LF06_06=PARTIALLY_PROVEN`; `CLAIM_LF06_07=UNPROVEN`; `CLAIM_LF06_08=PARTIALLY_PROVEN`; `CLAIM_LF06_09=UNPROVEN`; `CLAIM_LF06_10=UNPROVEN`; `REDUCE_ONLY_ENDPOINT_SUPPORT=DOCUMENTED_PROVEN_ON_POST_&#47;api&#47;v5&#47;trade&#47;order`; `REDUCE_ONLY_WIRE_TYPE_STATUS=PARTIALLY_PROVEN_REQUEST_BOOLEAN_RESPONSE_STRING_PRODUCTIVE_UNPROVEN`; `NET_MODE_POS_SIDE_STATUS=PARTIALLY_PROVEN`; `OVERSHOOT_PROTECTION_STATUS=UNPROVEN`; `ZERO_CROSS_FLIP_PROTECTION_STATUS=UNPROVEN`; `RACE_SHRINK_BEHAVIOR_STATUS=UNPROVEN`; `FLATTEN_PRICE_POLICY_OPERATIONALLY_USABLE=false`; `RUNTIME_REACHABLE=false`; `LF_07_AUTHORIZED=false`; `LIVE_FLATTEN_PROVABILITY=UNPROVEN_HARD_STOP`; `GATE_4_FLATTEN_CAPABILITY_REMAINS=FAIL`; `LIVE_AUTHORIZED=false`; no money movement; not execute; funding&#47;Canary remain blocked; historical next pointer superseded by §11.13.5.Z2AD) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.Z2AD | SSOT docs-only persist of the already-completed LF-07 productive-reachability adjudication (`AUTHORIZED_SCOPE=LF_07_SSOT_PERSIST_ONLY`; no GET; no order; no funding; `LF_07_ADJUDICATION=B`; `LF_07_ADJUDICATION_CLASS=PRODUCTIVE_REACHABILITY_NOT_ADMISSIBLE`; `PRODUCTIVE_REACHABILITY_ADMISSIBLE=false`; `FLATTEN_RUNTIME_REACHABLE_TODAY=false`; `EXISTING_EXECUTE_PATH_CAN_REACH_FLATTEN=false`; `FAIL_CLOSED_NEUTRALIZES_UNPROVEN_VENUE_SEMANTICS=false`; `OVERSHOOT_PROTECTION_STATUS=UNPROVEN`; `ZERO_CROSS_FLIP_PROTECTION_STATUS=UNPROVEN`; `RACE_SHRINK_BEHAVIOR_STATUS=UNPROVEN`; `GATE_4_FLATTEN_CAPABILITY_REMAINS=FAIL`; `GATE_6_PRICE_BOUND_FOR_FLATTEN_REMAINS=FAIL`; `GATE_8_WORST_CASE_LOSS_BOUND=UNINSTANTIABLE`; `LF_08_AUTHORIZED=false`; `LF_08_STARTED=false`; `LIVE_FLATTEN_PROVABILITY=UNPROVEN_HARD_STOP`; `LIVE_AUTHORIZED=false`; no money movement; not execute; funding&#47;Canary remain blocked; historical next pointer superseded by §11.13.5.Z2AE) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.Z2AE | SSOT docs-only persist of the already-completed LF-08 `LIVE_FLATTEN_PROVABILITY` re-adjudication (`AUTHORIZED_SCOPE=LF_08_SSOT_PERSIST_ONLY`; no GET; no order; no funding; `LF_08_ADJUDICATION=B`; `LF_08_ADJUDICATION_CLASS=LIVE_FLATTEN_PROVABILITY_UNPROVEN`; `LIVE_FLATTEN_PROVABILITY=UNPROVEN`; `LIVE_FLATTEN_PROVABILITY_REMAINS=UNPROVEN_HARD_STOP`; `MECHANISM_IMPLEMENTED=PARTIAL_OFFLINE_ONLY`; `OFFLINE_TEST_COVERAGE_SUFFICIENT_FOR_OFFLINE_CONTRACT=true`; `LIMIT_PRICE_CONTRACT_STATUS=PARTIAL_FAIL_CLOSED_NO_OPERATIONAL_PRICE`; `VENUE_SEMANTICS_FULLY_PROVEN=false`; `PRODUCTIVE_REACHABILITY_ADMISSIBLE=false`; `PRODUCTIVE_RUNTIME_PROOF_AVAILABLE=false`; `NEW_ADMISSIBLE_EVIDENCE_SINCE_LF_07=false`; `DOCS_PERSIST_IS_NOT_ADMISSIBLE_PRODUCTIVE_EVIDENCE=true`; `IMPLEMENTED_PLUS_OFFLINE_TESTED_IS_NOT_PRODUCTIVE_PROOF=true`; `FAIL_CLOSED_NEUTRALIZES_UNPROVEN_VENUE_SEMANTICS=false`; `LF_06_OVERALL_ADJUDICATION=NOT_PASS`; `OVERSHOOT_PROTECTION_STATUS=UNPROVEN`; `ZERO_CROSS_FLIP_PROTECTION_STATUS=UNPROVEN`; `RACE_SHRINK_BEHAVIOR_STATUS=UNPROVEN`; `GATE_4_FLATTEN_CAPABILITY_REMAINS=FAIL`; `GATE_6_PRICE_BOUND_FOR_FLATTEN_REMAINS=FAIL`; `GATE_8_WORST_CASE_LOSS_BOUND=UNINSTANTIABLE`; `LAST_CANONICALLY_CLOSED_STEP=LF_08`; `LF_09_AUTHORIZED=false`; `LF_09_STARTED=false`; `LIVE_AUTHORIZED=false`; no money movement; not execute; funding&#47;Canary remain blocked; historical next pointer superseded by §11.13.5.Z2AF) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.Z2AF | SSOT docs-only persist of the already-completed LF-09 blocker-DAG re-adjudication (`AUTHORIZED_SCOPE=LF_09_SSOT_PERSIST_ONLY`; no GET; no order; no funding; `LF_09_READ_ONLY_ADJUDICATION=COMPLETE`; `BLOCKER_DAG_CHANGED=false`; `LF_08_ADJUDICATION=B`; `LF_08_DID_NOT_CLOSE_LIVE_FLATTEN_PROVABILITY=true`; `LIVE_FLATTEN_PROVABILITY=UNPROVEN`; `LIVE_FLATTEN_PROVABILITY_REMAINS=UNPROVEN_HARD_STOP`; `FACE_VALUE_AUTHORITY=CONFLICTED`; `PARALLEL_NUMERIC_ROOT=FACE_VALUE_AUTHORITY_CONFLICT`; `RULE_C_STATUS=UNPROVEN`; `USD_USDC_OPERATOR=UNPROVEN`; `COVER_USDC_STATUS=UNINSTANTIATED`; `FUNDING=UNSATISFIED_NUMERIC_NONE`; `ENTRY_WORST_CASE_LOSS=UNINSTANTIABLE`; `FLATTEN_WORST_CASE_LOSS=UNINSTANTIABLE`; `PRODUCTIVE_REACHABILITY=NOT_ADMISSIBLE`; `FILL_DETERMINISM=UNPROVEN`; `CANARY_ADMISSIBILITY=NOT_ADMISSIBLE`; `PRODUCTIVE_RUNTIME_PROOF_ADMISSIBLE=false`; `NEW_ADMISSIBLE_PRODUCTIVE_EVIDENCE=false`; `LAST_CANONICALLY_CLOSED_STEP=LF_09`; `LF_10_AUTHORIZED=false`; `LF_10_STARTED=false`; `LIVE_AUTHORIZED=false`; no money movement; not execute; funding&#47;Canary remain blocked; historical next pointer superseded by §11.13.5.Z2AG) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.Z2AG | SSOT docs-only persist of the scoped API ctVal sizing authority split (`AUTHORIZED_SCOPE=Z2AG_SCOPED_API_CTVAL_SIZING_AUTHORITY_SPLIT_DOCS_ONLY`; no GET; no order; no funding; `DOCUMENTARY_FACE_VALUE_CONFLICT=CONFLICTED`; `OEM_SPEC_WRONG=false`; `GLOBAL_API_WINS=false`; `SILENT_OEM_DEFEAT=false`; `FACE_VALUE_CONFLICT_RESOLVED_GLOBALLY=false`; `API_EXECUTION_PRECEDENCE_RULE_STATUS=PROVEN_SCOPED_OKX_AGENT_TRADE_KIT_SWAP_FUTURES_OPTION_ORDER_SIZING_USE_INSTRUMENTS_CTVAL_DO_NOT_ASSUME`; `OPERATIVE_RUNTIME_CONTRACT_FACE_VALUE_FOR_API_SIZING=0.0001_BTC`; `API_SIZING_NOTIONAL=6.44085`; `API_SIZING_NOTIONAL_CLASS=API_SIZING_AND_INTERNAL_NOTIONAL_ENVELOPE_NOT_COVER_USDC_NOT_OEM_SETTLEMENT`; `COVER_USDC_STATUS=UNINSTANTIATED`; `SETTLEMENT_PNL=UNPROVEN`; `LIVE_FLATTEN_PROVABILITY=UNPROVEN`; `LF_10_AUTHORIZED=false`; `LIVE_AUTHORIZED=false`; no money movement; not execute; funding&#47;Canary remain blocked; historical next pointer superseded by §11.13.5.Z2AH) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.Z2AH | SSOT docs-only persist of the API execution denomination PROVEN adjudication (`AUTHORIZED_SCOPE=Z2AH_API_EXECUTION_DENOMINATION_PROVEN_DOCS_ONLY`; no GET; no order; no funding; `API_EXECUTION_DENOMINATION_STATUS=PROVEN`; `API_EXECUTION_CTVAL=0.0001_BTC`; `API_EXECUTION_CTMULT=1`; `API_EXECUTION_LOTSZ=1`; `API_EXECUTION_MINSZ=1`; `API_SIZING_AUTHORITY=INSTRUMENT_SPECIFIC_CTVAL_DO_NOT_ASSUME_OEM_OR_PRODUCT_CONTRACT_SIZE`; `OEM_DOCUMENTARY_CONTRACT_SIZE=0.01_BTC`; `OEM_DOCUMENTARY_FACE_VALUE_STATUS=RETAINED_NOT_ADJUDICATED_WRONG`; `OEM_SPEC_WRONG=false`; `GLOBAL_API_WINS=false`; `OEM_TO_API_100_TO_1_BRIDGE=INFERRED_NOT_PROVEN`; `OEM_TO_API_100_TO_1_BRIDGE_ALLOWED_FOR_API_SIZING=false`; `FACE_VALUE_CONFLICT_AS_API_NUMERIC_SAFETY_BLOCKER=CLOSED`; `FACE_VALUE_CONFLICT_AS_DOCUMENTARY_CONFLICT=OPEN_QUARANTINED`; `FAIL_CLOSED_CTVAL_GUARD_STATUS=REQUIRED`; `COVER_USDC_STATUS=UNINSTANTIATED`; `SETTLEMENT_PNL=UNPROVEN`; `LIVE_FLATTEN_PROVABILITY=UNPROVEN`; `LF_10_AUTHORIZED=false`; `LIVE_AUTHORIZED=false`; no money movement; not execute; funding&#47;Canary remain blocked; historical next pointer superseded by §11.13.5.Z2AI) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.Z2AI | SSOT docs-only persist of the already-completed LF-10 read-only adjudication (`AUTHORIZED_SCOPE=LF_10_SSOT_PERSIST_ONLY`; no GET; no order; no funding; `LF10_ADJUDICATION=COMPLETE_READ_ONLY_NO_NEW_PROVEN_CLOSURE`; `CLAIMS_PROVEN_THIS_STEP=NONE`; `NEW_EVIDENCE_FOUND=false`; `API_EXECUTION_DENOMINATION_STATUS=PROVEN`; `OEM_TO_API_100_TO_1_BRIDGE=INFERRED_NOT_PROVEN`; `POSITION_VALUE_STATUS=UNPROVEN_AS_UNIFIED_EXCHANGE_OR_OEM_VALUE`; `QTY_1_EXPOSURE_STATUS=API_SZ1_UNDERLYING_0.0001_BTC_PROVEN_OEM_QTY1_UNPROVEN_UNIFIED_UNPROVEN`; `EXPIRY_FEE_MONETARY_BASE_STATUS=OEM_OKX_IDENTITY_UNPROVEN`; `SETTLEMENT_PNL_STATUS=UNPROVEN`; `USD_USDC_OPERATOR_STATUS=UNPROVEN`; `FACE_VALUE_CONFLICT_AS_API_NUMERIC_SAFETY_BLOCKER=CLOSED`; `FACE_VALUE_CONFLICT_AS_DOCUMENTARY_CONFLICT=OPEN_QUARANTINED`; `COVER_USDC=UNINSTANTIATED`; `LIVE_FLATTEN_PROVABILITY=UNPROVEN_HARD_STOP`; `PRODUCTIVE_REACHABILITY=NOT_ADMISSIBLE`; `LAST_CANONICALLY_CLOSED_STEP=LF_10`; `LF_11_AUTHORIZED=false`; `LIVE_AUTHORIZED=false`; no money movement; not execute; funding&#47;Canary remain blocked; historical next pointer superseded by §11.13.5.Z2AJ) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.Z2AJ | SSOT docs-only persist of the already-completed USD&#47;USDC public conversion-candidate GET adjudication (`AUTHORIZED_SCOPE=Z2AJ_USD_USDC_PUBLIC_GET_ADJUDICATION_SSOT_PERSIST_ONLY`; no new GET; no authenticated request; no order; no funding; `ADJUDICATION_RESULT=C_UNPROVEN`; `CLAIMS_NEWLY_PROVEN_THIS_STEP=NONE`; `PUBLIC_CONVERSION_CANDIDATE_SURFACES_ADJUDICATED=true`; `USDC_USD_INDEX_1_NON_OPERATOR_NEGATIVE_CONTRACT=true`; `GET_1_OKX_CODE=0`; `GET_1_IDXPX=1`; `GET_2_OKX_CODE=51001`; `GET_3_OKX_CODE=51001`; `GET_4_OKX_CODE=51001`; `IDXPX_USDC_USD_1_IS_COVER_USDC_OPERATOR=false`; `USD_EQUALS_USDC_ASSUMED=false`; `NUMERIC_USD_USDC_OPERATOR_FOUND=false`; `USD_USDC_OPERATOR_STATUS=UNPROVEN`; `NO_CLIENT_CONVERSION_REQUIRED_PROVEN=false`; `CLIENT_FX_REQUIRED=UNPROVEN`; `COVER_USDC_STATUS=UNINSTANTIATED`; `SETTLEMENT_PNL_STATUS=UNPROVEN`; `LIVE_FLATTEN_PROVABILITY_STATUS=UNPROVEN_HARD_STOP`; `CONVERSION_NUMERIC_STATUS=UNINSTANTIATED_REQUIRES_LATER_PRODUCTIVE_USD_USDC_EVIDENCE`; `REPEAT_PUBLIC_USDC_USD_INDEX_OR_SPOT_GET_WITHOUT_NEW_DISCRIMINATING_HYPOTHESIS=FORBIDDEN`; `LAST_CANONICALLY_CLOSED_STEP=LF_10`; `LF_11_AUTHORIZED=false`; `LIVE_AUTHORIZED=false`; no money movement; not execute; funding&#47;Canary remain blocked; historical next pointer superseded by §11.13.5.Z2AK) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.Z2AK | SSOT docs-only persist of the already-completed LF-11 and LF-12 read-only adjudications (`AUTHORIZED_SCOPE=LF_11_AND_LF_12_SSOT_PERSIST_ONLY`; no GET; no order; no funding; `LF11_ADJUDICATION=C_UNPROVEN`; `LF12_ADJUDICATION=C_PREREQUISITES_NOT_CLOSED_PRODUCTIVE_FLATTEN_NOT_ADMISSIBLE`; `LIVE_FLATTEN_PROVABILITY=UNPROVEN`; `EXISTING_EVIDENCE_SUFFICIENT=false`; `FLATTEN_RUNTIME_REACHABILITY=ABSENT`; `FLATTEN_PRICE_BINDING=ABSENT`; `ORDER_COUNT_LIMIT_RAISE_TO_2_FORBIDDEN=true`; `CAN_LIVE_FLATTEN_BE_AUTHORIZED_SAFELY_NOW=false`; `ARCHIVED_EVIDENCE_AUTHORITY_CLASSIFICATION=INSPECTED_NOT_CANONICAL`; `LAST_CANONICALLY_CLOSED_STEP=LF_12`; `LIVE_AUTHORIZED=false`; no money movement; not execute; funding&#47;Canary remain blocked; historical next pointer superseded by §11.13.5.Z2AL) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.Z2AL | SSOT persist of static flatten price policy and dedicated flatten transport (`AUTHORIZED_SCOPE=STATIC_FLATTEN_PREREQUISITES_IMPLEMENTATION_ONLY`; no GET; no productive POST; `FLATTEN_PRICE_POLICY_IMPLEMENTED=true`; `FLATTEN_PRICE_POLICY_FULLY_BOUND=false`; `DEDICATED_FLATTEN_TRANSPORT_IMPLEMENTED=true`; `DEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED=false`; `REDUCE_ONLY_FLATTEN_INTENT_IMPLEMENTED=true`; `STATIC_FLATTEN_PREREQUISITES_STATUS=PASS_OFFLINE`; `LIVE_FLATTEN_PROVABILITY=UNPROVEN`; `ORDER_COUNT_LIMIT=1`; `CLOSE_POSITION_ENDPOINT_ALLOWLISTED=false`; `LAST_CANONICALLY_CLOSED_STEP=LF_12`; `LIVE_AUTHORIZED=false`; no money movement; not execute; funding&#47;Canary remain blocked; historical next pointer superseded by §11.13.5.Z2AM) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.Z2AM | SSOT docs-only persist of the already-completed post-Z2AL Owner-binding adjudication (`AUTHORIZED_SCOPE=POST_Z2AL_READ_ONLY_OWNER_BINDING_ADJUDICATION_SSOT_PERSIST_ONLY`; no GET; no order; no funding; `FRESHNESS_BINDING=OWNER_RATIFICATION_REQUIRED`; `FRESHNESS_PROVEN_EXISTING_THRESHOLD=NONE`; `FRESHNESS_UNRATIFIED_POLICY=NO_CANONICAL_DEFAULT_REMAINS_EXPLICIT`; `FRESHNESS_CANONICAL_DEFAULT=NONE`; `TEST_FIXTURE_5000_PROMOTED_TO_POLICY=false`; `MD_DEFAULT_5S_PROMOTED_TO_POLICY=false`; `TESTNET_DEFAULT_120S_PROMOTED_TO_POLICY=false`; `EXTRA_DEVIATION_BOUND=NOT_PROVEN_REQUIRED`; `EXTRA_DEVIATION_SAFETY_INVARIANT=NOT_PROVEN`; `EXTRA_DEVIATION_DEFENSE_IN_DEPTH=OPTIONAL_UNRATIFIED_CURRENTLY_REJECTED`; `Z2P_SLIPPAGE_RESERVE_NUMERIC_CLASS=COVER_ALGEBRA_NOT_FLATTEN_PX_GUARD`; `FLATTEN_PRICE_POLICY_IMPLEMENTED=true`; `FLATTEN_PRICE_POLICY_FULLY_BOUND=false`; `NEW_PROVEN_CLOSURE=NONE`; `LIVE_FLATTEN_PROVABILITY=UNPROVEN`; `LAST_CANONICALLY_CLOSED_STEP=LF_12`; `LIVE_AUTHORIZED=false`; no money movement; not execute; funding&#47;Canary remain blocked; historical next pointer superseded by §11.13.5.Z2AN) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.Z2AN | SSOT persist of Owner-ratified flatten `FRESHNESS_THRESHOLD_MS=5000` (`AUTHORIZED_SCOPE=POST_Z2AM_FRESHNESS_THRESHOLD_OWNER_POLICY_RATIFICATION_OFFLINE_ONLY`; no GET; no order; no funding; `OWNER_POLICY_ADJUDICATION=RATIFIED`; `FRESHNESS_THRESHOLD_MS=5000`; `FRESHNESS_THRESHOLD_RATIFIED=true`; `FRESHNESS_BINDING=OWNER_RATIFIED`; `FRESHNESS_POLICY_CLASS=NEW_EXPLICIT_OWNER_RATIFICATION_NOT_FIXTURE_PROMOTION`; `TEST_FIXTURE_5000_PROMOTED_TO_POLICY=false`; `MD_DEFAULT_5S_PROMOTED_TO_POLICY=false`; `TESTNET_DEFAULT_120S_PROMOTED_TO_POLICY=false`; `FIXTURE_VALUES_TREATED_AS_AUTHORITY=false`; `EXTRA_DEVIATION_BOUND=NOT_PROVEN_REQUIRED`; `FLATTEN_PRICE_POLICY_FULLY_BOUND=true`; `DEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED=false`; `LIVE_FLATTEN_PROVABILITY=UNPROVEN`; `LAST_CANONICALLY_CLOSED_STEP=LF_12`; `LIVE_AUTHORIZED=false`; no money movement; not execute; funding&#47;Canary remain blocked; historical next pointer superseded by §11.13.5.Z2AO) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.Z2AO | SSOT docs-only persist of the post-Z2AN extra-deviation-bound offline adjudication (`AUTHORIZED_SCOPE=POST_Z2AN_EXTRA_DEVIATION_BOUND_OFFLINE_READ_ONLY_ADJUDICATION_ONLY`; no GET; no order; no funding; `ADJUDICATION_RESULT=C`; `EXTRA_DEVIATION_BOUND_REQUIRED=false`; `EXTRA_DEVIATION_BOUND_PROVEN=false`; `EXTRA_DEVIATION_BOUND_VALUE=NONE`; `REST_QUOTE_LOCK_SUFFICIENT_WITHOUT_EXTRA_BOUND=true`; `OWNER_POLICY_REQUIRED=false`; `FIXTURE_VALUES_TREATED_AS_AUTHORITY=false`; `FINITE_EXTRA_DEVIATION_BOUND=NOT_OWNER_RATIFIED_REJECTED`; `FRESHNESS_THRESHOLD_MS=5000`; `LIVE_FLATTEN_PROVABILITY=UNPROVEN`; `LAST_CANONICALLY_CLOSED_STEP=LF_12`; `LIVE_AUTHORIZED=false`; no money movement; not execute; funding&#47;Canary remain blocked; historical next pointer superseded by §11.13.5.Z2AP) |
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §11.13.5.Z2AP | SSOT persist of the post-Z2AO live-flatten closure work package (`AUTHORIZED_SCOPE=POST_Z2AO_LIVE_FLATTEN_CLOSURE_WORK_PACKAGE_TO_NEXT_SAFETY_BOUNDARY`; no GET; no order; no funding; `TERMINAL_CLASS=B`; `PRODUCTIVE_PROOF_READY=true`; `FLATTEN_POST_ACTION_PROOF_CONTRACT_IMPLEMENTED=true`; `OWNER_BINDING_STILL_REQUIRED=LIVE_WIRE_AND_PRODUCTIVE_FLATTEN_SEPARATE_OWNER_GO`; `EXTRA_DEVIATION_BOUND_REQUIRED=false`; `DEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED=false`; `LIVE_FLATTEN_PROVABILITY=UNPROVEN`; `LAST_CANONICALLY_CLOSED_STEP=LF_12`; `LIVE_AUTHORIZED=false`; no money movement; not execute; funding&#47;Canary remain blocked) |
| [`evidence&#47;ops&#47;section_11_13_5_live_canary_forensic_reconciliation_v1&#47;20260812T120000Z&#47;`](../../evidence/ops/section_11_13_5_live_canary_forensic_reconciliation_v1/20260812T120000Z/) | Owner §11.13.5 sealed forensic classification + authoring evidence (derived; non-SSOT; no productive network; writes&#47;orders=0; `MANIFEST_VERIFY_RC=0`; Live unauthorized) |
| [`evidence&#47;ops&#47;section_11_13_5_b_pr_5879_squash_merge_and_pre_canary_readiness_v1&#47;20260812T123500Z&#47;`](../../evidence/ops/section_11_13_5_b_pr_5879_squash_merge_and_pre_canary_readiness_v1/20260812T123500Z/) | Owner §11.13.5.B PR `#5879` squash-merge closeout + pre-Canary dependency resolution (derived; non-SSOT; no execute; `MANIFEST_VERIFY_RC=0`) |
| [`evidence&#47;ops&#47;section_11_13_5_live_canary_trade_capability_attestation_v1&#47;20260812T135723Z&#47;`](../../evidence/ops/section_11_13_5_live_canary_trade_capability_attestation_v1/20260812T135723Z/) | Owner §11.13.5.C trade-key attestation proven evidence (derived; non-SSOT; no secret values; no orders; `MANIFEST_VERIFY_RC=0`) |
| [`evidence&#47;ops&#47;section_11_13_5_exchange_truth_adoption_v1&#47;20260812T151147Z&#47;`](../../evidence/ops/section_11_13_5_exchange_truth_adoption_v1/20260812T151147Z/) | Owner §11.13.5.D Exchange Truth Adoption evidence (derived; non-SSOT; no secret values; no orders; `MANIFEST_VERIFY_RC=0`) |
| [`evidence&#47;ops&#47;section_11_13_5_economic_baseline_and_okx_clearance_v1&#47;20260812T153425Z&#47;`](../../evidence/ops/section_11_13_5_economic_baseline_and_okx_clearance_v1/20260812T153425Z/) | Owner §11.13.5.E economic baseline + OKX clearance evidence (derived; non-SSOT; GET-only private-read; no orders; `MANIFEST_VERIFY_RC=0`) |
| [`evidence&#47;ops&#47;section_11_13_5_okx_temp_security_clearance_evidence_collection_v1&#47;20260815T190010Z&#47;`](../../evidence/ops/section_11_13_5_okx_temp_security_clearance_evidence_collection_v1/20260815T190010Z/) | Owner §11.13.5.E1 fresh OKX temp-security clearance evidence (derived; non-SSOT; productive withdrawal-UI observation; `CLEARANCE_EVIDENCE=PASS`; no withdrawals&#47;P2P sell&#47;orders; `MANIFEST_VERIFY_RC=0`) |
| [`evidence&#47;ops&#47;section_11_13_5_live_canary_cybersecurity_gate_reevaluation_v1&#47;20260815T193911Z&#47;`](../../evidence/ops/section_11_13_5_live_canary_cybersecurity_gate_reevaluation_v1/20260815T193911Z/) | Owner §11.13.5.F forensic Live-Canary cybersecurity-gate reevaluation PASS (derived; non-SSOT; `21&#47;21` proven; no orders&#47;withdrawals&#47;P2P sell; `MANIFEST_VERIFY_RC=0`) |
| [`evidence&#47;ops&#47;section_11_13_5_okx_50124_oneshot_post_classification_v1&#47;20260816T002530Z&#47;`](../../evidence/ops/section_11_13_5_okx_50124_oneshot_post_classification_v1/20260816T002530Z/) | Owner §11.13.5.J one-shot POST 401&#47;50124 classification evidence (derived; non-SSOT; `account&#47;instruments` separate diagnostic HTTP 200 empty SWAP, `NOT_ON_SUBMIT_PATH`, `CAUSAL_RELATION_UNPROVEN`; no trading POST in this pack; `ROOT_CAUSE_PROVEN=false`) |
| [`evidence&#47;ops&#47;section_11_13_5_post_k_cross_imr_leverage_get_bind_v1&#47;20260816T033800Z&#47;`](../../evidence/ops/section_11_13_5_post_k_cross_imr_leverage_get_bind_v1/20260816T033800Z/) | Owner §11.13.5.L post-K GET bind evidence (derived; non-SSOT; GET-only; `SET_ACCOUNT_LEVERAGE=3`; snapshot theoretical IM floor; not operational funding min; no orders; `MANIFEST_VERIFY_RC=0`) |
| [`evidence&#47;ops&#47;section_11_13_5_operational_funding_get_evidence_v1&#47;20260816T060349Z&#47;`](../../evidence/ops/section_11_13_5_operational_funding_get_evidence_v1/20260816T060349Z/) | Owner §11.13.5.S operational funding GET evidence (derived; non-SSOT; GET-only; fresh markPx; max-avail-size `availBuy=0`; not operational funding amount; no orders; `MANIFEST_VERIFY_RC=0`) |
| [`evidence&#47;ops&#47;section_11_13_5_v_fresh_xperp_trade_fee_get_evidence_v1&#47;20260816T075803Z&#47;`](../../evidence/ops/section_11_13_5_v_fresh_xperp_trade_fee_get_evidence_v1/20260816T075803Z/) | Owner §11.13.5.W fresh XPerp trade-fee GET evidence (derived; non-SSOT; GET-only; ratified query; `TAKER_RATE=-0.0005`; `FEE_RATE_RT=0.0010`; not funding amount; no orders; `MANIFEST_VERIFY_RC=0`) |
| [`evidence&#47;ops&#47;section_11_13_5_z2g_current_markpx_public_get_v1&#47;20260818T200745Z&#47;`](../../evidence/ops/section_11_13_5_z2g_current_markpx_public_get_v1/20260818T200745Z/) | Owner §11.13.5.Z2G current markPx public GET evidence (derived; non-SSOT; GET-only; public `&#47;api&#47;v5&#47;public&#47;mark-price`; `markPx=64495.3`; observational not OKX expiry-fee operand; not Cover USDC; no credentials; no orders; `MANIFEST_VERIFY_RC=0`) |
| [`evidence&#47;ops&#47;section_11_13_5_z2h_current_ticker_bid_ask_public_get_v1&#47;20260818T203435Z&#47;`](../../evidence/ops/section_11_13_5_z2h_current_ticker_bid_ask_public_get_v1/20260818T203435Z/) | Owner §11.13.5.Z2H current ticker bid&#47;ask public GET evidence (derived; non-SSOT; GET-only; public `&#47;api&#47;v5&#47;market&#47;ticker`; `bidPx=64529.9`; `askPx=64530`; observational not numeric slippage reserve; not Cover USDC; no credentials; no orders; `MANIFEST_VERIFY_RC=0`) |
| [`evidence&#47;ops&#47;section_11_13_5_z2k_current_public_tier_mmr_public_get_v1&#47;20260819T085545Z&#47;`](../../evidence/ops/section_11_13_5_z2k_current_public_tier_mmr_public_get_v1/20260819T085545Z/) | Owner §11.13.5.Z2K current public-tier MMR public GET evidence (derived; non-SSOT; GET-only; public `&#47;api&#47;v5&#47;public&#47;position-tiers`; qty=1 `mmr=0.01`; observational not numeric MM/Liq buffer; not Cover USDC; no credentials; no orders; `MANIFEST_VERIFY_RC=0`) |
| [`evidence&#47;ops&#47;section_11_13_5_z2m_fee_reserve_rates_rebind_get_v1&#47;20260819T102325Z&#47;`](../../evidence/ops/section_11_13_5_z2m_fee_reserve_rates_rebind_get_v1/20260819T102325Z/) | Owner §11.13.5.Z2N bind of PR `#5966` authenticated fee-reserve rates rebind GET evidence (derived; non-SSOT; GET already executed prior GO; `takerUSDC=-0.0005`; `makerUSDC=-0.0002`; rates proven not Cover USDC; no GET this persist; no orders; `MANIFEST_VERIFY_RC=0`) |
| [`evidence&#47;ops&#47;section_11_13_5_z2v_negative_account_runtime_probe_v1&#47;20260820T125156Z&#47;`](../../evidence/ops/section_11_13_5_z2v_negative_account_runtime_probe_v1/20260820T125156Z/) | Owner §11.13.5.Z2V bind of already-completed independent account-runtime GET probe (derived; non-SSOT; GET already executed prior GO; empty positions; `totalEq=0`; estimate zeros non-discriminating; not Cover USDC; no new GET this persist; no orders; `MANIFEST_VERIFY_RC=0`) |
| [`docs/ops/specs/SECTION_11_13_5_LIVE_CANARY_MINIMUM_EXPOSURE_V1.md`](../ops/specs/SECTION_11_13_5_LIVE_CANARY_MINIMUM_EXPOSURE_V1.md) | Derived §11.13.5 package spec (non-SSOT) |
| [`docs/ops/specs/SECTION_11_13_5_OWNER_EXECUTE_INPUT_CONTRACT_V1.md`](../ops/specs/SECTION_11_13_5_OWNER_EXECUTE_INPUT_CONTRACT_V1.md) | Owner execute-time input checklist for future canary (non-SSOT; no invented values) |
| [`docs/ops/specs/SECTION_11_13_3_OWNER_EXECUTE_INPUT_CONTRACT_V1.md`](../ops/specs/SECTION_11_13_3_OWNER_EXECUTE_INPUT_CONTRACT_V1.md) | Owner execute-time input checklist (non-SSOT; no invented values) |
| [`evidence&#47;ops&#47;section_11_12_8_close_okx_eea_demo_path_external_capability_unavailable_and_evaluate_alternate_derivatives_testnet_no_order_v1&#47;20260810T143709Z&#47;`](../../evidence/ops/section_11_12_8_close_okx_eea_demo_path_external_capability_unavailable_and_evaluate_alternate_derivatives_testnet_no_order_v1/20260810T143709Z/) | OKX EEA Demo path closeout &#47; no-order alternate evaluation (non-activating) |
| [`evidence&#47;ops&#47;section_11_12_8_okx_global_demo_venue_host_account_instrument_binding_v1&#47;20260810T151323Z&#47;`](../../evidence/ops/section_11_12_8_okx_global_demo_venue_host_account_instrument_binding_v1/20260810T151323Z/) | Historical OKX Global Demo binding package evidence (NO_ORDER; not active) |
| [`evidence&#47;ops&#47;section_11_12_8_retry_okx_eea_private_ro_xperp_verify_no_order_v1&#47;20260810T165847Z&#47;`](../../evidence/ops/section_11_12_8_retry_okx_eea_private_ro_xperp_verify_no_order_v1/20260810T165847Z/) | Bound private READ-only XPerp capability proof (NO_ORDER) |
| [`evidence&#47;ops&#47;section_11_12_8_okx_eea_demo_xperp_venue_host_account_instrument_binding_v1&#47;20260810T171225Z&#47;`](../../evidence/ops/section_11_12_8_okx_eea_demo_xperp_venue_host_account_instrument_binding_v1/20260810T171225Z/) | Active OKX EEA Demo XPerp binding package evidence (NO_ORDER) |

```text
THIS_SECTION_DEFINES_NO_SEMANTICS=true
SECTION_11_12_8_CLOSED=true
SECTION_11_13_STARTED=true
SECTION_11_13_LIVE_READINESS_EVALUATION_COMPLETED=true
SECTION_11_13_LIVE_SHADOW_CANARY_PROGRESSION_STARTED=false
FULLY_AUTONOMOUS_LIVE_TRADING_READY=false
LIVE_AUTHORIZED=false
PRE_LIVE_CYBERSECURITY_GATE=PASS
SECTION_11_12_9_EVALUATION_COMPLETED=true
SECTION_11_12_9_GATE_PASS=true
ELIGIBLE_FOR_LIVE_READINESS_EVALUATION=true
OKX_EEA_DEMO_PRODUCTIVE_ORDER_PATH_STATUS=CLOSED_EXTERNAL_CAPABILITY_UNAVAILABLE
OKX_GLOBAL_DEMO_BINDING_PACKAGE_STATUS=PREPARED_NO_ORDER_NOT_ACTIVATED_SUPERSEDED_BY_SECTION_11_12_8_5
OKX_EEA_DEMO_XPERP_BINDING_PACKAGE_STATUS=PREPARED_NO_ORDER_ACTIVE_BINDING
SECTION_11_12_8_STATUS=CLOSED_OKX_EEA_DEMO_XPERP_BOUNDED_CAMPAIGN_AND_CLEAN_CLOSEOUT_PROVEN
CANONICAL_ACTIVE_VENUE_BINDING=OKX_EEA_DEMO
CANONICAL_ACTIVE_HOST_BINDING=https://eea.okx.com
CANONICAL_ACTIVE_INSTRUMENT=BTC-USD_UM_XPERP-310328
CANONICAL_ACTIVE_INSTRUMENT_TYPE=FUTURES
CANONICAL_ACTIVE_RULE_TYPE=xperp
BTC_USDT_SWAP_PATH_STATUS=CLOSED_DEPRECATED_HISTORICAL_EVIDENCE_ONLY
BTC-USD_UM_XPERP-310328=ONLY_ACTIVE_SECTION_11_12_8_DERIVATIVES_CAMPAIGN_PATH
ACTIVE_SECTION_11_12_8_DERIVATIVES_CAMPAIGN_PATH=OKX_EEA_DEMO_XPERP
LEGACY_BTC_USDT_SWAP_ACTIVE_BINDING_REMOVED=true
OKX_GLOBAL_DEMO_ACTIVE_BINDING=false
PACKAGE_DEFAULT_ORDER_POST_AUTHORIZED=false
SWAP_RUNTIME_FALLBACK=false
SWAP_WRITE_AUTHORIZATION=false
XPERP_ONLY_ACTIVE_WRITE_SCOPE=true
CAMPAIGN_EXECUTION_PASS=true
CLORDID_HYPHEN_DEFECT_CLOSED=true
CANCEL_INSTID_DEFECT_CLOSED=true
ORDER_ACK_PROVEN=true
CLEAN_CLOSEOUT_PROOF_PASS=true
SECTION_11_12_8_CLOSEOUT_RECOMMENDED=false
ORDER_LIFECYCLE_PROOF_PASS=true
CAP_11_12_TESTNET_PROGRAM_CLOSED=true
TESTNET_ORDER_LIFECYCLE_PROVEN=true
TESTNET_RECONCILIATION_PROVEN=true
TESTNET_RESTART_PROVEN=true
TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN=true
TESTNET_DUPLICATE_ORDER_PREVENTION_PROVEN=true
TESTNET_KILL_SWITCH_PROVEN=true
TESTNET_AUTONOMOUS_RECOVERY_PROVEN=true
LONG_RUNNING_TESTNET_PROVEN=true
SECTION_11_12_1_RESIDUAL_PROOF_PASS=true
SECTION_11_12_1_RESIDUAL_BOUND=true
SECTION_11_12_2_RESIDUAL_PROOF_PASS=true
SECTION_11_12_2_RESIDUAL_BOUND=true
SECTION_11_12_3_RESIDUAL_PROOF_PASS=true
SECTION_11_12_3_RESIDUAL_BOUND=true
SECTION_11_12_4_RESIDUAL_PROOF_PASS=true
SECTION_11_12_4_RESIDUAL_BOUND=true
SECTION_11_12_5_RESIDUAL_PROOF_PASS=true
SECTION_11_12_5_RESIDUAL_BOUND=true
SECTION_11_12_6_RESIDUAL_PROOF_PASS=true
SECTION_11_12_6_RESIDUAL_BOUND=true
SECTION_11_12_7_RESIDUAL_PROOF_PASS=true
SECTION_11_12_7_RESIDUAL_BOUND=true
SECTION_11_12_8_RESIDUAL_PROOF_PASS=true
SECTION_11_12_8_RESIDUAL_BOUND=true
SECTION_11_12_9_11_RESIDUAL_PROOF_PASS=true
SECTION_11_12_9_11_RESIDUAL_BOUND=true
SECTION_11_12_9_12_PROOF_PASS=true
SECTION_11_12_9_12_PROOF_BOUND=true
SECTION_11_12_9_13_PROOF_PASS=true
SECTION_11_12_9_13_PROOF_BOUND=true
SECTION_11_12_9_14_PROOF_PASS=true
SECTION_11_12_9_14_PROOF_BOUND=true
SECTION_11_12_9_15_PROOF_PASS=true
SECTION_11_12_9_15_PROOF_BOUND=true
SECTION_11_12_9_16_PROOF_PASS=true
SECTION_11_12_9_16_PROOF_BOUND=true
SECTION_11_12_9_17_PROOF_PASS=true
SECTION_11_12_9_17_PROOF_BOUND=true
SECTION_11_12_9_18_PROOF_PASS=true
SECTION_11_12_9_18_PROOF_BOUND=true
SECTION_11_12_9_19_PROOF_PASS=true
SECTION_11_12_9_19_PROOF_BOUND=true
SECTION_11_12_9_20_REEVAL_PASS=true
SECTION_11_12_9_20_REEVAL_BOUND=true
SECTION_11_12_9_22_REEVAL_PASS=true
SECTION_11_12_9_22_REEVAL_BOUND=true
SECTION_11_12_9_23_ARCHITECTURE_REVIEW_PASS=true
SECTION_11_12_9_23_ARCHITECTURE_REVIEW_BOUND=true
SECTION_11_12_9_24_THREAT_MODEL_PASS=true
SECTION_11_12_9_24_THREAT_MODEL_BOUND=true
SECTION_11_12_9_25_SECRETS_REVIEW_PASS=true
SECTION_11_12_9_25_SECRETS_REVIEW_BOUND=true
SECTION_11_12_9_26_DEPENDENCY_AUDIT_EXECUTED=true
SECTION_11_12_9_26_DEPENDENCY_AUDIT_PASS=false
SECTION_11_12_9_26_DEPENDENCY_AUDIT_BOUND=true
SECTION_11_12_9_27_FORENSIC_REVIEW_EXECUTED=true
SECTION_11_12_9_27_FORENSIC_REVIEW_BOUND=true
FULL_SECURITY_COVERAGE_REVIEW_PROVEN=false
PR_5862_STATE=MERGED
PR_5862_MERGE_COMMIT_SHA=6530fc9e652e9c0c3c6c77bee0cac120bdafc5d8
SECTION_11_12_9_28_DEPENDENCY_AUDIT_REMEDIATION_EXECUTED=true
SECTION_11_12_9_28_DEPENDENCY_AUDIT_RERUN_PASS=true
SECTION_11_12_9_28_DEPENDENCY_AUDIT_RERUN_BOUND=true
PR_5863_STATE=MERGED
PR_5863_MERGE_COMMIT_SHA=b1ebe0f93d88ab22bb147c48fb27e1863b829e5e
SECTION_11_12_9_29_SBOM_PRESENT_EXECUTED=true
SECTION_11_12_9_29_SBOM_PRESENT_PASS=true
SECTION_11_12_9_29_SBOM_PRESENT_BOUND=true
SBOM_AUTHORIZED=true
SBOM_PRESENT=true
SBOM_PRESENT_PROVEN=true
SECTION_11_12_9_30_STATIC_SECURITY_ANALYSIS_EXECUTED=true
SECTION_11_12_9_30_STATIC_SECURITY_ANALYSIS_PASS=false
SECTION_11_12_9_30_STATIC_SECURITY_ANALYSIS_BOUND=true
SECTION_11_12_9_31_STATIC_SECURITY_ANALYSIS_REMEDIATION_EXECUTED=true
SECTION_11_12_9_31_STATIC_SECURITY_ANALYSIS_RERUN_PASS=true
SECTION_11_12_9_31_STATIC_SECURITY_ANALYSIS_RERUN_BOUND=true
STATIC_SECURITY_ANALYSIS=PASS
STATIC_SECURITY_ANALYSIS_PROVEN=true
STATIC_SECURITY_ANALYSIS_AUTHORIZED=true
HIGH_FINDINGS_OPEN=0
CRITICAL_FINDINGS_OPEN=0
SECTION_11_12_9_32_SECURITY_REGRESSION_EXECUTED=true
SECTION_11_12_9_32_SECURITY_REGRESSION_PASS=true
SECTION_11_12_9_32_SECURITY_REGRESSION_BOUND=true
SECURITY_REGRESSION=PASS
SECURITY_REGRESSION_PROVEN=true
SECURITY_REGRESSION_AUTHORIZED=true
SECTION_11_12_9_33_PENETRATION_PROGRAM_EXECUTED=true
SECTION_11_12_9_33_PENETRATION_PROGRAM_PASS=true
SECTION_11_12_9_33_PENETRATION_PROGRAM_BOUND=true
PENETRATION_PROGRAM=PASS
PENETRATION_PROGRAM_PROVEN=true
PENETRATION_PROGRAM_AUTHORIZED=true
CYBERSECURITY_ARCHITECTURE_REVIEW=PASS
THREAT_MODEL_CURRENT=true
SECRETS_REVIEW=PASS
DEPENDENCY_AUDIT=PASS
DEPENDENCY_AUDIT_PROVEN=true
PREVIOUS_REPORTING_INCONSISTENCY_RECONCILED=true
OPEN_LIST_MEMBERSHIP_IMPLIES_PROVEN=false
TESTNET_EVIDENCE_VERIFIED=true
TESTNET_LIFECYCLE_PROVEN=true
LONG_RUNNING_TESTNET_PROVEN=true
OPEN_TESTNET_PROVEN_FIELDS=
EARLIEST_OPEN_TESTNET_PROVEN_FIELD=
LONG_RUNNING_TESTNET_PROVEN_PREP_PATH_READY=true
SECTION_11_12_9_21_PREP_BOUND=true
SECTION_11_12_9_34_CREDENTIAL_LEAKAGE_TEST_EXECUTED=true
SECTION_11_12_9_34_CREDENTIAL_LEAKAGE_TEST_PASS=true
SECTION_11_12_9_34_CREDENTIAL_LEAKAGE_TEST_BOUND=true
CREDENTIAL_LEAKAGE_TEST=PASS
CREDENTIAL_LEAKAGE_TEST_PROVEN=true
CREDENTIAL_LEAKAGE_TEST_AUTHORIZED=true
SECTION_11_12_9_35_AUTHORITY_REPLAY_TEST_EXECUTED=true
SECTION_11_12_9_35_AUTHORITY_REPLAY_TEST_PASS=true
SECTION_11_12_9_35_AUTHORITY_REPLAY_TEST_BOUND=true
AUTHORITY_REPLAY_TEST=PASS
AUTHORITY_REPLAY_TEST_PROVEN=true
AUTHORITY_REPLAY_TEST_AUTHORIZED=true
SECTION_11_12_9_36_RECOVERY_SECURITY_TEST_EXECUTED=true
SECTION_11_12_9_36_RECOVERY_SECURITY_TEST_PASS=true
SECTION_11_12_9_36_RECOVERY_SECURITY_TEST_BOUND=true
RECOVERY_SECURITY_TEST=PASS
RECOVERY_SECURITY_TEST_PROVEN=true
RECOVERY_SECURITY_TEST_AUTHORIZED=true
SECTION_11_12_9_37_CRITICAL_FINDINGS_OPEN_EXECUTED=true
SECTION_11_12_9_37_CRITICAL_FINDINGS_OPEN_PASS=true
SECTION_11_12_9_37_CRITICAL_FINDINGS_OPEN_BOUND=true
CRITICAL_FINDINGS_OPEN=0
CRITICAL_FINDINGS_OPEN_PROVEN=true
CRITICAL_FINDINGS_OPEN_AUTHORIZED=true
GOVERNED_PRE_LIVE_FINDINGS_REGISTER_PRESENT=true
SECTION_11_12_9_38_HIGH_FINDINGS_OPEN_EXECUTED=true
SECTION_11_12_9_38_HIGH_FINDINGS_OPEN_PASS=true
SECTION_11_12_9_38_HIGH_FINDINGS_OPEN_BOUND=true
HIGH_FINDINGS_OPEN=0
HIGH_FINDINGS_OPEN_PROVEN=true
HIGH_FINDINGS_OPEN_AUTHORIZED=true
SECTION_11_12_9_39_LIVE_TESTNET_ISOLATION_EXECUTED=true
SECTION_11_12_9_39_LIVE_TESTNET_ISOLATION_PASS=true
SECTION_11_12_9_39_LIVE_TESTNET_ISOLATION_BOUND=true
LIVE_TESTNET_ISOLATION_PROVEN=true
LIVE_TESTNET_ISOLATION_AUTHORIZED=true
SECTION_11_12_9_40_LIVE_DEFAULT_BLOCK_EXECUTED=true
SECTION_11_12_9_40_LIVE_DEFAULT_BLOCK_PASS=true
SECTION_11_12_9_40_LIVE_DEFAULT_BLOCK_BOUND=true
LIVE_DEFAULT_BLOCK_PROVEN=true
LIVE_DEFAULT_BLOCK_AUTHORIZED=true
SECTION_11_12_9_40R_RECOVERY_BIND_29_40_EXECUTED=true
SECTION_11_12_9_40R_RECOVERY_BIND_29_40_PASS=true
SECTION_11_12_9_40R_RECOVERY_BIND_29_40_BOUND=true
RECOVERY_BIND_PACKAGES_29_THROUGH_40=true
SECTION_11_12_9_41_LIVE_ARMING_FAIL_CLOSED_EXECUTED=true
SECTION_11_12_9_41_LIVE_ARMING_FAIL_CLOSED_PASS=true
SECTION_11_12_9_41_LIVE_ARMING_FAIL_CLOSED_BOUND=true
LIVE_ARMING_FAIL_CLOSED_AUTHORIZED=true
LIVE_ARMING_FAIL_CLOSED_PROVEN=true
SECTION_11_12_9_42_AUDIT_EVIDENCE_EXECUTED=true
SECTION_11_12_9_42_AUDIT_EVIDENCE_PASS=true
SECTION_11_12_9_42_AUDIT_EVIDENCE_BOUND=true
AUDIT_EVIDENCE_VERIFIED=true
AUDIT_EVIDENCE_VERIFIED_AUTHORIZED=true
SECTION_11_12_9_43_MANIFEST_VERIFY_RC_EXECUTED=true
SECTION_11_12_9_43_MANIFEST_VERIFY_RC_PASS=true
SECTION_11_12_9_43_MANIFEST_VERIFY_RC_BOUND=true
MANIFEST_VERIFY_RC=0
MANIFEST_VERIFY_RC_AUTHORIZED=true
MANIFEST_VERIFY_RC_GATE_CRITERION_BOUND=true
SECTION_11_12_9_44_PRE_LIVE_GATE_EXECUTED=true
SECTION_11_12_9_44_PRE_LIVE_GATE_PASS=true
SECTION_11_12_9_44_PRE_LIVE_GATE_BOUND=true
PRE_LIVE_CYBERSECURITY_GATE_AUTHORIZED=true
PRE_LIVE_CYBERSECURITY_GATE=PASS
ELIGIBLE_FOR_LIVE_READINESS_EVALUATION=true
SECTION_11_13_LIVE_READINESS_EVALUATION_AUTHORIZED=true
SECTION_11_13_LIVE_READINESS_EVALUATION_EXECUTED=true
SECTION_11_13_LIVE_READINESS_EVALUATION_PASS=true
SECTION_11_13_LIVE_READINESS_EVALUATION_BOUND=true
SECTION_11_13_LIVE_READINESS_EVALUATION_COMPLETED=true
SECTION_11_13_STARTED=true
SECTION_11_13_LIVE_SHADOW_CANARY_PROGRESSION_STARTED=false
SECTION_11_13_LIVE_ACTIVATION_AUTHORIZED=false
FULLY_AUTONOMOUS_LIVE_TRADING_READY=false
FULLY_AUTONOMOUS_LIVE_TRADING_ACTIVE=false
LIVE_PRIVATE_READ_ONLY_PROVEN=true
LIVE_PRIVATE_READ_ONLY_EXECUTED=true
LIVE_PRIVATE_READ_ONLY_AUTHORIZED=true
SECTION_11_13_2_PREPARATION_SURFACE_READY=true
SECTION_11_13_2_PRODUCTIVE_EXECUTE_PATH_READY=true
SECTION_11_13_2_PRODUCTIVE_EXECUTE_UNLOCK_AUTHORING_BOUND=true
SECTION_11_13_3_PREPARATION_SURFACE_READY=true
SECTION_11_13_3_PRODUCTIVE_EXECUTE_PATH_READY=true
SECTION_11_13_3_PRODUCTIVE_EXECUTE_UNLOCK_AUTHORING_BOUND=true
LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_PROVEN=true
LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_EXECUTED=true
LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_AUTHORIZED=true
LIVE_DRY_RUN_ORDER_PLAN_PROVEN=true
LIVE_DRY_RUN_ORDER_PLAN_EXECUTED=true
LIVE_DRY_RUN_ORDER_PLAN_AUTHORIZED=true
ORDER_PLAN_RESULT=BLOCKED_NO_EXECUTE
SECTION_11_13_5_PREPARATION_SURFACE_READY=true
SECTION_11_13_5_PRODUCTIVE_EXECUTE_PATH_READY=true
SECTION_11_13_5_PRODUCTIVE_SURFACE_AUTHORING_BOUND=true
SECTION_11_13_PRE_CANARY_GOVERNANCE_CYBERSECURITY_NOTION_AUDIT_BOUND=true
SECTION_11_13_5_B_PR_5879_MERGE_CLOSEOUT_AND_PRE_CANARY_READINESS_BOUND=true
SECTION_11_13_5_C_LIVE_CANARY_TRADE_KEY_ATTESTATION_BOUND=true
SECTION_11_13_5_D_EXCHANGE_TRUTH_ADOPTION_BOUND=true
SECTION_11_13_5_E_ECONOMIC_BASELINE_AND_OKX_CLEARANCE_BOUND=true
SECTION_11_13_5_E1_FRESH_OKX_TEMP_SECURITY_CLEARANCE_BOUND=true
SECTION_11_13_5_F_LIVE_CANARY_CYBERSECURITY_GATE_PASS_BOUND=true
SECTION_11_13_5_G_CANARY_SUBMIT_TRANSPORT_PREPARATION_BOUND=true
SECTION_11_13_5_H_CANARY_EXECUTION_PLUMBING_REMEDIATION_BOUND=true
SECTION_11_13_5_I_POST_HTTP_401_BOUNDED_REMEDIATION_BOUND=true
SECTION_11_13_5_J_OKX_50124_ONESHOT_POST_CLASSIFICATION_BOUND=true
SECTION_11_13_5_K_EEA_XPERP_310404_REBIND_PREPARATION_BOUND=true
SECTION_11_13_5_L_POST_K_GET_BIND_BOUND=true
SECTION_11_13_5_M_PR_5906_PERSISTENCE_CLOSEOUT_BOUND=true
SECTION_11_13_5_N_FUNDING_AMOUNT_EVALUATION_BOUND=true
SECTION_11_13_5_O_OPERATIONAL_FUNDING_EVIDENCE_BOUND=true
SECTION_11_13_5_P_OPERATIONAL_FORMULA_RATIFICATION_BOUND=true
SECTION_11_13_5_Q_OPERATIONAL_FUNDING_POLICY_SPEC_BOUND=true
SECTION_11_13_5_R_OPERATIONAL_FUNDING_POLICY_DECISIONS_BOUND=true
SECTION_11_13_5_S_OPERATIONAL_FUNDING_GET_EVIDENCE_BOUND=true
SECTION_11_13_5_T_OPERATIONAL_FORMULA_INSTANTIATION_BOUND=true
SECTION_11_13_5_U_OPERATIONAL_RESERVE_POLICY_FORM_RATIFICATION_BOUND=true
SECTION_11_13_5_V_XPERP_TRADE_FEE_QUERY_GRAMMAR_AND_FIELD_MAPPING_BOUND=true
SECTION_11_13_5_W_FRESH_XPERP_TRADE_FEE_GET_EVIDENCE_BOUND=true
SECTION_11_13_5_X_XPERP_DELIVERY_FEE_ALGEBRA_RATIFICATION_FAIL_CLOSED_BOUND=true
SECTION_11_13_5_Y_XPERP_DELIVERY_FEE_ALGEBRA_BODY_PARTIAL_CONFLICT_BOUND=true
PRODUCTIVE_CANARY_SURFACE_MERGED_TO_ORIGIN_MAIN=true
PR_5879_MERGE_COMMIT_SHA=b3dadd86d6821882c8184bd1f6f8e207cbc4af43
PR_5902_SQUASH_MERGE_SHA=4adb0af23181cd9a8c032bbb57d3b189413a4226
PR_5905_SQUASH_MERGE_SHA=2caad4a2e68b89c788bb5a5b654a4f32fdba38c5
PR_5906_SQUASH_MERGE_SHA=bc59e1e331588ab7e727c6909baa69e8a00d93da
PR_5907_SQUASH_MERGE_SHA=27ceae9115de0ae8db196ce8417730f328c5e251
PR_5908_SQUASH_MERGE_SHA=2c55d81dd25f7bab41a63c89ad05d8635b3eda6f
PR_5909_SQUASH_MERGE_SHA=8c36b48bd4410459f6cbe4aaaa94a2ce3ca8a6e8
PR_5910_SQUASH_MERGE_SHA=736e7e21e215ce23bdade697c67393b5685bbde4
PR_5911_SQUASH_MERGE_SHA=e0b3438ef10e35e2b25461b8868f1db2324fa0a6
PR_5912_SQUASH_MERGE_SHA=b4dc3f1a57f463e7a354bfe4c5709bc3a230a36f
PR_5913_SQUASH_MERGE_SHA=d96f8ec50637f06b327dd882aa619464b87d9f91
PR_5914_SQUASH_MERGE_SHA=3e1dd5c2bbaed30241cfcd3f47c795d6b412ce7a
PR_5916_SQUASH_MERGE_SHA=0ff8f7307cdbb7c5e1fceb0b9ea9727fc3813c25
OWNER_MERGE_GO_FOR_BOUNDED_POST_401_REMEDIATION_PR_STATUS=DONE_MERGED
OWNER_MERGE_GO_FOR_POST_K_PERSISTENCE_REMEDIATION_PR_STATUS=CONSUMED_CLOSED
LIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED=false
LIVE_CANARY_MINIMUM_EXPOSURE_PROVEN=false
CANARY_SUBMIT_TRANSPORT_IMPLEMENTED=true
CANARY_SUBMIT_TRANSPORT_SCOPE=SECTION_11_13_5_LIVE_CANARY_MINIMUM_EXPOSURE_ONLY
CANARY_SUBMIT_TRANSPORT_ACTIVATED=false
CANARY_EXECUTION_PLUMBING_REMEDIATION_PREPARED=true
GENERAL_LIVE_SUBMIT_UNLOCKED=false
SUBMIT_UNLOCKED=false
LIVE_RECONCILIATION_PROVEN=true
BLOCKS_NEW_ENTRY=false
UNRESOLVED_ECONOMIC_DIVERGENCE_BLOCKS_NEW_ENTRY=false
TRADE_ATTESTATION=true
WITHDRAW_ATTESTATION=false
CANARY_TRADE_KEY_BINDING=PROVEN
SECRETREF_STATUS=RESOLVED
EXCHANGE_TRUTH_ADOPTION_STATUS=ADOPTED_PROVEN
ECONOMIC_BASELINE_ADOPTION_STATUS=OWNER_POLICIES_ADOPTED_PROVEN
ECONOMIC_DIVERGENCE_STATUS=RESOLVED_NO_UNRESOLVED_DIVERGENCE
OKX_TEMP_SECURITY_RESTRICTION=NONE_CLEARED
OKX_TEMP_SECURITY_CLEARANCE_EVIDENCE=PRESENT_PROVEN
PRE_LIVE_CYBERSECURITY_GATE=PASS
LIVE_CANARY_CYBERSECURITY_GATE=PASS
ELIGIBLE_FOR_LIVE_CANARY_EVALUATION=true
TERMINAL_STATE=HISTORICAL_FIRST_401_UNPROVEN_LATEST_ONESHOT_TRADING_POST_401_50124_OBSERVED_NOT_INSTRUMENT_GET_ROOT_CAUSE_UNPROVEN_NOT_RETRY_NOT_PROVEN
PRIOR_OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE_STATUS=CONSUMED_ONCE_FAIL_CLOSED_NO_EXECUTE
OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE_STATUS=CONSUMED
CANARY_FIRST_SUBMIT_ATTEMPTED=true
CANARY_FIRST_SUBMIT_HTTP_STATUS=401
CANARY_FIRST_SUBMIT_ACKNOWLEDGED=false
CANARY_SUBMIT_AUTHORIZATION_STATUS=UNAUTHORIZED_UNSATISFIED
EXCHANGE_FINAL_ORDER_STATE=ABSENT
EXCHANGE_FINAL_POSITION_STATE=FLAT
POST_401_ROOT_CAUSE=UNPROVEN_FAIL_CLOSED
HISTORICAL_FIRST_401_ROOT_CAUSE=UNPROVEN_FAIL_CLOSED
LATEST_50124_CLASSIFICATION=OKX_50124_OBSERVED_ONESHOT_TRADING_POST
HTTP_401_REQUEST_CLASS=ONESHOT_TRADING_POST_/api/v5/trade/order
HTTP_50124_INSTRUMENT_SPECIFIC_PROVEN=false
ROOT_CAUSE_PROVEN=false
50124_SUBTYPE=UNKNOWN_NOT_PROVEN
ACCOUNT_INSTRUMENTS_NOT_ON_SUBMIT_PATH=true
ACCOUNT_INSTRUMENTS_CAUSAL_RELATION_TO_50124=UNPROVEN
HISTORICAL_OWNER_GO_TOKEN_NAME_IS_NOT_PROVEN_MARKET_PERMISSION_ROOT_CAUSE=true
CANARY_HAS_NO_STRATEGY_SELECTION_CONSUMER=true
ONESHOT_INST_ID=BTC-USDT-SWAP
RETRY_SAFE_NOW=false
HISTORICAL_AUTH_50110_CLEARED_AT_11_13_5_I=true
CURRENT_PRIVATE_GET_AUTH_STATUS=SEE_CURRENT_CANONICAL_OR_ADJUDICATED_SOURCE
OWNER_GO_LIVE_CANARY_TRADE_KEY_ATTESTATION_STATUS=CONSUMED_PROVEN
OWNER_GO_EXCHANGE_TRUTH_ADOPTION_STATUS=CONSUMED_ADOPTED_PROVEN
OWNER_GO_ECONOMIC_BASELINE_AND_OKX_CLEARANCE_EVIDENCE_STATUS=CONSUMED
OWNER_GO_CAP11_OKX_TEMP_SECURITY_CLEARANCE_FRESH_EVIDENCE_CANONICAL_PERSISTENCE_STATUS=CONSUMED
OWNER_GO_PERSIST_LIVE_CANARY_CYBERSECURITY_GATE_PASS_STATUS=CONSUMED
OWNER_GO_CANARY_SUBMIT_TRANSPORT_PREPARATION_STATUS=CONSUMED
OWNER_GO_SECTION_11_13_5_CANARY_EXECUTION_PLUMBING_REMEDIATION_PREPARATION_STATUS=CONSUMED
OWNER_GO_SECTION_11_13_5_POST_HTTP_401_BOUNDED_REMEDIATION_PREPARATION_STATUS=CONSUMED
OWNER_GO_SECTION_11_13_5_OKX_50124_MARKET_PERMISSION_REMEDIATION_AND_CLASSIFICATION_PREPARATION_STATUS=CONSUMED
OWNER_GO_SECTION_11_13_5_EEA_XPERP_310404_REBIND_PREPARATION_STATUS=CONSUMED_MERGED
OWNER_GO_FOR_NEW_FUNDING_STATUS=CONSUMED_EVALUATION_ONLY_AMOUNT_UNPROVEN
OWNER_GO_REQUIRED_FOR_OPERATIONAL_CANARY_FUNDING_AMOUNT_EVIDENCE_STATUS=CONSUMED_EVIDENCE_ONLY_AMOUNT_UNPROVEN
OWNER_GO_REQUIRED_TO_RATIFY_OPERATIONAL_FUNDING_FORMULA_STATUS=CONSUMED_RATIFICATION_ONLY_FORMULA_ABSENT
OWNER_GO_BUILD_OPERATIONAL_FUNDING_POLICY_SPEC_ONLY_STATUS=CONSUMED_POLICY_SPEC_ONLY_TEMPLATE_UNFILLED
OWNER_FILL_OPERATIONAL_FUNDING_POLICY_DECISIONS_STATUS=CONSUMED_POLICY_GRAMMAR_PERSISTED_NOT_FORMULA_RATIFICATION
OWNER_GO_FOR_BOUNDED_OPERATIONAL_FUNDING_GET_EVIDENCE_STATUS=CONSUMED_GET_ONLY_EVIDENCE_AMOUNT_UNPROVEN
OWNER_GO_REQUIRED_FOR_OPERATIONAL_FORMULA_INSTANTIATION_STATUS=CONSUMED_INSTANTIATION_ONLY_FORMULA_ABSENT
OWNER_GO_REQUIRED_TO_SUPPLY_NUMERIC_OPERATIONAL_RESERVE_TERMS_STATUS=NOT_GRANTED_SUPERSEDED_BY_SECTION_11_13_5_U
OWNER_GO_TO_RATIFY_OPERATIONAL_RESERVE_POLICY_FORMS_STATUS=CONSUMED_POLICY_FORMS_RATIFIED_NOT_FORMULA_BODY
OWNER_GO_REQUIRED_FOR_BOUNDED_GET_ONLY_EVIDENCE_TO_INSTANTIATE_RATIFIED_RESERVE_POLICY_FORMS_STATUS=CONSUMED_GET_ONLY_PARTIAL_INSTANTIATION_TRADE_FEE_50016_FAIL_CLOSED
OWNER_GO_FOR_READ_ONLY_FORENSIC_ANALYSIS_OF_UNRESOLVED_RESERVE_POLICY_INPUTS_STATUS=CONSUMED_READ_ONLY_FORENSIC_NO_GET
OWNER_GO_TO_RATIFY_INSTRUMENT_RELEVANT_XPERP_TRADE_FEE_QUERY_GRAMMAR_AND_TAKER_MAKER_FIELD_MAPPING_STATUS=CONSUMED_POLICY_RATIFICATION_ONLY
OWNER_GO_REQUIRED_FOR_BOUNDED_GET_ONLY_FRESH_XPERP_TRADE_FEE_EVIDENCE_USING_RATIFIED_QUERY_GRAMMAR_STATUS=CONSUMED_GET_ONLY_FRESH_TRADE_FEE_EVIDENCE
OWNER_GO_TO_PERSIST_FRESH_XPERP_TRADE_FEE_GET_EVIDENCE_STATUS=CONSUMED
OWNER_GO_TO_RATIFY_INSTRUMENT_RELEVANT_XPERP_DELIVERY_FEE_ALGEBRA_STATUS=CONSUMED_ALGEBRA_BODY_ABSENT
OWNER_GO_REQUIRED_TO_SUPPLY_INSTRUMENT_RELEVANT_XPERP_DELIVERY_FEE_ALGEBRA_BODY_STATUS=CONSUMED_PARTIAL_SUB_ALGEBRA_RATE_OPERAND_CONFLICT
OWNER_GO_REQUIRED_TO_RESOLVE_XPERP_EXPIRATION_DELIVERY_RATE_OPERAND_CONFLICT_STATUS=CONSUMED_OPERAND_UNPROVEN
OWNER_GO_REQUIRED_TO_SUPPLY_OR_POINT_TO_A_NORMATIVE_XPERP_EEA_EXPIRATION_DELIVERY_FEE_RULE_THAT_BINDS_PRODUCT_TO_RATE_OPERAND_STATUS=NOT_GRANTED_SUPERSEDED_BY_SECTION_11_13_5_Z1
OWNER_GO_TO_REVIEW_AND_CORRECT_IF_PROVEN_THE_SECTION_11_13_5_Z_PREMISE_OF_A_DISTINCT_EEA_XPERP_EXPIRY_DELIVERY_FEE_STATUS=CONSUMED_FEE_EXISTENCE_UNPROVEN
OWNER_GO_FOR_TARGETED_NORMATIVE_SOURCE_ACQUISITION_TO_RESOLVE_EDGE_I_E4_E8_STATUS=CONSUMED_NO_NORMATIVE_STATEMENT_FOUND
OWNER_GO_FOR_TARGETED_READ_ONLY_TARGET_EXACT_TRADE_FEE_PATH_STATUS=CONSUMED_FAMILY_SCOPE_PROVEN_EVENT_B_UNPROVEN
OWNER_GO_FOR_TRADE_FEE_DELIVERY_FIELD_EVENT_B_SEMANTICS_SEARCH_STATUS=CONSUMED_LABEL_ONLY
OWNER_GO_FOR_CANONICAL_EDGE_I_CLOSEOUT_STATUS=CONSUMED_DOCS_ONLY
OWNER_GO_FOR_FAIL_CLOSED_UNKNOWN_NONE_DELIVERY_TERM_IN_OPERATIONAL_RESERVE_COMPOSITION_DOCS_ONLY_STATUS=CONSUMED_DOCS_ONLY_Z2_POINTER_UNCHANGED
OWNER_GO_REQUIRED_TO_SUPPLY_OR_POINT_TO_A_CURRENT_NORMATIVE_OKX_EEA_OEM_XPERP_NORMAL_EXPIRY_FEE_APPLICABILITY_STATEMENT_STATUS=CONSUMED_BOUND_BY_OWNER_GO_BIND_OKX_TICKET_7823581
OWNER_GO_BIND_OKX_TICKET_7823581_STATUS=CONSUMED_DOCS_ONLY_RATE_NON_OPERATIVE
OWNER_GO_REQUIRED_TO_SUPPLY_OR_POINT_TO_A_CURRENT_NORMATIVE_OKX_EEA_OEM_XPERP_NORMAL_EXPIRY_FEE_MONETARY_BASE_STATUS=SUPERSEDED_NOT_CRITICAL_PATH_FOR_MINIMUM_EXPOSURE_CANARY
OWNER_GO_BOUND_UNPROVEN_NORMAL_EXPIRY_FEE_ECONOMIC_RISK_WITH_INTERNAL_CONSERVATIVE_RESERVE_STATUS=CONSUMED_CONTRACT_ONLY_NOT_EXECUTE
OWNER_GO_REQUIRED_TO_RESOLVE_REMAINING_UNPROVEN_POSITION_VALUE_FX_AND_ROUNDING_FOR_OPERATIONAL_RESERVE_STATUS=CONSUMED_CONTRACT_ONLY_NOT_EXECUTE
OWNER_GO_REQUIRED_TO_RATIFY_EXACT_FORMULA_BODY_STATUS=CONSUMED_CONTRACT_ONLY_NOT_EXECUTE
OWNER_GO_REQUIRED_TO_BIND_UNINSTANTIATED_FORMULA_TERM_INSTANCES_AND_FX_ROUNDING_BEFORE_FUNDING_STATUS=CONSUMED_CONTRACT_ONLY_NOT_EXECUTE
OWNER_GO_REQUIRED_FOR_PRODUCTIVE_EVIDENCE_TO_INSTANTIATE_REMAINING_UNPROVEN_COVER_USDC_TERMS_BEFORE_FUNDING_STATUS=CONSUMED_GET_ONLY_MARKPX_OBSERVED_NOT_COVER_USDC
OWNER_GO_REQUIRED_FOR_PRODUCTIVE_EVIDENCE_TO_RESOLVE_REMAINING_UNPROVEN_COVER_USDC_TERMS_AFTER_CURRENT_MARKPX_BEFORE_FUNDING_STATUS=CONSUMED_GET_ONLY_TICKER_BID_ASK_OBSERVED_NOT_COVER_USDC
OWNER_GO_REQUIRED_FOR_PRODUCTIVE_EVIDENCE_TO_RESOLVE_REMAINING_UNPROVEN_COVER_USDC_TERMS_AFTER_CURRENT_TICKER_BID_ASK_BEFORE_FUNDING_STATUS=CONSUMED_GET_ONLY_PUBLIC_TIER_MMR_OBSERVED_NOT_COVER_USDC
OWNER_GO_REQUIRED_FOR_PRODUCTIVE_EVIDENCE_TO_RESOLVE_REMAINING_UNPROVEN_COVER_USDC_TERMS_AFTER_FEE_RESERVE_RATES_REBIND_BEFORE_FUNDING_STATUS=CONSUMED_GET_ONLY_SAME_PACK_MARKPX_INTERNAL_NOTIONAL_ENVELOPE_NOT_COVER_USDC
OWNER_GO_REQUIRED_FOR_PRODUCTIVE_EVIDENCE_TO_RESOLVE_REMAINING_UNPROVEN_COVER_USDC_TERMS_AFTER_SAME_PACK_INTERNAL_NOTIONAL_ENVELOPE_BEFORE_FUNDING_STATUS=CONSUMED_GET_ONLY_SAME_PACK_SLIPPAGE_RESERVE_NOT_COVER_USDC
OWNER_GO_REQUIRED_FOR_PRODUCTIVE_EVIDENCE_TO_RESOLVE_REMAINING_UNPROVEN_COVER_USDC_TERMS_AFTER_SAME_PACK_SLIPPAGE_RESERVE_BEFORE_FUNDING_STATUS=CONSUMED_GET_ONLY_SAME_PACK_MM_LIQ_BUFFER_NOT_COVER_USDC
OWNER_GO_DOCS_ONLY_STATUS=CONSUMED_DOCS_ONLY_0003_VS_0001_PROVENANCE_HISTORICAL_SUPERSEDED
OWNER_POLICY_OVERRIDE_GO_STATUS=CONSUMED_RATE_ADJUDICATION_NOT_EXECUTE
OWNER_GO_CANONICALIZATION_RESEARCH_ADJUDICATION_ONLY_STATUS=CONSUMED_SEMANTIC_CLARIFICATION_NOT_EXECUTE
SEMANTIC_PROPOSITION_VERDICT=PROVEN
NUMERIC_PROPOSITION_VERDICT=UNPROVEN
CLIENT_FX_PROPOSITION_VERDICT=UNPROVEN
VENUE_INTERNAL_CONVERSION_SEMANTIC_PROVEN=true
VENUE_NUMERIC_CONVERSION_OPERATOR_PROVEN=false
CLIENT_SIDE_FX_REQUIRED_PROVEN=false
MODEL_3_SEMANTICS_CANONICALIZED=true
MODEL_3_NUMERIC_COVER_CANONICALIZED=false
NAMED_REMAINING_COVER_USDC_TERM=FINITE_PHYSICAL_USDC_COVER_AMOUNT_ABSENT
NEW_CANARY_OWNER_GO_GRANTED=false
LIVE_AUTHORIZED=false
LF10_ADJUDICATION=COMPLETE_READ_ONLY_NO_NEW_PROVEN_CLOSURE
CLAIMS_PROVEN_THIS_STEP=NONE
NEW_EVIDENCE_FOUND=false
POSITION_VALUE_STATUS=UNPROVEN_AS_UNIFIED_EXCHANGE_OR_OEM_VALUE
QTY_1_EXPOSURE_STATUS=API_SZ1_UNDERLYING_0.0001_BTC_PROVEN_OEM_QTY1_UNPROVEN_UNIFIED_UNPROVEN
EXPIRY_FEE_MONETARY_BASE_STATUS=OEM_OKX_IDENTITY_UNPROVEN
SETTLEMENT_PNL_STATUS=UNPROVEN
USD_USDC_OPERATOR_STATUS=UNPROVEN
LF_11_AUTHORIZED=false
LF_12_AUTHORIZED=false
LF11_ADJUDICATION=C_UNPROVEN
LF12_ADJUDICATION=C_PREREQUISITES_NOT_CLOSED_PRODUCTIVE_FLATTEN_NOT_ADMISSIBLE
LF_11_READ_ONLY_ADJUDICATION=COMPLETE
LF_12_READ_ONLY_ADJUDICATION=COMPLETE
EXISTING_EVIDENCE_SUFFICIENT=false
FLATTEN_RUNTIME_REACHABILITY=DEDICATED_PATH_IMPLEMENTED_LIVE_WIRE_DISABLED
FLATTEN_PRICE_BINDING=QUOTE_LOCKED_IMPLEMENTED_OWNER_RATIFIED_FRESHNESS_MS_5000
FLATTEN_PRICE_POLICY_IMPLEMENTED=true
FLATTEN_PRICE_POLICY_FULLY_BOUND=true
FRESHNESS_BINDING=OWNER_RATIFIED
FRESHNESS_THRESHOLD_MS=5000
FRESHNESS_THRESHOLD_RATIFIED=true
FRESHNESS_POLICY_CLASS=NEW_EXPLICIT_OWNER_RATIFICATION_NOT_FIXTURE_PROMOTION
FRESHNESS_PROVEN_EXISTING_THRESHOLD=NONE
FRESHNESS_UNRATIFIED_POLICY=SUPERSEDED_BY_Z2AN_OWNER_RATIFICATION
FRESHNESS_CANONICAL_DEFAULT=5000
TEST_FIXTURE_5000_PROMOTED_TO_POLICY=false
MD_DEFAULT_5S_PROMOTED_TO_POLICY=false
TESTNET_DEFAULT_120S_PROMOTED_TO_POLICY=false
FIXTURE_VALUES_TREATED_AS_AUTHORITY=false
EXTRA_DEVIATION_BOUND=NOT_REQUIRED_FOR_DEDICATED_FLATTEN_CONTRACT
EXTRA_DEVIATION_BOUND_REQUIRED=false
EXTRA_DEVIATION_BOUND_PROVEN=false
EXTRA_DEVIATION_BOUND_VALUE=NONE
EXTRA_DEVIATION_SAFETY_INVARIANT=NOT_PROVEN
EXTRA_DEVIATION_DEFENSE_IN_DEPTH=OPTIONAL_UNRATIFIED_CURRENTLY_REJECTED
EXTRA_DEVIATION_BOUND_RATIFIED=false
REST_QUOTE_LOCK_SUFFICIENT_WITHOUT_EXTRA_BOUND=true
PRODUCTIVE_PROOF_READY=true
FLATTEN_POST_ACTION_PROOF_CONTRACT_IMPLEMENTED=true
Z2P_SLIPPAGE_RESERVE_NUMERIC_CLASS=COVER_ALGEBRA_NOT_FLATTEN_PX_GUARD
NEW_PROVEN_CLOSURE=NONE
DEDICATED_FLATTEN_TRANSPORT_IMPLEMENTED=true
DEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED=false
REDUCE_ONLY_FLATTEN_INTENT_IMPLEMENTED=true
STATIC_FLATTEN_PREREQUISITES_STATUS=PASS_OFFLINE
ORDER_COUNT_LIMIT_RAISE_TO_2_FORBIDDEN=true
CAN_LIVE_FLATTEN_BE_AUTHORIZED_SAFELY_NOW=false
ARCHIVED_OFF_REPO_EVIDENCE_INSPECTED=true
ARCHIVED_EVIDENCE_AUTHORITY_CLASSIFICATION=INSPECTED_NOT_CANONICAL
POSITION_VALUE_ALGEBRA_STATUS=UNPROVEN
POSITION_VALUE_ALGEBRA_LAYERING=PARTIALLY_PROVEN_TARGET_INPUT_CONFLICTED
GENERAL_LINEAR_NOTIONAL_ALGEBRA_STATUS=PROVEN
API_LINEAR_NOTIONAL_FORMULA=sz*ctVal*markPx
CTMULT_INCLUDED_IN_API_NOTIONAL_FORMULA=false
TARGET_FACE_VALUE_AUTHORITY_STATUS=DOCUMENTARY_CONFLICTED_API_SIZING_USES_INSTRUMENT_CTVAL
DOCUMENTARY_FACE_VALUE_CONFLICT=CONFLICTED
OEM_SPEC_WRONG=false
GLOBAL_API_WINS=false
SILENT_OEM_DEFEAT=false
FACE_VALUE_CONFLICT_RESOLVED_GLOBALLY=false
API_EXECUTION_DENOMINATION_STATUS=PROVEN
API_EXECUTION_CTVAL=0.0001_BTC
API_EXECUTION_CTMULT=1
API_EXECUTION_LOTSZ=1
API_EXECUTION_MINSZ=1
API_SIZING_AUTHORITY=INSTRUMENT_SPECIFIC_CTVAL_DO_NOT_ASSUME_OEM_OR_PRODUCT_CONTRACT_SIZE
OEM_DOCUMENTARY_CONTRACT_SIZE=0.01_BTC
OEM_DOCUMENTARY_FACE_VALUE_STATUS=RETAINED_NOT_ADJUDICATED_WRONG
OEM_TO_API_100_TO_1_BRIDGE=INFERRED_NOT_PROVEN
OEM_TO_API_100_TO_1_BRIDGE_ALLOWED_FOR_API_SIZING=false
OEM_CONTRACT_EQUALS_100_API_CONTRACTS_PROVEN=false
FACE_VALUE_CONFLICT_AS_API_NUMERIC_SAFETY_BLOCKER=CLOSED
FACE_VALUE_CONFLICT_AS_DOCUMENTARY_CONFLICT=OPEN_QUARANTINED
FAIL_CLOSED_CTVAL_GUARD_STATUS=REQUIRED
API_EXECUTION_PRECEDENCE_RULE_STATUS=PROVEN_SCOPED_OKX_AGENT_TRADE_KIT_SWAP_FUTURES_OPTION_ORDER_SIZING_USE_INSTRUMENTS_CTVAL_DO_NOT_ASSUME
OPERATIVE_RUNTIME_CONTRACT_FACE_VALUE_FOR_API_SIZING=0.0001_BTC
API_SIZING_NOTIONAL=6.44085
API_SIZING_NOTIONAL_CLASS=API_SIZING_AND_INTERNAL_NOTIONAL_ENVELOPE_NOT_COVER_USDC_NOT_OEM_SETTLEMENT
SETTLEMENT_PNL=UNPROVEN
TARGET_POSITION_VALUE_NUMERIC_INSTANTIATION_STATUS=UNPROVEN
REAL_FIRST_PARTY_NUMERIC_CONFLICT=true
CONFLICT_FACTOR=100
CONFLICT_FACTOR_IS_OPERATIVE_API_SIZING_CONVERSION=false
OEM_SPEC_CONTRACT_SIZE=0.01_BTC
TARGET_CTVAL=0.0001
GUIDE_CONTRACT_SIZE=0.0001_BTC
INTERNAL_NOTIONAL_ENVELOPE_USED_AS_OEM_PROOF=false
NAMED_REMAINING_POSITION_VALUE_ALGEBRA_GAP=TARGET_CONTRACT_FACE_VALUE_CONFLICT_0.01_BTC_VS_0.0001_BTC
TARGET_INSTID_310404_CTMULT_NUMERIC_PROVEN=true
TARGET_INSTID_310404_CTMULT=1
RULE_FX_STATUS=UNPROVEN
RULE_ROUNDING_STATUS=UNPROVEN
FX_STATUS=UNPROVEN
ROUNDING_STATUS=UNPROVEN
MONETARY_BASE_STATUS=UNPROVEN
OEM_OKX_MONETARY_BASE_IDENTITY_STATUS=UNPROVEN
OPERATIVE_EXPIRY_FEE_RATE=0.0003
EXPIRY_SETTLEMENT_RATE=0.0003
EXPIRY_SETTLEMENT_RATE_PERCENT=0.03%
EXPIRY_SETTLEMENT_RATE_VALUE_PROVENANCE=VERIFIED_FIRST_PARTY_OKX_API_ARTIFACT
EXPIRY_SETTLEMENT_RATE_ADJUDICATION=OWNER_RATIFIED_FROM_VERIFIED_FIRST_PARTY_OKX_DELIVERY_FIELD
EXPIRY_RATE_GATE=PASS
EXPIRY_RATE_BLOCKER=false
SUPPORT_REQUIRED_FOR_RATE_DECISION=false
SUPPORT_RATE_0_0001_STATUS=HISTORICAL_SUPERSEDED
SUPPORT_TICKET_7823581_STATUS=HISTORICAL_SUPERSEDED_FOR_RATE_ADJUDICATION
RATE_ADJUDICATION_CLOSED=true
PEAK_TRADE_EXPIRY_RESERVE_RATE=0.0003
PEAK_TRADE_EXPIRY_RESERVE_RATE_SOURCE=PEAK_TRADE_POLICY_REUSE_OF_SAME_NUMERIC_VALUE
MARKPX_TERM_STATUS=SAME_PACK_OBSERVED_BOUND_FOR_INTERNAL_NOTIONAL_ENVELOPE_NOT_OKX_DELIVERY_FEE_OPERAND
MARKPX_CURRENT_VALUE=64408.5
INTERNAL_NOTIONAL_ENVELOPE_NUMERIC=6.44085
INTERNAL_NOTIONAL_ENVELOPE_UNIT=PEAK_TRADE_INTERNAL_NOTIONAL_UNIT
INTERNAL_NOTIONAL_ENVELOPE_STATUS=PROVEN
NUMERIC_FEE_RESERVE=0.00644085
NUMERIC_FEE_RESERVE_STATUS=PROVEN_INTERNAL_ALGEBRA_NOT_COVER_USDC
DELIVERY_COVER_INTERNAL_NUMERIC=0.001932255
BID_ASK_TERM_STATUS=SAME_PACK_OBSERVED_BOUND_FOR_SLIPPAGE_RESERVE
BID_PX=64805.6
ASK_PX=64805.7
TICKSZ=0.1
SLIPPAGE_RESERVE_NUMERIC=0.00002
SLIPPAGE_RESERVE_NUMERIC_STATUS=PROVEN_INTERNAL_ALGEBRA_NOT_COVER_USDC
MMR_TERM_STATUS=SAME_PACK_OBSERVED_BOUND_FOR_MM_LIQ_BUFFER_NOT_ACCOUNT_EFFECTIVE
MMR_PUBLIC_TIER_QTY_ONE_CURRENT_VALUE=0.01
MMR_SOURCE=THIS_SAME_PACK_PUBLIC_POSITION_TIERS_GET
Z2K_HISTORICAL_MMR_NOT_USED_AS_OPERATIVE_INPUT=true
MM_LIQ_BUFFER_NUMERIC=0.0644085
MM_LIQ_BUFFER_NUMERIC_STATUS=PROVEN_INTERNAL_ALGEBRA_NOT_COVER_USDC
EXCHANGE_TRUTH_CHANGED=false
B08_EXACT_FORMULA_BODY_STATUS=RATIFIED_INTERNAL_CONSERVATIVE_QTY1_NOT_COVER_USDC
COVER_USDC_STATUS=UNINSTANTIATED
NUMERIC_FUNDING_AMOUNT=NONE
NUMERIC_FUNDING_AMOUNT_PRODUCED=false
PHYSICAL_USDC_COVER_AMOUNT_AVAILABLE=false
FEE_RESERVE_RATES_GRAMMAR_STATUS=SEALED
FEE_RESERVE_RATES_INSTANCE_STATUS=SAME_PACK_TAKER_MAKER_FROZEN_NUMERIC_FEE_RESERVE_PROVEN_INTERNAL
FEE_RESERVE_RATES_EXECUTION_PATH_STATUS=RATIFIED_GET_EXECUTED_EVIDENCE_BOUND
FEE_RESERVE_RATES_REBIND_GET_EXECUTION_PATH_RATIFIED=true
FEE_RESERVE_RATES_REBIND_GET_EVIDENCE_BOUND=true
FEE_RESERVE_RATES_ADJUDICATION=PROVEN
SAME_PACK_WITH_Z2N_FEE_FREEZE=true
HISTORICAL_W_PACK_IS_NOT_EXECUTE_FRESH=true
MARKET_DASHBOARD_FAMILY_TAXONOMY_USED=false
EARLIEST_UNRESOLVED_DEPENDENCY=MULTIPLE_INDEPENDENT_BLOCKERS
EARLIEST_UNRESOLVED_SECTION_POINTER=SECTION_5_3_CANARY_SUBMIT_AUTHORIZATION_CONTRACT
CURRENT_PROGRAM_NEXT_SURFACE_POINTER=SECTION_5_3_CANARY_SUBMIT_AUTHORIZATION_CONTRACT_BOUND_NOT_AUTHORIZED
CANARY_SUBMIT_AUTHORIZATION_STATUS=UNAUTHORIZED_UNSATISFIED
CURRENT_SUI_L4_STATE=FAIL_CLOSED_AT_MAX_AVAILABLE
CURRENT_SUI_L4_FAIL_CLOSED_PERSIST=SECTION_5_3_BIND_CURRENT_SUI_L4_FAIL_CLOSED_MAX_AVAILABLE_ZERO_END_STATE_NO_REPAIR_V1
CURRENT_SUI_CANARY_L4_PRE_SUBMIT_NO_WIRE_PROVEN=false
CURRENT_SUI_PRETRADE_CONSUMPTION_PROVEN=false
CURRENT_SUI_ORDER_PLAN_PROVEN=false
CURRENT_SUI_PRE_SUBMIT_PAYLOAD_PROVEN=false
CURRENT_MAX_AVAILABLE_GATE_RESULT=FAIL_CLOSED:VENUE_CONTRACT_COUNT_EXCEEDS_MAXBUY
ROOT_CAUSE_OF_MAX_AVAILABLE_ZERO=UNPROVEN
FUNDING_CAUSALITY_PROVEN=false
COVER_USDC_CAUSALITY_PROVEN=false
AVAILABLE_MARGIN_CAUSALITY_PROVEN=false
NO_REPAIR_AUTHORIZED=true
NO_FUNDING_MUTATION_AUTHORIZED=true
NO_COVER_USDC_INSTANTIATION_AUTHORIZED=true
CANARY_SUBMIT_AUTHORIZATION_NOT_SATISFIED_BY_THIS_L4_FAIL_CLOSED=true
LAST_CANONICALLY_CLOSED_STEP=LF_12
PUBLIC_CONVERSION_CANDIDATE_SURFACES_ADJUDICATED=true
USDC_USD_INDEX_1_NON_OPERATOR_NEGATIVE_CONTRACT=true
IDXPX_USDC_USD_1_IS_COVER_USDC_OPERATOR=false
USD_EQUALS_USDC_ASSUMED=false
NUMERIC_USD_USDC_OPERATOR_FOUND=false
NO_CLIENT_CONVERSION_REQUIRED_PROVEN=false
CLIENT_FX_REQUIRED=UNPROVEN
ADJUDICATION_RESULT=C_UNPROVEN
CLAIMS_NEWLY_PROVEN_THIS_STEP=NONE
CONVERSION_NUMERIC_STATUS=UNINSTANTIATED_REQUIRES_LATER_PRODUCTIVE_USD_USDC_EVIDENCE
NEXT_CANONICAL_STEP_POINTER=OWNER_GO_REQUIRED_SEPARATE_FOR_PRODUCTIVE_LIVE_FLATTEN_PROOF_NOT_AUTHORIZED_BY_THIS_CLOSURE_Z2AP_OFFLINE_POST_ACTION_PROOF_CONTRACT_BOUND_PRODUCTIVE_PROOF_READY_TRUE_LIVE_FLATTEN_UNPROVEN_NO_LIVE_WIRE_NO_ORDER_COUNT_LIMIT_RAISE_TO_2_NO_RUNTIME_READ_NO_PRODUCTIVE_FLATTEN_NO_GET_NO_ORDER_NO_ALLOWLIST_CANARY_NOT_AUTHORIZED_SUPPORT_CONTACT_NOT_AUTHORIZED
NEXT_CANONICAL_STEP_POINTER_ROLE=HISTORICAL_Z2AP_FLATTEN_PROOF_POINTER_SUPERSEDED_AS_PROGRAM_NEXT_STEP_NOT_DELETED
SECTION_11_13_2_PACKAGE_POINTER=src&#47;ops&#47;section_11_13_2_live_private_read_only_v1&#47;
SECTION_11_13_2_PROOF_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_13_2_live_private_read_only_proven_v1&#47;20260811T170310Z&#47;
SECTION_11_13_3_PACKAGE_POINTER=src&#47;ops&#47;section_11_13_3_live_shadow_with_exchange_reconciliation_v1&#47;
SECTION_11_13_3_PROOF_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_13_3_live_shadow_with_exchange_reconciliation_proven_v1&#47;20260811T211828Z&#47;
SECTION_11_13_4_PACKAGE_POINTER=src&#47;ops&#47;section_11_13_4_live_dry_run_order_plan_v1&#47;
SECTION_11_13_4_PROOF_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_13_4_live_dry_run_order_plan_proven_v1&#47;20260811T230805Z&#47;
SECTION_11_13_5_PACKAGE_POINTER=src&#47;ops&#47;section_11_13_5_live_canary_minimum_exposure_v1&#47;
SECTION_11_13_5_FORENSIC_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_13_5_live_canary_forensic_reconciliation_v1&#47;20260812T120000Z&#47;
SECTION_11_13_PRE_CANARY_AUDIT_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_13_pre_canary_governance_cybersecurity_notion_audit_v1&#47;20260812T121500Z&#47;
SECTION_11_13_5_B_PRE_CANARY_READINESS_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_13_5_b_pr_5879_squash_merge_and_pre_canary_readiness_v1&#47;20260812T123500Z&#47;
SECTION_11_13_5_C_TRADE_KEY_ATTESTATION_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_13_5_live_canary_trade_capability_attestation_v1&#47;20260812T135723Z&#47;
SECTION_11_13_5_D_EXCHANGE_TRUTH_ADOPTION_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_13_5_exchange_truth_adoption_v1&#47;20260812T151147Z&#47;
SECTION_11_13_5_E_ECONOMIC_BASELINE_AND_OKX_CLEARANCE_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_13_5_economic_baseline_and_okx_clearance_v1&#47;20260812T153425Z&#47;
SECTION_11_13_5_E1_FRESH_OKX_TEMP_SECURITY_CLEARANCE_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_13_5_okx_temp_security_clearance_evidence_collection_v1&#47;20260815T190010Z&#47;
SECTION_11_13_5_F_LIVE_CANARY_CYBERSECURITY_GATE_REEVALUATION_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_13_5_live_canary_cybersecurity_gate_reevaluation_v1&#47;20260815T193911Z&#47;
SECTION_11_13_5_G_CANARY_SUBMIT_TRANSPORT_PREPARATION_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_13_5_canary_submit_transport_preparation_v1&#47;20260815T204500Z&#47;
SECTION_11_13_5_J_OKX_50124_ONESHOT_POST_CLASSIFICATION_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_13_5_okx_50124_oneshot_post_classification_v1&#47;20260816T002530Z&#47;
SECTION_11_13_5_L_POST_K_GET_BIND_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_13_5_post_k_cross_imr_leverage_get_bind_v1&#47;20260816T033800Z&#47;
SECTION_11_13_5_S_OPERATIONAL_FUNDING_GET_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_13_5_operational_funding_get_evidence_v1&#47;20260816T060349Z&#47;
SECTION_11_13_5_W_FRESH_XPERP_TRADE_FEE_GET_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_13_5_v_fresh_xperp_trade_fee_get_evidence_v1&#47;20260816T075803Z&#47;
SECTION_11_13_5_Z2G_CURRENT_MARKPX_PUBLIC_GET_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_13_5_z2g_current_markpx_public_get_v1&#47;20260818T200745Z&#47;
SECTION_11_13_5_Z2H_CURRENT_TICKER_BID_ASK_PUBLIC_GET_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_13_5_z2h_current_ticker_bid_ask_public_get_v1&#47;20260818T203435Z&#47;
SECTION_11_13_5_Z2K_CURRENT_PUBLIC_TIER_MMR_PUBLIC_GET_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_13_5_z2k_current_public_tier_mmr_public_get_v1&#47;20260819T085545Z&#47;
SECTION_11_13_5_Z2N_FEE_RESERVE_RATES_REBIND_GET_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_13_5_z2m_fee_reserve_rates_rebind_get_v1&#47;20260819T102325Z&#47;
SECTION_11_13_1_LIVE_READINESS_EVAL_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_13_live_readiness_evaluation_v1&#47;20260811T134610Z&#47;
SECTION_11_12_9_44_PRE_LIVE_GATE_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_9_44_pre_live_cybersecurity_gate_pass_v1&#47;20260811T133046Z&#47;
ZAP_DAST_EXECUTED=false
DOCS_NO_LIVE_ENABLE_PREEXISTING_OPEN=true
CANONICAL_EXECUTE_OWNER_GO_SCOPE=EXECUTE_BOUNDED_LONG_RUNNING_PRODUCTIVE_TESTNET_CAMPAIGN_NOW
SECTION_11_12_8_REOPENED=false
PERMANENT_BOUND_CLIENT_QUERY_SIGN_FIX=true
IMMUTABLE_BASELINE_PREFLIGHT_REQUIRED_FOR_WIRE_SEND=true
SECTION_11_12_9_21_PREP_EVIDENCE_POINTER=docs&#47;evidence&#47;capability_11_long_running_testnet_proven_prep_eval_v1&#47;
SECTION_11_12_9_21_LONG_RUNNING_CAMPAIGN_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_9_21_execute_bounded_long_running_productive_testnet_campaign_now&#47;20260811T005425Z&#47;
SECTION_11_12_9_22_REEVAL_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_9_22_pre_live_cybersecurity_gate_post_long_running_reevaluation_v1&#47;20260811T020006Z&#47;
SECTION_11_12_9_23_ARCHITECTURE_REVIEW_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_9_23_pre_live_cybersecurity_architecture_review_v1&#47;20260811T021353Z&#47;
SECTION_11_12_9_24_THREAT_MODEL_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_9_24_pre_live_threat_model_current_v1&#47;20260811T023114Z&#47;
SECTION_11_12_9_25_SECRETS_REVIEW_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_9_25_pre_live_credential_hygiene_review_v1&#47;20260811T025933Z&#47;
SECTION_11_12_9_26_DEPENDENCY_AUDIT_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_9_26_pre_live_dependency_audit_v1&#47;20260811T031527Z&#47;
SECTION_11_12_9_27_FORENSIC_REVIEW_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_9_26_post_dependency_audit_forensic_gap_and_remediation_review_v1&#47;20260811T033939Z&#47;
SECTION_11_12_9_28_DEPENDENCY_AUDIT_REMEDIATION_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_9_27_dependency_audit_rb01_rb02_remediation_and_rerun_v1&#47;20260811T035809Z&#47;
PR_5862_SQUASH_MERGE_CLOSEOUT_POINTER=evidence&#47;ops&#47;section_11_12_9_27_pr_5862_squash_merge_closeout_v1&#47;20260811T040810Z&#47;
PR_5863_SQUASH_MERGE_CLOSEOUT_POINTER=evidence&#47;ops&#47;section_11_12_9_28_pr_5863_squash_merge_closeout_v1&#47;20260811T041913Z&#47;
SECTION_11_12_9_29_SBOM_PRESENT_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_9_29_pre_live_sbom_present_v1&#47;20260811T042745Z&#47;
SECTION_11_12_9_30_STATIC_SECURITY_ANALYSIS_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_9_30_pre_live_static_security_analysis_v1&#47;20260811T043159Z&#47;
SECTION_11_12_9_31_STATIC_SECURITY_ANALYSIS_REMEDIATION_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_9_31_static_security_analysis_high_remediation_and_rerun_v1&#47;20260811T043722Z&#47;
SECTION_11_12_9_32_SECURITY_REGRESSION_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_9_32_pre_live_security_regression_v1&#47;20260811T044255Z&#47;
SECTION_11_12_9_33_PENETRATION_PROGRAM_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_9_33_pre_live_penetration_program_v1&#47;20260811T044900Z&#47;
SECTION_11_12_9_34_CREDENTIAL_LEAKAGE_TEST_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_9_34_pre_live_credential_leakage_test_v1&#47;20260811T045537Z&#47;
SECTION_11_12_9_35_AUTHORITY_REPLAY_TEST_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_9_35_pre_live_authority_replay_test_v1&#47;20260811T050403Z&#47;
SECTION_11_12_9_36_RECOVERY_SECURITY_TEST_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_9_36_pre_live_recovery_security_test_v1&#47;20260811T050823Z&#47;
SECTION_11_12_9_37_CRITICAL_FINDINGS_OPEN_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_9_37_pre_live_critical_findings_open_v1&#47;20260811T052152Z&#47;
SECTION_11_12_9_38_HIGH_FINDINGS_OPEN_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_9_38_pre_live_high_findings_open_v1&#47;20260811T052547Z&#47;
SECTION_11_12_9_39_LIVE_TESTNET_ISOLATION_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_9_39_pre_live_live_testnet_isolation_proven_v1&#47;20260811T052914Z&#47;
SECTION_11_12_9_40_LIVE_DEFAULT_BLOCK_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_9_40_pre_live_live_default_block_proven_v1&#47;20260811T053222Z&#47;
SECTION_11_12_9_40R_RECOVERY_BIND_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_9_recover_bind_pre_live_packages_29_through_40_v1&#47;20260811T054023Z&#47;
SECTION_11_12_9_41_LIVE_ARMING_FAIL_CLOSED_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_9_41_pre_live_live_arming_fail_closed_proven_v1&#47;20260811T060013Z&#47;
SECTION_11_12_9_42_AUDIT_EVIDENCE_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_9_42_pre_live_audit_evidence_verified_v1&#47;20260811T125657Z&#47;
SECTION_11_12_9_43_MANIFEST_VERIFY_RC_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_9_43_pre_live_manifest_verify_rc_v1&#47;20260811T131157Z&#47;
SECTION_11_12_9_44_PRE_LIVE_GATE_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_9_44_pre_live_cybersecurity_gate_pass_v1&#47;20260811T133046Z&#47;
SECTION_11_12_9_21_PREP_IS_NOT_LONG_RUNNING_TESTNET_PROVEN=true
SECTION_11_12_9_21_PREP_IS_NOT_EXECUTE_AUTHORIZATION=true
SECTION_11_12_9_21_PREP_IS_NOT_SECTION_11_12_8_REOPEN=true
SECTION_11_12_9_22_REEVAL_PASS_IS_NOT_PRE_LIVE_CYBERSECURITY_GATE_PASS=true
LONG_RUNNING_TESTNET_PROVEN_IS_NOT_PRE_LIVE_CYBERSECURITY_GATE_PASS=true
SECTION_11_12_9_23_ARCHITECTURE_REVIEW_PASS_IS_NOT_PRE_LIVE_CYBERSECURITY_GATE_PASS=true
CYBERSECURITY_ARCHITECTURE_REVIEW_PASS_IS_NOT_THREAT_MODEL_CURRENT=true
CYBERSECURITY_ARCHITECTURE_REVIEW_PASS_IS_NOT_PRE_LIVE_CYBERSECURITY_GATE_PASS=true
SECTION_11_12_9_24_THREAT_MODEL_PASS_IS_NOT_PRE_LIVE_CYBERSECURITY_GATE_PASS=true
THREAT_MODEL_CURRENT_IS_NOT_PRE_LIVE_CYBERSECURITY_GATE_PASS=true
THREAT_MODEL_CURRENT_IS_NOT_SECRETS_REVIEW=true
VENUE_THREAT_MODEL_DELTA_IS_NOT_THREAT_MODEL_CURRENT=true
SECTION_11_12_9_25_SECRETS_REVIEW_PASS_IS_NOT_PRE_LIVE_CYBERSECURITY_GATE_PASS=true
SECRETS_REVIEW_IS_NOT_PRE_LIVE_CYBERSECURITY_GATE_PASS=true
SECRETS_REVIEW_IS_NOT_CREDENTIAL_LEAKAGE_TEST=true
SECRETS_REVIEW_IS_NOT_DEPENDENCY_AUDIT=true
SECTION_11_12_9_26_DEPENDENCY_AUDIT_FAIL_IS_NOT_DEPENDENCY_AUDIT_PROVEN=true
SECTION_11_12_9_26_DEPENDENCY_AUDIT_FAIL_IS_NOT_PRE_LIVE_CYBERSECURITY_GATE_PASS=true
DEPENDENCY_AUDIT_IS_NOT_PRE_LIVE_CYBERSECURITY_GATE_PASS=true
DEPENDENCY_AUDIT_IS_NOT_SBOM_PRESENT=true
DEPENDENCY_AUDIT_FAIL_IS_NOT_REMEDIATION_AUTHORIZATION=true
SECTION_11_12_9_27_FORENSIC_REVIEW_IS_NOT_REMEDIATION_AUTHORIZATION=true
SECTION_11_12_9_27_FORENSIC_REVIEW_IS_NOT_DEPENDENCY_AUDIT_PROVEN=true
SECTION_11_12_9_27_FORENSIC_REVIEW_IS_NOT_PRE_LIVE_CYBERSECURITY_GATE_PASS=true
FULL_SECURITY_COVERAGE_REVIEW_PROVEN_IS_NOT_PRE_LIVE_CYBERSECURITY_GATE_PASS=true
SECTION_11_12_9_28_DEPENDENCY_AUDIT_PASS_IS_NOT_PRE_LIVE_CYBERSECURITY_GATE_PASS=true
SECTION_11_12_9_28_DEPENDENCY_AUDIT_PASS_IS_NOT_SBOM_PRESENT=true
DEPENDENCY_AUDIT_PROVEN_IS_NOT_PRE_LIVE_CYBERSECURITY_GATE_PASS=true
SECTION_11_12_9_29_SBOM_PRESENT_IS_NOT_PRE_LIVE_CYBERSECURITY_GATE_PASS=true
SBOM_PRESENT_IS_NOT_PRE_LIVE_CYBERSECURITY_GATE_PASS=true
SBOM_PRESENT_IS_NOT_STATIC_SECURITY_ANALYSIS=true
SBOM_PRESENT_IS_NOT_LIVE_AUTHORIZED=true
SBOM_PRESENT_IS_NOT_SECTION_11_13_STARTED=true
SECTION_11_12_9_30_STATIC_SECURITY_ANALYSIS_FAIL_IS_NOT_STATIC_SECURITY_ANALYSIS_PROVEN=true
SECTION_11_12_9_30_STATIC_SECURITY_ANALYSIS_FAIL_IS_NOT_PRE_LIVE_CYBERSECURITY_GATE_PASS=true
STATIC_SECURITY_ANALYSIS_IS_NOT_PRE_LIVE_CYBERSECURITY_GATE_PASS=true
STATIC_SECURITY_ANALYSIS_IS_NOT_SECURITY_REGRESSION=true
STATIC_SECURITY_ANALYSIS_FAIL_IS_NOT_REMEDIATION_AUTHORIZATION=true
SECTION_11_12_9_31_STATIC_SECURITY_ANALYSIS_PASS_IS_NOT_PRE_LIVE_CYBERSECURITY_GATE_PASS=true
SECTION_11_12_9_31_STATIC_SECURITY_ANALYSIS_PASS_IS_NOT_SECURITY_REGRESSION=true
STATIC_SECURITY_ANALYSIS_PROVEN_IS_NOT_PRE_LIVE_CYBERSECURITY_GATE_PASS=true
SECTION_11_12_9_32_SECURITY_REGRESSION_PASS_IS_NOT_PRE_LIVE_CYBERSECURITY_GATE_PASS=true
SECURITY_REGRESSION_IS_NOT_PRE_LIVE_CYBERSECURITY_GATE_PASS=true
SECURITY_REGRESSION_IS_NOT_PENETRATION_PROGRAM=true
SECURITY_REGRESSION_IS_NOT_CREDENTIAL_LEAKAGE_TEST=true
SECURITY_REGRESSION_IS_NOT_LIVE_AUTHORIZED=true
SECURITY_REGRESSION_IS_NOT_SECTION_11_13_STARTED=true
SECTION_11_12_9_33_PENETRATION_PROGRAM_PASS_IS_NOT_PRE_LIVE_CYBERSECURITY_GATE_PASS=true
PENETRATION_PROGRAM_IS_NOT_PRE_LIVE_CYBERSECURITY_GATE_PASS=true
PENETRATION_PROGRAM_IS_NOT_CREDENTIAL_LEAKAGE_TEST=true
PENETRATION_PROGRAM_IS_NOT_AUTHORITY_REPLAY_TEST=true
PENETRATION_PROGRAM_IS_NOT_RECOVERY_SECURITY_TEST=true
PENETRATION_PROGRAM_IS_NOT_ZAP_DAST=true
PENETRATION_PROGRAM_IS_NOT_LIVE_AUTHORIZED=true
PENETRATION_PROGRAM_IS_NOT_SECTION_11_13_STARTED=true
SECTION_11_12_9_34_CREDENTIAL_LEAKAGE_TEST_PASS_IS_NOT_PRE_LIVE_CYBERSECURITY_GATE_PASS=true
CREDENTIAL_LEAKAGE_TEST_IS_NOT_PRE_LIVE_CYBERSECURITY_GATE_PASS=true
CREDENTIAL_LEAKAGE_TEST_IS_NOT_SECRETS_REVIEW=true
CREDENTIAL_LEAKAGE_TEST_IS_NOT_PENETRATION_PROGRAM=true
CREDENTIAL_LEAKAGE_TEST_IS_NOT_AUTHORITY_REPLAY_TEST=true
CREDENTIAL_LEAKAGE_TEST_IS_NOT_RECOVERY_SECURITY_TEST=true
CREDENTIAL_LEAKAGE_TEST_IS_NOT_LIVE_AUTHORIZED=true
CREDENTIAL_LEAKAGE_TEST_IS_NOT_SECTION_11_13_STARTED=true
SECTION_11_12_9_35_AUTHORITY_REPLAY_TEST_PASS_IS_NOT_PRE_LIVE_CYBERSECURITY_GATE_PASS=true
AUTHORITY_REPLAY_TEST_IS_NOT_PRE_LIVE_CYBERSECURITY_GATE_PASS=true
AUTHORITY_REPLAY_TEST_IS_NOT_CREDENTIAL_LEAKAGE_TEST=true
AUTHORITY_REPLAY_TEST_IS_NOT_PENETRATION_PROGRAM=true
AUTHORITY_REPLAY_TEST_IS_NOT_RECOVERY_SECURITY_TEST=true
AUTHORITY_REPLAY_TEST_IS_NOT_LIVE_AUTHORIZED=true
AUTHORITY_REPLAY_TEST_IS_NOT_SECTION_11_13_STARTED=true
SECTION_11_12_9_36_RECOVERY_SECURITY_TEST_PASS_IS_NOT_PRE_LIVE_CYBERSECURITY_GATE_PASS=true
RECOVERY_SECURITY_TEST_IS_NOT_PRE_LIVE_CYBERSECURITY_GATE_PASS=true
RECOVERY_SECURITY_TEST_IS_NOT_AUTHORITY_REPLAY_TEST=true
RECOVERY_SECURITY_TEST_IS_NOT_PENETRATION_PROGRAM=true
RECOVERY_SECURITY_TEST_IS_NOT_LIVE_KILL_SWITCH_PROVEN=true
RECOVERY_SECURITY_TEST_IS_NOT_LIVE_AUTHORIZED=true
RECOVERY_SECURITY_TEST_IS_NOT_SECTION_11_13_STARTED=true
SECTION_11_12_9_37_CRITICAL_FINDINGS_OPEN_PASS_IS_NOT_PRE_LIVE_CYBERSECURITY_GATE_PASS=true
CRITICAL_FINDINGS_OPEN_IS_NOT_PRE_LIVE_CYBERSECURITY_GATE_PASS=true
CRITICAL_FINDINGS_OPEN_IS_NOT_HIGH_FINDINGS_OPEN=true
CRITICAL_FINDINGS_OPEN_IS_NOT_LIVE_AUTHORIZED=true
CRITICAL_FINDINGS_OPEN_IS_NOT_SECTION_11_13_STARTED=true
SECTION_11_12_9_38_HIGH_FINDINGS_OPEN_PASS_IS_NOT_PRE_LIVE_CYBERSECURITY_GATE_PASS=true
HIGH_FINDINGS_OPEN_IS_NOT_PRE_LIVE_CYBERSECURITY_GATE_PASS=true
HIGH_FINDINGS_OPEN_IS_NOT_CRITICAL_FINDINGS_OPEN=true
HIGH_FINDINGS_OPEN_IS_NOT_LIVE_TESTNET_ISOLATION_PROVEN=true
HIGH_FINDINGS_OPEN_IS_NOT_LIVE_AUTHORIZED=true
HIGH_FINDINGS_OPEN_IS_NOT_SECTION_11_13_STARTED=true
SECTION_11_12_9_39_LIVE_TESTNET_ISOLATION_PASS_IS_NOT_PRE_LIVE_CYBERSECURITY_GATE_PASS=true
LIVE_TESTNET_ISOLATION_PROVEN_IS_NOT_PRE_LIVE_CYBERSECURITY_GATE_PASS=true
LIVE_TESTNET_ISOLATION_PROVEN_IS_NOT_LIVE_DEFAULT_BLOCK_PROVEN=true
LIVE_TESTNET_ISOLATION_PROVEN_IS_NOT_LIVE_ARMING_FAIL_CLOSED_PROVEN=true
LIVE_TESTNET_ISOLATION_PROVEN_IS_NOT_LIVE_AUTHORIZED=true
LIVE_TESTNET_ISOLATION_PROVEN_IS_NOT_SECTION_11_13_STARTED=true
SECTION_11_12_9_40_LIVE_DEFAULT_BLOCK_PASS_IS_NOT_PRE_LIVE_CYBERSECURITY_GATE_PASS=true
LIVE_DEFAULT_BLOCK_PROVEN_IS_NOT_PRE_LIVE_CYBERSECURITY_GATE_PASS=true
LIVE_DEFAULT_BLOCK_PROVEN_IS_NOT_LIVE_ARMING_FAIL_CLOSED_PROVEN=true
LIVE_DEFAULT_BLOCK_PROVEN_IS_NOT_LIVE_TESTNET_ISOLATION_PROVEN=true
LIVE_DEFAULT_BLOCK_PROVEN_IS_NOT_LIVE_AUTHORIZED=true
LIVE_DEFAULT_BLOCK_PROVEN_IS_NOT_SECTION_11_13_STARTED=true
SECTION_11_12_9_40R_RECOVERY_BIND_IS_NOT_PRE_LIVE_CYBERSECURITY_GATE_PASS=true
RECOVERY_BIND_29_40_IS_NOT_PRE_LIVE_CYBERSECURITY_GATE_PASS=true
RECOVERY_BIND_29_40_IS_NOT_LIVE_ARMING_FAIL_CLOSED_PROVEN=true
RECOVERY_BIND_29_40_IS_NOT_LIVE_ARMING_AUTHORIZATION=true
RECOVERY_BIND_29_40_IS_NOT_LIVE_AUTHORIZED=true
SECTION_11_12_9_41_LIVE_ARMING_FAIL_CLOSED_PASS_IS_NOT_PRE_LIVE_CYBERSECURITY_GATE_PASS=true
LIVE_ARMING_FAIL_CLOSED_PROVEN_IS_NOT_PRE_LIVE_CYBERSECURITY_GATE_PASS=true
LIVE_ARMING_FAIL_CLOSED_PROVEN_IS_NOT_LIVE_AUTHORIZED=true
LIVE_ARMING_FAIL_CLOSED_PROVEN_IS_NOT_SECTION_11_13_STARTED=true
LIVE_ARMING_FAIL_CLOSED_PROVEN_IS_NOT_LIVE_DEFAULT_BLOCK_PROVEN=true
LIVE_ARMING_FAIL_CLOSED_PROVEN_IS_NOT_AUDIT_EVIDENCE_VERIFIED=true
SECTION_11_12_9_42_AUDIT_EVIDENCE_PASS_IS_NOT_PRE_LIVE_CYBERSECURITY_GATE_PASS=true
AUDIT_EVIDENCE_VERIFIED_IS_NOT_PRE_LIVE_CYBERSECURITY_GATE_PASS=true
AUDIT_EVIDENCE_VERIFIED_IS_NOT_LIVE_AUTHORIZED=true
AUDIT_EVIDENCE_VERIFIED_IS_NOT_SECTION_11_13_STARTED=true
AUDIT_EVIDENCE_VERIFIED_IS_NOT_MANIFEST_VERIFY_RC_GATE_CRITERION=true
AUDIT_EVIDENCE_VERIFIED_IS_NOT_TESTNET_EVIDENCE_VERIFIED=true
SECTION_11_12_9_43_MANIFEST_VERIFY_RC_PASS_IS_NOT_PRE_LIVE_CYBERSECURITY_GATE_PASS=true
MANIFEST_VERIFY_RC_GATE_CRITERION_IS_NOT_PRE_LIVE_CYBERSECURITY_GATE_PASS=true
MANIFEST_VERIFY_RC_GATE_CRITERION_IS_NOT_LIVE_AUTHORIZED=true
MANIFEST_VERIFY_RC_GATE_CRITERION_IS_NOT_SECTION_11_13_STARTED=true
MANIFEST_VERIFY_RC_GATE_CRITERION_IS_NOT_AUDIT_EVIDENCE_VERIFIED=true
MANIFEST_VERIFY_RC_GATE_CRITERION_IS_NOT_TESTNET_EVIDENCE_VERIFIED=true
SECTION_11_12_9_44_PRE_LIVE_GATE_PASS_IS_NOT_LIVE_AUTHORIZED=true
PRE_LIVE_CYBERSECURITY_GATE_PASS_IS_NOT_LIVE_AUTHORIZED=true
PRE_LIVE_CYBERSECURITY_GATE_PASS_IS_NOT_SECTION_11_13_STARTED=true
PRE_LIVE_CYBERSECURITY_GATE_PASS_IS_NOT_LIVE_ENABLED=true
PRE_LIVE_CYBERSECURITY_GATE_PASS_IS_NOT_LIVE_ARMED=true
PRE_LIVE_CYBERSECURITY_GATE_PASS_IS_NOT_LIVE_ORDER_AUTHORIZED=true
ELIGIBLE_FOR_LIVE_READINESS_EVALUATION_IS_NOT_LIVE_AUTHORIZED=true
ELIGIBLE_FOR_LIVE_READINESS_EVALUATION_IS_NOT_SECTION_11_13_STARTED=true
SECTION_11_13_LIVE_READINESS_EVALUATION_COMPLETED_IS_NOT_LIVE_AUTHORIZED=true
SECTION_11_13_STARTED_IS_NOT_LIVE_AUTHORIZED=true
SECTION_11_13_STARTED_IS_NOT_LIVE_ACTIVATION=true
FULLY_AUTONOMOUS_LIVE_TRADING_READY_FALSE_IS_NOT_LIVE_STAGE_BYPASS=true
SECTION_11_13_LIVE_READINESS_EVALUATION_COMPLETED_IS_NOT_FULLY_AUTONOMOUS_LIVE_TRADING_READY=true
SECTION_11_13_LIVE_READINESS_EVALUATION_COMPLETED_IS_NOT_LIVE_PRIVATE_READ_ONLY_PROVEN=true
SECTION_11_13_2_PREPARATION_IS_NOT_LIVE_PRIVATE_READ_ONLY_PROVEN=true
SECTION_11_13_2_PRODUCTIVE_EXECUTE_PATH_READY_IS_NOT_LIVE_PRIVATE_READ_ONLY_PROVEN=true
SECTION_11_13_2_PREPARATION_IS_NOT_LIVE_AUTHORIZED=true
LIVE_PRIVATE_READ_ONLY_PROVEN_IS_NOT_LIVE_AUTHORIZED=true
LIVE_PRIVATE_READ_ONLY_PROVEN_IS_NOT_LIVE_SHADOW_AUTHORIZATION=true
LIVE_PRIVATE_READ_ONLY_AUTHORIZED_IS_NOT_LIVE_AUTHORIZED=true
CAPABILITY_11_7_CONTRACTS_ONLY_IS_NOT_SECTION_11_13_2_NETWORK_UNLOCK=true
FIXTURE_PASS_IS_NOT_LIVE_PRIVATE_READ_ONLY_PROVEN=true
OWNER_GO_PREPARATION_IS_NOT_OWNER_GO_LIVE_PRIVATE_READ_ONLY=true
OWNER_GO_PRODUCTIVE_EXECUTE_UNLOCK_AUTHORING_IS_NOT_OWNER_GO_LIVE_PRIVATE_READ_ONLY=true
LIVE_PRIVATE_READ_ONLY_PROVEN_IS_NOT_LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION=true
SECTION_11_13_3_PREPARATION_IS_NOT_LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_PROVEN=true
SECTION_11_13_3_PRODUCTIVE_EXECUTE_PATH_READY_IS_NOT_LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_PROVEN=true
SECTION_11_13_3_PRODUCTIVE_EXECUTE_UNLOCK_AUTHORING_IS_NOT_OWNER_GO_LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION=true
SECTION_11_13_3_PREPARATION_IS_NOT_LIVE_AUTHORIZED=true
SECTION_11_13_3_PREPARATION_IS_NOT_LIVE_DRY_RUN_ORDER_PLAN=true
LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_PROVEN_IS_NOT_LIVE_AUTHORIZED=true
LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_PROVEN_IS_NOT_LIVE_RECONCILIATION_PROVEN=true
LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_PROVEN_IS_NOT_LIVE_DRY_RUN_ORDER_PLAN=true
LIVE_DRY_RUN_ORDER_PLAN_PROVEN_IS_NOT_LIVE_AUTHORIZED=true
LIVE_DRY_RUN_ORDER_PLAN_PROVEN_IS_NOT_LIVE_RECONCILIATION_PROVEN=true
LIVE_DRY_RUN_ORDER_PLAN_PROVEN_IS_NOT_LIVE_CANARY_MINIMUM_EXPOSURE=true
LIVE_DRY_RUN_ORDER_PLAN_PROVEN_IS_NOT_ORDER_SUBMIT=true
BLOCKED_NO_EXECUTE_IS_EXPECTED_SAFETY_RESULT_UNDER_UNRESOLVED_DIVERGENCE=true
CAPABILITY_11_7_CONTRACTS_ONLY_IS_NOT_SECTION_11_13_3_NETWORK_UNLOCK=true
OWNER_GO_PREPARATION_IS_NOT_OWNER_GO_LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION=true
OWNER_GO_LIVE_DRY_RUN_ORDER_PLAN_IS_CONSUMED=true
OWNER_GO_LIVE_DRY_RUN_ORDER_PLAN_IS_NOT_LIVE_CANARY=true
SECTION_11_13_5_AUTHORING_IS_NOT_LIVE_CANARY_MINIMUM_EXPOSURE_PROVEN=true
SECTION_11_13_5_PRODUCTIVE_EXECUTE_PATH_READY_IS_NOT_LIVE_CANARY_EXECUTE=true
SECTION_11_13_5_AUTHORING_IS_NOT_LIVE_AUTHORIZED=true
FORENSIC_CLASSIFICATION_IS_NOT_LIVE_RECONCILIATION_PROVEN=true
CAPABILITY_11_9_FIXTURE_ONLY_IS_NOT_SECTION_11_13_5_NETWORK_UNLOCK=true
OWNER_GO_SECTION_11_13_LIVE_CANARY_PRODUCTIVE_SURFACE_AUTHORING_IS_CONSUMED=true
OWNER_GO_SECTION_11_13_LIVE_CANARY_PRODUCTIVE_SURFACE_AUTHORING_IS_NOT_CANARY_EXECUTE=true
OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE_PRIOR_FAIL_CLOSED_CONSUME_IS_NOT_REUSABLE=true
OWNER_GO_SECTION_11_13_PRE_CANARY_GOVERNANCE_CYBERSECURITY_NOTION_AUDIT_IS_CONSUMED=true
OWNER_GO_SECTION_11_13_PRE_CANARY_AUDIT_IS_NOT_CANARY_EXECUTE=true
LIVE_CANARY_CYBERSECURITY_GATE_NOT_PASSED_IS_NOT_PRE_LIVE_GATE_FAIL=true
PRE_LIVE_CYBERSECURITY_GATE_PASS_IS_NOT_LIVE_CANARY_CYBERSECURITY_GATE_PASS=true
OKX_TEMP_SECURITY_CLEARANCE_PRESENT_PROVEN_IS_NOT_LIVE_CANARY_CYBERSECURITY_GATE_PASS=true
EXCHANGE_TRUTH_ADOPTION_IS_NOT_CANARY_AUTHORIZATION=true
EXCHANGE_TRUTH_ADOPTION_IS_NOT_LIVE_CANARY_CYBERSECURITY_GATE_PASS=true
EXCHANGE_TRUTH_ADOPTION_IS_NOT_GENERAL_LIVE_AUTHORIZATION=true
EXCHANGE_TRUTH_ADOPTION_IS_NOT_ECONOMIC_BASELINE_POLICY_ADOPTION=true
OWNER_GO_EXCHANGE_TRUTH_ADOPTION_IS_CONSUMED=true
LIVE_RECONCILIATION_PROVEN_IS_NOT_LIVE_AUTHORIZED=true
LIVE_RECONCILIATION_PROVEN_IS_NOT_CANARY_AUTHORIZATION=true
ECONOMIC_BASELINE_ADOPTION_IS_NOT_OKX_TEMP_SECURITY_CLEARANCE=true
OKX_TEMP_SECURITY_CLEARANCE_ABSENT_OR_UNPROVEN_IS_NOT_WALL_CLOCK_ALONE=true
OKX_TEMP_SECURITY_CLEARANCE_PRESENT_PROVEN_IS_NOT_WALL_CLOCK_ALONE=true
OWNER_GO_ECONOMIC_BASELINE_AND_OKX_CLEARANCE_EVIDENCE_IS_CONSUMED=true
OWNER_GO_ECONOMIC_BASELINE_AND_OKX_CLEARANCE_EVIDENCE_IS_NOT_CANARY_EXECUTE=true
OWNER_GO_CAP11_OKX_TEMP_SECURITY_CLEARANCE_FRESH_EVIDENCE_CANONICAL_PERSISTENCE_IS_CONSUMED=true
OWNER_GO_CAP11_OKX_TEMP_SECURITY_CLEARANCE_FRESH_EVIDENCE_CANONICAL_PERSISTENCE_IS_NOT_GATE_REEVAL=true
OWNER_GO_CAP11_OKX_TEMP_SECURITY_CLEARANCE_FRESH_EVIDENCE_CANONICAL_PERSISTENCE_IS_NOT_CANARY_EXECUTE=true
OWNER_GO_PERSIST_LIVE_CANARY_CYBERSECURITY_GATE_PASS_IS_CONSUMED=true
OWNER_GO_PERSIST_LIVE_CANARY_CYBERSECURITY_GATE_PASS_IS_NOT_CANARY_EXECUTE=true
OWNER_GO_PERSIST_LIVE_CANARY_CYBERSECURITY_GATE_PASS_IS_NOT_LIVE_AUTHORIZED=true
LIVE_CANARY_CYBERSECURITY_GATE_PASS_IS_NOT_CANARY_EXECUTE=true
LIVE_CANARY_CYBERSECURITY_GATE_PASS_IS_NOT_LIVE_AUTHORIZED=true
LIVE_CANARY_CYBERSECURITY_GATE_PASS_IS_NOT_OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE=true
CANARY_SUBMIT_TRANSPORT_IMPLEMENTED_IS_NOT_CANARY_EXECUTE=true
CANARY_SUBMIT_TRANSPORT_IMPLEMENTED_IS_NOT_SUBMIT_UNLOCKED=true
CANARY_SUBMIT_TRANSPORT_IMPLEMENTED_IS_NOT_GENERAL_LIVE_SUBMIT_UNLOCK=true
CANARY_SUBMIT_TRANSPORT_IMPLEMENTED_IS_NOT_LIVE_AUTHORIZED=true
OWNER_GO_CANARY_SUBMIT_TRANSPORT_PREPARATION_IS_CONSUMED=true
OWNER_GO_CANARY_SUBMIT_TRANSPORT_PREPARATION_IS_NOT_CANARY_EXECUTE=true
OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE_CONSUMED_IS_NOT_CANARY_PROVEN=true
OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE_CONSUMED_IS_NOT_RETRY_SAFE=true
POST_401_ROOT_CAUSE_UNPROVEN_IS_NOT_PROVEN_50113=true
OBSERVED_ONESHOT_POST_50124_IS_NOT_INSTRUMENT_GET_401=true
OBSERVED_ONESHOT_POST_50124_IS_NOT_HISTORICAL_FIRST_401=true
ACCOUNT_INSTRUMENTS_EMPTY_SWAP_IS_NOT_ON_SUBMIT_PATH=true
ACCOUNT_INSTRUMENTS_EMPTY_SWAP_IS_NOT_50124_CAUSE=true
GET_TAMPER_50113_IS_NOT_INCIDENT_BODY=true
HISTORICAL_50110_CLEARED_IS_NOT_ONESHOT_50124=true
MARKET_PERMISSION_GO_TOKEN_NAME_IS_NOT_ROOT_CAUSE_PROVEN=true
CLASSIFICATION_IS_NOT_RETRY_SAFE=true
SEPARATE_DIAGNOSTIC_EVIDENCE_IS_NOT_ROOT_CAUSE_PROVEN=true
MERGE_IS_NOT_EXECUTE=true

RECOVERY_BIND_29_40_IS_NOT_SECTION_11_13_STARTED=true
XPERP_BOUNDED_CAMPAIGN_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_8_bounded_okx_eea_demo_xperp_campaign_execute_v1&#47;20260810T181703Z&#47;
XPERP_BOUNDED_CAMPAIGN_FORENSIC_POINTER=evidence&#47;ops&#47;section_11_12_8_bounded_okx_eea_demo_xperp_campaign_execute_v1&#47;20260810T181703Z&#47;derived_forensic_closeout_v1&#47;
XPERP_BOUNDED_ACK_PROOF_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_8_retry_bounded_okx_eea_demo_xperp_ack_proof_after_clordid_fix_v1&#47;20260810T194806Z&#47;
XPERP_BOUNDED_CLEAN_CLOSEOUT_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_8_retry_bounded_okx_eea_demo_xperp_clean_closeout_after_cancel_instid_fix_v1&#47;20260810T200151Z&#47;
XPERP_SECTION_11_12_8_CLOSEOUT_PACKAGE_POINTER=evidence&#47;ops&#47;section_11_12_8_closeout_package_v1&#47;20260810T201332Z&#47;
SECTION_11_12_9_EVALUATION_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_9_pre_live_cybersecurity_acceptance_gate_evidence_bound_evaluation_v1&#47;20260810T202800Z&#47;
SECTION_11_12_9_2_NOMENCLATURE_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_9_2_cap_11_12_testnet_program_nomenclature_reconcile_v1&#47;20260810T205051Z&#47;
SECTION_11_12_1_RESIDUAL_PROOF_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_1_cap_11_12_testnet_progression_residual_proof_v1&#47;20260810T211204Z&#47;
SECTION_11_12_2_RESIDUAL_PROOF_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_2_cap_11_12_testnet_progression_residual_proof_v1&#47;20260810T211449Z&#47;
SECTION_11_12_3_RESIDUAL_PROOF_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_3_cap_11_12_testnet_progression_residual_proof_v1&#47;20260810T211709Z&#47;
SECTION_11_12_4_RESIDUAL_PROOF_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_4_cap_11_12_testnet_progression_residual_proof_v1&#47;20260810T211915Z&#47;
SECTION_11_12_5_RESIDUAL_PROOF_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_5_cap_11_12_testnet_progression_residual_proof_v1&#47;20260810T212119Z&#47;
SECTION_11_12_6_RESIDUAL_PROOF_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_6_cap_11_12_testnet_progression_residual_proof_v1&#47;20260810T212326Z&#47;
SECTION_11_12_7_RESIDUAL_PROOF_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_7_cap_11_12_testnet_progression_residual_proof_v1&#47;20260810T212535Z&#47;
SECTION_11_12_8_RESIDUAL_PROOF_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_8_cap_11_12_testnet_progression_residual_proof_v1&#47;20260810T212942Z&#47;
SECTION_11_12_9_11_RESIDUAL_PROOF_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_9_11_open_testnet_proven_fields_reporting_reconcile_residual_proof_v1&#47;20260810T213441Z&#47;
SECTION_11_12_9_12_PROOF_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_testnet_order_lifecycle_proven_v1&#47;20260810T215942Z&#47;
SECTION_11_12_9_13_PROOF_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_testnet_reconciliation_proven_v1&#47;20260810T221902Z&#47;
SECTION_11_12_9_14_PROOF_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_testnet_restart_proven_v1&#47;20260810T223606Z&#47;
SECTION_11_12_9_15_PROOF_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_testnet_unknown_submit_recovery_proven_v1&#47;20260810T224947Z&#47;
SECTION_11_12_9_16_PROOF_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_testnet_duplicate_order_prevention_proven_v1&#47;20260810T230257Z&#47;
SECTION_11_12_9_17_PROOF_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_testnet_kill_switch_proven_v1&#47;20260810T232151Z&#47;
SECTION_11_12_9_18_PROOF_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_testnet_autonomous_recovery_proven_v1&#47;20260810T233904Z&#47;
SECTION_11_12_9_19_PROOF_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_testnet_evidence_verified_v1&#47;20260810T235545Z&#47;
SECTION_11_12_9_20_REEVAL_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_9_20_pre_live_cybersecurity_gate_post_cap_11_12_close_reevaluation_v1&#47;20260811T001530Z&#47;
PREDECESSOR_GET_PROOF_IS_NOT_TARGETED_TRADE_PROOF=true
PREDECESSOR_ORDERLESS_GET_PROOF_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_8_autonomous_okx_eea_demo_credential_ip_resolve_v1&#47;20260808T203507Z&#47;
XPERP_PRIVATE_RO_PROOF_EVIDENCE_POINTER=evidence&#47;ops&#47;section_11_12_8_retry_okx_eea_private_ro_xperp_verify_no_order_v1&#47;20260810T165847Z&#47;
ALTERNATE_EVALUATION_IS_NOT_VENUE_ACTIVATION=true
BINDING_PACKAGE_IS_NOT_VENUE_ACTIVATION=true
WRITE_PATH_WIRED_IS_NOT_CAMPAIGN_STARTED=true
CAMPAIGN_EXECUTION_PASS_IS_NOT_SECTION_CLOSE=true
HISTORICAL_GLOBAL_OR_SWAP_EVIDENCE_IS_NOT_ACTIVE_BINDING=true
NO_PARALLEL_ACTIVE_SWAP_NAVIGATION=true
FURTHER_OKX_EEA_DEMO_ORDER_POSTS_AUTHORIZED_SWAP_PATH_ONLY=true
SECTION_11_12_9_EVALUATION_COMPLETED_IS_NOT_GATE_PASS=true
SECTION_11_12_1_RESIDUAL_PROOF_PASS_IS_NOT_TESTNET_ORDER_LIFECYCLE_PROVEN=true
SECTION_11_12_1_RESIDUAL_BOUND_IS_NOT_CAP_11_12_TESTNET_PROGRAM_CLOSED=true
SECTION_11_12_2_RESIDUAL_PROOF_PASS_IS_NOT_TESTNET_ORDER_LIFECYCLE_PROVEN=true
SECTION_11_12_2_RESIDUAL_BOUND_IS_NOT_CAP_11_12_TESTNET_PROGRAM_CLOSED=true
SECTION_11_12_3_RESIDUAL_PROOF_PASS_IS_NOT_TESTNET_ORDER_LIFECYCLE_PROVEN=true
SECTION_11_12_3_RESIDUAL_BOUND_IS_NOT_CAP_11_12_TESTNET_PROGRAM_CLOSED=true
SECTION_11_12_4_RESIDUAL_PROOF_PASS_IS_NOT_TESTNET_ORDER_LIFECYCLE_PROVEN=true
SECTION_11_12_4_RESIDUAL_BOUND_IS_NOT_CAP_11_12_TESTNET_PROGRAM_CLOSED=true
SECTION_11_12_5_RESIDUAL_PROOF_PASS_IS_NOT_TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN=true
SECTION_11_12_5_RESIDUAL_BOUND_IS_NOT_CAP_11_12_TESTNET_PROGRAM_CLOSED=true
SECTION_11_12_6_RESIDUAL_PROOF_PASS_IS_NOT_TESTNET_RESTART_PROVEN=true
SECTION_11_12_6_RESIDUAL_BOUND_IS_NOT_CAP_11_12_TESTNET_PROGRAM_CLOSED=true
SECTION_11_12_7_RESIDUAL_PROOF_PASS_IS_NOT_TESTNET_KILL_SWITCH_PROVEN=true
SECTION_11_12_7_RESIDUAL_BOUND_IS_NOT_CAP_11_12_TESTNET_PROGRAM_CLOSED=true
SECTION_11_12_8_RESIDUAL_PROOF_PASS_IS_NOT_TESTNET_EVIDENCE_VERIFIED=true
SECTION_11_12_8_RESIDUAL_BOUND_IS_NOT_CAP_11_12_TESTNET_PROGRAM_CLOSED=true
OPEN_TESTNET_PROVEN_FIELDS_MEMBERSHIP_IS_NOT_PROVEN=true
TESTNET_EVIDENCE_VERIFIED_IN_OPEN_LIST_IS_NOT_TESTNET_EVIDENCE_VERIFIED_TRUE=true
SECTION_11_12_9_11_RESIDUAL_PROOF_PASS_IS_NOT_TESTNET_ORDER_LIFECYCLE_PROVEN=true
SECTION_11_12_9_11_RESIDUAL_BOUND_IS_NOT_CAP_11_12_TESTNET_PROGRAM_CLOSED=true
SECTION_11_12_9_12_PROOF_PASS_IS_NOT_TESTNET_RECONCILIATION_PROVEN=true
SECTION_11_12_9_12_PROOF_BOUND_IS_NOT_CAP_11_12_TESTNET_PROGRAM_CLOSED=true
SECTION_11_12_9_13_PROOF_PASS_IS_NOT_TESTNET_RESTART_PROVEN=true
SECTION_11_12_9_13_PROOF_BOUND_IS_NOT_CAP_11_12_TESTNET_PROGRAM_CLOSED=true
SECTION_11_12_9_14_PROOF_PASS_IS_NOT_TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN=true
SECTION_11_12_9_14_PROOF_BOUND_IS_NOT_CAP_11_12_TESTNET_PROGRAM_CLOSED=true
SECTION_11_12_9_15_PROOF_PASS_IS_NOT_TESTNET_DUPLICATE_ORDER_PREVENTION_PROVEN=true
SECTION_11_12_9_15_PROOF_BOUND_IS_NOT_CAP_11_12_TESTNET_PROGRAM_CLOSED=true
SECTION_11_12_9_16_PROOF_PASS_IS_NOT_TESTNET_KILL_SWITCH_PROVEN=true
SECTION_11_12_9_16_PROOF_BOUND_IS_NOT_CAP_11_12_TESTNET_PROGRAM_CLOSED=true
SECTION_11_12_9_17_PROOF_PASS_IS_NOT_TESTNET_AUTONOMOUS_RECOVERY_PROVEN=true
SECTION_11_12_9_17_PROOF_BOUND_IS_NOT_CAP_11_12_TESTNET_PROGRAM_CLOSED=true
SECTION_11_12_9_18_PROOF_PASS_IS_NOT_TESTNET_EVIDENCE_VERIFIED=true
SECTION_11_12_9_18_PROOF_BOUND_IS_NOT_CAP_11_12_TESTNET_PROGRAM_CLOSED=true
SECTION_11_12_9_19_PROOF_PASS_IS_NOT_PRE_LIVE_CYBERSECURITY_GATE_PASS=true
SECTION_11_12_9_19_PROOF_PASS_IS_NOT_LONG_RUNNING_TESTNET_PROVEN=true
SECTION_11_12_9_19_PROOF_PASS_IS_NOT_SECTION_11_13_STARTED=true
SECTION_11_12_9_19_PROOF_BOUND_IS_NOT_LIVE_AUTHORIZED=true
CAP_11_12_TESTNET_PROGRAM_CLOSED_IS_NOT_PRE_LIVE_CYBERSECURITY_GATE_PASS=true
SECTION_11_12_9_20_REEVAL_PASS_IS_NOT_PRE_LIVE_CYBERSECURITY_GATE_PASS=true
SECTION_11_12_9_20_REEVAL_PASS_IS_NOT_LONG_RUNNING_TESTNET_PROVEN=true
TESTNET_LIFECYCLE_PROVEN_IS_NOT_LONG_RUNNING_TESTNET_PROVEN=true
TESTNET_LIFECYCLE_PROVEN_IS_NOT_PRE_LIVE_CYBERSECURITY_GATE_PASS=true
SECTION_11_12_9_20_REEVAL_PASS_IS_NOT_SECTION_11_13_STARTED=true
SECTION_11_12_9_20_REEVAL_BOUND_IS_NOT_LIVE_AUTHORIZED=true
OPEN_RESIDUAL_LATENT_OKX_BOUND_CLIENT_SIGN_REQUEST_PATH_OMITS_QUERY_STRING=true
OPEN_RESIDUAL_PERMANENT_BOUND_CLIENT_QUERY_SIGN_FIX_IN_THIS_BINDING=false
OPEN_RESIDUAL_DOES_NOT_BLOCK_TESTNET_RECONCILIATION_PROVEN=true
OPEN_RESIDUAL_DOES_NOT_BLOCK_TESTNET_RESTART_PROVEN=true
OPEN_RESIDUAL_DOES_NOT_BLOCK_TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN=true
OPEN_RESIDUAL_DOES_NOT_BLOCK_TESTNET_DUPLICATE_ORDER_PREVENTION_PROVEN=true
OPEN_RESIDUAL_DOES_NOT_BLOCK_TESTNET_KILL_SWITCH_PROVEN=true
OPEN_RESIDUAL_DOES_NOT_BLOCK_TESTNET_AUTONOMOUS_RECOVERY_PROVEN=true
OPEN_RESIDUAL_DOES_NOT_BLOCK_TESTNET_EVIDENCE_VERIFIED=true
```

---

## 8. Wichtigste Research- / Economic-Evidence-Dokumente

| Dokument | Rolle |
|----------|-------|
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) | Economic Validity / evidence gates (aktuell) |
| [`Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md`](Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md) | Historische PART-III-Vorgängerreferenz (SUPERSEDED) |
| [`docs/ops/runbooks/INTEGRATED_PAPER_SHADOW_ECONOMIC_VALIDITY_PIPELINE_V1.md`](../ops/runbooks/INTEGRATED_PAPER_SHADOW_ECONOMIC_VALIDITY_PIPELINE_V1.md) | Gate-Split: Paper-Shadow Observation Readiness vs integriertes Economic Evidence Bundle vs ECONOMIC_VALIDITY_PASS |
| [`docs/ops/runbooks/INTEGRATED_PAPER_SHADOW_OBSERVATION_SESSION_CAPABILITY_V1.md`](../ops/runbooks/INTEGRATED_PAPER_SHADOW_OBSERVATION_SESSION_CAPABILITY_V1.md) | Kanonischer Observation-Pfad (Entrypoint/Model/Readiness/Evidence) ohne Default-Autorisierung |
| [`docs/ops/runbooks/PAPER_SHADOW_OBSERVATION_OPERATOR_GO_AND_SESSION_PREREGISTRATION_CAPABILITY_V1.md`](../ops/runbooks/PAPER_SHADOW_OBSERVATION_OPERATOR_GO_AND_SESSION_PREREGISTRATION_CAPABILITY_V1.md) | Session-Preregistration + scoped Operator-GO / Authorization-Readiness (keine Session-Ausführung) |
| [`docs/ops/runbooks/INTEGRATED_PAPER_SHADOW_OBSERVATION_WALLCLOCK_SESSION_EXECUTION_CAPABILITY_V1.md`](../ops/runbooks/INTEGRATED_PAPER_SHADOW_OBSERVATION_WALLCLOCK_SESSION_EXECUTION_CAPABILITY_V1.md) | Wallclock OKX-EEA public MD Observation (technisch; keine produktive Default-Autorisierung) |
| [`docs/ops/runbooks/INTEGRATED_PAPER_SHADOW_PRODUCTIVE_AUTHORIZATION_ISSUANCE_AND_REAL_NETWORK_EXECUTION_CAPABILITY_V1.md`](../ops/runbooks/INTEGRATED_PAPER_SHADOW_PRODUCTIVE_AUTHORIZATION_ISSUANCE_AND_REAL_NETWORK_EXECUTION_CAPABILITY_V1.md) | Produktive Issuance + realer Public-MD-Run (Merge autorisiert keine Session) |
| [`ECONOMIC_DIAGNOSTIC_OPTIMIZATION_BOUNDARY_AND_CANONICAL_TRADING_LOGIC_IMMUTABILITY_CONTRACT_V0.md`](ECONOMIC_DIAGNOSTIC_OPTIMIZATION_BOUNDARY_AND_CANONICAL_TRADING_LOGIC_IMMUTABILITY_CONTRACT_V0.md) | Optimierungsgrenze |
| [`docs/STRATEGY_RESEARCH_PLAYBOOK.md`](../STRATEGY_RESEARCH_PLAYBOOK.md) | Research-Workflow |
| [`docs/PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md`](../PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md) | Research → Portfolio-Pfad |
| [`docs/audit/EVIDENCE_INDEX.md`](../audit/EVIDENCE_INDEX.md) | Evidence-Index |

OLS / Offline Linear Evidence ist Economic-Validation-**Support**, keine Runtime-, Trading-, Promotion- oder Sizing-Authority.
`ECONOMIC_VALIDITY_OFFLINE_GATE_PASS` ist Legacy-Offline-Sub-Evidence only; System-`ECONOMIC_VALIDITY_PASS` erfordert `INTEGRATED_ECONOMIC_EVIDENCE_BUNDLE_VERIFIED`.
Paper Shadow ist Evidence-Generator only; `PAPER_SHADOW_OBSERVATION_AUTHORIZED=false` ohne verifiziertes, scoped Operator-GO-Artefakt.
Readiness ist nicht Authorization; Authorization ist nicht Execution.

---

## 8.1 Local verification minimum / CI dedup (navigation only)

| Dokument | Rolle |
|----------|-------|
| [`docs/ops/specs/GOVERNANCE_VERIFICATION_MINIMUM_LOCAL_CI_DEDUP_V1.md`](../ops/specs/GOVERNANCE_VERIFICATION_MINIMUM_LOCAL_CI_DEDUP_V1.md) | Governance verification minimum &#47; local CI dedup (navigation pointer; Semantik im Master Runbook §15.3 + JSON-Owner) |
| [`docs/ops/specs/GOVERNANCE_VERIFICATION_MINIMUM_LOCAL_CI_DEDUP_V1.json`](../ops/specs/GOVERNANCE_VERIFICATION_MINIMUM_LOCAL_CI_DEDUP_V1.json) | Machine-readable policy owner |

```text
THIS_SECTION_DEFINES_NO_SEMANTICS=true
CANONICAL_SEMANTICS=docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#15.3
```

---

## 8.2 EG-I82-JOIN closeout (navigation only)

| Pfad | Rolle |
|------|-------|
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §5.8 | SSOT-Zeiger auf EG-I82-JOIN-Closeout (navigation only; Semantik ausschließlich im Master Runbook) |

```text
THIS_SECTION_DEFINES_NO_SEMANTICS=true
THIS_DOCUMENT_POINTS_ONLY_TO_CANONICAL_OWNERS=true
CANONICAL_SEMANTICS=docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#5.8
```

---

## 8.3 Historical Package-N consumer E2E closeout (navigation only)

| Pfad | Rolle |
|------|-------|
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §5.9 | SSOT-Zeiger auf historisches no-order Package-N consumer E2E closeout (navigation only; Semantik ausschließlich im Master Runbook; bound SHA `9f09d6d18484e35e788f5e4eaada2c598926b77f`; not current `origin&#47;main`) |

```text
THIS_SECTION_DEFINES_NO_SEMANTICS=true
THIS_DOCUMENT_POINTS_ONLY_TO_CANONICAL_OWNERS=true
CANONICAL_SEMANTICS=docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#5.9
```

---

## 8.4 MG-I82-EMITTER-CUTOVER preparation (navigation only)

| Pfad | Rolle |
|------|-------|
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §5.10 | SSOT-Zeiger auf MG-I82-EMITTER-CUTOVER-Preparation (navigation only; Semantik ausschließlich im Master Runbook; `PREPARATION_COMPLETE`; emitter cutover not executed; §5.8 not reopened; Z2 pointer unchanged) |
| [`docs/ops/specs/I82_EMITTER_CUTOVER_PREPARATION_INVENTORY_V1.json`](../ops/specs/I82_EMITTER_CUTOVER_PREPARATION_INVENTORY_V1.json) | Machine-readable identity-plane inventory (navigation only; no independent semantics) |
| [`src/ops/i82_emitter_cutover_preparation_contract_v1.py`](../../src/ops/i82_emitter_cutover_preparation_contract_v1.py) | Additive sidecar &#47; compatibility contract owner (not an emitter) |

```text
THIS_SECTION_DEFINES_NO_SEMANTICS=true
THIS_DOCUMENT_POINTS_ONLY_TO_CANONICAL_OWNERS=true
CANONICAL_SEMANTICS=docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#5.10
```

---

## 8.5 MG-I82-EMITTER-CUTOVER MU6 producer cutover (navigation only)

| Pfad | Rolle |
|------|-------|
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) §5.11 | SSOT-Zeiger auf MG-I82-EMITTER-CUTOVER MU6 (navigation only; Semantik ausschließlich im Master Runbook; `EMITTER_CUTOVER_COMPLETE`; SHA256 producer; MD5-12 alias retained; §5.8 not reopened; Z2 pointer unchanged) |
| [`docs/ops/specs/I82_EMITTER_CUTOVER_PREPARATION_INVENTORY_V1.json`](../ops/specs/I82_EMITTER_CUTOVER_PREPARATION_INVENTORY_V1.json) | Machine-readable identity-plane inventory (navigation only; no independent semantics) |
| [`src/ops/i82_emitter_cutover_preparation_contract_v1.py`](../../src/ops/i82_emitter_cutover_preparation_contract_v1.py) | Identity-plane contract owner after MU6 cutover |
| [`src/experiments/base.py`](../../src/experiments/base.py) | Productive `get_experiment_id` SHA256 emitter |

```text
THIS_SECTION_DEFINES_NO_SEMANTICS=true
THIS_DOCUMENT_POINTS_ONLY_TO_CANONICAL_OWNERS=true
CANONICAL_SEMANTICS=docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#5.11
```

---

## 9. Wichtigste Runbooks

| Dokument | Rolle |
|----------|-------|
| [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) | Canonical Master Runbook (aktuelle semantische Autorität) |
| [`docs/runbooks/canonical/PEAK_TRADE_CANONICAL_RUNTIME_OPERATIONS_DASHBOARD_AND_PROCESS_SUPERVISION_RUNBOOK_V2_4.md`](../runbooks/canonical/PEAK_TRADE_CANONICAL_RUNTIME_OPERATIONS_DASHBOARD_AND_PROCESS_SUPERVISION_RUNBOOK_V2_4.md) | Canonical Runtime Operations V2.4 (`AUTHORITY_CLASSIFICATION=DERIVED_DOMAIN_AUTHORITY_ONLY`; `RUNTIME_OPERATIONS_RUNBOOK_IS_SSOT=false`; Master Runbook bleibt einzige SSOT mit absoluter Precedence; Manifest [`…_V2_4_RATIFICATION.json`](../runbooks/canonical/PEAK_TRADE_CANONICAL_RUNTIME_OPERATIONS_DASHBOARD_AND_PROCESS_SUPERVISION_RUNBOOK_V2_4_RATIFICATION.json); **kein** Runtime-/Trading-/Testnet-/Live-/Order-/Credential-Authorization-Effekt) |
| [`docs/runbooks/canonical/PEAK_TRADE_CANONICAL_CYBERSECURITY_RUNBOOK_V2_1.md`](../runbooks/canonical/PEAK_TRADE_CANONICAL_CYBERSECURITY_RUNBOOK_V2_1.md) | Canonical Cybersecurity Runbook V2.1 phase-aware / **mandatory** Pre-Live Security Gate (`AUTHORITY_CLASSIFICATION=DERIVED_DOMAIN_AUTHORITY_ONLY`; `CYBERSECURITY_RUNBOOK_IS_SSOT=false`; Master §4.8 / §4.8.1 / §11.12.9; Manifest [`…_V2_1_RATIFICATION.json`](../runbooks/canonical/PEAK_TRADE_CANONICAL_CYBERSECURITY_RUNBOOK_V2_1_RATIFICATION.json); `PRE_LIVE_CYBERSECURITY_GATE_CONTRACT=MANDATORY`; `PRE_LIVE_CYBERSECURITY_GATE=PASS`; `ELIGIBLE_FOR_LIVE_READINESS_EVALUATION=true`; `LIVE_PRIVATE_READ_ONLY_PROVEN=true`; `LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_PROVEN=true`; `LIVE_DRY_RUN_ORDER_PLAN_PROVEN=true`; `LIVE_AUTHORIZED=false`; `FUTURE_IMPLEMENTATION_BOUND_TO_CANONICAL_SECURITY_INVARIANTS=true`; **kein** Runtime-/Trading-/Testnet-/Live-/Order-/Credential-Authorization-Effekt; `CANARY_FIRST_SUBMIT_ATTEMPTED=true`; `CANARY_SUBMIT_AUTHORIZATION_STATUS=UNAUTHORIZED_UNSATISFIED`) |
| [`Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md`](Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md) | Historische Vollautonomie-Vorgängerreferenz (SUPERSEDED) |
| [`docs/ops/market_dashboard/PEAK_TRADE_MARKET_DASHBOARD_LANDSCAPE_MASTER_RUNBOOK_V2.md`](../ops/market_dashboard/PEAK_TRADE_MARKET_DASHBOARD_LANDSCAPE_MASTER_RUNBOOK_V2.md) | Market Dashboard Landscape V2 (visual read-only consumer; `LANDSCAPE_AUTHORITY_EFFECT=NONE`; Documentation Anchor = documentary index only; `OPERATOR_PRODUCT_GATE=true`; `INTRABAR_CAPABILITY=PASS`; `REGIME_BULL_BEAR_SWITCH_BINDING=COMPLETE`; `NEXT_CANONICAL_ACTION=STOP_IDLE`; `WORKSTREAM_STATE=FINAL_CLOSEOUT_COMPLETE_STOP_IDLE`) |
| [`docs/ops/runbooks/README.md`](../ops/runbooks/README.md) | Operative Runbooks |
| [`docs/ops/RUNBOOK_INDEX.md`](../ops/RUNBOOK_INDEX.md) | Index |
| [`docs/DISASTER_RECOVERY_RUNBOOK.md`](../DISASTER_RECOVERY_RUNBOOK.md) | DR |
| [`docs/LIVE_DEPLOYMENT_PLAYBOOK.md`](../LIVE_DEPLOYMENT_PLAYBOOK.md) | Deployment (non-authorizing) |

---

## 10. Reihenfolge der Implementierung

Maßgeblich ausschließlich im Canonical Master Runbook und dessen Capability-Reihenfolge. Historische STEP-29-Übersicht bleibt in der SUPERSEDED-Datei v4.4.12 nachlesbar.

Kurzüberblick (keine lokale Semantik):

```text
29A Constitutional Freeze
→ 29B Market Context
→ 29C Scope Init
→ 29D Scope Event Generator
→ 29E Bull/Bear
→ 29F Survival/Suitability
→ 29G Double Play
→ 29H Entry/Exit Policy
→ 29I Offline Trading Logic Replay
→ 29J Backtest Economic Realism
→ 29K Strategy Registry
→ 29L / 29L.1 / 29L.2 MV2 Wiring + Parity + OLS Scaffolding
→ 29M Economic Viability Evidence
→ 29N Promotion Gate Binding
→ 29O–29Q Intent / Risk / Order Intent
→ 29R–29T Runtime Rewire / Fenced Writer / Zero-Order
→ 29U–29Z Shadow → Paper → Testnet → SLO → Canary → Production
```

Aktueller Progress-Ist: [`PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md`](PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md) (non-authorizing).

---

## 11. Hinweise für neue Entwickler

1. **Immer hier starten** — dann `docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md` vollständig lesen (`CURSOR_MUST_READ_CANONICAL_RUNBOOK_FIRST=true`).
2. **Keine Vermutung über Owner** — read-only inventarisieren; Unbekanntheit = fail-closed, keine Mutation.
3. **Reuse-before-new** — bestehende Owner erweitern; keine parallele SSOT, kein zweites Runbook, keine parallele Pipeline.
4. **Docs-only vs. Runtime** — diese Map und reine Doku-PRs autorisieren nichts Live-/Order-/Scheduler-seitig.
5. **Frontdoor** für allgemeine Produktdoku: [`docs/README.md`](../README.md).
6. **Onboarding**: [`docs/GETTING_STARTED.md`](../GETTING_STARTED.md), [`docs/DEV_SETUP.md`](../DEV_SETUP.md), Python-Worktree-Bootstrap [`docs/runtime/PEAK_TRADE_WORKTREE_PYTHON_ENVIRONMENT_BOOTSTRAP_CONTRACT_V1.md`](../runtime/PEAK_TRADE_WORKTREE_PYTHON_ENVIRONMENT_BOOTSTRAP_CONTRACT_V1.md).
7. **CI / Docs Gates**: Token Policy und Reference Targets vor Push lokal prüfen; Ops-Drift-Registry bei Canonical-Doku-Änderungen mitziehen.

---

## 12. Explizite Nicht-Authority

```text
NO_SEMANTICS_IN_THIS_DOCUMENT=true
NO_TRADING_LOGIC_DEFINED_HERE=true
NO_SAFETY_OVERRIDE_DEFINED_HERE=true
NO_PROMOTION_AUTHORITY_DEFINED_HERE=true
NO_RUNTIME_ACTIVATION_BY_READING=true
NO_LIVE_FROM_DOCS_ALONE=true
MAP_OF_TRUTH_AUTHORITY=NAVIGATION_ONLY
DECISION_MAP_AUTHORITY=NAVIGATION_ONLY
SELECTION_OWNER=CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1
LANDSCAPE_ROLE=VISUAL_READ_ONLY_CONSUMER
LANDSCAPE_AUTHORITY_EFFECT=NONE
ATLAS_ROLE=NAVIGATION_INVENTORY_ONLY
ATLAS_AUTHORITY=NONE
USP_ROLE=NON_AUTHORITY_OBSERVABILITY_READMODEL
USP_AUTHORITY_EFFECT=NONE
WEBUI_ROLE=READ_ONLY_CONSUMER
WEBUI_AUTHORITY_EFFECT=NONE
DDO_ROLE=OFFLINE_OBSERVATION_ONLY
DDO_AUTHORITY_EFFECT=NONE
PRODUCTIVE_LEARNING_AUTHORITY=NONE
PRODUCTIVE_PROMOTION_AUTHORITY=NONE
```

Bei Widerspruch zwischen dieser Map und einem kanonischen Owner gewinnt der Owner. Diese Map wird dann navigativ korrigiert — nicht die Owner-Semantik.
